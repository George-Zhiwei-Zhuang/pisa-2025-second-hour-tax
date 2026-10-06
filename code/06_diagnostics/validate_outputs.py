#!/usr/bin/env python3
"""Fail loudly if reproduced outputs depart from the audited release."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402


def load(relative: str):
    return json.loads(project_path(relative).read_text(encoding="utf-8"))


def assert_between(value: float, lower: float, upper: float, label: str) -> None:
    if not lower <= value <= upper:
        raise AssertionError(f"{label}: {value} outside [{lower}, {upper}]")


def main() -> int:
    logger = configure_logging("validate_outputs")
    processed_counts = project_path("data", "processed", "analysis_counts.json")
    counts = load(
        "data/processed/analysis_counts.json"
        if processed_counts.is_file()
        else "output/tables/analysis_counts.json"
    )
    assert counts["strict_main_students"] == 205_114
    assert counts["strict_main_systems"] == 84
    assert counts["strict_adaptive_students"] == 454_324

    main_results = load("output/tables/main_effects.json")
    assert_between(main_results["points"]["fixed_coefficient"], -8.5, -8.1, "main points")
    assert_between(main_results["sd"]["fixed_coefficient"], -0.095, -0.091, "main SD")
    assert main_results["sd"]["negative_systems"] == 78
    assert main_results["sd"]["significant_negative_systems"] == 39

    comparative = load("output/tables/comparative_effects.json")
    for pair in ("science", "reading", "math"):
        assert comparative[pair]["ldw_sd"]["random_coefficient"] < 0
        assert comparative[pair]["conventional_sd"]["random_coefficient"] > 0
        assert comparative[pair]["gap_points"]["random_coefficient"] < -10

    balance = load("output/tables/balance.json")
    assert all(result["fixed_p_value"] > 0.1 for result in balance.values())
    adaptive = load("output/tables/adaptive_effects.json")
    assert adaptive["main"]["fixed_p_value"] > 0.1
    assert adaptive["escs_interaction"]["fixed_p_value"] > 0.1

    process = load("output/tables/process_effects.json")
    assert abs(process["item_exposure"]["random_coefficient"]) < 0.001
    assert_between(
        process["credit_assigned"]["random_coefficient"],
        -0.020,
        -0.017,
        "normalized credit",
    )
    assert_between(
        process["total_time_log"]["random_percent"], -18.0, -15.0, "total time"
    )
    assert_between(
        process["first_action_time_log"]["random_percent"],
        -19.0,
        -16.0,
        "mean first-action time",
    )
    assert process["disengaged"]["random_coefficient"] > 0.02

    heterogeneity = load("output/tables/heterogeneity.json")
    by_name = {row["moderator"]: row for row in heterogeneity}
    assert len(by_name) == 12
    assert by_name["perseverance"]["fixed_q_value"] < 0.01
    assert by_name["self_regulation"]["fixed_q_value"] > 0.05

    diagnostics = load("output/tables/design_diagnostics.json")
    assert diagnostics["eligible_duplicate_student_ids"] == 0
    assert diagnostics["strict_duplicate_student_ids"] == 0
    assert diagnostics["nonpositive_final_weights"] == 0
    assert diagnostics["ldw_pv_complete_students"] == counts["strict_main_students"]
    assert_between(
        diagnostics["ldw_process_match_share"], 0.985, 0.995, "process match"
    )
    assert_between(
        diagnostics["strict_system_treatment_share_min"],
        0.45,
        0.48,
        "minimum system treatment share",
    )
    assert_between(
        diagnostics["strict_system_treatment_share_max"],
        0.51,
        0.54,
        "maximum system treatment share",
    )
    support_counts = {
        row["minimum_students_per_order"]: row
        for row in diagnostics["support_thresholds"]
    }
    assert set(support_counts) == {1, 2, 5, 10}
    assert support_counts[1]["students"] == counts["strict_main_students"]
    assert support_counts[2]["systems"] == 84
    assert support_counts[5]["systems"] == 32
    assert support_counts[10]["systems"] == 11

    meta = load("output/tables/meta_robustness.json")
    assert meta["points"]["random_modified_hartung_knapp"]["ci_high"] < 0
    assert meta["sd"]["random_modified_hartung_knapp"]["ci_high"] < 0
    assert meta["points"]["sign_test"]["negative_systems"] == 78
    assert meta["points"]["sign_test"]["one_sided_p_value"] < 0.001
    assert_between(
        meta["points"]["leave_one_out"]["random_min"],
        -9.3,
        -9.0,
        "leave-one-out minimum",
    )
    assert_between(
        meta["points"]["leave_one_out"]["random_max"],
        -8.8,
        -8.5,
        "leave-one-out maximum",
    )
    assert_between(
        meta["points"]["equal_system"]["coefficient"],
        -10.0,
        -9.0,
        "equal-system mean",
    )
    assert meta["points"]["prediction_interval"]["high"] > 0

    support = load("output/tables/support_sensitivity.json")
    assert math.isclose(
        support["1"]["points"]["random_coefficient"],
        main_results["points"]["random_coefficient"],
        abs_tol=1e-10,
    )
    assert_between(
        support["2"]["points"]["random_coefficient"],
        -8.6,
        -8.0,
        "two-per-order sensitivity",
    )
    assert support["2"]["systems"] == 84
    assert support["5"]["systems"] == 32
    assert support["10"]["systems"] == 11
    assert support["10"]["points"]["random_p_value"] > 0.10

    expected_files = [
        "output/tables/table_01_main_effect.csv",
        "output/tables/table_02_comparative_advantage.csv",
        "output/tables/table_03_balance.csv",
        "output/tables/table_04_process.csv",
        "output/tables/table_05_heterogeneity.csv",
        "output/tables/table_a1_adaptive_science.csv",
        "output/tables/table_a2_meta_robustness.csv",
        "output/tables/table_a3_support_sensitivity.csv",
        "output/tables/table_a4_design_audit.csv",
        "output/tables/table_a5_booklet_counts.csv",
        "output/figures/figure_01_system_forest.pdf",
        "output/figures/figure_02_mirrored_effects.pdf",
        "output/figures/figure_03_heterogeneity.pdf",
        "output/figures/figure_04_process.pdf",
        "output/figures/figure_a1_leave_one_system_out.pdf",
        "output/figures/figure_a2_support_sensitivity.pdf",
    ]
    missing = [path for path in expected_files if not project_path(path).is_file()]
    if missing:
        raise AssertionError(f"Missing final outputs: {missing}")
    report = {
        "status": "passed",
        "audited_release": "PISA 2025 PUFs available 2026-09-12",
        "assertions": 54,
        "main_fixed_points": main_results["points"]["fixed_coefficient"],
        "main_fixed_sd": main_results["sd"]["fixed_coefficient"],
        "strict_main_students": counts["strict_main_students"],
        "strict_adaptive_students": counts["strict_adaptive_students"],
    }
    write_json(project_path("output", "logs", "validation_report.json"), report)
    logger.info("All output validation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
