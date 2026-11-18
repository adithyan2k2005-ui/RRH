"""Unit tests for context-adjusted expected performance baselines in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.performance.expected_performance import (
    compute_expected_batting_metrics,
    compute_expected_bowling_metrics,
)


class TestExpectedPerformanceUnit:
    """Verifies leave-one-match-out zero-contamination and hierarchical fallback behavior."""

    @pytest.fixture
    def synthetic_multimatch_df(self):
        """Constructs deliveries across 3 matches within identical context."""
        # Context: T20, Middle, 5-7 wkts, 1st innings
        # Match 1: 50 balls, scored 100 runs (2.0 runs/ball)
        # Match 2: 50 balls, scored 50 runs (1.0 runs/ball)
        # Match 3: 50 balls, scored 50 runs (1.0 runs/ball)
        m1 = pd.DataFrame({
            "match_id": [1] * 50, "innings": [1] * 50, "match_format": ["T20"] * 50,
            "bowling_innings_phase": ["Middle"] * 50, "wickets_remaining_before": [6] * 50,
            "is_legal_ball": [True] * 50, "extras_type": [pd.NA] * 50,
            "runs_scored_on_ball": [2] * 50, "runs_charged_to_bowler_on_ball": [2] * 50,
            "is_team_wicket": [False] * 50, "is_bowler_wicket": [False] * 50,
            "dismissed_player_id": [pd.NA] * 50, "striker_id": [101] * 50,
        })
        m2 = pd.DataFrame({
            "match_id": [2] * 50, "innings": [1] * 50, "match_format": ["T20"] * 50,
            "bowling_innings_phase": ["Middle"] * 50, "wickets_remaining_before": [6] * 50,
            "is_legal_ball": [True] * 50, "extras_type": [pd.NA] * 50,
            "runs_scored_on_ball": [1] * 50, "runs_charged_to_bowler_on_ball": [1] * 50,
            "is_team_wicket": [False] * 50, "is_bowler_wicket": [False] * 50,
            "dismissed_player_id": [pd.NA] * 50, "striker_id": [102] * 50,
        })
        m3 = pd.DataFrame({
            "match_id": [3] * 50, "innings": [1] * 50, "match_format": ["T20"] * 50,
            "bowling_innings_phase": ["Middle"] * 50, "wickets_remaining_before": [6] * 50,
            "is_legal_ball": [True] * 50, "extras_type": [pd.NA] * 50,
            "runs_scored_on_ball": [1] * 50, "runs_charged_to_bowler_on_ball": [1] * 50,
            "is_team_wicket": [False] * 50, "is_bowler_wicket": [False] * 50,
            "dismissed_player_id": [pd.NA] * 50, "striker_id": [103] * 50,
        })
        return pd.concat([m1, m2, m3], ignore_index=True)

    def test_leave_one_match_out_prevents_same_match_contamination(self, synthetic_multimatch_df):
        """Verifies Match 1 outcomes do NOT contaminate Match 1 expected baseline."""
        exp = compute_expected_batting_metrics(synthetic_multimatch_df, min_support=20)

        # For Match 1 deliveries:
        # Out-of-fold training matches are Match 2 and Match 3.
        # Match 2 + Match 3 = 100 balls, 100 runs -> expected runs = 1.0 runs/ball!
        # If Match 1 contaminated itself, expected would be (100 + 50 + 50) / 150 = 1.33!
        m1_exp = exp.loc[synthetic_multimatch_df["match_id"] == 1, "expected_batter_runs"]
        assert np.allclose(m1_exp.values, 1.0, atol=0.01)

        # For Match 2 deliveries:
        # Out-of-fold training matches are Match 1 and Match 3.
        # Match 1 + Match 3 = 100 + 50 = 150 runs / 100 balls = 1.50 runs/ball!
        m2_exp = exp.loc[synthetic_multimatch_df["match_id"] == 2, "expected_batter_runs"]
        assert np.allclose(m2_exp.values, 1.50, atol=0.01)

    def test_deterministic_reproducibility(self, synthetic_multimatch_df):
        """Evaluating expected performance twice yields bitwise identical results."""
        exp1 = compute_expected_batting_metrics(synthetic_multimatch_df)
        exp2 = compute_expected_batting_metrics(synthetic_multimatch_df)
        pd.testing.assert_frame_equal(exp1, exp2)
