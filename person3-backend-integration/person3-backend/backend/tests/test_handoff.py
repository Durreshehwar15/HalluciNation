"""Prove the backend can be copied without the repository's root configuration."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_copied_backend_collects_without_root_pytest_config(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    copied = tmp_path / "backend"
    shutil.copytree(
        backend,
        copied,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.db"),
    )
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [str(Path(sys.executable).with_name("pytest")), "--collect-only", "-q"],
        cwd=copied,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests/test_api.py::test_ticket_persistence_and_errors" in result.stdout
    assert "tests/test_docker_live.py::test_real_docker_fix_passes" in result.stdout
