"""Nine real HTTP checks with GitHub reads and Docker; never grants approval or publishes.

Requires a token and an existing branch containing demo-repo. Switch is explicitly
mocked. Successful approval/publishing are covered separately by test_api.py with
fake external services, not claimed as live integration here.
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
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("Unavailable: set GITHUB_TOKEN; no mocked fallback is used.")
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="support-live-api-") as directory:
        env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{directory}/tickets.db",
            "GITHUB_TOKEN": token,
            "MOCK_PATCH_PATH": "demo-repo/app.py",
            "VERIFIER_PROJECT_DIR": "demo-repo",
            # Provision a credential only to exercise missing-auth rejection.
            # The script never uses it to approve or publish anything.
            "HUMAN_APPROVAL_TOKEN": secrets.token_urlsafe(32),
        }
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--app-dir",
                    "backend",
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
                            raise RuntimeError("Uvicorn exited during startup")
                        try:
                            if client.get("/openapi.json").status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Uvicorn startup timed out")
                        time.sleep(0.1)

                    def check(method, path, expected, **kwargs):
                        response = client.request(method, path, **kwargs)
                        records.append(
                            {
                                "method": method,
                                "path": path,
                                "status": response.status_code,
                                "expected": expected,
                            }
                        )
                        if response.status_code != expected:
                            raise RuntimeError(
                                f"{method} {path}: HTTP {response.status_code}, expected {expected}: {response.text}"
                            )
                        return response.json()

                    prefix = "/tickets/HTTP-LIVE-001"
                    check(
                        "POST",
                        "/tickets",
                        201,
                        json={
                            "ticket_id": "HTTP-LIVE-001",
                            "title": "Demo addition regression",
                            "description": "add(2,3) returns -1",
                            "repository": args.repository,
                            "branch": args.branch,
                        },
                    )
                    assert len(check("GET", "/tickets", 200)["items"]) == 1
                    assert check("GET", prefix, 200)["status"] == "submitted"
                    assert (
                        check("POST", prefix + "/analyze", 200)["status"]
                        == "patch_ready"
                    )
                    assert any(
                        e["actor"] == "switch:mock"
                        for e in check("GET", prefix + "/events", 200)["items"]
                    )
                    patch = check("GET", prefix + "/patch", 200)
                    check(
                        "POST",
                        prefix + "/approve",
                        401,
                        json={
                            "patch_hash": patch["patch_hash"],
                            "base_sha": patch["base_sha"],
                        },
                    )
                    verification = check("POST", prefix + "/verify", 200)
                    assert verification["status"] == "passed", verification
                    assert verification["patch_hash"] == patch["patch_hash"]
                    assert verification["base_sha"] == patch["base_sha"]
                    check("POST", prefix + "/pull-request", 409)
                    result = {
                        "passed": True,
                        "repository": args.repository,
                        "branch": args.branch,
                        "base_sha": patch["base_sha"],
                        "patch_hash": patch["patch_hash"],
                        "real": [
                            "Uvicorn HTTP",
                            "FastAPI",
                            "SQLite",
                            "GitHub reads/snapshot",
                            "Docker verification",
                        ],
                        "mocked": ["Switch analysis"],
                        "not_executed": [
                            "human approval",
                            "GitHub candidate publishing",
                            "Mattermost",
                        ],
                        "verification": verification,
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
