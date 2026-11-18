"""Unit Tests for Ranking Stability and Correlation Metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ranking.ranking_stability import compute_rank_correlations


def test_compute_rank_correlations_perfect():
    """Verifies that perfectly monotonically aligned series yield correlation = 1.0."""
    s1 = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    s2 = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0])

    rho, tau = compute_rank_correlations(s1, s2)
    assert pytest.approx(rho, abs=1e-4) == 1.0
    assert pytest.approx(tau, abs=1e-4) == 1.0


def test_compute_rank_correlations_inverted():
    """Verifies that perfectly reversed series yield correlation = -1.0."""
    s1 = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    s2 = pd.Series([50.0, 40.0, 30.0, 20.0, 10.0])

    rho, tau = compute_rank_correlations(s1, s2)
    assert pytest.approx(rho, abs=1e-4) == -1.0
    assert pytest.approx(tau, abs=1e-4) == -1.0

