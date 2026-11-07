"""Real HTTP smoke test with restart/persistence; no external credentials needed."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{directory}/smoke.db",
        "GITHUB_TOKEN": "",
    }

    def start():
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
                "8765",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Uvicorn failed to start")
            try:
                if (
                    httpx.get("http://127.0.0.1:8765/docs", timeout=1).status_code
                    == 200
                ):
                    return process
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError("Uvicorn startup deadline exceeded")

    process = start()
    try:
        with httpx.Client(base_url="http://127.0.0.1:8765") as client:
            response = client.post(
                "/tickets",
                json={
                    "ticket_id": "SMOKE-001",
                    "title": "Smoke",
                    "description": "Persistence test",
                    "repository": "o/r",
                },
            )
            assert response.status_code == 201, response.text
            schema = client.get("/openapi.json").json()
            assert sum(len(v) for k, v in schema["paths"].items()) == 9
            assert client.post("/tickets/SMOKE-001/analyze").status_code == 502
    finally:
        process.terminate()
        process.wait(timeout=5)
    process = start()
    try:
        ticket = httpx.get("http://127.0.0.1:8765/tickets/SMOKE-001").json()
        assert ticket["status"] == "analysis_failed"
        print(
            "Real Uvicorn HTTP smoke: 9 OpenAPI operations, ticket creation, safe integration error, SQLite restart persistence: PASS"
        )
    finally:
        process.terminate()
        process.wait(timeout=5)
