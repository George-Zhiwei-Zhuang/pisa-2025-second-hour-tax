#!/usr/bin/env python3
"""Re-estimate the main effect under increasingly strict within-stratum support."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import meta_analysis, standardize_columns, survey_pv  # noqa: E402

THRESHOLDS = (1, 2, 5, 10)


def main() -> int:
    logger = configure_logging("support_sensitivity")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    main_systems = pd.read_csv(
        project_path("output", "tables", "system_main_effects.csv")
    )
    pv_columns = [f"PV{k}CMPS" for k in range(1, 11)]
    group_counts = (
        frame.groupby(["design_stratum", "ldw_second"], observed=True)
        .size()
        .unstack(fill_value=0)
    )
    group_counts["min_arm"] = group_counts.min(axis=1)

    system_rows = []
    summaries = {}
    for threshold in THRESHOLDS:
        eligible_groups = set(group_counts.index[group_counts["min_arm"] >= threshold])
        threshold_frame = frame[frame["design_stratum"].isin(eligible_groups)]
        for system, sample in threshold_frame.groupby("CNT", observed=True, sort=True):
            sample = sample.reset_index(drop=True)
            if sample.empty:
                continue
            weight = sample["W_FSTUWT"].to_numpy(float)
            outcomes = sample[pv_columns].to_numpy(float)
            treatment = sample[["ldw_second"]].to_numpy(float)
            groups = sample["design_stratum"].to_numpy()
            points = survey_pv(sample, outcomes, treatment, groups, 0)
            standardized = survey_pv(
                sample,
                standardize_columns(outcomes, weight),
                treatment,
                groups,
                0,
            )
            row = {"minimum_students_per_order": threshold, "system": system}
            row.update({f"points_{key}": value for key, value in points.to_dict().items()})
            row.update(
                {f"sd_{key}": value for key, value in standardized.to_dict().items()}
            )
            system_rows.append(row)

        subset = pd.DataFrame(
            [row for row in system_rows if row["minimum_students_per_order"] == threshold]
        )
        retained_systems = set(subset["system"])
        same_system_main = main_systems[main_systems["system"].isin(retained_systems)]
        summaries[str(threshold)] = {
            "students": int(len(threshold_frame)),
            "strata": int(len(eligible_groups)),
            "systems": int(subset["system"].nunique()),
            "points": meta_analysis(
                subset["points_coefficient"].to_numpy(),
                subset["points_standard_error"].to_numpy(),
            ),
            "sd": meta_analysis(
                subset["sd_coefficient"].to_numpy(),
                subset["sd_standard_error"].to_numpy(),
            ),
            "main_sample_same_systems": {
                "points": meta_analysis(
                    same_system_main["points_coefficient"].to_numpy(),
                    same_system_main["points_standard_error"].to_numpy(),
                ),
                "sd": meta_analysis(
                    same_system_main["sd_coefficient"].to_numpy(),
                    same_system_main["sd_standard_error"].to_numpy(),
                ),
            },
        }
        logger.info("Minimum per order %s: %s", threshold, summaries[str(threshold)])

    pd.DataFrame(system_rows).to_csv(
        project_path("output", "tables", "system_support_sensitivity.csv"), index=False
    )
    write_json(
        project_path("output", "tables", "support_sensitivity.json"), summaries
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
