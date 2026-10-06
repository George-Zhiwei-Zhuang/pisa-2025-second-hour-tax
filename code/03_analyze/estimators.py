"""Survey-weighted fixed-effect estimators for PISA plausible values and BRR-Fay."""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy.stats import norm, t


@dataclass
class Estimate:
    coefficient: float
    standard_error: float
    variance_sampling: float
    variance_plausible: float
    p_value: float
    ci_low: float
    ci_high: float
    n: int
    groups: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _as_2d(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return values[:, None] if values.ndim == 1 else values


def weighted_mean_sd(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    mean = np.average(values[valid], weights=weights[valid])
    variance = np.average((values[valid] - mean) ** 2, weights=weights[valid])
    return float(mean), float(np.sqrt(variance))


def standardize_columns(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    values = _as_2d(values).copy()
    for column in range(values.shape[1]):
        mean, sd = weighted_mean_sd(values[:, column], weights)
        values[:, column] = (values[:, column] - mean) / sd
    return values


def enforce_mixed_groups(
    frame: pd.DataFrame, group_col: str, treatment_col: str
) -> pd.DataFrame:
    mixed = frame.groupby(group_col, observed=True)[treatment_col].transform("nunique")
    return frame.loc[mixed.eq(2)].copy()


def fe_betas(
    outcomes: np.ndarray,
    regressors: np.ndarray,
    weights: np.ndarray,
    groups: np.ndarray,
) -> np.ndarray:
    """Return WLS slopes after absorbing a single set of group fixed effects."""
    y = _as_2d(outcomes)
    x = _as_2d(regressors)
    w = np.asarray(weights, dtype=float)
    group_codes, _ = pd.factorize(groups, sort=False)
    valid = (
        np.isfinite(w)
        & (w > 0)
        & (group_codes >= 0)
        & np.isfinite(x).all(axis=1)
        & np.isfinite(y).all(axis=1)
    )
    y = y[valid]
    x = x[valid]
    w = w[valid]
    group_codes = group_codes[valid]
    _, group_codes = np.unique(group_codes, return_inverse=True)
    group_count = int(group_codes.max()) + 1
    group_weight = np.bincount(group_codes, weights=w, minlength=group_count)
    if np.any(group_weight <= 0):
        raise ValueError("Fixed-effect group with non-positive total weight")

    x_means = np.column_stack(
        [
            np.bincount(group_codes, weights=w * x[:, j], minlength=group_count)
            / group_weight
            for j in range(x.shape[1])
        ]
    )
    y_means = np.column_stack(
        [
            np.bincount(group_codes, weights=w * y[:, j], minlength=group_count)
            / group_weight
            for j in range(y.shape[1])
        ]
    )
    x_within = x - x_means[group_codes]
    y_within = y - y_means[group_codes]
    cross_x = x_within.T @ (w[:, None] * x_within)
    cross_xy = x_within.T @ (w[:, None] * y_within)
    try:
        return np.linalg.solve(cross_x, cross_xy)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(cross_x) @ cross_xy


def _estimate_from_variance(
    coefficient: float,
    sampling: float,
    plausible: float,
    n: int,
    groups: int,
) -> Estimate:
    total = max(0.0, sampling + plausible)
    se = float(np.sqrt(total))
    z = coefficient / se if se > 0 else np.nan
    p = float(2 * norm.sf(abs(z))) if np.isfinite(z) else np.nan
    return Estimate(
        coefficient=float(coefficient),
        standard_error=se,
        variance_sampling=float(sampling),
        variance_plausible=float(plausible),
        p_value=p,
        ci_low=float(coefficient - 1.96 * se),
        ci_high=float(coefficient + 1.96 * se),
        n=int(n),
        groups=int(groups),
    )


def survey_pv(
    frame: pd.DataFrame,
    outcomes: np.ndarray,
    regressors: np.ndarray,
    groups: np.ndarray,
    coefficient_index: int,
    final_weight: str = "W_FSTUWT",
    replicate_prefix: str = "W_FSTURWT",
    replicates: int = 80,
    fay_factor: float = 0.05,
) -> Estimate:
    """Combine 10 plausible values with 80 BRR-Fay replicate estimates."""
    y = _as_2d(outcomes)
    x = _as_2d(regressors)
    full = fe_betas(y, x, frame[final_weight].to_numpy(float), groups)
    replicate_betas = np.empty((replicates, full.shape[0], full.shape[1]))
    for r in range(1, replicates + 1):
        replicate_betas[r - 1] = fe_betas(
            y,
            x,
            frame[f"{replicate_prefix}{r}"].to_numpy(float),
            groups,
        )
    chosen_full = full[coefficient_index]
    chosen_replicates = replicate_betas[:, coefficient_index, :]
    sampling_by_pv = fay_factor * np.square(chosen_replicates - chosen_full).sum(axis=0)
    sampling = float(sampling_by_pv.mean())
    plausible_between = float(np.var(chosen_full, ddof=1)) if y.shape[1] > 1 else 0.0
    plausible = (1.0 + 1.0 / y.shape[1]) * plausible_between
    return _estimate_from_variance(
        coefficient=float(chosen_full.mean()),
        sampling=sampling,
        plausible=plausible,
        n=len(frame),
        groups=pd.Series(groups).nunique(),
    )


def survey_observed(
    frame: pd.DataFrame,
    outcome: np.ndarray,
    regressors: np.ndarray,
    groups: np.ndarray,
    coefficient_index: int,
    final_weight: str = "W_FSTUWT",
    replicate_prefix: str = "W_FSTURWT",
    replicates: int = 80,
    fay_factor: float = 0.05,
) -> Estimate:
    y = _as_2d(outcome)
    x = _as_2d(regressors)
    full = fe_betas(y, x, frame[final_weight].to_numpy(float), groups)[
        coefficient_index, 0
    ]
    replicate_betas = np.empty(replicates)
    for r in range(1, replicates + 1):
        replicate_betas[r - 1] = fe_betas(
            y,
            x,
            frame[f"{replicate_prefix}{r}"].to_numpy(float),
            groups,
        )[coefficient_index, 0]
    sampling = float(fay_factor * np.square(replicate_betas - full).sum())
    return _estimate_from_variance(
        coefficient=float(full),
        sampling=sampling,
        plausible=0.0,
        n=len(frame),
        groups=pd.Series(groups).nunique(),
    )


def meta_analysis(coefficients: np.ndarray, standard_errors: np.ndarray) -> dict[str, float | int]:
    coefficients = np.asarray(coefficients, float)
    standard_errors = np.asarray(standard_errors, float)
    valid = np.isfinite(coefficients) & np.isfinite(standard_errors) & (standard_errors > 0)
    b = coefficients[valid]
    v = standard_errors[valid] ** 2
    k = len(b)
    fixed_weights = 1.0 / v
    fixed = float(np.sum(fixed_weights * b) / np.sum(fixed_weights))
    fixed_se = float(np.sqrt(1.0 / np.sum(fixed_weights)))
    q = float(np.sum(fixed_weights * (b - fixed) ** 2))
    c = float(np.sum(fixed_weights) - np.sum(fixed_weights**2) / np.sum(fixed_weights))
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    random_weights = 1.0 / (v + tau2)
    random = float(np.sum(random_weights * b) / np.sum(random_weights))
    random_se = float(np.sqrt(1.0 / np.sum(random_weights)))
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
    return {
        "k": k,
        "fixed_coefficient": fixed,
        "fixed_standard_error": fixed_se,
        "fixed_p_value": float(2 * norm.sf(abs(fixed / fixed_se))),
        "fixed_ci_low": fixed - 1.96 * fixed_se,
        "fixed_ci_high": fixed + 1.96 * fixed_se,
        "random_coefficient": random,
        "random_standard_error": random_se,
        "random_p_value": float(2 * norm.sf(abs(random / random_se))),
        "random_ci_low": random - 1.96 * random_se,
        "random_ci_high": random + 1.96 * random_se,
        "tau_squared": tau2,
        "q": q,
        "i_squared": i2,
    }


def modified_hartung_knapp(
    coefficients: np.ndarray, standard_errors: np.ndarray
) -> dict[str, float | int]:
    """Modified Hartung-Knapp inference around a DL random-effects mean.

    The variance scale is bounded below by one, avoiding an anti-conservative
    Hartung-Knapp interval when observed dispersion happens to be unusually small.
    """
    coefficients = np.asarray(coefficients, float)
    standard_errors = np.asarray(standard_errors, float)
    valid = (
        np.isfinite(coefficients)
        & np.isfinite(standard_errors)
        & (standard_errors > 0)
    )
    b = coefficients[valid]
    v = standard_errors[valid] ** 2
    k = len(b)
    if k < 2:
        raise ValueError("Modified Hartung-Knapp inference requires at least two studies")
    dl = meta_analysis(b, np.sqrt(v))
    tau2 = float(dl["tau_squared"])
    weights = 1.0 / (v + tau2)
    coefficient = float(np.sum(weights * b) / np.sum(weights))
    residual_scale = float(np.sum(weights * (b - coefficient) ** 2) / (k - 1))
    variance = max(1.0, residual_scale) / np.sum(weights)
    standard_error = float(np.sqrt(variance))
    critical = float(t.ppf(0.975, df=k - 1))
    statistic = coefficient / standard_error
    return {
        "k": k,
        "coefficient": coefficient,
        "standard_error": standard_error,
        "p_value": float(2 * t.sf(abs(statistic), df=k - 1)),
        "ci_low": coefficient - critical * standard_error,
        "ci_high": coefficient + critical * standard_error,
        "degrees_freedom": k - 1,
        "tau_squared": tau2,
        "residual_scale": residual_scale,
    }


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    p = np.asarray(p_values, float)
    result = np.full_like(p, np.nan)
    valid = np.isfinite(p)
    order = np.argsort(p[valid])
    ranked = p[valid][order]
    adjusted = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    unsorted = np.empty_like(adjusted)
    unsorted[order] = np.minimum(adjusted, 1.0)
    result[valid] = unsorted
    return result
