#!/usr/bin/env python3
"""Estimate how second-hour placement changes LDW response and process behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import meta_analysis, survey_observed  # noqa: E402

OUTCOMES = {
    "item_exposure": "n_items",
    "credit_assigned": "credit_share",
    "learn_credit": "learn_credit_share",
    "apply_credit": "apply_credit_share",
    "show_credit": "show_credit_share",
    "not_reached": "not_reached_share",
    "disengaged": "disengaged_share",
    "total_time_log": "log1p_total_time",
    "actions_log": "log1p_total_actions",
    "first_action_time_log": "log1p_mean_first_action_time",
}


def main() -> int:
    logger = configure_logging("process_outcomes")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    frame = frame[frame["n_items"].gt(0)].copy()
    rows = []
    summaries = {}
    for label, column in OUTCOMES.items():
        for system, sample in frame.groupby("CNT", observed=True, sort=True):
            sample = sample[sample[column].notna()].reset_index(drop=True)
            if sample.empty:
                continue
            estimate = survey_observed(
                sample,
                sample[column].to_numpy(float),
                sample[["ldw_second"]].to_numpy(float),
                sample["design_stratum"].to_numpy(),
                coefficient_index=0,
            )
            row = {"outcome": label, "variable": column, "system": system}
            row.update(estimate.to_dict())
            rows.append(row)
        system_rows = pd.DataFrame([row for row in rows if row["outcome"] == label])
        summaries[label] = meta_analysis(
            system_rows["coefficient"].to_numpy(), system_rows["standard_error"].to_numpy()
        )
        if label.endswith("_log"):
            for mode in ("fixed", "random"):
                coefficient = summaries[label][f"{mode}_coefficient"]
                summaries[label][f"{mode}_percent"] = float(100 * np.expm1(coefficient))
        logger.info("%s: %s", label, summaries[label])
    pd.DataFrame(rows).to_csv(
        project_path("output", "tables", "system_process_effects.csv"), index=False
    )
    write_json(project_path("output", "tables", "process_effects.json"), summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
