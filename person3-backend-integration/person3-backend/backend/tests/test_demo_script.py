"""Run the trusted demonstration and require an observable source change."""

import subprocess
import sys
from pathlib import Path


def test_demo_shows_real_failure_code_change_and_passing_fix():
    root = Path(__file__).resolve().parents[2]
    original = (root / "demo-repo/app.py").read_bytes()
    result = subprocess.run(
        [sys.executable, str(root / "scripts/demo.py")],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 failed, 1 passed" in result.stdout
    assert "-    return a - b" in result.stdout
    assert "+    return a + b" in result.stdout
    assert "3 passed" in result.stdout
    assert (root / "demo-repo/app.py").read_bytes() == original
