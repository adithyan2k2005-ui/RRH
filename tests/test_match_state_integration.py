"""Integration tests for match state reconstruction using actual dataset records."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.match_state import reconstruct_match_states
from src.validation.validate_match_state import validate_reconstructed_states


@pytest.fixture(scope="module")
def processed_data():
    """Loads actual processed datasets for integration testing."""
    p = PROJECT_ROOT / "data" / "processed"
    bbb_df = pd.read_parquet(p / "ball_by_ball.parquet")
    matches_df = pd.read_parquet(p / "matches.parquet")
    comps_df = pd.read_parquet(p / "competitions.parquet")
    return bbb_df, matches_df, comps_df


class TestMatchStateIntegration:
    """Integration tests on actual supplied tournament records."""

    def test_full_dataset_reconstruction_integrity(self, processed_data):
        """Verify reconstruct_match_states processes all 200,999 rows without loss."""
        bbb_df, matches_df, comps_df = processed_data
        states = reconstruct_match_states(bbb_df, matches_df, comps_df)

        assert len(states) == len(bbb_df)
        assert len(states) == 200999

        # Required columns present
        required_cols = [
            "match_id", "innings", "delivery_seq", "is_legal_ball",
            "runs_scored_on_ball", "team_runs_on_ball", "runs_charged_to_bowler_on_ball",
            "is_team_wicket", "is_bowler_wicket", "bowling_innings_phase",
            "innings_score_before", "wickets_lost_before", "wickets_remaining_before",
            "legal_balls_bowled_before", "scheduled_balls_remaining_before",
            "current_run_rate", "target", "runs_required_before", "required_run_rate",
            "is_target_revised", "reconstruction_status", "is_pressure_ready"
        ]
        for col in required_cols:
            assert col in states.columns, f"Missing output feature: {col}"

    def test_zero_future_leakage_across_all_innings(self, processed_data):
        """Verify strict zero future data leakage across all 1,724 real innings."""
        bbb_df, matches_df, comps_df = processed_data
        states = reconstruct_match_states(bbb_df, matches_df, comps_df)

        metrics = validate_reconstructed_states(states, matches_df)

        assert metrics["leakage_score_violations"] == 0
        assert metrics["leakage_wickets_violations"] == 0
        assert metrics["leakage_legal_balls_violations"] == 0
        assert metrics["cumulative_score_mismatches"] == 0
        assert metrics["chase_runs_required_discrepancies"] == 0

    def test_super_overs_reconstruction(self, processed_data):
        """Verify Super Over innings (3 and 4) are reconstructed with 6 scheduled balls."""
        bbb_df, matches_df, comps_df = processed_data
        states = reconstruct_match_states(bbb_df, matches_df, comps_df)

        super_overs = states[states["innings"].isin([3, 4])]
        assert len(super_overs) > 0

        # Scheduled balls must be 6 for Super Overs
        assert (super_overs["scheduled_balls"] == 6).all()
        assert (super_overs["bowling_innings_phase"] == "SuperOver").all()

        # Innings 4 (chase) must have a target set from Innings 3
        inn4 = super_overs[super_overs["innings"] == 4]
        assert inn4["target"].notnull().all()

    def test_saved_match_states_parquet_readable(self):
        """Verify data/processed/match_states.parquet exists and has valid schema."""
        parquet_path = PROJECT_ROOT / "data" / "processed" / "match_states.parquet"
        assert parquet_path.exists(), "match_states.parquet does not exist"

        df = pd.read_parquet(parquet_path)
        assert len(df) == 200999
        assert "innings_score_before" in df.columns
        assert "required_run_rate" in df.columns
        assert (df["is_pressure_ready"] == True).all()

