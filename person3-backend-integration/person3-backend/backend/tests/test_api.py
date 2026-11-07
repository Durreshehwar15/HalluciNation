import pytest
from app.main import create_app
from app.services.docker_runner import VerificationResult
from fastapi.testclient import TestClient

BASE = "a" * 40


class GitHubFake:
    def __init__(self):
        self.sha = BASE
        self.calls = 0

    def branch_sha(self, repository, branch):
        return self.sha

    def read_file(self, repository, path, sha):
        return "def add(a, b):\n    return a - b\n"

    def publish(self, ticket, patch):
        self.calls += 1
        return {
            "url": "https://github.com/o/r/pull/1",
            "number": 1,
            "head_sha": "b" * 40,
            "branch": "fix/" + ticket.ticket_id,
        }


class RunnerFake:
    def verify(self, repository, patch):
        return VerificationResult(status="passed", exit_code=0, output="1 passed")


@pytest.fixture
def setup(tmp_path):
    github = GitHubFake()
    app = create_app(
        database_url=f"sqlite:///{tmp_path}/test.db",
        human_token="human-secret",
        human_identity="reviewer",
        github=github,
        runner=RunnerFake(),
    )
    with TestClient(app) as client:
        yield client, github, app


def ticket(client):
    response = client.post(
        "/tickets",
        json={
            "ticket_id": "TICKET-001",
            "title": "Login failure",
            "description": "Correct password returns error",
            "repository": "o/r",
            "priority": "high",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def analyze(client):
    ticket(client)
    r = client.post("/tickets/TICKET-001/analyze")
    assert r.status_code == 200, r.text
    return client.get("/tickets/TICKET-001/patch").json()


def test_ticket_persistence_and_errors(setup):
    c, _, _ = setup
    assert ticket(c)["status"] == "submitted"
    assert len(c.get("/tickets").json()["items"]) == 1
    assert c.get("/tickets/TICKET-001").json()["branch"] == "main"
    assert c.get("/tickets/missing").status_code == 404
    assert c.post("/tickets", json={"title": "x"}).status_code == 422
    assert (
        c.post(
            "/tickets",
            json={
                "ticket_id": "TICKET-001",
                "title": "x",
                "description": "x",
                "repository": "o/r",
            },
        ).status_code
        == 409
    )


def test_full_workflow_with_preapproval_verification(setup):
    c, gh, _ = setup
    patch = analyze(c)
    assert patch["base_sha"] == BASE
    assert patch["diff"].startswith("--- a/")
    assert any(
        e["actor"] == "switch:mock"
        for e in c.get("/tickets/TICKET-001/events").json()["items"]
    )
    assert c.post("/tickets/TICKET-001/verify").json()["status"] == "passed"
    assert c.post("/tickets/TICKET-001/pull-request").status_code == 409
    body = {"patch_hash": patch["patch_hash"], "base_sha": BASE}
    assert c.post("/tickets/TICKET-001/approve", json=body).status_code == 401
    assert (
        c.post(
            "/tickets/TICKET-001/approve",
            json=body,
            headers={"Authorization": "Bearer agent"},
        ).status_code
        == 401
    )
    assert (
        c.post(
            "/tickets/TICKET-001/approve",
            json=body,
            headers={"Authorization": "Bearer human-secret"},
        ).status_code
        == 200
    )
    r = c.post(
        "/tickets/TICKET-001/pull-request",
        headers={"Authorization": "Bearer human-secret"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["number"] == 1
    assert (
        c.post(
            "/tickets/TICKET-001/pull-request",
            headers={"Authorization": "Bearer human-secret"},
        ).status_code
        == 200
    )
    assert gh.calls == 1
    assert c.post("/tickets/TICKET-001/analyze").status_code == 409


def test_stale_approval_and_base_rejected(setup):
    c, gh, _ = setup
    patch = analyze(c)
    auth = {"Authorization": "Bearer human-secret"}
    body = {"patch_hash": "0" * 64, "base_sha": BASE}
    assert (
        c.post("/tickets/TICKET-001/approve", json=body, headers=auth).status_code
        == 409
    )
    body["patch_hash"] = patch["patch_hash"]
    assert (
        c.post("/tickets/TICKET-001/approve", json=body, headers=auth).status_code
        == 200
    )
    c.post("/tickets/TICKET-001/verify")
    gh.sha = "c" * 40
    assert c.post("/tickets/TICKET-001/pull-request", headers=auth).status_code == 409
    assert gh.calls == 0


def test_invalid_transitions(setup):
    c, _, _ = setup
    ticket(c)
    assert c.get("/tickets/TICKET-001/patch").status_code == 409
    assert c.post("/tickets/TICKET-001/verify").status_code == 409
    assert c.post("/tickets/TICKET-001/pull-request").status_code == 409
    assert c.post("/tickets/TICKET-001/analyze").status_code == 200
    assert c.post("/tickets/TICKET-001/analyze").status_code == 409


def test_verification_failure_blocks_publication(setup):
    c, gh, app = setup
    patch = analyze(c)
    app.state.runner.verify = lambda *args: VerificationResult(
        status="failed", exit_code=1, output="regression"
    )
    assert c.post("/tickets/TICKET-001/verify").json()["status"] == "failed"
    auth = {"Authorization": "Bearer human-secret"}
    assert (
        c.post(
            "/tickets/TICKET-001/approve",
            json={"patch_hash": patch["patch_hash"], "base_sha": BASE},
            headers=auth,
        ).status_code
        == 200
    )
    assert c.post("/tickets/TICKET-001/pull-request", headers=auth).status_code == 409
    assert gh.calls == 0


def test_agent_cannot_submit_approval_fields(setup):
    c, _, _ = setup
    body = {
        "title": "x",
        "description": "x",
        "repository": "o/r",
        "status": "approved",
        "approved_by": "agent",
    }
    assert c.post("/tickets", json=body).status_code == 422


def test_credentials_fail_closed(setup):
    c, _, app = setup
    patch = analyze(c)
    app.state.human_token = ""
    assert (
        c.post(
            "/tickets/TICKET-001/approve",
            json={"patch_hash": patch["patch_hash"], "base_sha": BASE},
        ).status_code
        == 503
    )


def test_analysis_failure_is_persisted_and_retryable(setup):
    from app.services.github_service import IntegrationError

    c, gh, _ = setup
    ticket(c)
    original = gh.branch_sha

    def failed(*args):
        raise IntegrationError("GitHub unavailable")

    gh.branch_sha = failed
    assert c.post("/tickets/TICKET-001/analyze").status_code == 502
    assert c.get("/tickets/TICKET-001").json()["status"] == "analysis_failed"
    gh.branch_sha = original
    assert c.post("/tickets/TICKET-001/analyze").json()["status"] == "patch_ready"


def test_verification_does_not_block_other_ticket_writes(setup):
    import threading
    import time

    c, _, app = setup
    analyze(c)
    started, release = threading.Event(), threading.Event()

    def slow(*args):
        started.set()
        release.wait(1)
        return VerificationResult(status="passed", exit_code=0)

    app.state.runner.verify = slow
    worker = threading.Thread(target=lambda: c.post("/tickets/TICKET-001/verify"))
    worker.start()
    assert started.wait(2)
    try:
        before = time.monotonic()
        response = c.post(
            "/tickets",
            json={"title": "Other", "description": "Other", "repository": "o/r"},
        )
        elapsed = time.monotonic() - before
        assert response.status_code == 201
        assert elapsed < 0.5
    finally:
        release.set()
        worker.join(3)


def test_unexpected_adapter_failure_is_safe_and_retryable(setup):
    c, _, app = setup
    ticket(c)

    def fail(*args):
        raise RuntimeError("provider-secret-should-not-leak")

    app.state.switch.analyze = fail
    response = c.post("/tickets/TICKET-001/analyze")
    assert response.status_code == 502
    assert "provider-secret" not in response.text
    assert c.get("/tickets/TICKET-001").json()["status"] == "analysis_failed"


def test_non_ascii_authorization_is_rejected_without_server_error(setup):
    c, _, _ = setup
    patch = analyze(c)
    response = c.post(
        "/tickets/TICKET-001/approve",
        json={"patch_hash": patch["patch_hash"], "base_sha": BASE},
        headers={b"Authorization": b"Bearer \xff"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "401"
