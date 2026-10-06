#!/usr/bin/env python3
"""Estimate the preregistered-style adaptive-versus-linear science appendix."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import (  # noqa: E402
    enforce_mixed_groups,
    meta_analysis,
    standardize_columns,
    survey_pv,
    weighted_mean_sd,
)


def main() -> int:
    logger = configure_logging("adaptive_appendix")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_adaptive.parquet"))
    pv_cols = [f"PV{k}SCIE" for k in range(1, 11)]
    rows = []
    for specification in ("main", "escs_interaction"):
        for system, system_frame in frame.groupby("CNT", observed=True, sort=True):
            sample = system_frame.copy()
            if specification == "escs_interaction":
                sample = sample[sample["ESCS"].notna()].copy()
                sample = enforce_mixed_groups(sample, "design_stratum", "adaptive")
            if sample.empty:
                continue
            weight = sample["W_FSTUWT"].to_numpy(float)
            outcome = standardize_columns(sample[pv_cols].to_numpy(float), weight)
            treatment = sample["adaptive"].to_numpy(float)
            if specification == "main":
                regressors = treatment[:, None]
                coefficient_index = 0
            else:
                moderator = sample["ESCS"].to_numpy(float)
                mean, sd = weighted_mean_sd(moderator, weight)
                moderator = (moderator - mean) / sd
                regressors = np.column_stack(
                    [treatment, moderator, treatment * moderator]
                )
                coefficient_index = 2
            estimate = survey_pv(
                sample,
                outcome,
                regressors,
                sample["design_stratum"].to_numpy(),
                coefficient_index,
            )
            row = {"specification": specification, "system": system}
            row.update(estimate.to_dict())
            rows.append(row)
        logger.info("Completed adaptive specification %s", specification)
    results = pd.DataFrame(rows)
    results.to_csv(
        project_path("output", "tables", "system_adaptive_effects.csv"), index=False
    )
    summary = {}
    for specification in ("main", "escs_interaction"):
        subset = results[results["specification"] == specification]
        summary[specification] = meta_analysis(
            subset["coefficient"].to_numpy(), subset["standard_error"].to_numpy()
        )
        summary[specification]["n_students"] = int(
            frame.shape[0]
            if specification == "main"
            else sum(
                enforce_mixed_groups(
                    group[group["ESCS"].notna()].copy(), "design_stratum", "adaptive"
                ).shape[0]
                for _, group in frame.groupby("CNT", observed=True)
            )
        )
    write_json(project_path("output", "tables", "adaptive_effects.json"), summary)
    logger.info("Adaptive summary: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
