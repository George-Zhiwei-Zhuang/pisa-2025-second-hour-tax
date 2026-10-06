#!/usr/bin/env python3
"""Construct student- and item-level LDW process outcomes from the LDW PUF."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyspssio import read_metadata, read_sav

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402

IDS = ["CNT", "CNTRYID", "CNTSCHID", "CNTSTUID", "BOOKID"]
VALID_CODES = np.array(["0", "1", "2", "3", "4", "5", "9", "r"], dtype=object)
CREDIT_CODES = np.array(["1", "2", "3", "4", "5"], dtype=object)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--student-output",
        type=Path,
        default=project_path("data", "processed", "ldw_student"),
    )
    parser.add_argument(
        "--item-output", type=Path, default=project_path("data", "processed", "ldw_items")
    )
    parser.add_argument("--chunksize", type=int, default=25_000)
    return parser.parse_args()


def safe_share(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(
        numerator,
        denominator,
        out=np.full(numerator.shape, np.nan, dtype=float),
        where=denominator > 0,
    )


def main() -> int:
    args = parse_args()
    logger = configure_logging("prepare_ldw")
    metadata = read_metadata(str(args.input))
    names = metadata["var_names"]
    labels = metadata["var_labels"]
    score_vars = [name for name in names if re.fullmatch(r"P\d+M\d+S", name)]
    if len(score_vars) != 48:
        raise RuntimeError(f"Expected 48 scored LDW variables, found {len(score_vars)}")
    stage_by_score = {}
    max_credit_by_score = {}
    for score in score_vars:
        label = labels.get(score, "").lower()
        stage_by_score[score] = next(
            (stage for stage in ("learn", "apply", "show") if stage in label), "other"
        )
        numeric_codes = [
            int(code)
            for code in metadata["var_value_labels"].get(score, {})
            if str(code).isdigit() and 0 <= int(code) <= 5
        ]
        max_credit_by_score[score] = max(numeric_codes)
    usecols = IDS + score_vars
    for score in score_vars:
        stem = score[:-1]
        usecols.extend([f"{stem}TT", f"{stem}A", f"{stem}F"])

    for directory in (args.student_output, args.item_output):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    reader = read_sav(
        str(args.input),
        usecols=usecols,
        include_user_missing=True,
        data_only=True,
        chunksize=args.chunksize,
    )
    rows = 0
    item_rows = 0
    for index, chunk in enumerate(reader):
        for column in ("CNT", "CNTSCHID", "CNTSTUID"):
            chunk[column] = chunk[column].astype("string")
        chunk["BOOKID"] = pd.to_numeric(chunk["BOOKID"], errors="coerce")

        score = chunk[score_vars].fillna("").astype(str).to_numpy(dtype=object)
        valid = np.isin(score, VALID_CODES)
        credit = np.isin(score, CREDIT_CODES)
        not_reached = score == "r"
        disengaged = score == "9"
        no_credit = score == "0"
        denominator = valid.sum(axis=1)
        numeric_score = np.zeros(score.shape, dtype=float)
        for value in range(1, 6):
            numeric_score[score == str(value)] = value
        max_credit = np.array([max_credit_by_score[var] for var in score_vars], dtype=float)
        score_fraction = numeric_score / max_credit[None, :]

        summary = chunk[IDS].copy()
        summary["n_items"] = denominator.astype(float)
        summary["credit_share"] = safe_share(
            np.where(valid, score_fraction, 0.0).sum(axis=1), denominator
        )
        summary["any_credit_share"] = safe_share(credit.sum(axis=1), denominator)
        summary["not_reached_share"] = safe_share(not_reached.sum(axis=1), denominator)
        summary["disengaged_share"] = safe_share(disengaged.sum(axis=1), denominator)
        summary["no_credit_share"] = safe_share(no_credit.sum(axis=1), denominator)

        for stage in ("learn", "apply", "show"):
            mask = np.array([stage_by_score[var] == stage for var in score_vars])
            stage_valid = valid[:, mask]
            stage_denominator = stage_valid.sum(axis=1)
            summary[f"{stage}_credit_share"] = safe_share(
                np.where(stage_valid, score_fraction[:, mask], 0.0).sum(axis=1),
                stage_denominator,
            )

        for suffix, output_name in (
            ("TT", "total_time"),
            ("A", "total_actions"),
            ("F", "total_first_action_time"),
        ):
            columns = [f"{score_var[:-1]}{suffix}" for score_var in score_vars]
            values = chunk[columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
            values[(values >= 99_000_000) | (~valid)] = np.nan
            summary[output_name] = np.nansum(values, axis=1)
            summary.loc[np.isfinite(values).sum(axis=1) == 0, output_name] = np.nan
        summary["mean_first_action_time"] = safe_share(
            summary["total_first_action_time"].to_numpy(float), denominator
        )
        for column in ("total_time", "total_actions", "total_first_action_time"):
            summary[f"log1p_{column}"] = np.log1p(summary[column].clip(lower=0))
        summary["log1p_mean_first_action_time"] = np.log1p(
            summary["mean_first_action_time"].clip(lower=0)
        )

        pq.write_table(
            pa.Table.from_pandas(summary, preserve_index=False),
            args.student_output / f"part-{index:03d}.parquet",
            compression="zstd",
            compression_level=8,
        )

        long_parts = []
        for position, score_var in enumerate(score_vars):
            selected = valid[:, position]
            if not selected.any():
                continue
            stem = score_var[:-1]
            long_parts.append(
                pd.DataFrame(
                    {
                        "CNTSTUID": chunk.loc[selected, "CNTSTUID"].array,
                        "item": score_var,
                        "stage": stage_by_score[score_var],
                        "credit": credit[selected, position].astype(float),
                        "score_fraction": score_fraction[selected, position].astype(float),
                        "not_reached": not_reached[selected, position].astype(float),
                        "disengaged": disengaged[selected, position].astype(float),
                        "time": pd.to_numeric(
                            chunk.loc[selected, f"{stem}TT"], errors="coerce"
                        ).to_numpy(float),
                        "actions": pd.to_numeric(
                            chunk.loc[selected, f"{stem}A"], errors="coerce"
                        ).to_numpy(float),
                        "first_action_time": pd.to_numeric(
                            chunk.loc[selected, f"{stem}F"], errors="coerce"
                        ).to_numpy(float),
                    }
                )
            )
        long = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
        for column in ("time", "actions", "first_action_time"):
            if column in long:
                long.loc[long[column] >= 99_000_000, column] = np.nan
        if not long.empty:
            pq.write_table(
                pa.Table.from_pandas(long, preserve_index=False),
                args.item_output / f"part-{index:03d}.parquet",
                compression="zstd",
                compression_level=8,
            )
        rows += len(summary)
        item_rows += len(long)
        logger.info("Chunk %s: %s students; %s administered item records", index, len(summary), len(long))

    payload = {
        "source": args.input.name,
        "students": rows,
        "administered_item_records": item_rows,
        "score_variables": score_vars,
        "stage_by_score_variable": stage_by_score,
        "max_credit_by_score_variable": max_credit_by_score,
        "status_codes": {
            "0": "no credit",
            "1-5": "partial or full credit",
            "7": "not applicable; excluded from denominator",
            "9": "disengaged",
            "r": "not reached",
        },
    }
    write_json(args.student_output / "_metadata.json", payload)
    write_json(args.item_output / "_metadata.json", payload)
    (args.student_output / "_SUCCESS").touch()
    (args.item_output / "_SUCCESS").touch()
    logger.info("LDW conversion complete: %s students; %s item records", rows, item_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
