#!/usr/bin/env python3
"""Create submission-ready CSV, Markdown, and LaTeX tables from analysis outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path  # noqa: E402

TABLE_DIR = project_path("output", "tables")
MODERATOR_LABELS = {
    "perseverance": "Perseverance",
    "test_effort": "Test effort",
    "digital_distraction": "Digital distraction",
    "curiosity": "Curiosity",
    "socioeconomic_status": "Socioeconomic status",
    "family_support": "Family support",
    "help_seeking": "Help seeking",
    "self_regulation": "Self-regulation",
    "ai_for_learning": "AI for learning",
    "feedback_seeking": "Feedback seeking",
    "ict_feedback": "ICT feedback",
    "ai_use_at_school": "AI use at school",
}


def load_json(name: str):
    return json.loads((TABLE_DIR / name).read_text(encoding="utf-8"))


def stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def effect(coefficient: float, standard_error: float, p_value: float, digits: int = 3) -> str:
    return f"{coefficient:.{digits}f}{stars(p_value)} ({standard_error:.{digits}f})"


def save_table(frame: pd.DataFrame, stem: str, note: str) -> None:
    frame.to_csv(TABLE_DIR / f"{stem}.csv", index=False)
    markdown = frame.to_markdown(index=False) + f"\n\n*Notes:* {note}\n"
    (TABLE_DIR / f"{stem}.md").write_text(markdown, encoding="utf-8")
    latex = frame.to_latex(index=False, escape=True) + f"\n% Notes: {note}\n"
    (TABLE_DIR / f"{stem}.tex").write_text(latex, encoding="utf-8")


def main() -> int:
    logger = configure_logging("make_tables")
    main_results = load_json("main_effects.json")
    rows = []
    for scale, label in (("points", "PISA points"), ("sd", "Within-system SD")):
        result = main_results[scale]
        for mode, estimator in (("fixed", "Fixed-effect meta"), ("random", "Random-effects meta")):
            rows.append(
                {
                    "Scale": label,
                    "Estimator": estimator,
                    "Effect (SE)": effect(
                        result[f"{mode}_coefficient"],
                        result[f"{mode}_standard_error"],
                        result[f"{mode}_p_value"],
                    ),
                    "95% CI": f"[{result[f'{mode}_ci_low']:.3f}, {result[f'{mode}_ci_high']:.3f}]",
                    "Systems": result["k"],
                }
            )
    save_table(
        pd.DataFrame(rows),
        "table_01_main_effect",
        "The coefficient is the effect of assigning LDW to hour 2. All models absorb school × mirrored-domain strata and use ten plausible values and 80 BRR-Fay weights.",
    )

    comparative = load_json("comparative_effects.json")
    rows = []
    for pair in ("science", "reading", "math"):
        result = comparative[pair]
        rows.append(
            {
                "Mirrored pair": pair.title(),
                "LDW effect, SD (SE)": effect(
                    result["ldw_sd"]["random_coefficient"],
                    result["ldw_sd"]["random_standard_error"],
                    result["ldw_sd"]["random_p_value"],
                ),
                "Paired-domain effect, SD (SE)": effect(
                    result["conventional_sd"]["random_coefficient"],
                    result["conventional_sd"]["random_standard_error"],
                    result["conventional_sd"]["random_p_value"],
                ),
                "LDW minus paired gap, points (SE)": effect(
                    result["gap_points"]["random_coefficient"],
                    result["gap_points"]["random_standard_error"],
                    result["gap_points"]["random_p_value"],
                    digits=2,
                ),
                "Systems": result["gap_points"]["k"],
            }
        )
    save_table(
        pd.DataFrame(rows),
        "table_02_comparative_advantage",
        "Random-effects meta-estimates. Positive paired-domain coefficients mean a first-hour advantage because LDW-second assignment places that conventional domain first.",
    )

    balance = load_json("balance.json")
    balance_labels = {
        "age_years": "Age (years)",
        "female": "Female",
        "escs_sd": "ESCS",
        "parent_education_years": "Parental education (years)",
        "home_possessions_sd": "Home possessions",
        "immigrant": "Immigrant",
    }
    rows = []
    for key, label in balance_labels.items():
        result = balance[key]
        rows.append(
            {
                "Covariate": label,
                "Difference (SE)": effect(
                    result["fixed_coefficient"],
                    result["fixed_standard_error"],
                    result["fixed_p_value"],
                    digits=4,
                ),
                "p-value": f"{result['fixed_p_value']:.3f}",
                "Systems": result["k"],
            }
        )
    save_table(
        pd.DataFrame(rows),
        "table_03_balance",
        "Fixed-effect meta-estimates. Binary-variable differences are proportions; continuous variables retain their documented PUF units.",
    )

    process = load_json("process_effects.json")
    process_labels = {
        "item_exposure": ("Administered items", "items", 1.0),
        "credit_assigned": ("Normalized credit", "percentage points", 100.0),
        "learn_credit": ("Learn-phase credit", "percentage points", 100.0),
        "apply_credit": ("Apply-phase credit", "percentage points", 100.0),
        "show_credit": ("Show-phase credit", "percentage points", 100.0),
        "not_reached": ("Not reached", "percentage points", 100.0),
        "disengaged": ("Disengaged", "percentage points", 100.0),
        "total_time_log": ("Total time", "percent", None),
        "actions_log": ("Number of actions", "percent", None),
        "first_action_time_log": ("Mean first-action time", "percent", None),
    }
    rows = []
    for key, (label, unit, multiplier) in process_labels.items():
        result = process[key]
        row = {"Outcome": label, "Unit": unit, "Systems": result["k"]}
        for mode in ("fixed", "random"):
            coefficient = result[f"{mode}_coefficient"]
            standard_error = result[f"{mode}_standard_error"]
            if multiplier is None:
                transformed = 100 * np.expm1(coefficient)
                lower = 100 * np.expm1(coefficient - 1.96 * standard_error)
                upper = 100 * np.expm1(coefficient + 1.96 * standard_error)
                row[f"{mode.title()} effect"] = f"{transformed:.2f} [{lower:.2f}, {upper:.2f}]"
            else:
                row[f"{mode.title()} effect"] = effect(
                    multiplier * coefficient,
                    multiplier * standard_error,
                    result[f"{mode}_p_value"],
                    digits=3,
                )
        rows.append(row)
    save_table(
        pd.DataFrame(rows),
        "table_04_process",
        "Proportion outcomes are percentage-point changes. Logged timing/action outcomes are transformed as 100×(exp(beta)−1). Mean first-action time is the student's mean across applicable LDW items. Credit is each item's awarded score divided by its maximum score.",
    )

    heterogeneity = pd.read_csv(TABLE_DIR / "heterogeneity.csv")
    heterogeneity_table = pd.DataFrame(
        {
            "Moderator": heterogeneity["moderator"].map(MODERATOR_LABELS),
            "Interaction, SD/SD (SE)": [
                effect(b, se, p)
                for b, se, p in zip(
                    heterogeneity["fixed_coefficient"],
                    heterogeneity["fixed_standard_error"],
                    heterogeneity["fixed_p_value"],
                )
            ],
            "BH q-value": heterogeneity["fixed_q_value"].map(lambda value: f"{value:.3f}"),
            "Systems": heterogeneity["k"].astype(int),
            "Post-treatment": heterogeneity["post_treatment"].map({True: "Yes", False: "No"}),
        }
    )
    save_table(
        heterogeneity_table,
        "table_05_heterogeneity",
        "Positive interactions attenuate the LDW second-hour penalty. Moderators are standardized within system. Benjamini-Hochberg q-values adjust across the 12 prespecified moderators. Test effort is post-treatment and descriptive.",
    )

    adaptive = load_json("adaptive_effects.json")
    rows = []
    for key, label in (("main", "Adaptive assignment"), ("escs_interaction", "Adaptive × ESCS")):
        result = adaptive[key]
        rows.append(
            {
                "Specification": label,
                "Effect, SD (SE)": effect(
                    result["fixed_coefficient"],
                    result["fixed_standard_error"],
                    result["fixed_p_value"],
                ),
                "95% CI": f"[{result['fixed_ci_low']:.3f}, {result['fixed_ci_high']:.3f}]",
                "Students": result["n_students"],
                "Systems": result["k"],
            }
        )
    save_table(
        pd.DataFrame(rows),
        "table_a1_adaptive_science",
        "Science outcome models absorb school × booklet strata. The appendix uses books 1–6 and compares SPATH=2 (adaptive) with SPATH=1 (linear).",
    )

    meta = load_json("meta_robustness.json")
    rows = []
    for scale, label in (("points", "PISA points"), ("sd", "Within-system SD")):
        result = meta[scale]
        specifications = [
            (
                "Inverse-variance fixed effect",
                result["fixed"]["fixed_coefficient"],
                result["fixed"]["fixed_standard_error"],
                result["fixed"]["fixed_ci_low"],
                result["fixed"]["fixed_ci_high"],
                result["fixed"]["fixed_p_value"],
                "—",
            ),
            (
                "DerSimonian–Laird random effects",
                result["random_dl"]["random_coefficient"],
                result["random_dl"]["random_standard_error"],
                result["random_dl"]["random_ci_low"],
                result["random_dl"]["random_ci_high"],
                result["random_dl"]["random_p_value"],
                f"[{result['prediction_interval']['low']:.3f}, {result['prediction_interval']['high']:.3f}]",
            ),
            (
                "Modified Hartung–Knapp",
                result["random_modified_hartung_knapp"]["coefficient"],
                result["random_modified_hartung_knapp"]["standard_error"],
                result["random_modified_hartung_knapp"]["ci_low"],
                result["random_modified_hartung_knapp"]["ci_high"],
                result["random_modified_hartung_knapp"]["p_value"],
                "—",
            ),
            (
                "Equal-system mean",
                result["equal_system"]["coefficient"],
                result["equal_system"]["standard_error"],
                result["equal_system"]["ci_low"],
                result["equal_system"]["ci_high"],
                result["equal_system"]["p_value"],
                "—",
            ),
        ]
        for specification, coefficient, standard_error, low, high, p_value, prediction in specifications:
            rows.append(
                {
                    "Scale": label,
                    "Cross-system summary": specification,
                    "Estimate (SE)": effect(coefficient, standard_error, p_value),
                    "95% CI": f"[{low:.3f}, {high:.3f}]",
                    "95% prediction interval": prediction,
                    "Systems": result["fixed"]["k"],
                }
            )
        for specification, coefficient in (
            ("Median system", result["median_system"]["coefficient"]),
            ("10% trimmed mean", result["ten_percent_trimmed"]["coefficient"]),
            (
                "Analysis-sample-size weighted mean",
                result["analysis_sample_size_weighted"]["coefficient"],
            ),
        ):
            rows.append(
                {
                    "Scale": label,
                    "Cross-system summary": specification,
                    "Estimate (SE)": f"{coefficient:.3f}",
                    "95% CI": "—",
                    "95% prediction interval": "—",
                    "Systems": result["fixed"]["k"],
                }
            )
    save_table(
        pd.DataFrame(rows),
        "table_a2_meta_robustness",
        "All summaries use the same released system estimates. Modified Hartung–Knapp applies a t critical value and bounds the residual scale below by one. The sign test finds 78 of 84 point estimates below zero (one-sided p < 0.001). Descriptive medians and weighted/trimmed means have no reported sampling interval.",
    )

    support = load_json("support_sensitivity.json")
    rows = []
    for threshold in sorted(support, key=int):
        result = support[threshold]
        rows.append(
            {
                "Minimum students in each order": int(threshold),
                "Students": result["students"],
                "Strata": result["strata"],
                "Systems": result["systems"],
                "Random effect, points (SE)": effect(
                    result["points"]["random_coefficient"],
                    result["points"]["random_standard_error"],
                    result["points"]["random_p_value"],
                ),
                "Random effect, SD (SE)": effect(
                    result["sd"]["random_coefficient"],
                    result["sd"]["random_standard_error"],
                    result["sd"]["random_p_value"],
                ),
                "Main-sample effect in same systems, points": effect(
                    result["main_sample_same_systems"]["points"]["random_coefficient"],
                    result["main_sample_same_systems"]["points"]["random_standard_error"],
                    result["main_sample_same_systems"]["points"]["random_p_value"],
                ),
            }
        )
    save_table(
        pd.DataFrame(rows),
        "table_a3_support_sensitivity",
        "Each row rebuilds the analytic sample from school × mirrored-domain strata containing at least the stated number of students in both booklet orders, then repeats the full ten-PV, 80-replicate analysis. The final column re-synthesizes the original main-sample system estimates over exactly the systems retained at that threshold, exposing changes in system composition.",
    )

    diagnostics = load_json("design_diagnostics.json")
    diagnostic_rows = [
        ("Eligible students", diagnostics["eligible_students"]),
        ("Eligible systems", diagnostics["eligible_systems"]),
        ("Eligible design strata", diagnostics["eligible_strata"]),
        ("Strict-overlap students", diagnostics["strict_students"]),
        ("Strict-overlap strata", diagnostics["strict_strata"]),
        ("Strict-overlap share", f"{100 * diagnostics['strict_share']:.2f}%"),
        ("Duplicate eligible student IDs", diagnostics["eligible_duplicate_student_ids"]),
        ("Duplicate strict-sample student IDs", diagnostics["strict_duplicate_student_ids"]),
        ("Nonpositive final weights", diagnostics["nonpositive_final_weights"]),
        ("Complete LDW plausible-value records", diagnostics["ldw_pv_complete_students"]),
        ("LDW process-data match", f"{100 * diagnostics['ldw_process_match_share']:.2f}%"),
        (
            "System treatment-share range",
            f"{diagnostics['strict_system_treatment_share_min']:.3f}–{diagnostics['strict_system_treatment_share_max']:.3f}",
        ),
        ("Median eligible stratum size", f"{diagnostics['stratum_size']['median']:.1f}"),
        ("10th–90th percentile stratum size", f"{diagnostics['stratum_size']['p10']:.1f}–{diagnostics['stratum_size']['p90']:.1f}"),
    ]
    save_table(
        pd.DataFrame(diagnostic_rows, columns=["Diagnostic", "Value"]),
        "table_a4_design_audit",
        "Counts are generated directly from the pinned PUFs before outcome analysis. The treatment-share range is calculated across systems after imposing strict within-school × pair overlap.",
    )

    booklet = pd.read_csv(TABLE_DIR / "booklet_counts.csv")
    booklet_table = pd.DataFrame(
        {
            "Mirrored pair": booklet["paired_domain"].str.title(),
            "Book": booklet["BOOKID"].astype(int),
            "LDW hour": np.where(booklet["ldw_second"].eq(1), 2, 1),
            "Students": booklet["students"].astype(int),
            "Sum of final weights": booklet["weighted_students"].map(lambda value: f"{value:,.0f}"),
        }
    )
    save_table(
        booklet_table,
        "table_a5_booklet_counts",
        "Counts cover all students assigned to the six eligible mirrored booklets before the within-stratum overlap restriction.",
    )
    logger.info("Created ten table families in CSV, Markdown, and LaTeX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
