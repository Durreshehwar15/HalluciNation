"""Untrusted Python runs only inside an operator-built, restricted Docker image."""

import os
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

from pydantic import BaseModel

from .github_service import IntegrationError


class VerificationResult(BaseModel):
    status: str
    exit_code: int | None = None
    output: str = ""
    patch_hash: str | None = None
    base_sha: str | None = None


class DockerRunner:
    def __init__(
        self, github, image="support-fix-verifier:local", timeout=60, project_dir=""
    ):
        self.github, self.image, self.timeout = github, image, timeout
        if project_dir and (
            Path(project_dir).is_absolute()
            or ".." in Path(project_dir).parts
            or "," in project_dir
        ):
            raise ValueError("Invalid verifier project directory")
        self.project_dir = project_dir

    def verify(self, repository, patch):
        deadline = time.monotonic() + self.timeout
        name = "support-verify-" + uuid.uuid4().hex
        try:
            with tempfile.TemporaryDirectory(prefix="support-verify-") as root:
                # Snapshot comes from the pinned base, never the branch's moving HEAD.
                files = self.github.snapshot(
                    repository,
                    patch.base_sha,
                    timeout=min(self.timeout, 20),
                    root=self.project_dir,
                )
                for change in patch.files:
                    if change.path not in files:
                        raise IntegrationError(
                            "Candidate may only replace existing source files"
                        )
                    files[change.path] = change.content.encode()
                os.chmod(root, 0o755)
                for path, content in files.items():
                    target = Path(root, path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    target.chmod(0o644)
                for directory in Path(root).rglob("*"):
                    if directory.is_dir():
                        directory.chmod(0o755)
                command = [
                    "docker",
                    "run",
                    "--rm",
                    "--pull=never",
                    "--name",
                    name,
                    "--network=none",
                    "--read-only",
                    "--user=65534:65534",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "--memory=256m",
                    "--memory-swap=256m",
                    "--cpus=1",
                    "--pids-limit=64",
                    "--ulimit",
                    "nofile=256:256",
                    "--log-driver=none",
                    "--tmpfs",
                    "/tmp:rw,noexec,nosuid,size=32m",
                    "--mount",
                    f"type=bind,src={root},dst=/workspace,readonly",
                    "--workdir",
                    "/workspace" + ("/" + self.project_dir if self.project_dir else ""),
                    "--env",
                    "PYTHONDONTWRITEBYTECODE=1",
                    "--env",
                    "PYTHONPATH=/workspace",
                    "--entrypoint",
                    "python",
                    self.image,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--override-ini",
                    "addopts=",
                    "tests",
                ]
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                captured = bytearray()

                def drain():
                    while chunk := process.stdout.read(4096):
                        captured.extend(chunk[: max(0, 16384 - len(captured))])

                reader = threading.Thread(target=drain, daemon=True)
                reader.start()
                try:
                    code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    return VerificationResult(
                        status="timeout", output="Verification exceeded its deadline"
                    )
                finally:
                    reader.join(timeout=2)
                    process.stdout.close()
                text = captured.decode(errors="replace")
                status = (
                    "passed"
                    if code == 0
                    else ("unavailable" if code in (125, 126, 127) else "failed")
                )
                return VerificationResult(status=status, exit_code=code, output=text)
        except (FileNotFoundError, OSError) as exc:
            return VerificationResult(
                status="unavailable", output=f"Docker unavailable: {type(exc).__name__}"
            )
        finally:
            try:
                subprocess.run(
                    ["docker", "rm", "-f", name],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
