#!/usr/bin/env python3
"""Create the paper's main and appendix figures from saved estimates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path  # noqa: E402

TABLE_DIR = project_path("output", "tables")
FIGURE_DIR = project_path("output", "figures")
BLUE = "#35618D"
ORANGE = "#D26A3D"
GREY = "#6B7280"
MODERATOR_LABELS = {
    "perseverance": "Perseverance",
    "test_effort": "Test effort (post-treatment)",
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


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    logger = configure_logging("make_figures")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
        }
    )

    systems = pd.read_csv(TABLE_DIR / "system_main_effects.csv").sort_values(
        "sd_coefficient"
    )
    fig, ax = plt.subplots(figsize=(8.2, 18))
    y = np.arange(len(systems))
    ax.errorbar(
        systems["sd_coefficient"],
        y,
        xerr=1.96 * systems["sd_standard_error"],
        fmt="o",
        ms=3.2,
        lw=0.8,
        color=BLUE,
        ecolor="#9CB2C8",
        capsize=1.5,
    )
    main_result = json.loads((TABLE_DIR / "main_effects.json").read_text())["sd"]
    ax.axvline(0, color="black", lw=0.8)
    ax.axvline(main_result["fixed_coefficient"], color=ORANGE, lw=2, label="Fixed-effect meta-estimate")
    ax.set_yticks(y, systems["system"], fontsize=7.3)
    ax.set_xlabel("Effect of LDW in hour 2 (within-system SD)")
    ax.set_title("Second-hour effects by participating system")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", color="#E5E7EB", lw=0.7)
    save(fig, "figure_01_system_forest")

    comparative = json.loads((TABLE_DIR / "comparative_effects.json").read_text())
    pair_order = ["science", "reading", "math"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    base = np.arange(len(pair_order))
    for offset, key, label, color in (
        (-0.12, "ldw_sd", "LDW placed second", BLUE),
        (0.12, "conventional_sd", "Paired domain placed first", ORANGE),
    ):
        estimates = np.array([comparative[pair][key]["random_coefficient"] for pair in pair_order])
        errors = np.array([comparative[pair][key]["random_standard_error"] for pair in pair_order])
        ax.errorbar(estimates, base + offset, xerr=1.96 * errors, fmt="o", ms=7, color=color, capsize=3, label=label)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(base, [pair.title() for pair in pair_order])
    ax.invert_yaxis()
    ax.set_xlabel("Order effect (within-system SD)")
    ax.set_title("Mirrored order shifts measured comparative advantage")
    ax.grid(axis="x", color="#E5E7EB", lw=0.7)
    ax.legend(frameon=False)
    save(fig, "figure_02_mirrored_effects")

    heterogeneity = pd.read_csv(TABLE_DIR / "heterogeneity.csv").sort_values(
        "fixed_coefficient"
    )
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    y = np.arange(len(heterogeneity))
    colors = np.where(heterogeneity["fixed_q_value"] < 0.05, BLUE, GREY)
    for index, row in heterogeneity.reset_index(drop=True).iterrows():
        ax.errorbar(
            row["fixed_coefficient"],
            index,
            xerr=1.96 * row["fixed_standard_error"],
            fmt="o",
            color=colors[index],
            capsize=2.5,
        )
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, heterogeneity["moderator"].map(MODERATOR_LABELS))
    ax.set_xlabel("Interaction with LDW-second assignment (SD per moderator SD)")
    ax.set_title("Learner-type heterogeneity")
    ax.grid(axis="x", color="#E5E7EB", lw=0.7)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=BLUE,
                   markeredgecolor=BLUE, label="BH q < 0.05"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=GREY,
                   markeredgecolor=GREY, label="BH q ≥ 0.05"),
        ],
        frameon=False,
        loc="lower right",
    )
    save(fig, "figure_03_heterogeneity")

    process = json.loads((TABLE_DIR / "process_effects.json").read_text())
    labels = {
        "credit_assigned": "Normalized credit (pp)",
        "learn_credit": "Learn credit (pp)",
        "apply_credit": "Apply credit (pp)",
        "show_credit": "Show credit (pp)",
        "not_reached": "Not reached (pp)",
        "disengaged": "Disengaged (pp)",
        "total_time_log": "Total time (%)",
        "actions_log": "Actions (%)",
        "first_action_time_log": "Mean first-action time (%)",
    }
    values = []
    errors_low = []
    errors_high = []
    for key in labels:
        coefficient = process[key]["random_coefficient"]
        se = process[key]["random_standard_error"]
        if key.endswith("_log"):
            point = 100 * np.expm1(coefficient)
            low = 100 * np.expm1(coefficient - 1.96 * se)
            high = 100 * np.expm1(coefficient + 1.96 * se)
        else:
            point = 100 * coefficient
            low = 100 * (coefficient - 1.96 * se)
            high = 100 * (coefficient + 1.96 * se)
        values.append(point)
        errors_low.append(point - low)
        errors_high.append(high - point)
    fig, ax = plt.subplots(figsize=(8.4, 5.5))
    y = np.arange(len(labels))
    ax.errorbar(values, y, xerr=np.vstack([errors_low, errors_high]), fmt="o", color=BLUE, capsize=3)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, list(labels.values()))
    ax.invert_yaxis()
    ax.set_xlabel("Effect of LDW in hour 2")
    ax.set_title("Response and process channels")
    ax.grid(axis="x", color="#E5E7EB", lw=0.7)
    save(fig, "figure_04_process")

    influence = pd.read_csv(TABLE_DIR / "system_influence.csv")
    influence = influence[influence["scale"].eq("points")].copy()
    baseline = json.loads((TABLE_DIR / "main_effects.json").read_text())["points"][
        "random_coefficient"
    ]
    influence = influence.sort_values("random_coefficient").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    x = np.arange(len(influence))
    ax.scatter(x, influence["random_coefficient"], s=24, color=BLUE, alpha=0.85)
    ax.axhline(baseline, color=ORANGE, lw=2, label="All-system random-effects estimate")
    influential = influence["random_shift"].abs().nlargest(4).index
    offsets = [(-12, -14), (-12, 10), (-18, 28), (24, 14)]
    for index, offset in zip(sorted(influential), offsets):
        row = influence.loc[index]
        ax.annotate(
            str(row["system"]),
            (index, row["random_coefficient"]),
            xytext=offset,
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    spread = influence["random_coefficient"].max() - influence["random_coefficient"].min()
    margin = max(0.08, 0.18 * spread)
    ax.set_ylim(
        influence["random_coefficient"].min() - margin,
        influence["random_coefficient"].max() + margin,
    )
    ax.set_xlabel("Omitted system (ordered by re-estimated effect)")
    ax.set_ylabel("Leave-one-system-out effect (PISA points)")
    ax.set_title("No single system materially drives the second-hour estimate")
    ax.grid(axis="y", color="#E5E7EB", lw=0.7)
    ax.legend(frameon=False)
    save(fig, "figure_a1_leave_one_system_out")

    support = json.loads((TABLE_DIR / "support_sensitivity.json").read_text())
    thresholds = sorted((int(value) for value in support), key=int)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6))
    for ax, scale, label in (
        (axes[0], "points", "PISA points"),
        (axes[1], "sd", "Within-system SD"),
    ):
        estimates = np.array(
            [support[str(value)][scale]["random_coefficient"] for value in thresholds]
        )
        errors = np.array(
            [support[str(value)][scale]["random_standard_error"] for value in thresholds]
        )
        ax.errorbar(
            thresholds,
            estimates,
            yerr=1.96 * errors,
            fmt="o-",
            color=BLUE,
            capsize=3,
            label="Threshold-restricted strata",
        )
        comparison = np.array(
            [
                support[str(value)]["main_sample_same_systems"][scale][
                    "random_coefficient"
                ]
                for value in thresholds
            ]
        )
        ax.plot(
            thresholds,
            comparison,
            "s--",
            color=ORANGE,
            label="Main sample, same systems",
        )
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(thresholds)
        ax.set_xlabel("Minimum students per order within stratum")
        ax.set_ylabel(f"Random-effects estimate ({label})")
        ax.grid(axis="y", color="#E5E7EB", lw=0.7)
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle(
        "Stricter support changes both the local sample and system composition",
        fontweight="bold",
    )
    fig.tight_layout()
    save(fig, "figure_a2_support_sensitivity")
    logger.info("Created six figures in PNG and PDF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
