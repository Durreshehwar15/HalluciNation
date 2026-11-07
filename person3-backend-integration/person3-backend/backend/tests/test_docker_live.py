"""Opt-in real Docker tests. Require an operator-built local verifier image."""

import os
from pathlib import Path

import pytest
from app.schemas import Candidate, FileChange
from app.services.docker_runner import DockerRunner

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "1",
    reason="Set RUN_DOCKER_TESTS=1 after building trusted verifier image",
)
BASE = "a" * 40


class LocalDemoSnapshot:
    def snapshot(self, repository, sha, **kwargs):
        root = Path(__file__).resolve().parents[2] / "demo-repo"
        return {
            "app.py": (root / "app.py").read_bytes(),
            "tests/test_app.py": (root / "tests/test_app.py").read_bytes(),
        }


def make_patch(content):
    return Candidate(
        base_sha=BASE,
        summary="Trusted integration fixture",
        files=[FileChange(path="app.py", content=content)],
    )


def test_real_docker_bug_fails():
    result = DockerRunner(LocalDemoSnapshot()).verify(
        "fixture/demo", make_patch("def add(a,b):\n    return a-b\n")
    )
    assert result.status == "failed", result.output
    assert "2 failed, 1 passed" in result.output


def test_real_docker_fix_passes():
    result = DockerRunner(LocalDemoSnapshot()).verify(
        "fixture/demo", make_patch("def add(a,b):\n    return a+b\n")
    )
    assert result.status == "passed", result.output
    assert "3 passed" in result.output


def test_real_docker_infinite_candidate_times_out():
    result = DockerRunner(LocalDemoSnapshot(), timeout=3).verify(
        "fixture/demo", make_patch("while True:\n    pass\n")
    )
    assert result.status == "timeout", result.output


def test_real_docker_enforces_isolation():
    class IsolationSnapshot:
        def snapshot(self, *args, **kwargs):
            return {
                "app.py": b"",
                "tests/test_limits.py": b"""
import os
import socket
import pytest

def test_permissions_and_network():
    assert os.getuid()==65534
    assert os.getenv('GITHUB_TOKEN') is None
    assert not os.path.exists('/var/run/docker.sock')
    with pytest.raises(OSError):
        open('/workspace/forbidden', 'w')
    with pytest.raises(OSError):
        open('/etc/forbidden', 'w')
    with pytest.raises(OSError):
        socket.create_connection(('1.1.1.1',443), timeout=1)
    status=open('/proc/self/status').read()
    assert 'CapEff:\\t0000000000000000' in status
""",
            }

    result = DockerRunner(IsolationSnapshot()).verify(
        "fixture/demo", make_patch("def add(a,b):\n    return a+b\n")
    )
    assert result.status == "passed", result.output
