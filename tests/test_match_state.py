"""Unit tests for match state reconstruction and leakage prevention in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.match_state import reconstruct_match_states


class TestMatchStateUnit:
    """Unit tests using controlled synthetic fixtures to verify match state calculations and zero leakage."""

    @pytest.fixture
    def synthetic_match_data(self):
        """Constructs a clean 2-innings synthetic match for causal testing."""
        # Match metadata: 20 overs, standard match
        matches_df = pd.DataFrame({
            "match_id": [999],
            "comp_id": [10],
            "match_date": ["2024-05-01"],
            "stage": ["League"],
            "knock_out": [0],
            "first_inn_revised_overs": [pd.NA],
            "second_inn_revised_overs": [pd.NA],
            "revised_target": [pd.NA],
            "result": ["Team B won"],
        })

        # Innings 1: 4 deliveries: 1 run, 4 runs, 0 runs (wicket), 2 runs -> Total 7 runs
        inn1 = pd.DataFrame({
            "match_id": [999] * 4,
            "innings": [1] * 4,
            "overid": [1] * 4,
            "over_ball_num": [1, 2, 3, 4],
            "innings_ball_num": [1, 2, 3, 4],
            "runs": [1, 4, 0, 2],
            "extras_type": [None, None, None, None],
            "extras1_runs": [0, 0, 0, 0],
            "extras_2_runs": [0, 0, 0, 0],
            "is_wicket": [False, False, True, False],
            "dismissal_type": [None, None, "Bowled", None],
            "dismissed_player_id": [None, None, 101, None],
            "bowl_speed": [130.0, 132.0, 128.0, 131.0],
        })

        # Innings 2 (Chase target = 7 + 1 = 8): 3 deliveries:
        # Ball 1: wide (1 run)
        # Ball 2: 2 runs
        # Ball 3: 6 runs (target reached)
        inn2 = pd.DataFrame({
            "match_id": [999] * 3,
            "innings": [2] * 3,
            "overid": [1] * 3,
            "over_ball_num": [1, 2, 3],
            "innings_ball_num": [1, 2, 3],
            "runs": [0, 2, 6],
            "extras_type": ["wide", None, None],
            "extras1_runs": [1, 0, 0],
            "extras_2_runs": [0, 0, 0],
            "is_wicket": [False, False, False],
            "dismissal_type": [None, None, None],
            "dismissed_player_id": [None, None, None],
            "bowl_speed": [125.0, 127.0, 129.0],
        })

        bbb_df = pd.concat([inn1, inn2], ignore_index=True)
        return bbb_df, matches_df

    def test_zero_leakage_and_innings_reset(self, synthetic_match_data):
        """Verify pre-delivery states strictly exclude current delivery and reset at innings 2."""
        bbb_df, matches_df = synthetic_match_data
        states = reconstruct_match_states(bbb_df, matches_df)

        # Innings 1 verification
        inn1_states = states[states["innings"] == 1].reset_index(drop=True)

        # Ball 1: Pre-delivery score, wickets, and legal balls MUST be 0
        assert inn1_states.loc[0, "innings_score_before"] == 0
        assert inn1_states.loc[0, "wickets_lost_before"] == 0
        assert inn1_states.loc[0, "wickets_remaining_before"] == 10
        assert inn1_states.loc[0, "legal_balls_bowled_before"] == 0
        assert pd.isna(inn1_states.loc[0, "current_run_rate"])  # No division by zero

        # Ball 2: After Ball 1 (1 run, 0 wkts, 1 legal ball)
        assert inn1_states.loc[1, "innings_score_before"] == 1
        assert inn1_states.loc[1, "wickets_lost_before"] == 0
        assert inn1_states.loc[1, "legal_balls_bowled_before"] == 1
        assert inn1_states.loc[1, "current_run_rate"] == 6.0

        # Ball 3: After Ball 2 (4 runs) -> score = 1 + 4 = 5
        assert inn1_states.loc[2, "innings_score_before"] == 5
        assert inn1_states.loc[2, "wickets_lost_before"] == 0
        assert inn1_states.loc[2, "legal_balls_bowled_before"] == 2

        # Ball 4: After Ball 3 (Wicket fell on Ball 3!)
        # Wicket must now be reflected in pre-ball state of Ball 4
        assert inn1_states.loc[3, "innings_score_before"] == 5
        assert inn1_states.loc[3, "wickets_lost_before"] == 1
        assert inn1_states.loc[3, "wickets_remaining_before"] == 9
        assert inn1_states.loc[3, "legal_balls_bowled_before"] == 3

    def test_second_innings_chase_calculations(self, synthetic_match_data):
        """Verify target setting, runs required, and required run rate progression in chase."""
        bbb_df, matches_df = synthetic_match_data
        states = reconstruct_match_states(bbb_df, matches_df)

        inn2_states = states[states["innings"] == 2].reset_index(drop=True)

        # Target should be Innings 1 total (7) + 1 = 8
        assert (inn2_states["target"] == 8).all()

        # Ball 1 (Wide delivery):
        # Pre-ball score = 0, req runs = 8, balls remaining = 120
        assert inn2_states.loc[0, "innings_score_before"] == 0
        assert inn2_states.loc[0, "runs_required_before"] == 8
        assert inn2_states.loc[0, "scheduled_balls_remaining_before"] == 120
        assert inn2_states.loc[0, "required_run_rate"] == (6.0 * 8) / 120

        # Ball 2 (After Wide):
        # The wide added 1 run to the score, BUT consumed 0 legal balls!
        # Pre-ball score = 1, req runs = 8 - 1 = 7, balls remaining = 120!
        assert inn2_states.loc[1, "innings_score_before"] == 1
        assert inn2_states.loc[1, "runs_required_before"] == 7
        assert inn2_states.loc[1, "legal_balls_bowled_before"] == 0  # 0 legal balls!
        assert inn2_states.loc[1, "scheduled_balls_remaining_before"] == 120  # Still 120!
        assert inn2_states.loc[1, "required_run_rate"] == (6.0 * 7) / 120

        # Ball 3 (After 2 runs scored on legal ball 2):
        # Pre-ball score = 1 + 2 = 3, req runs = 8 - 3 = 5, balls remaining = 119
        assert inn2_states.loc[2, "innings_score_before"] == 3
        assert inn2_states.loc[2, "runs_required_before"] == 5
        assert inn2_states.loc[2, "legal_balls_bowled_before"] == 1
        assert inn2_states.loc[2, "scheduled_balls_remaining_before"] == 119

    def test_dls_revised_target_handling(self):
        """Verify officially revised targets override default (innings 1 + 1) target."""
        matches_df = pd.DataFrame({
            "match_id": [888],
            "first_inn_revised_overs": [pd.NA],
            "second_inn_revised_overs": [90.0],  # 15 overs = 90 balls
            "revised_target": [171.0],          # DLS target
        })

        inn1 = pd.DataFrame({
            "match_id": [888],
            "innings": [1],
            "overid": [1],
            "over_ball_num": [1],
            "innings_ball_num": [1],
            "runs": [4],
            "extras_type": [None],
            "extras1_runs": [0],
            "extras_2_runs": [0],
            "is_wicket": [False],
            "dismissal_type": [None],
            "dismissed_player_id": [None],
        })

        inn2 = pd.DataFrame({
            "match_id": [888],
            "innings": [2],
            "overid": [1],
            "over_ball_num": [1],
            "innings_ball_num": [1],
            "runs": [1],
            "extras_type": [None],
            "extras1_runs": [0],
            "extras_2_runs": [0],
            "is_wicket": [False],
            "dismissal_type": [None],
            "dismissed_player_id": [None],
        })

        bbb_df = pd.concat([inn1, inn2], ignore_index=True)
        states = reconstruct_match_states(bbb_df, matches_df)

        inn2_state = states[states["innings"] == 2].iloc[0]

        assert inn2_state["target"] == 171
        assert inn2_state["is_target_revised"] == True
        assert inn2_state["scheduled_balls"] == 90
        assert inn2_state["scheduled_balls_remaining_before"] == 90
        assert inn2_state["runs_required_before"] == 171
        assert inn2_state["required_run_rate"] == (6.0 * 171) / 90

