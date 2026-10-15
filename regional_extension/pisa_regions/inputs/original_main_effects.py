#!/usr/bin/env python3
"""Estimate the LDW second-hour effect by system with PISA survey inference."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import meta_analysis, standardize_columns, survey_pv  # noqa: E402


def main() -> int:
    logger = configure_logging("main_effects")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    pv_cols = [f"PV{k}CMPS" for k in range(1, 11)]
    rows = []
    for system, sample in frame.groupby("CNT", observed=True, sort=True):
        sample = sample.reset_index(drop=True)
        y = sample[pv_cols].to_numpy(float)
        x = sample[["ldw_second"]].to_numpy(float)
        groups = sample["design_stratum"].to_numpy()
        raw = survey_pv(sample, y, x, groups, coefficient_index=0)
        standardized = survey_pv(
            sample,
            standardize_columns(y, sample["W_FSTUWT"].to_numpy(float)),
            x,
            groups,
            coefficient_index=0,
        )
        row = {"system": system, "n": len(sample)}
        row.update({f"points_{k}": v for k, v in raw.to_dict().items()})
        row.update({f"sd_{k}": v for k, v in standardized.to_dict().items()})
        rows.append(row)
        logger.info("%s: %.3f points (SE %.3f)", system, raw.coefficient, raw.standard_error)
    systems = pd.DataFrame(rows)
    systems.to_csv(project_path("output", "tables", "system_main_effects.csv"), index=False)

    results = {}
    for scale in ("points", "sd"):
        results[scale] = meta_analysis(
            systems[f"{scale}_coefficient"].to_numpy(),
            systems[f"{scale}_standard_error"].to_numpy(),
        )
        results[scale]["negative_systems"] = int(
            (systems[f"{scale}_coefficient"] < 0).sum()
        )
        results[scale]["significant_negative_systems"] = int(
            (
                (systems[f"{scale}_coefficient"] < 0)
                & (systems[f"{scale}_p_value"] < 0.05)
            ).sum()
        )
    write_json(project_path("output", "tables", "main_effects.json"), results)
    logger.info("Meta-analysis: %s", results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
