#!/usr/bin/env python3
"""Download the official PISA 2025 public-use files with range retries.

The OECD asks PUF users to accept its terms and provide research information.
Run this script only after reviewing the PUF access page and pass
``--accept-oecd-terms`` to record that acknowledgement locally.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    key: str
    filename: str
    url: str
    expected_bytes: int
    expected_sha256: str


SOURCES = {
    source.key: source
    for source in (
        Source(
            "student",
            "CY09_MS_STU_PUF.zip",
            "https://webfs.oecd.org/pisa2022/2025/CY09_MS_STU_PUF.zip",
            992_910_196,
            "ef5a76cc20215c09308a541cb3c6ee66583d068ede8535c0b735288e0a71f985",
        ),
        Source(
            "cognitive",
            "CY09_MS_COG_PUF.zip",
            "https://webfs.oecd.org/pisa2022/2025/CY09_MS_COG_PUF.zip",
            224_749_839,
            "e16982bba1b3c20f4dff18256bed1ef9be2b551c5b4a552d13cbbe8ecc6a2a1d",
        ),
        Source(
            "ldw",
            "CY09_MS_LDW_PUF.zip",
            "https://webfs.oecd.org/pisa2022/2025/CY09_MS_LDW_PUF.zip",
            93_184_353,
            "4ac45bfbbd99bcaa38563c21abd05901c1ab6271d2985c35ccf3029d70641b3e",
        ),
    )
}


def sha256(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def download_part(
    source: Source,
    part_path: Path,
    start: int,
    end: int,
    retries: int,
) -> dict[str, int | str]:
    expected = end - start + 1
    if part_path.is_file() and part_path.stat().st_size == expected:
        return {"part": part_path.name, "bytes": expected, "status": "reused"}
    if part_path.exists():
        part_path.unlink()

    request = urllib.request.Request(
        source.url,
        headers={
            "Range": f"bytes={start}-{end}",
            "User-Agent": "PISA-2025-replication/1.0",
        },
    )
    for attempt in range(1, retries + 1):
        temporary = part_path.with_suffix(part_path.suffix + ".tmp")
        try:
            with urllib.request.urlopen(
                request, timeout=180, context=ssl_context()
            ) as response, temporary.open("wb") as output:
                status = getattr(response, "status", None)
                if status != 206:
                    raise RuntimeError(f"range request returned HTTP {status}")
                shutil.copyfileobj(response, output, length=1024 * 1024)
            actual = temporary.stat().st_size
            if actual != expected:
                raise RuntimeError(
                    f"part {part_path.name}: expected {expected} bytes, received {actual}"
                )
            temporary.replace(part_path)
            return {"part": part_path.name, "bytes": actual, "status": "downloaded"}
        except (OSError, RuntimeError, urllib.error.URLError) as error:
            temporary.unlink(missing_ok=True)
            if attempt == retries:
                raise RuntimeError(
                    f"failed {source.key} bytes {start}-{end} after {retries} attempts"
                ) from error
            time.sleep(min(2**attempt, 20))
    raise AssertionError("unreachable")


def download_source(
    source: Source,
    raw_dir: Path,
    workers: int,
    chunk_bytes: int,
    retries: int,
) -> dict[str, int | str]:
    destination = raw_dir / source.filename
    if destination.is_file() and destination.stat().st_size == source.expected_bytes:
        checksum = sha256(destination)
        if checksum != source.expected_sha256:
            raise RuntimeError(
                f"{destination} has the expected size but checksum {checksum}; "
                f"the pinned release checksum is {source.expected_sha256}"
            )
        return {
            "key": source.key,
            "filename": source.filename,
            "bytes": source.expected_bytes,
            "sha256": checksum,
            "status": "reused",
        }
    if destination.exists():
        raise RuntimeError(
            f"{destination} exists but has the wrong size; move it aside before rerunning"
        )

    part_dir = raw_dir / ".parts" / source.key
    part_dir.mkdir(parents=True, exist_ok=True)
    ranges: list[tuple[Path, int, int]] = []
    for index, start in enumerate(range(0, source.expected_bytes, chunk_bytes)):
        end = min(start + chunk_bytes - 1, source.expected_bytes - 1)
        ranges.append((part_dir / f"part-{index:05d}", start, end))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                download_part,
                source,
                part_path,
                start,
                end,
                retries,
            )
            for part_path, start, end in ranges
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    assembling = destination.with_suffix(destination.suffix + ".assembling")
    with assembling.open("wb") as output:
        for part_path, _, _ in ranges:
            with part_path.open("rb") as stream:
                shutil.copyfileobj(stream, output, length=8 * 1024 * 1024)
    if assembling.stat().st_size != source.expected_bytes:
        raise RuntimeError(f"assembled {source.key} file has the wrong size")
    assembling.replace(destination)
    shutil.rmtree(part_dir)
    checksum = sha256(destination)
    if checksum != source.expected_sha256:
        raise RuntimeError(
            f"Downloaded {source.key} checksum {checksum}; expected {source.expected_sha256}"
        )
    return {
        "key": source.key,
        "filename": source.filename,
        "bytes": source.expected_bytes,
        "sha256": checksum,
        "status": "downloaded",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir", type=Path, default=Path("data/raw"), help="raw-data directory"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        choices=tuple(SOURCES),
        default=list(SOURCES),
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk-mib", type=int, default=16)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--accept-oecd-terms", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.accept_oecd_terms:
        raise SystemExit(
            "Review https://survey.oecd.org/index.php?r=survey/index&sid=197663 "
            "and rerun with --accept-oecd-terms."
        )
    if args.workers < 1 or args.chunk_mib < 1 or args.retries < 1:
        raise SystemExit("workers, chunk-mib, and retries must be positive")
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    results = [
        download_source(
            SOURCES[key],
            args.raw_dir,
            args.workers,
            args.chunk_mib * 1024 * 1024,
            args.retries,
        )
        for key in args.files
    ]
    manifest_path = args.raw_dir / "download_manifest.json"
    previous = {}
    if manifest_path.exists():
        try:
            previous = {
                row["key"]: row
                for row in json.loads(manifest_path.read_text(encoding="utf-8")).get(
                    "sources", []
                )
            }
        except (json.JSONDecodeError, KeyError, TypeError):
            previous = {}
    previous.update({row["key"]: row for row in results})
    manifest_path.write_text(
        json.dumps(
            {
                "sources": [previous[key] for key in sorted(previous)],
                "terms_acknowledged": True,
                "downloaded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "python": os.sys.version,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"manifest": str(manifest_path), "sources": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
