#!/usr/bin/env python3
"""Convert the PISA 2025 student SPSS PUF to compact, typed Parquet parts."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyspssio import read_metadata, read_sav

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, existing, project_path, write_json  # noqa: E402

IDS = [
    "CNT",
    "CNTRYID",
    "CNTSCHID",
    "CNTSTUID",
    "STRATUM",
    "SUBNATIO",
    "REGION",
    "OECD",
    "ADMINMODE",
    "BOOKID",
    "Option_LDW",
    "Option_UH",
]
COVARIATES = [
    "AGE",
    "ST004D01T",
    "IMMIG",
    "PAREDINT",
    "HISEI",
    "HOMEPOS",
    "ESCS",
]
MODERATORS = [
    "PERSEV",
    "CURIO",
    "SELFREG",
    "FAMSUP",
    "EFFORT1",
    "AIUSESCH",
    "ICTFEED",
    "ST097Q06DA",
    "ST433Q02DA",
    "ST433Q04DA",
    "ST433Q06DA",
    "ST434Q03DA",
    "ST438Q04DA",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=project_path("data", "processed", "student")
    )
    parser.add_argument("--chunksize", type=int, default=100_000)
    return parser.parse_args()


def clean_chunk(chunk: pd.DataFrame, ordered_columns: list[str]) -> pd.DataFrame:
    for column in ordered_columns:
        if column not in chunk:
            chunk[column] = np.nan
    chunk = chunk[ordered_columns].copy()

    string_columns = ["CNT", "CNTSCHID", "CNTSTUID", "STRATUM", "SUBNATIO", "REGION"]
    for column in string_columns:
        if column in chunk:
            chunk[column] = chunk[column].astype("string")

    for column in chunk.columns.difference(string_columns):
        chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype("float64")

    chunk["female"] = np.where(
        chunk["ST004D01T"].isin([1.0, 2.0]),
        (chunk["ST004D01T"] == 1.0).astype(float),
        np.nan,
    )
    chunk["immigrant"] = np.where(
        chunk["IMMIG"].isin([1.0, 2.0, 3.0]),
        chunk["IMMIG"].isin([2.0, 3.0]).astype(float),
        np.nan,
    )
    chunk["digital_distraction"] = 5.0 - chunk["ST097Q06DA"]
    help_items = pd.concat(
        [5.0 - chunk[name] for name in ("ST433Q02DA", "ST433Q04DA", "ST433Q06DA")],
        axis=1,
    )
    chunk["help_seeking"] = help_items.mean(axis=1, skipna=True)
    chunk.loc[help_items.notna().sum(axis=1) < 2, "help_seeking"] = np.nan
    chunk["feedback_seeking"] = chunk["ST434Q03DA"]
    chunk["ai_for_learning"] = chunk["ST438Q04DA"]
    return chunk


def main() -> int:
    args = parse_args()
    logger = configure_logging("prepare_student")
    metadata = read_metadata(str(args.input))
    names = metadata["var_names"]
    plausible_values = [
        f"PV{draw}{domain}"
        for domain in ("CMPS", "SCIE", "MATH", "READ")
        for draw in range(1, 11)
    ]
    weights = ["W_FSTUWT"] + [f"W_FSTURWT{draw}" for draw in range(1, 81)]
    requested = IDS + COVARIATES + MODERATORS + plausible_values + weights
    usecols = existing(requested, names)
    missing = sorted(set(requested) - set(usecols))
    if missing:
        logger.warning("Variables absent from PUF: %s", ", ".join(missing))

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    reader = read_sav(
        str(args.input),
        usecols=usecols,
        include_user_missing=False,
        data_only=True,
        chunksize=args.chunksize,
    )
    rows = 0
    for index, chunk in enumerate(reader):
        clean = clean_chunk(chunk, usecols)
        table = pa.Table.from_pandas(clean, preserve_index=False)
        target = args.output / f"part-{index:03d}.parquet"
        pq.write_table(table, target, compression="zstd", compression_level=8)
        rows += len(clean)
        logger.info("Wrote %s rows to %s", len(clean), target.name)

    write_json(
        args.output / "_metadata.json",
        {
            "source": args.input.name,
            "rows": rows,
            "columns": usecols,
            "derived": [
                "female",
                "immigrant",
                "digital_distraction",
                "help_seeking",
                "feedback_seeking",
                "ai_for_learning",
            ],
            "case_count_reported_by_spss": metadata["case_count"],
        },
    )
    (args.output / "_SUCCESS").touch()
    logger.info("Student conversion complete: %s rows", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
