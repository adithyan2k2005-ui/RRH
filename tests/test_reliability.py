"""Unit tests for player reliability model and uncertainty estimation in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.reliability.uncertainty import apply_empirical_bayes_shrinkage, compute_confidence_intervals
from src.reliability.reliability_model import compute_batter_reliability_scores


class TestReliabilityUnit:
    """Verifies Empirical Bayes shrinkage, CI ordering, eligibility gating, and score bounds."""

    def test_empirical_bayes_shrinkage_pulls_small_samples_to_prior(self):
        """Small samples are heavily shrunk towards prior; large samples retain observed value."""
        # 3 players with same observed mean (+2.0), but sample sizes 2 balls, 20 balls, 200 balls
        means = pd.Series([2.0, 2.0, 2.0], index=[1, 2, 3])
        sizes = pd.Series([2, 20, 200], index=[1, 2, 3])
        prior = 0.0
        k_noise = 20.0

        shrunk, weights = apply_empirical_bayes_shrinkage(means, sizes, population_prior=prior, k_noise=k_noise)

        # Player 1 (n=2): weight = 2 / (2 + 20) = 0.0909 -> shrunk ~ 0.18
        assert shrunk.loc[1] < 0.25
        assert weights.loc[1] < 0.15

        # Player 2 (n=20): weight = 20 / 40 = 0.50 -> shrunk ~ 1.00
        assert shrunk.loc[2] == pytest.approx(1.00, abs=0.05)

        # Player 3 (n=200): weight = 200 / 220 = 0.909 -> shrunk ~ 1.82
        assert shrunk.loc[3] > 1.80

    def test_confidence_intervals_mathematically_ordered(self):
        """Lower confidence bound must be <= estimate <= upper confidence bound."""
        est = pd.Series([0.5, -0.2, 1.2], index=[1, 2, 3])
        std = pd.Series([0.8, 1.1, 0.4], index=[1, 2, 3])
        counts = pd.Series([5, 10, 20], index=[1, 2, 3])

        se, lo, hi = compute_confidence_intervals(est, std, counts, confidence_level=0.90)

        assert (se > 0).all()
        assert (lo <= est).all()
        assert (est <= hi).all()

    def test_reliability_scores_bounds_and_eligibility_gating(self):
        """Reliability scores are bounded in [0, 100] and NaN for ineligible players."""
        df = pd.DataFrame({
            "shrunk_hp_combined_impact": [0.8, -0.5, 0.2],
            "batting_pressure_uplift": [0.5, -0.3, 0.0],
            "positive_match_ratio": [0.8, 0.2, 0.5],
            "worst_quartile_match_impact": [0.3, -0.6, 0.0],
            "shrinkage_weight": [0.8, 0.6, 0.2],
            "cluster_se": [0.2, 0.4, 0.6],
            "eligibility_status": ["ELIGIBLE", "ELIGIBLE", "INELIGIBLE"],
        }, index=[101, 102, 103])

        res = compute_batter_reliability_scores(df)

        # Eligible players have scores in [0, 100]
        assert not pd.isna(res.loc[101, "reliability_score"])
        assert 0.0 <= res.loc[101, "reliability_score"] <= 100.0

        assert not pd.isna(res.loc[102, "reliability_score"])
        assert 0.0 <= res.loc[102, "reliability_score"] <= 100.0

        # Monotonicity: Player 101 (high impact & uplift) must score higher than 102
        assert res.loc[101, "reliability_score"] > res.loc[102, "reliability_score"]

        # Ineligible player must have NaN score
        assert pd.isna(res.loc[103, "reliability_score"])

