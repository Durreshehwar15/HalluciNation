"""Exercise nine endpoints over real HTTP, with LOCAL FIXTURE GitHub and mock Switch.

Uses real Docker tests and SQLite. Successful approval is an automated auth test
with a disposable test credential, not human authorization. PR response is fake;
no remote repository is contacted, no real credentials are read, nothing publishes.
"""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    credential = secrets.token_urlsafe(32)
    records = []
    with (
        tempfile.TemporaryDirectory(prefix="support-local-http-") as directory,
        tempfile.TemporaryFile() as log,
    ):
        env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{directory}/tickets.db",
            "HUMAN_APPROVAL_TOKEN": credential,
            "GITHUB_TOKEN": "",
            "GH_TOKEN": "",
            "PYTHONPATH": os.pathsep.join(
                [str(root / "backend"), str(root / "backend/tests")]
            ),
        }
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "http_fixture:create_test_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            with httpx.Client(
                base_url=f"http://127.0.0.1:{port}", timeout=90
            ) as client:
                deadline = time.monotonic() + 15
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Fixture Uvicorn exited during startup")
                    try:
                        if client.get("/docs").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Fixture Uvicorn startup timed out")
                    time.sleep(0.1)

                def check(method, path, expected, **kwargs):
                    response = client.request(method, path, **kwargs)
                    records.append(
                        {
                            "method": method,
                            "path": path,
                            "expected": expected,
                            "status": response.status_code,
                        }
                    )
                    if response.status_code != expected:
                        raise RuntimeError(
                            f"{method} {path}: {response.status_code}, expected {expected}: {response.text}"
                        )
                    return response.json()

                schema = client.get("/openapi.json").json()
                operations = {
                    (m.upper(), p)
                    for p, v in schema["paths"].items()
                    for m in v
                    if m in ("get", "post")
                }
                expected = {
                    ("POST", "/tickets"),
                    ("GET", "/tickets"),
                    ("GET", "/tickets/{ticket_id}"),
                }
                expected.update(
                    (method, f"/tickets/{{ticket_id}}/{name}")
                    for method, name in [
                        ("POST", "analyze"),
                        ("GET", "events"),
                        ("GET", "patch"),
                        ("POST", "approve"),
                        ("POST", "verify"),
                        ("POST", "pull-request"),
                    ]
                )
                assert operations == expected
                prefix = "/tickets/LOCAL-001"
                created = check(
                    "POST",
                    "/tickets",
                    201,
                    json={
                        "ticket_id": "LOCAL-001",
                        "title": "Addition regression",
                        "description": "add(2,3) returns -1",
                        "repository": "fixture/local-demo",
                    },
                )
                assert created["status"] == "submitted"
                assert (
                    check("GET", "/tickets", 200)["items"][0]["ticket_id"]
                    == "LOCAL-001"
                )
                assert check("GET", prefix, 200)["branch"] == "main"
                assert (
                    check("POST", prefix + "/analyze", 200)["status"] == "patch_ready"
                )
                assert any(
                    e["actor"] == "switch:mock"
                    for e in check("GET", prefix + "/events", 200)["items"]
                )
                patch = check("GET", prefix + "/patch", 200)
                assert (
                    patch["diff"].startswith("--- a/")
                    and "return a + b" in patch["files"][0]["content"]
                )
                body = {
                    "patch_hash": patch["patch_hash"],
                    "base_sha": patch["base_sha"],
                }
                auth = {"Authorization": "Bearer " + credential}
                check("POST", prefix + "/approve", 401, json=body)
                check("POST", prefix + "/pull-request", 409)
                check(
                    "POST",
                    prefix + "/approve",
                    409,
                    json={**body, "patch_hash": "0" * 64},
                    headers=auth,
                )
                verified = check("POST", prefix + "/verify", 200)
                assert verified["status"] == "passed", verified
                assert (
                    verified["patch_hash"] == patch["patch_hash"]
                    and verified["base_sha"] == patch["base_sha"]
                )
                approved = check(
                    "POST", prefix + "/approve", 200, json=body, headers=auth
                )
                assert approved["approved_by"] == "test-fixture"
                pr = check("POST", prefix + "/pull-request", 200, headers=auth)
                assert pr["url"].startswith("https://example.invalid/MOCK-")
                assert check("GET", prefix, 200)["status"] == "pr_created"
                check("POST", prefix + "/analyze", 409)
                check("GET", "/tickets/missing", 404)
                check("POST", "/tickets", 422, json={"title": "incomplete"})
                result = {
                    "passed": True,
                    "real": [
                        "Uvicorn HTTP",
                        "FastAPI",
                        "SQLite",
                        "Docker verification",
                    ],
                    "mocked": [
                        "GitHub branch/file/snapshot/PR fixture",
                        "Switch analysis",
                    ],
                    "approval": "Disposable test credential; not real human approval",
                    "remote_operations": "None. No GitHub credentials used or repositories accessed.",
                    "verification": verified,
                    "checks": records,
                }
                output = json.dumps(result, indent=2) + "\n"
                if args.output:
                    args.output.write_text(output)
                print(output, end="")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
