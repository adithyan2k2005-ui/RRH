"""Unit Tests for Ranking Output Formatting and Integrity."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ranking.submission_formatter import format_batter_output, format_bowler_output


def test_format_batter_output_schema():
    """Verifies that format_batter_output creates the exact expected schema without missing values."""
    mock_df = pd.DataFrame({
        "rank": [1],
        "striker_id": [152],
        "player_name": ["Ravindra Jadeja"],
        "reliability_score": [84.80],
        "hp_matches": [23],
        "hp_balls": [233],
        "hp_batter_runs": [382],
        "hp_combined_impact_per_ball": [0.9979],
        "ord_combined_impact_per_ball": [0.0232],
        "batting_pressure_uplift": [0.9747],
        "positive_match_ratio": [0.7391],
        "cluster_se": [0.3051],
        "eligibility_status": ["ELIGIBLE"],
    })

    formatted = format_batter_output(mock_df)

    expected_cols = [
        "rank", "player_id", "player_name", "reliability_score",
        "pressure_matches", "pressure_balls_faced", "pressure_runs",
        "high_pressure_impact", "ordinary_performance_baseline",
        "pressure_uplift", "consistency_metric", "uncertainty_measure",
        "eligibility_status",
    ]
    assert list(formatted.columns) == expected_cols
    assert formatted["player_id"].iloc[0] == 152
    assert formatted["reliability_score"].iloc[0] == 84.80


def test_format_bowler_output_schema():
    """Verifies that format_bowler_output creates the exact expected schema without missing values."""
    mock_df = pd.DataFrame({
        "rank": [1],
        "bowler_id": [7699],
        "player_name": ["Abbas Afridi"],
        "reliability_score": [88.32],
        "hp_matches": [14],
        "hp_balls": [159],
        "hp_runs_conceded": [250],
        "hp_bowler_wickets": [19],
        "hp_combined_impact_per_ball": [1.2669],
        "ord_combined_impact_per_ball": [0.4464],
        "bowling_pressure_uplift": [0.8205],
        "positive_match_ratio": [0.8571],
        "cluster_se": [0.5432],
        "eligibility_status": ["ELIGIBLE"],
    })

    formatted = format_bowler_output(mock_df)

    expected_cols = [
        "rank", "player_id", "player_name", "reliability_score",
        "pressure_matches", "pressure_legal_balls", "pressure_runs_conceded",
        "pressure_wickets", "high_pressure_impact", "ordinary_performance_baseline",
        "pressure_uplift", "consistency_metric", "uncertainty_measure",
        "eligibility_status",
    ]
    assert list(formatted.columns) == expected_cols
    assert formatted["player_id"].iloc[0] == 7699
    assert formatted["pressure_wickets"].iloc[0] == 19

