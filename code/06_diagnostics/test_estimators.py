#!/usr/bin/env python3
"""Small-data unit tests for the custom fixed-effect and multiple-testing code."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03_analyze"))
from estimators import (  # noqa: E402
    benjamini_hochberg,
    fe_betas,
    meta_analysis,
    modified_hartung_knapp,
)


class EstimatorTests(unittest.TestCase):
    def test_absorbed_wls_recovers_slope(self):
        groups = np.repeat(np.arange(20), 10)
        treatment = np.tile(np.r_[np.zeros(5), np.ones(5)], 20)
        group_intercept = np.repeat(np.linspace(-4, 4, 20), 10)
        outcome = group_intercept + 2.75 * treatment
        weights = np.linspace(0.5, 2.0, len(outcome))
        result = fe_betas(outcome, treatment, weights, groups)
        self.assertAlmostEqual(result[0, 0], 2.75, places=12)

    def test_two_outcomes_are_vectorized(self):
        groups = np.repeat(np.arange(5), 8)
        treatment = np.tile(np.r_[np.zeros(4), np.ones(4)], 5)
        outcomes = np.column_stack([treatment, -3 * treatment])
        result = fe_betas(outcomes, treatment, np.ones(len(groups)), groups)
        np.testing.assert_allclose(result, [[1.0, -3.0]], atol=1e-12)

    def test_bh_is_monotone_in_rank(self):
        p = np.array([0.04, 0.001, 0.2, 0.03])
        q = benjamini_hochberg(p)
        ranked = q[np.argsort(p)]
        self.assertTrue(np.all(np.diff(ranked) >= -1e-12))
        self.assertTrue(np.all((q >= p) & (q <= 1)))

    def test_meta_identical_effects(self):
        result = meta_analysis(np.array([1.0, 1.0, 1.0]), np.array([0.2, 0.3, 0.4]))
        self.assertAlmostEqual(result["fixed_coefficient"], 1.0)
        self.assertAlmostEqual(result["random_coefficient"], 1.0)
        self.assertEqual(result["tau_squared"], 0.0)

    def test_modified_hartung_knapp_contains_common_effect(self):
        result = modified_hartung_knapp(
            np.array([1.0, 1.0, 1.0, 1.0]), np.array([0.2, 0.3, 0.4, 0.5])
        )
        self.assertAlmostEqual(result["coefficient"], 1.0)
        self.assertLess(result["ci_low"], 1.0)
        self.assertGreater(result["ci_high"], 1.0)


if __name__ == "__main__":
    unittest.main()
