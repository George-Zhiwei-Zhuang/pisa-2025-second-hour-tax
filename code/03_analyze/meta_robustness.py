#!/usr/bin/env python3
"""Stress-test cross-system synthesis and leave-one-system-out influence."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, t

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import configure_logging, project_path, write_json  # noqa: E402
from estimators import meta_analysis, modified_hartung_knapp  # noqa: E402


def distribution_summary(
    coefficients: np.ndarray, standard_errors: np.ndarray, sample_sizes: np.ndarray
) -> dict[str, object]:
    b = np.asarray(coefficients, float)
    se = np.asarray(standard_errors, float)
    n = np.asarray(sample_sizes, float)
    k = len(b)
    primary = meta_analysis(b, se)
    hksj = modified_hartung_knapp(b, se)

    equal = float(np.mean(b))
    equal_se = float(np.std(b, ddof=1) / np.sqrt(k))
    equal_critical = float(t.ppf(0.975, k - 1))
    order = np.argsort(b)
    trim = int(np.floor(0.10 * k))
    trimmed = b[order][trim : k - trim]
    size_weights = n / n.sum()

    leave_rows = []
    for index in range(k):
        keep = np.arange(k) != index
        leave = meta_analysis(b[keep], se[keep])
        leave_rows.append(
            {
                "omitted_index": index,
                "fixed_coefficient": leave["fixed_coefficient"],
                "random_coefficient": leave["random_coefficient"],
                "fixed_shift": leave["fixed_coefficient"]
                - primary["fixed_coefficient"],
                "random_shift": leave["random_coefficient"]
                - primary["random_coefficient"],
            }
        )
    leave = pd.DataFrame(leave_rows)
    negatives = int((b < 0).sum())
    prediction_critical = float(t.ppf(0.975, max(k - 2, 1)))
    prediction_radius = prediction_critical * np.sqrt(
        primary["tau_squared"] + primary["random_standard_error"] ** 2
    )

    return {
        "fixed": primary,
        "random_dl": primary,
        "random_modified_hartung_knapp": hksj,
        "equal_system": {
            "coefficient": equal,
            "standard_error": equal_se,
            "p_value": float(2 * t.sf(abs(equal / equal_se), k - 1)),
            "ci_low": equal - equal_critical * equal_se,
            "ci_high": equal + equal_critical * equal_se,
            "k": k,
        },
        "median_system": {"coefficient": float(np.median(b)), "k": k},
        "ten_percent_trimmed": {
            "coefficient": float(np.mean(trimmed)),
            "systems_retained": int(len(trimmed)),
            "k": k,
        },
        "analysis_sample_size_weighted": {
            "coefficient": float(np.sum(size_weights * b)),
            "k": k,
        },
        "sign_test": {
            "negative_systems": negatives,
            "positive_or_zero_systems": k - negatives,
            "one_sided_p_value": float(
                binomtest(negatives, k, 0.5, alternative="greater").pvalue
            ),
        },
        "prediction_interval": {
            "low": float(primary["random_coefficient"] - prediction_radius),
            "high": float(primary["random_coefficient"] + prediction_radius),
        },
        "leave_one_out": {
            "fixed_min": float(leave["fixed_coefficient"].min()),
            "fixed_max": float(leave["fixed_coefficient"].max()),
            "random_min": float(leave["random_coefficient"].min()),
            "random_max": float(leave["random_coefficient"].max()),
            "max_abs_fixed_shift": float(leave["fixed_shift"].abs().max()),
            "max_abs_random_shift": float(leave["random_shift"].abs().max()),
        },
        "leave_rows": leave_rows,
    }


def main() -> int:
    logger = configure_logging("meta_robustness")
    systems = pd.read_csv(
        project_path("output", "tables", "system_main_effects.csv")
    ).sort_values("system").reset_index(drop=True)
    output: dict[str, object] = {}
    influence_rows = []
    for scale in ("points", "sd"):
        summary = distribution_summary(
            systems[f"{scale}_coefficient"].to_numpy(float),
            systems[f"{scale}_standard_error"].to_numpy(float),
            systems["n"].to_numpy(float),
        )
        leave_rows = summary.pop("leave_rows")
        output[scale] = summary
        for system, row in zip(systems["system"], leave_rows):
            influence_rows.append({"scale": scale, "system": system, **row})
        logger.info("%s robustness: %s", scale, summary)

    pd.DataFrame(influence_rows).drop(columns="omitted_index").to_csv(
        project_path("output", "tables", "system_influence.csv"), index=False
    )
    write_json(project_path("output", "tables", "meta_robustness.json"), output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
