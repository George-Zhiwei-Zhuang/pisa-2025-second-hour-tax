#!/usr/bin/env python3
"""Write hashes for every redistributable file in the data-free package."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "MANIFEST.sha256"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "raw",
    "external",
    "interim",
    "logs",
    "processed",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
    return hasher.hexdigest()


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path == OUTPUT or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return not any(part in EXCLUDED_PARTS for part in relative.parts)


def main() -> int:
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and included(path))
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in files]
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} entries to {OUTPUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
