import io
import json
import subprocess
from unittest.mock import Mock, patch

import httpx
import pytest
from app.schemas import Candidate, FileChange
from app.services.docker_runner import DockerRunner
from app.services.github_service import GitHubService, IntegrationError

BASE = "a" * 40


def candidate():
    return Candidate(
        base_sha=BASE,
        summary="Fix",
        files=[FileChange(path="app.py", content="fixed\n")],
    )


@pytest.mark.parametrize(
    "path",
    [
        "../app.py",
        "/app.py",
        "a/../app.py",
        ".github/x.py",
        "tests/test_app.py",
        "x\\app.py",
        "app.sh",
        "a//app.py",
    ],
)
def test_candidate_rejects_unsafe_paths(path):
    with pytest.raises(ValueError):
        FileChange(path=path, content="")


def test_docker_fixed_command_and_limits():
    github = Mock()
    github.snapshot.return_value = {
        "app.py": b"bug\n",
        "tests/test_app.py": b"assert True\n",
    }
    process = Mock(stdout=io.BytesIO())
    process.wait.return_value = 0
    with (
        patch(
            "app.services.docker_runner.subprocess.Popen", return_value=process
        ) as run,
        patch("app.services.docker_runner.subprocess.run"),
    ):
        result = DockerRunner(github).verify("o/r", candidate())
        assert result.status == "passed"
        args = run.call_args.args[0]
        for option in [
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--memory=256m",
            "--pids-limit=64",
            "--pull=never",
        ]:
            assert option in args
        assert args[-8:] == [
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--override-ini",
            "addopts=",
            "tests",
        ]
        assert run.call_args.kwargs.get("shell", False) is False


def test_docker_timeout_cleans_container():
    gh = Mock()
    gh.snapshot.return_value = {"app.py": b"bug"}
    proc = Mock(stdout=io.BytesIO())
    proc.wait.side_effect = [subprocess.TimeoutExpired("docker", 1), 0]
    with (
        patch("app.services.docker_runner.subprocess.Popen", return_value=proc),
        patch("app.services.docker_runner.subprocess.run") as cleanup,
    ):
        result = DockerRunner(gh, timeout=1).verify("o/r", candidate())
        assert result.status == "timeout"
        proc.kill.assert_called_once()
        assert cleanup.call_args.args[0][:3] == ["docker", "rm", "-f"]


def test_github_branch_and_file():
    def handler(r):
        if "/branches/" in r.url.path:
            return httpx.Response(200, json={"commit": {"sha": BASE}})
        return httpx.Response(
            200, json={"type": "file", "encoding": "base64", "content": "YnVnCg=="}
        )

    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert gh.branch_sha("o/r", "feature/x") == BASE
    assert gh.read_file("o/r", "app.py", BASE) == "bug\n"


def test_github_api_errors_do_not_leak_tokens():
    gh = GitHubService(
        "secret",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(401, text="secret"))
        ),
    )
    with pytest.raises(IntegrationError, match="401") as e:
        gh.branch_sha("o/r", "main")
    assert "secret" not in str(e.value)


@pytest.mark.parametrize("changed_head", [False, True])
def test_publish_creates_atomic_commit_and_pr(changed_head):
    calls = []
    head = "b" * 40

    def handler(r):
        body = json.loads(r.content) if r.content else None
        calls.append((r.method, r.url.path, body))
        path = r.url.path
        if "/branches/" in path:
            return httpx.Response(200, json={"commit": {"sha": BASE}})
        if r.method == "GET" and "/git/commits/" in path:
            return httpx.Response(200, json={"tree": {"sha": "d" * 40}})
        if r.method == "GET" and path.endswith("/pulls"):
            return httpx.Response(200, json=[])
        if r.method == "GET" and "/git/ref/" in path:
            return httpx.Response(404, json={})
        if r.method == "GET" and "/git/trees/" in path:
            return httpx.Response(
                200,
                json={"tree": [{"path": "app.py", "type": "blob", "mode": "100755"}]},
            )
        if path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "e" * 40})
        if path.endswith("/git/commits"):
            return httpx.Response(201, json={"sha": head})
        if path.endswith("/git/refs"):
            return httpx.Response(201, json={})
        if r.method == "POST" and path.endswith("/pulls"):
            return httpx.Response(
                201,
                json={
                    "html_url": "https://github.com/o/r/pull/1",
                    "number": 1,
                    "head": {"sha": "f" * 40 if changed_head else head},
                },
            )
        if r.method == "PATCH" and "/pulls/" in path:
            return httpx.Response(200, json={})
        raise AssertionError(str(r.url))

    from types import SimpleNamespace

    ticket = SimpleNamespace(
        repository="o/r", branch="main", ticket_id="TICKET-001", title="Fix"
    )
    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    if changed_head:
        with pytest.raises(IntegrationError, match="head changed"):
            gh.publish(ticket, candidate())
        assert any(m == "PATCH" and b == {"state": "closed"} for m, p, b in calls)
        return
    result = gh.publish(ticket, candidate())
    assert result["number"] == 1
    tree = next(b for m, p, b in calls if m == "POST" and p.endswith("/git/trees"))
    assert tree["tree"][0]["content"] == "fixed\n"
    assert tree["tree"][0]["mode"] == "100755"
    commit = next(b for m, p, b in calls if m == "POST" and p.endswith("/git/commits"))
    assert commit["parents"] == [BASE]
    assert not any("merge" in p for _, p, _ in calls)


def test_docker_daemon_failure_is_unavailable():
    gh = Mock()
    gh.snapshot.return_value = {"app.py": b"bug"}
    proc = Mock(stdout=io.BytesIO())
    proc.wait.return_value = 125
    with (
        patch("app.services.docker_runner.subprocess.Popen", return_value=proc),
        patch("app.services.docker_runner.subprocess.run"),
    ):
        assert DockerRunner(gh).verify("o/r", candidate()).status == "unavailable"


def test_snapshot_rejects_symlinks():
    handler = lambda r: httpx.Response(
        200,
        json={
            "tree": [
                {"path": "app.py", "type": "blob", "mode": "120000", "sha": "b" * 40}
            ]
        },
    )
    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(IntegrationError, match="Symlinks"):
        gh.snapshot("o/r", BASE)


def test_snapshot_pins_base_and_preserves_tests():
    seen = []

    def handler(r):
        seen.append(r.url.path)
        if "/trees/" in r.url.path:
            return httpx.Response(
                200,
                json={
                    "tree": [
                        {
                            "path": "app.py",
                            "type": "blob",
                            "mode": "100644",
                            "sha": "b" * 40,
                            "size": 4,
                        },
                        {
                            "path": "tests/test_app.py",
                            "type": "blob",
                            "mode": "100644",
                            "sha": "c" * 40,
                            "size": 4,
                        },
                    ]
                },
            )
        return httpx.Response(200, json={"content": "YnVnCg=="})

    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert set(gh.snapshot("o/r", BASE)) == {"app.py", "tests/test_app.py"}
    assert seen[0].endswith(BASE)


def test_runner_streams_output_without_unbounded_disk_file():
    import io

    gh = Mock()
    gh.snapshot.return_value = {"app.py": b"bug"}
    proc = Mock(stdout=io.BytesIO(b"x" * 100000))
    proc.wait.return_value = 0
    with (
        patch(
            "app.services.docker_runner.subprocess.Popen", return_value=proc
        ) as launch,
        patch("app.services.docker_runner.subprocess.run"),
    ):
        result = DockerRunner(gh).verify("o/r", candidate())
        assert launch.call_args.kwargs["stdout"] == subprocess.PIPE
        assert len(result.output) == 16384


def test_snapshot_rejects_unsupported_pytest_configuration():
    gh = GitHubService(
        "test",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(
                    200,
                    json={
                        "tree": [
                            {
                                "path": "pytest.ini",
                                "type": "blob",
                                "mode": "100644",
                                "sha": "b" * 40,
                            }
                        ]
                    },
                )
            )
        ),
    )
    with pytest.raises(IntegrationError, match="configuration"):
        gh.snapshot("o/r", BASE)


def test_snapshot_uses_overall_deadline():
    def handler(r):
        assert 0 < r.extensions["timeout"]["read"] <= 2
        return httpx.Response(200, json={"tree": []})

    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(IntegrationError, match="no Python"):
        gh.snapshot("o/r", BASE, timeout=2)


def test_retry_rejects_changed_file_mode():
    patch = candidate()

    def handler(r):
        if "/git/commits/" in r.url.path:
            return httpx.Response(
                200, json={"parents": [{"sha": BASE}], "tree": {"sha": "bad-tree"}}
            )
        if "/git/trees/" in r.url.path:
            return httpx.Response(
                200,
                json={"tree": [{"path": "app.py", "type": "blob", "mode": "100755"}]},
            )
        if r.url.path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "expected-tree"})
        raise AssertionError(str(r.url))

    gh = GitHubService(
        "test", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(IntegrationError, match="approved"):
        gh._validate_commit("o/r", "b" * 40, patch)
