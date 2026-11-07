"""Validate the transfer artifact without any real credentials or remote calls."""

import subprocess
import sys
import zipfile
from pathlib import Path


def test_package_preserves_layout_and_excludes_secrets_and_outputs(tmp_path):
    root = tmp_path / "source"
    files = {
        "INTEGRATION.md": "Manual transfer instructions",
        "backend/app/main.py": "# fixture source\n",
        "backend/requirements.txt": "fastapi\n",
        "backend/pytest.ini": "[pytest]\npythonpath = .\n",
        "backend/.env.example": "GITHUB_TOKEN=\n",
        "backend/.env": "GITHUB_TOKEN=not-a-real-token-do-not-package\n",
        "backend/local.sqlite3": "runtime database",
        "backend/tickets.db-wal": "runtime journal",
        "backend/.venv/lib/private.py": "do not package",
        "backend/__pycache__/private.pyc": "do not package",
        "backend/.git/config": "do not package",
        "demo-repo/app.py": "# buggy fixture\n",
        "scripts/demo.py": "# fixture demo\n",
        "docs/frontend-integration.md": "Frontend contract",
        "docs/test-results.txt": "temporary output",
        "docs/live-api-validation.json": "temporary output",
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (root / "backend/app/link.py").symlink_to(root / "backend/.env")
    output = tmp_path / "handoff.zip"
    script = Path(__file__).resolve().parents[2] / "scripts/package_integration.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source-root",
            str(root),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(output) as bundle:
        names = set(bundle.namelist())
        assert "person3-backend/INTEGRATION.md" in names
        assert "person3-backend/backend/pytest.ini" in names
        assert "person3-backend/demo-repo/app.py" in names
        assert "person3-backend/scripts/demo.py" in names
        assert bundle.read("person3-backend/.env.example") == b"GITHUB_TOKEN=\n"
        for name in names:
            assert not any(
                part in {".git", ".venv", "__pycache__"} for part in Path(name).parts
            )
            assert Path(name).name not in {
                ".env",
                "test-results.txt",
                "live-api-validation.json",
                "link.py",
            }
            assert not name.endswith((".sqlite3", ".db-wal", ".pyc"))
        assert all(
            b"not-a-real-token-do-not-package" not in bundle.read(name)
            for name in names
        )


def test_package_rejects_populated_example_credentials(tmp_path):
    root = tmp_path / "source"
    (root / "backend").mkdir(parents=True)
    (root / "INTEGRATION.md").write_text("Guide")
    (root / "backend/.env.example").write_text("GITHUB_TOKEN=fictional-secret-value\n")
    output = tmp_path / "unsafe.zip"
    script = Path(__file__).resolve().parents[2] / "scripts/package_integration.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source-root",
            str(root),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode != 0
    assert not output.exists()
    assert "fictional-secret-value" not in result.stdout + result.stderr
