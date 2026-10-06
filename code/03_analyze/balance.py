#!/usr/bin/env python3
"""Check baseline covariate balance within the strict mirrored-order design."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import enforce_mixed_groups, meta_analysis, survey_observed  # noqa: E402

COVARIATES = {
    "age_years": "AGE",
    "female": "female",
    "escs_sd": "ESCS",
    "parent_education_years": "PAREDINT",
    "home_possessions_sd": "HOMEPOS",
    "immigrant": "immigrant",
}


def main() -> int:
    logger = configure_logging("balance")
    frame = pd.read_parquet(project_path("data", "processed", "analysis_main.parquet"))
    rows = []
    summary = {}
    for label, column in COVARIATES.items():
        for system, system_frame in frame.groupby("CNT", observed=True, sort=True):
            sample = system_frame[system_frame[column].notna()].copy()
            sample = enforce_mixed_groups(sample, "design_stratum", "ldw_second")
            if sample.empty:
                continue
            estimate = survey_observed(
                sample,
                sample[column].to_numpy(float),
                sample[["ldw_second"]].to_numpy(float),
                sample["design_stratum"].to_numpy(),
                0,
            )
            row = {"covariate": label, "variable": column, "system": system}
            row.update(estimate.to_dict())
            rows.append(row)
        estimates = pd.DataFrame([row for row in rows if row["covariate"] == label])
        summary[label] = meta_analysis(
            estimates["coefficient"].to_numpy(), estimates["standard_error"].to_numpy()
        )
        logger.info("%s: %s", label, summary[label])
    pd.DataFrame(rows).to_csv(
        project_path("output", "tables", "system_balance.csv"), index=False
    )
    write_json(project_path("output", "tables", "balance.json"), summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
