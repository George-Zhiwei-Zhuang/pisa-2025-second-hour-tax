#!/usr/bin/env python3
"""Verify the pinned PISA 2025 archives before any data are read."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, sha256, write_json  # noqa: E402

EXPECTED = {
    "CY09_MS_STU_PUF.zip": (
        992_910_196,
        "ef5a76cc20215c09308a541cb3c6ee66583d068ede8535c0b735288e0a71f985",
    ),
    "CY09_MS_COG_PUF.zip": (
        224_749_839,
        "e16982bba1b3c20f4dff18256bed1ef9be2b551c5b4a552d13cbbe8ecc6a2a1d",
    ),
    "CY09_MS_LDW_PUF.zip": (
        93_184_353,
        "4ac45bfbbd99bcaa38563c21abd05901c1ab6271d2985c35ccf3029d70641b3e",
    ),
}


def main() -> int:
    logger = configure_logging("verify_data")
    raw = project_path("data", "raw")
    report = []
    for filename, (expected_size, expected_hash) in EXPECTED.items():
        path = raw / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}")
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        try:
            with zipfile.ZipFile(path) as archive:
                corrupt_member = archive.testzip()
            zip_test = "passed" if corrupt_member is None else corrupt_member
        except NotImplementedError:
            # The OECD archives currently use a compression method that some
            # Python builds cannot decompress. The system unzip utility supports
            # it and still performs a complete member/CRC check.
            completed = subprocess.run(
                ["unzip", "-tqq", str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            corrupt_member = None if completed.returncode == 0 else completed.stdout.strip()
            zip_test = "passed (system unzip)" if corrupt_member is None else corrupt_member
        passed = (
            actual_size == expected_size
            and actual_hash == expected_hash
            and corrupt_member is None
        )
        row = {
            "filename": filename,
            "bytes": actual_size,
            "sha256": actual_hash,
            "zip_test": zip_test,
            "passed": passed,
        }
        report.append(row)
        logger.info("%s: %s", filename, "passed" if passed else "FAILED")
        if not passed:
            raise RuntimeError(f"Integrity check failed: {json.dumps(row)}")
    write_json(project_path("output", "logs", "data_integrity.json"), report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
