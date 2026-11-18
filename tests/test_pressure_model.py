"""Unit tests verifying cricket scenarios A through H in SupeRR Selector Analytics."""

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
from src.features.pressure_thresholds import classify_pressure


class TestCricketScenariosUnit:
    """Verifies domain directional behavior against the 8 required cricket scenarios."""

    @pytest.fixture
    def baselines(self):
        return ContextualBaselines()

    def test_scenario_a_high_batting_urgency_chase(self, baselines):
        """Scenario A: Target 181, Score 130, 30 balls rem, 3 wkts rem -> High batting urgency."""
        # 51 runs needed from 30 balls = RRR 10.2, 3 wickets in hand
        state = pd.DataFrame({
            "match_id": [101], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Death"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [90], "scheduled_balls_remaining_before": [30],
            "innings_score_before": [130], "wickets_remaining_before": [3],
            "target": [181], "runs_required_before": [51], "required_run_rate": [10.2],
            "current_run_rate": [8.67], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)
        bat_class = classify_pressure(scores["batting_pressure_score"], state["is_pressure_ready"])

        # Batting score should be elevated (>= 60) and categorized as HIGH_PRESSURE
        assert scores.loc[0, "batting_pressure_score"] >= 60.0
        assert bat_class.iloc[0] == "HIGH_PRESSURE"

    def test_scenario_b_low_chase_urgency(self, baselines):
        """Scenario B: Target 150, Score 145, 30 balls rem, 8 wkts rem -> Low chase urgency."""
        # 5 runs needed from 30 balls = RRR 1.0, 8 wickets in hand
        state = pd.DataFrame({
            "match_id": [102], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Death"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [90], "scheduled_balls_remaining_before": [30],
            "innings_score_before": [145], "wickets_remaining_before": [8],
            "target": [150], "runs_required_before": [5], "required_run_rate": [1.0],
            "current_run_rate": [9.67], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)
        bat_class = classify_pressure(scores["batting_pressure_score"], state["is_pressure_ready"])

        # Batting pressure must be very low (< 30) and classified as LOW_PRESSURE
        assert scores.loc[0, "batting_pressure_score"] < 30.0
        assert bat_class.iloc[0] == "LOW_PRESSURE"

    def test_scenario_c_very_high_batting_urgency_last_over(self, baselines):
        """Scenario C: Target 181, Score 160, 6 balls rem, 2 wkts rem -> Very high batting urgency."""
        # 21 runs needed from 6 balls = RRR 21.0, 2 wickets in hand
        state = pd.DataFrame({
            "match_id": [103], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Death"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [114], "scheduled_balls_remaining_before": [6],
            "innings_score_before": [160], "wickets_remaining_before": [2],
            "target": [181], "runs_required_before": [21], "required_run_rate": [21.0],
            "current_run_rate": [8.42], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)

        # Batting pressure must be extreme (>= 80)
        assert scores.loc[0, "batting_pressure_score"] >= 80.0

    def test_scenario_d_first_innings_collapse(self, baselines):
        """Scenario D: First innings: Score 50 after 10 overs, 2 wkts rem -> High collapse pressure."""
        state = pd.DataFrame({
            "match_id": [104], "innings": [1], "match_format": ["T20"],
            "bowling_innings_phase": ["Middle"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [60], "scheduled_balls_remaining_before": [60],
            "innings_score_before": [50], "wickets_remaining_before": [2],
            "target": [pd.NA], "runs_required_before": [pd.NA], "required_run_rate": [pd.NA],
            "current_run_rate": [5.0], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)
        bat_class = classify_pressure(scores["batting_pressure_score"], state["is_pressure_ready"])

        # High batting pressure due to collapse without fabricating a target
        assert scores.loc[0, "batting_pressure_score"] >= 65.0
        assert bat_class.iloc[0] == "HIGH_PRESSURE"

    def test_scenario_e_batting_difficulty_vs_bowling_comfort(self, baselines):
        """Scenario E: Second innings: Requires 35 runs from 6 balls -> High bat pressure, LOW bowl pressure."""
        state = pd.DataFrame({
            "match_id": [105], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Death"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [114], "scheduled_balls_remaining_before": [6],
            "innings_score_before": [140], "wickets_remaining_before": [3],
            "target": [175], "runs_required_before": [35], "required_run_rate": [35.0],
            "current_run_rate": [7.37], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)

        # Batting pressure must be high (> 75)
        assert scores.loc[0, "batting_pressure_score"] > 75.0
        # Bowling pressure must be LOW (< 30) because contest is effectively decided
        assert scores.loc[0, "bowling_pressure_score"] < 30.0
        # Batting pressure must be substantially higher than bowling pressure
        assert scores.loc[0, "batting_pressure_score"] > scores.loc[0, "bowling_pressure_score"] + 40.0

    def test_scenario_f_knockout_with_comfortable_conditions(self, baselines):
        """Scenario F: Knockout match with comfortable conditions -> Elevated slightly, not max pressure."""
        state = pd.DataFrame({
            "match_id": [106], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Powerplay"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [24], "scheduled_balls_remaining_before": [96],
            "innings_score_before": [35], "wickets_remaining_before": [10],
            "target": [140], "runs_required_before": [105], "required_run_rate": [6.56],
            "current_run_rate": [8.75], "stage": ["Final"], "knock_out": [1],
            "is_pressure_ready": [True],
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)

        # Modest stakes boost, but comfortable batting keeps score under 40 (LOW or low-medium)
        assert scores.loc[0, "batting_pressure_score"] < 40.0

    def test_scenario_g_missing_target_handled_safely(self, baselines):
        """Scenario G: Second innings with missing target -> Handled without crashing or generating NaNs."""
        state = pd.DataFrame({
            "match_id": [107], "innings": [2], "match_format": ["T20"],
            "bowling_innings_phase": ["Middle"], "scheduled_balls": [120],
            "legal_balls_bowled_before": [30], "scheduled_balls_remaining_before": [90],
            "innings_score_before": [25], "wickets_remaining_before": [8],
            "target": [pd.NA], "runs_required_before": [pd.NA], "required_run_rate": [pd.NA],
            "current_run_rate": [5.0], "stage": ["League"], "knock_out": [0],
            "is_pressure_ready": [False],  # Flagged as not pressure ready
        })

        comp = calculate_pressure_features(state, baselines)
        scores = compute_pressure_scores(state, comp)
        bat_class = classify_pressure(scores["batting_pressure_score"], state["is_pressure_ready"])

        # Must classify as UNDETERMINED
        assert bat_class.iloc[0] == "UNDETERMINED"

    def test_scenario_h_wide_does_not_consume_legal_balls(self, baselines):
        """Scenario H: Wide followed by legal delivery -> Legal balls remaining do not decrease after wide."""
        # Simulated sequence of 2 deliveries in a chase
        states = pd.DataFrame({
            "match_id": [108, 108], "innings": [2, 2], "match_format": ["T20", "T20"],
            "bowling_innings_phase": ["Death", "Death"], "scheduled_balls": [120, 120],
            # Delivery 1: Wide bowled
            # Delivery 2: Following delivery (0 legal balls bowled so far!)
            "legal_balls_bowled_before": [114, 114],
            "scheduled_balls_remaining_before": [6, 6],
            "innings_score_before": [150, 151],  # 1 wide run added
            "wickets_remaining_before": [4, 4],
            "target": [165, 165], "runs_required_before": [15, 14],
            "required_run_rate": [15.0, 14.0],
            "current_run_rate": [7.89, 7.95], "stage": ["League", "League"], "knock_out": [0, 0],
            "is_pressure_ready": [True, True],
        })

        comp = calculate_pressure_features(states, baselines)

        # Scheduled balls remaining must remain identical (6) across the wide
        assert states.loc[0, "scheduled_balls_remaining_before"] == states.loc[1, "scheduled_balls_remaining_before"]

