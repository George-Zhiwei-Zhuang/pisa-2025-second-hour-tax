#!/usr/bin/env python3
"""Estimate mirrored LDW/conventional-domain order effects and their difference."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import meta_analysis, standardize_columns, survey_pv  # noqa: E402

DOMAIN_CODE = {"science": "SCIE", "reading": "READ", "math": "MATH"}


def main() -> int:
    logger = configure_logging("comparative_advantage")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    rows = []
    summaries = {}
    for pair, domain in DOMAIN_CODE.items():
        pair_frame = frame[frame["paired_domain"] == pair]
        for system, sample in pair_frame.groupby("CNT", observed=True, sort=True):
            sample = sample.reset_index(drop=True)
            conventional_columns = [f"PV{k}{domain}" for k in range(1, 11)]
            complete = np.isfinite(sample[conventional_columns].to_numpy(float)).all(axis=1)
            sample = sample.loc[complete].copy()
            if sample.empty:
                logger.warning("Skipping %s/%s: conventional-domain PVs unavailable", pair, system)
                continue
            mixed = sample.groupby("design_stratum", observed=True)["ldw_second"].transform(
                "nunique"
            )
            sample = sample.loc[mixed.eq(2)].reset_index(drop=True)
            if sample.empty:
                logger.warning("Skipping %s/%s: no mixed complete-case stratum", pair, system)
                continue
            x = sample[["ldw_second"]].to_numpy(float)
            groups = sample["design_stratum"].to_numpy()
            weight = sample["W_FSTUWT"].to_numpy(float)
            ldw = sample[[f"PV{k}CMPS" for k in range(1, 11)]].to_numpy(float)
            conventional = sample[conventional_columns].to_numpy(float)
            estimates = {
                "ldw_points": survey_pv(sample, ldw, x, groups, 0),
                "conventional_points": survey_pv(sample, conventional, x, groups, 0),
                "gap_points": survey_pv(sample, ldw - conventional, x, groups, 0),
                "ldw_sd": survey_pv(
                    sample, standardize_columns(ldw, weight), x, groups, 0
                ),
                "conventional_sd": survey_pv(
                    sample, standardize_columns(conventional, weight), x, groups, 0
                ),
            }
            row = {"pair": pair, "paired_domain_code": domain, "system": system, "n": len(sample)}
            for name, estimate in estimates.items():
                row.update({f"{name}_{key}": value for key, value in estimate.to_dict().items()})
            rows.append(row)
        logger.info("Completed pair %s", pair)

    system_results = pd.DataFrame(rows)
    system_results.to_csv(
        project_path("output", "tables", "system_comparative_effects.csv"), index=False
    )
    for pair in DOMAIN_CODE:
        summaries[pair] = {}
        subset = system_results[system_results["pair"] == pair]
        for outcome in ("ldw_points", "conventional_points", "gap_points", "ldw_sd", "conventional_sd"):
            summaries[pair][outcome] = meta_analysis(
                subset[f"{outcome}_coefficient"].to_numpy(),
                subset[f"{outcome}_standard_error"].to_numpy(),
            )
    write_json(
        project_path("output", "tables", "comparative_effects.json"), summaries
    )
    logger.info("Comparative summaries: %s", summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
