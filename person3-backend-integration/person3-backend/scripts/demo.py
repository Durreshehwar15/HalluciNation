"""Reproduce the KNOWN trusted demo bug locally; never executes agent output.

Production verification uses DockerRunner, never this demonstration helper.
"""

import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "demo-repo"
command = [sys.executable, "-m", "pytest", "-q", "-o", "pythonpath=.", "tests"]
with tempfile.TemporaryDirectory(prefix="support-trusted-demo-") as root:
    shutil.copytree(
        source,
        root,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    print("BEFORE FIX (expected two regression failures)", flush=True)
    before = subprocess.run(command, cwd=root, check=False)
    if before.returncode != 1:
        raise SystemExit("Unexpected baseline result")
    # Fixed, reviewed fixture. No agent-supplied command or code is accepted.
    app_path = Path(root, "app.py")
    original = app_path.read_text()
    fixed = original.replace("return a - b", "return a + b", 1)
    if original == fixed:
        raise SystemExit("Expected demo bug not found; no code was changed")
    print("ACTUAL SOURCE DIFF", flush=True)
    print(
        "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                fixed.splitlines(keepends=True),
                fromfile="a/app.py",
                tofile="b/app.py",
            )
        ),
        end="",
        flush=True,
    )
    app_path.write_text(fixed)
    print("AFTER FIX (expected three passing tests)", flush=True)
    after = subprocess.run(command, cwd=root, check=False)
    if after.returncode != 0:
        raise SystemExit("Fixed demo failed")
print("Demo reproduced; original demo-repo/app.py remains intentionally buggy.")
