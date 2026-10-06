#!/usr/bin/env python3
"""Build and inspect the data-free versioned replication archive."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.1.0"
PACKAGE_NAME = f"pisa_2025_second_hour_tax_replication_v{VERSION}"
FORBIDDEN_SUFFIXES = {".sav", ".parquet"}
SKIP_PARTS = {".git", ".venv", "__pycache__"}
DATA_SUBDIRS = {"raw", "external", "interim", "processed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT.parent / "deliverables"
    )
    return parser.parse_args()


def include(relative: Path) -> bool:
    if any(part in SKIP_PARTS for part in relative.parts):
        return False
    if relative.suffix in {".pyc", ".pyo"}:
        return False
    if len(relative.parts) >= 2 and relative.parts[0] == "data":
        if relative.parts[1] in DATA_SUBDIRS:
            return relative.name == ".gitkeep"
    return True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / f"{PACKAGE_NAME}.zip"
    sidecar_path = args.output_dir / f"{PACKAGE_NAME}.zip.sha256"

    with tempfile.TemporaryDirectory(prefix="pisa2025_release_") as temporary:
        stage_root = Path(temporary) / PACKAGE_NAME
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT)
            if not include(relative):
                continue
            destination = stage_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for source in sorted(stage_root.rglob("*")):
                if source.is_file():
                    archive.write(source, source.relative_to(stage_root.parent))

    with zipfile.ZipFile(archive_path) as archive:
        corrupt = archive.testzip()
        names = archive.namelist()
    if corrupt is not None:
        raise RuntimeError(f"Corrupt archive member: {corrupt}")
    forbidden = [
        name
        for name in names
        if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
        or (Path(name).suffix.lower() == ".zip" and Path(name).name.startswith("CY09_"))
    ]
    if forbidden:
        raise RuntimeError(f"Microdata leaked into release archive: {forbidden}")

    checksum = sha256(archive_path)
    sidecar_path.write_text(f"{checksum}  {archive_path.name}\n", encoding="utf-8")
    print(f"Archive: {archive_path}")
    print(f"Files: {len(names)}")
    print(f"Bytes: {archive_path.stat().st_size}")
    print(f"SHA-256: {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
