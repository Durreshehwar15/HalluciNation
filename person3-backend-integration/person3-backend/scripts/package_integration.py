"""Build a local, allowlisted Person 3 transfer ZIP. No Git/network operations."""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "pycache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "superpowers",
}
DOCS = {
    "api-contract.md",
    "integration-guide.md",
    "integration-checklist.md",
    "frontend-integration.md",
    "switch-integration.md",
    "verification.md",
}


def included(path):
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.parts[0] == "docs":
        return len(path.parts) == 2 and path.name in DOCS
    if path.parts[0] == "scripts":
        return len(path.parts) == 2 and path.suffix == ".py"
    if path.parts[0] in {"backend", "demo-repo"}:
        return path.suffix in {".py", ".md", ".ini"} or path.name in {
            "requirements.txt",
            "Dockerfile",
            ".dockerignore",
            ".env.example",
        }
    return path.as_posix() == "INTEGRATION.md"


def build(source, output):
    source = source.resolve()
    entries = {}
    for relative in ("INTEGRATION.md", "backend", "demo-repo", "scripts", "docs"):
        path = source / relative
        paths = sorted(path.rglob("*")) if path.is_dir() else [path]
        for file in paths:
            if file.is_symlink() or not file.is_file():
                continue
            name = file.relative_to(source)
            if included(name):
                entries[name.as_posix()] = file.read_bytes()
    if "INTEGRATION.md" not in entries or "backend/.env.example" not in entries:
        raise ValueError("Missing INTEGRATION.md or backend/.env.example")
    for name, data in entries.items():
        if name.endswith(".env.example"):
            for line in data.decode("utf-8").splitlines():
                if line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if re.search(
                    r"TOKEN|SECRET|PASSWORD|API_KEY", key.upper()
                ) and value.strip().strip("\"'"):
                    raise ValueError("Refusing populated credential in .env.example")
    entries[".env.example"] = entries["backend/.env.example"]
    manifest = {
        name: hashlib.sha256(data).hexdigest() for name, data in sorted(entries.items())
    }
    entries["MANIFEST.json"] = (
        json.dumps({"sha256": manifest}, indent=2) + "\n"
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo("person3-backend/" + name)
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(f"{digest}  {output.name}\n")
    print(f"Created {output}: {len(entries)} files; SHA256 {digest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source_root, args.output)


if __name__ == "__main__":
    main()
