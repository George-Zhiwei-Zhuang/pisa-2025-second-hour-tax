#!/usr/bin/env python3
"""Build the strict mirrored-order and adaptive-science analysis samples."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402

ELIGIBLE_BOOKS = [5.0, 6.0, 9.0, 10.0, 11.0, 12.0]
PAIR = {
    5.0: ("science", "SCIE", 1),
    6.0: ("science", "SCIE", 0),
    9.0: ("reading", "READ", 1),
    10.0: ("reading", "READ", 0),
    11.0: ("math", "MATH", 1),
    12.0: ("math", "MATH", 0),
}


def main() -> int:
    logger = configure_logging("construct_samples")
    student_path = project_path("data", "processed", "student")
    ldw_path = project_path("data", "processed", "ldw_student")
    cognitive_path = project_path(
        "data", "processed", "cognitive", "cognitive.parquet"
    )
    output_dir = project_path("data", "processed")

    weights = ["W_FSTUWT"] + [f"W_FSTURWT{k}" for k in range(1, 81)]
    pvs = [
        f"PV{k}{domain}"
        for domain in ("CMPS", "SCIE", "READ", "MATH")
        for k in range(1, 11)
    ]
    covariates = [
        "AGE",
        "female",
        "ESCS",
        "PAREDINT",
        "HOMEPOS",
        "immigrant",
    ]
    moderators = [
        "PERSEV",
        "EFFORT1",
        "digital_distraction",
        "CURIO",
        "ESCS",
        "FAMSUP",
        "help_seeking",
        "SELFREG",
        "ai_for_learning",
        "feedback_seeking",
        "ICTFEED",
        "AIUSESCH",
    ]
    identifiers = ["CNT", "CNTSCHID", "CNTSTUID", "BOOKID"]
    columns = list(dict.fromkeys(identifiers + weights + pvs + covariates + moderators))
    student = pd.read_parquet(
        student_path,
        columns=columns,
        filters=[("BOOKID", "in", ELIGIBLE_BOOKS)],
    )
    student = student[student["BOOKID"].isin(ELIGIBLE_BOOKS)].copy()
    mapping = student["BOOKID"].map(PAIR)
    student["paired_domain"] = mapping.map(lambda value: value[0])
    student["paired_domain_code"] = mapping.map(lambda value: value[1])
    student["ldw_second"] = mapping.map(lambda value: value[2]).astype(float)
    student["design_stratum"] = (
        student["CNT"].astype(str)
        + "|"
        + student["CNTSCHID"].astype(str)
        + "|"
        + student["paired_domain"].astype(str)
    )
    mixed = student.groupby("design_stratum", observed=True)["ldw_second"].transform(
        "nunique"
    )
    main = student.loc[mixed.eq(2)].copy()

    process_columns = [
        "CNTSTUID",
        "n_items",
        "credit_share",
        "learn_credit_share",
        "apply_credit_share",
        "show_credit_share",
        "not_reached_share",
        "disengaged_share",
        "no_credit_share",
        "total_time",
        "total_actions",
        "mean_first_action_time",
        "log1p_total_time",
        "log1p_total_actions",
        "log1p_total_first_action_time",
        "log1p_mean_first_action_time",
    ]
    process = pd.read_parquet(ldw_path, columns=process_columns)
    main = main.merge(process, on="CNTSTUID", how="left", validate="one_to_one")
    main.to_parquet(
        output_dir / "analysis_main.parquet",
        index=False,
        compression="zstd",
        compression_level=8,
    )

    adaptive_columns = list(
        dict.fromkeys(
            identifiers
            + weights
            + [f"PV{k}SCIE" for k in range(1, 11)]
            + ["ESCS"]
        )
    )
    adaptive_student = pd.read_parquet(
        student_path,
        columns=adaptive_columns,
        filters=[("BOOKID", "in", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])],
    )
    cognitive = pd.read_parquet(cognitive_path, columns=["CNTSTUID", "SPATH"])
    cognitive = cognitive[cognitive["SPATH"].isin(["1.0", "2.0"])].drop_duplicates(
        "CNTSTUID"
    )
    adaptive = adaptive_student.merge(
        cognitive, on="CNTSTUID", how="inner", validate="one_to_one"
    )
    adaptive = adaptive[
        adaptive["BOOKID"].isin([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        & adaptive["SPATH"].isin(["1.0", "2.0"])
    ].copy()
    adaptive["adaptive"] = (adaptive["SPATH"] == "2.0").astype(float)
    adaptive["design_stratum"] = (
        adaptive["CNT"].astype(str)
        + "|"
        + adaptive["CNTSCHID"].astype(str)
        + "|"
        + adaptive["BOOKID"].astype("Int64").astype(str)
    )
    mixed_adaptive = adaptive.groupby("design_stratum", observed=True)[
        "adaptive"
    ].transform("nunique")
    adaptive = adaptive.loc[mixed_adaptive.eq(2)].copy()
    adaptive.to_parquet(
        output_dir / "analysis_adaptive.parquet",
        index=False,
        compression="zstd",
        compression_level=8,
    )

    counts = {
        "eligible_ldw_book_students": int(len(student)),
        "strict_main_students": int(len(main)),
        "strict_main_share": float(len(main) / len(student)),
        "strict_main_systems": int(main["CNT"].nunique()),
        "strict_main_by_pair": {
            key: int(value)
            for key, value in main.groupby("paired_domain", observed=True).size().items()
        },
        "strict_process_students": int(main["n_items"].gt(0).sum()),
        "strict_adaptive_students": int(len(adaptive)),
        "strict_adaptive_systems": int(adaptive["CNT"].nunique()),
    }
    write_json(output_dir / "analysis_counts.json", counts)
    # Keep a data-free copy with the released tables so the archived package can
    # validate its published outputs before the user downloads the restricted-size
    # PUFs and reconstructs the processed Parquet files.
    write_json(project_path("output", "tables", "analysis_counts.json"), counts)
    pd.DataFrame(
        [
            {"pair": pair, "book": int(book), "ldw_second": z, "paired_domain_code": code}
            for book, (pair, code, z) in PAIR.items()
        ]
    ).sort_values(["pair", "book"]).to_csv(
        project_path("docs", "booklet-map.csv"), index=False
    )
    logger.info("Constructed strict main sample: %s", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
