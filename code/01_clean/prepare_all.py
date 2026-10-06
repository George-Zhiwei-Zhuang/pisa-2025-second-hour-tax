#!/usr/bin/env python3
"""Extract each large archive temporarily and run its converter in sequence."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path  # noqa: E402

SOURCES = (
    ("CY09_MS_STU_PUF.zip", "CY09_MS_STU_PUF.sav", "prepare_student.py"),
    ("CY09_MS_LDW_PUF.zip", "CY09_MS_LDW_20260806.sav", "prepare_ldw.py"),
    ("CY09_MS_COG_PUF.zip", "CY09_MS_COG_20260806.sav", "prepare_cognitive.py"),
)


def extract_member(archive_path: Path, member: str, destination: Path) -> None:
    """Extract one member, falling back for newer ZIP compression methods."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            archive.extract(member, destination)
    except NotImplementedError:
        (destination / member).unlink(missing_ok=True)
        subprocess.run(
            ["unzip", "-qq", "-o", str(archive_path), member, "-d", str(destination)],
            check=True,
        )


def main() -> int:
    logger = configure_logging("prepare_all")
    raw = project_path("data", "raw")
    converter_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="pisa2025_second_hour_") as temporary:
        temporary_root = Path(temporary)
        for archive_name, sav_name, converter_name in SOURCES:
            extraction_dir = temporary_root / Path(archive_name).stem
            extraction_dir.mkdir()
            archive_path = raw / archive_name
            logger.info("Extracting %s", archive_name)
            extract_member(archive_path, sav_name, extraction_dir)
            logger.info("Converting %s", sav_name)
            subprocess.run(
                [
                    sys.executable,
                    str(converter_dir / converter_name),
                    "--input",
                    str(extraction_dir / sav_name),
                ],
                check=True,
                cwd=project_path(),
            )
    logger.info("All three public-use files converted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
