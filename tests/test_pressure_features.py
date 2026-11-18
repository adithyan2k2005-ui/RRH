"""Unit tests for pressure factor components in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.pressure_baselines import ContextualBaselines
from src.features.pressure_features import calculate_pressure_features


class TestPressureFeaturesUnit:
    """Unit tests verifying mathematical behavior of normalized pressure factors."""

    @pytest.fixture
    def sample_states(self):
        """Constructs synthetic match states across varying chase and 1st innings situations."""
        return pd.DataFrame({
            "match_id": [1, 1, 2, 2],
            "innings": [2, 2, 1, 1],
            "match_format": ["T20", "T20", "T20I", "T20I"],
            "bowling_innings_phase": ["Middle", "Death", "Powerplay", "Middle"],
            "scheduled_balls": [120, 120, 120, 120],
            "legal_balls_bowled_before": [60, 114, 24, 60],
            "scheduled_balls_remaining_before": [60, 6, 96, 60],
            "innings_score_before": [60, 150, 20, 50],
            "wickets_remaining_before": [9, 3, 8, 2],
            "target": [150, 180, pd.NA, pd.NA],
            "runs_required_before": [90, 30, pd.NA, pd.NA],
            "required_run_rate": [9.0, 30.0, pd.NA, pd.NA],
            "current_run_rate": [6.0, 7.89, 5.0, 5.0],
            "stage": ["League", "Final", "League", "League"],
            "knock_out": [0, 1, 0, 0],
        })

    def test_wicket_vulnerability_bounds_and_monotonicity(self, sample_states):
        """Verify wicket vulnerability increases non-linearly as wickets in hand decrease."""
        comp = calculate_pressure_features(sample_states)
        v = comp["wicket_vulnerability"]

        assert (v >= 0.0).all() and (v <= 1.0).all()
        # Row 0 (9 wickets in hand) should have much lower vulnerability than Row 1 (3 in hand)
        assert v.iloc[0] < v.iloc[1]
        # Row 3 (2 in hand) should have very high vulnerability
        assert v.iloc[3] > 0.70

    def test_time_pressure_increases_with_overs_bowled(self, sample_states):
        """Verify time pressure approaches 1.0 as legal balls are consumed."""
        comp = calculate_pressure_features(sample_states)
        t = comp["time_pressure"]

        assert (t >= 0.0).all() and (t <= 1.0).all()
        # Over 10 (60 balls) = 0.50
        assert t.iloc[0] == pytest.approx(0.50, abs=0.01)
        # Over 19 (114 balls) = 0.95
        assert t.iloc[1] == pytest.approx(0.95, abs=0.01)

    def test_chase_urgency_responds_to_required_run_rate(self, sample_states):
        """Verify chase urgency is high for steep RRR and low for easy chases."""
        comp = calculate_pressure_features(sample_states)
        u = comp["chase_urgency"]

        # Row 0: RRR 9.0 (around par) -> ~0.40 - 0.55
        assert 0.30 <= u.iloc[0] <= 0.60
        # Row 1: RRR 30.0 (extreme rate needed) -> > 0.95
        assert u.iloc[1] > 0.90
        # Row 2 & 3: First innings -> NaN
        assert pd.isna(u.iloc[2]) and pd.isna(u.iloc[3])

    def test_match_closeness_peaks_near_par_in_chase(self, sample_states):
        """Verify match closeness peaks when match is in the balance."""
        comp = calculate_pressure_features(sample_states)
        c = comp["match_closeness"]

        # Row 0 (RRR 9.0, around par) should have high closeness
        assert c.iloc[0] > 0.50
        # Row 1 (RRR 30.0, virtually impossible chase) should have low closeness
        assert c.iloc[1] < 0.10

    def test_knockout_stakes_multiplier(self, sample_states):
        """Verify knockout fixtures receive expected 1.15 stakes multiplier."""
        comp = calculate_pressure_features(sample_states)
        s = comp["match_stakes_multiplier"]

        assert s.iloc[0] == 1.00  # League
        assert s.iloc[1] == 1.15  # Final (Knockout)

