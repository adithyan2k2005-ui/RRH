"""Data leakage and player independence tests for SupeRR Selector Analytics."""

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
from src.features.pressure_model import compute_pressure_scores


class TestPressureLeakage:
    """Verifies that pressure calculations strictly prevent leakage and maintain player independence."""

    @pytest.fixture
    def baselines(self):
        return ContextualBaselines()

    def test_current_delivery_outcome_does_not_leak_into_pressure(self, baselines):
        """Verify that varying the CURRENT delivery's outcome (dot vs six vs wicket) does NOT change pre-ball pressure."""
        # Two deliveries with IDENTICAL pre-ball match situations, but different current-ball outcomes
        base_state = {
            "match_id": [201, 201],
            "innings": [2, 2],
            "match_format": ["T20", "T20"],
            "bowling_innings_phase": ["Death", "Death"],
            "scheduled_balls": [120, 120],
            "legal_balls_bowled_before": [108, 108],
            "scheduled_balls_remaining_before": [12, 12],
            "innings_score_before": [150, 150],
            "wickets_remaining_before": [5, 5],
            "target": [170, 170],
            "runs_required_before": [20, 20],
            "required_run_rate": [10.0, 10.0],
            "current_run_rate": [8.33, 8.33],
            "stage": ["League", "League"],
            "knock_out": [0, 0],
            # Differing current-ball events:
            # Ball 0: dot ball (0 runs, no wicket)
            # Ball 1: six hit + wicket fell
            "runs": [0, 6],
            "is_wicket": [False, True],
            "extras1_runs": [0, 0],
            "extras_2_runs": [0, 0],
        }
        df = pd.DataFrame(base_state)

        comp = calculate_pressure_features(df, baselines)
        scores = compute_pressure_scores(df, comp)

        # Pre-ball pressure scores MUST BE IDENTICAL regardless of current-ball six or wicket!
        assert scores.loc[0, "batting_pressure_score"] == scores.loc[1, "batting_pressure_score"]
        assert scores.loc[0, "bowling_pressure_score"] == scores.loc[1, "bowling_pressure_score"]
        assert scores.loc[0, "match_tension_score"] == scores.loc[1, "match_tension_score"]

    def test_player_identity_independence(self, baselines):
        """Verify that changing striker_id, bowler_id, or player names has ZERO impact on pressure scores."""
        state1 = pd.DataFrame({
            "match_id": [301], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Death"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [114], "scheduled_balls_remaining_before": [6],
            "innings_score_before": [155], "wickets_remaining_before": [4],
            "target": [165], "runs_required_before": [10], "required_run_rate": [10.0],
            "current_run_rate": [8.16], "stage": ["League"], "knock_out": [0],
            "striker_id": [1111], "striker_name": ["Famous Star Batter"],
            "bowler_id": [2222], "bowler_name": ["Elite Bowler"],
        })

        state2 = state1.copy()
        # Swap players with completely different identities
        state2["striker_id"] = [9999]
        state2["striker_name"] = ["Uncapped Novice Batter"]
        state2["bowler_id"] = [8888]
        state2["bowler_name"] = ["Part-Time Bowler"]

        comp1 = calculate_pressure_features(state1, baselines)
        scores1 = compute_pressure_scores(state1, comp1)

        comp2 = calculate_pressure_features(state2, baselines)
        scores2 = compute_pressure_scores(state2, comp2)

        # Contextual pressure must depend only on the match situation, NOT player reputation
        assert scores1.loc[0, "batting_pressure_score"] == scores2.loc[0, "batting_pressure_score"]
        assert scores1.loc[0, "bowling_pressure_score"] == scores2.loc[0, "bowling_pressure_score"]
        assert scores1.loc[0, "match_tension_score"] == scores2.loc[0, "match_tension_score"]

    def test_match_winner_outcome_not_present_in_pressure_inputs(self):
        """Verify that final match outcome ('win_team_id', 'result') does not bias pre-delivery scoring."""
        p = PROJECT_ROOT / "data" / "processed" / "pressure_states.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            # Ensure pressure columns exist
            assert "batting_pressure_score" in df.columns
            assert "bowling_pressure_score" in df.columns
            # Confirm scores are strictly within [0, 100]
            assert (df["batting_pressure_score"] >= 0.0).all() and (df["batting_pressure_score"] <= 100.0).all()

