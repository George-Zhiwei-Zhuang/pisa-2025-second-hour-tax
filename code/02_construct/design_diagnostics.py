#!/usr/bin/env python3
"""Audit booklet allocation, overlap, identifiers, and analysis-sample flow."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402

ELIGIBLE_BOOKS = [5.0, 6.0, 9.0, 10.0, 11.0, 12.0]
PAIR = {
    5.0: ("science", 1),
    6.0: ("science", 0),
    9.0: ("reading", 1),
    10.0: ("reading", 0),
    11.0: ("math", 1),
    12.0: ("math", 0),
}


def main() -> int:
    logger = configure_logging("design_diagnostics")
    student_path = project_path("data", "processed", "student")
    eligible = pd.read_parquet(
        student_path,
        columns=["CNT", "CNTSCHID", "CNTSTUID", "BOOKID", "W_FSTUWT"],
        filters=[("BOOKID", "in", ELIGIBLE_BOOKS)],
    )
    eligible = eligible[eligible["BOOKID"].isin(ELIGIBLE_BOOKS)].copy()
    eligible["paired_domain"] = eligible["BOOKID"].map(
        lambda book: PAIR[book][0]
    )
    eligible["ldw_second"] = eligible["BOOKID"].map(
        lambda book: PAIR[book][1]
    ).astype(float)
    eligible["design_stratum"] = (
        eligible["CNT"].astype(str)
        + "|"
        + eligible["CNTSCHID"].astype(str)
        + "|"
        + eligible["paired_domain"]
    )

    strata = (
        eligible.groupby(
            ["CNT", "CNTSCHID", "paired_domain", "design_stratum"],
            observed=True,
        )
        .agg(
            students=("CNTSTUID", "size"),
            second_hour=("ldw_second", "sum"),
        )
        .reset_index()
    )
    strata["first_hour"] = strata["students"] - strata["second_hour"]
    strata["min_arm"] = strata[["first_hour", "second_hour"]].min(axis=1)
    strata["treatment_share"] = strata["second_hour"] / strata["students"]

    threshold_rows = []
    for threshold in (1, 2, 5, 10):
        retained = strata[strata["min_arm"] >= threshold]
        threshold_rows.append(
            {
                "minimum_students_per_order": threshold,
                "strata": int(len(retained)),
                "students": int(retained["students"].sum()),
                "share_of_eligible_students": float(
                    retained["students"].sum() / len(eligible)
                ),
                "systems": int(retained["CNT"].nunique()),
            }
        )
    support = pd.DataFrame(threshold_rows)
    support.to_csv(project_path("output", "tables", "sample_support.csv"), index=False)

    strict_ids = set(strata.loc[strata["min_arm"] >= 1, "design_stratum"])
    eligible["strict"] = eligible["design_stratum"].isin(strict_ids)
    system = (
        eligible.groupby("CNT", observed=True)
        .agg(
            eligible_students=("CNTSTUID", "size"),
            eligible_treatment_share=("ldw_second", "mean"),
            strict_students=("strict", "sum"),
        )
        .reset_index()
    )
    strict = eligible[eligible["strict"]]
    strict_system = (
        strict.groupby("CNT", observed=True)
        .agg(
            strict_treatment_share=("ldw_second", "mean"),
            strict_weighted_treatment_share=(
                "ldw_second",
                lambda z: float(
                    np.average(z, weights=strict.loc[z.index, "W_FSTUWT"])
                ),
            ),
            strict_strata=("design_stratum", "nunique"),
        )
        .reset_index()
    )
    system = system.merge(strict_system, on="CNT", validate="one_to_one")
    system["strict_share"] = system["strict_students"] / system["eligible_students"]
    system.to_csv(
        project_path("output", "tables", "system_design_diagnostics.csv"),
        index=False,
    )

    booklet = (
        eligible.groupby(["paired_domain", "BOOKID", "ldw_second"], observed=True)
        .agg(students=("CNTSTUID", "size"), weighted_students=("W_FSTUWT", "sum"))
        .reset_index()
        .sort_values(["paired_domain", "BOOKID"])
    )
    booklet["BOOKID"] = booklet["BOOKID"].astype(int)
    booklet.to_csv(project_path("output", "tables", "booklet_counts.csv"), index=False)

    main = pd.read_parquet(
        project_path("data", "processed", "analysis_main.parquet"),
        columns=["CNTSTUID", "n_items"] + [f"PV{k}CMPS" for k in range(1, 11)],
    )
    adaptive = pd.read_parquet(
        project_path("data", "processed", "analysis_adaptive.parquet"),
        columns=["CNTSTUID", "adaptive", "W_FSTUWT"],
    )
    pv_columns = [f"PV{k}CMPS" for k in range(1, 11)]
    diagnostics = {
        "eligible_students": int(len(eligible)),
        "eligible_systems": int(eligible["CNT"].nunique()),
        "eligible_strata": int(len(strata)),
        "strict_students": int(strict.shape[0]),
        "strict_strata": int((strata["min_arm"] >= 1).sum()),
        "strict_share": float(strict.shape[0] / len(eligible)),
        "eligible_duplicate_student_ids": int(eligible["CNTSTUID"].duplicated().sum()),
        "strict_duplicate_student_ids": int(main["CNTSTUID"].duplicated().sum()),
        "nonpositive_final_weights": int((eligible["W_FSTUWT"] <= 0).sum()),
        "ldw_pv_complete_students": int(main[pv_columns].notna().all(axis=1).sum()),
        "ldw_process_matched_students": int(main["n_items"].gt(0).sum()),
        "ldw_process_match_share": float(main["n_items"].gt(0).mean()),
        "adaptive_students": int(len(adaptive)),
        "adaptive_weighted_share": float(
            np.average(adaptive["adaptive"], weights=adaptive["W_FSTUWT"])
        ),
        "strict_system_treatment_share_min": float(
            system["strict_treatment_share"].min()
        ),
        "strict_system_treatment_share_max": float(
            system["strict_treatment_share"].max()
        ),
        "stratum_size": {
            "median": float(strata["students"].median()),
            "p10": float(strata["students"].quantile(0.10)),
            "p90": float(strata["students"].quantile(0.90)),
            "max": int(strata["students"].max()),
        },
        "support_thresholds": threshold_rows,
    }
    write_json(
        project_path("output", "tables", "design_diagnostics.json"), diagnostics
    )
    logger.info("Design diagnostics: %s", diagnostics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
