#!/usr/bin/env python3
"""Extract assignment-path fields needed for the adaptive-science appendix."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyspssio import read_metadata, read_sav

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, existing, project_path, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=project_path("data", "processed", "cognitive")
    )
    parser.add_argument("--chunksize", type=int, default=100_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = configure_logging("prepare_cognitive")
    metadata = read_metadata(str(args.input))
    requested = [
        "CNT",
        "CNTRYID",
        "CNTSCHID",
        "CNTSTUID",
        "STRATUM",
        "BOOKID",
        "Option_LDW",
        "SPATH",
        "SCORE_ItemSet",
        "SCORE_TEST",
        "SS1_ItemSet",
        "SS1_TEST",
        "SS1_LEV",
        "SS2_ItemSet",
        "SS2_TEST",
        "SS2_LEV",
    ]
    usecols = existing(requested, metadata["var_names"])
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    rows = 0
    compact_parts = []
    reader = read_sav(
        str(args.input),
        usecols=usecols,
        include_user_missing=False,
        data_only=True,
        chunksize=args.chunksize,
    )
    for index, chunk in enumerate(reader):
        for column in ("CNT", "CNTSCHID", "CNTSTUID", "STRATUM", "SPATH"):
            if column in chunk:
                chunk[column] = chunk[column].astype("string")
        for column in chunk.columns.difference(["CNT", "CNTSCHID", "CNTSTUID", "STRATUM", "SPATH"]):
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype(float)
        pq.write_table(
            pa.Table.from_pandas(chunk, preserve_index=False),
            args.output / f"part-{index:03d}.parquet",
            compression="zstd",
            compression_level=8,
        )
        compact_parts.append(chunk)
        rows += len(chunk)
        logger.info("Wrote cognitive chunk %s (%s rows)", index, len(chunk))
    compact = pd.concat(compact_parts, ignore_index=True)
    pq.write_table(
        pa.Table.from_pandas(compact, preserve_index=False),
        args.output / "cognitive.parquet",
        compression="zstd",
        compression_level=8,
    )
    write_json(
        args.output / "_metadata.json",
        {
            "source": args.input.name,
            "rows": rows,
            "columns": usecols,
            "spath_value_labels": metadata["var_value_labels"].get("SPATH", {}),
        },
    )
    (args.output / "_SUCCESS").touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
