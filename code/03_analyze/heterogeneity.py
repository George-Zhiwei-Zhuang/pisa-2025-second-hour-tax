#!/usr/bin/env python3
"""Estimate prespecified learner-type heterogeneity in the LDW order effect."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import (  # noqa: E402
    benjamini_hochberg,
    enforce_mixed_groups,
    meta_analysis,
    standardize_columns,
    survey_pv,
    weighted_mean_sd,
)

MODERATORS = {
    "perseverance": ("PERSEV", False),
    "test_effort": ("EFFORT1", True),
    "digital_distraction": ("digital_distraction", False),
    "curiosity": ("CURIO", False),
    "socioeconomic_status": ("ESCS", False),
    "family_support": ("FAMSUP", False),
    "help_seeking": ("help_seeking", False),
    "self_regulation": ("SELFREG", False),
    "ai_for_learning": ("ai_for_learning", False),
    "feedback_seeking": ("feedback_seeking", False),
    "ict_feedback": ("ICTFEED", False),
    "ai_use_at_school": ("AIUSESCH", False),
}


def main() -> int:
    logger = configure_logging("heterogeneity")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    pv_cols = [f"PV{k}CMPS" for k in range(1, 11)]
    system_rows = []
    summary_rows = []
    for label, (column, post_treatment) in MODERATORS.items():
        for system, system_frame in frame.groupby("CNT", observed=True, sort=True):
            sample = system_frame[system_frame[column].notna()].copy()
            sample = enforce_mixed_groups(sample, "design_stratum", "ldw_second")
            if len(sample) < 100:
                continue
            weight = sample["W_FSTUWT"].to_numpy(float)
            moderator = sample[column].to_numpy(float)
            mean, sd = weighted_mean_sd(moderator, weight)
            if not np.isfinite(sd) or sd <= 0:
                continue
            moderator = (moderator - mean) / sd
            treatment = sample["ldw_second"].to_numpy(float)
            regressors = np.column_stack(
                [treatment, moderator, treatment * moderator]
            )
            outcome = standardize_columns(sample[pv_cols].to_numpy(float), weight)
            estimate = survey_pv(
                sample,
                outcome,
                regressors,
                sample["design_stratum"].to_numpy(),
                coefficient_index=2,
            )
            row = {
                "moderator": label,
                "variable": column,
                "post_treatment": post_treatment,
                "system": system,
            }
            row.update(estimate.to_dict())
            system_rows.append(row)
        estimates = pd.DataFrame(
            [row for row in system_rows if row["moderator"] == label]
        )
        meta = meta_analysis(
            estimates["coefficient"].to_numpy(), estimates["standard_error"].to_numpy()
        )
        summary_rows.append(
            {
                "moderator": label,
                "variable": column,
                "post_treatment": post_treatment,
                **meta,
            }
        )
        logger.info("%s: %s", label, meta)
    summary = pd.DataFrame(summary_rows)
    summary["fixed_q_value"] = benjamini_hochberg(summary["fixed_p_value"].to_numpy())
    summary["random_q_value"] = benjamini_hochberg(summary["random_p_value"].to_numpy())
    summary = summary.sort_values("fixed_p_value")
    pd.DataFrame(system_rows).to_csv(
        project_path("output", "tables", "system_heterogeneity.csv"), index=False
    )
    summary.to_csv(project_path("output", "tables", "heterogeneity.csv"), index=False)
    write_json(
        project_path("output", "tables", "heterogeneity.json"),
        summary.to_dict(orient="records"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
