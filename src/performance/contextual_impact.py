"""Contextual Impact and Performance Residuals Module for SupeRR Selector Analytics.

Computes delivery-level context-adjusted residuals for batting and bowling:
- batting_run_impact: actual batter runs minus context expected runs
- batting_dismissal_impact: expected dismissal risk minus actual dismissal (wicket preservation)
- batting_combined_impact: runs-equivalent combined impact (with documented wicket value)
- bowling_run_impact: expected runs conceded minus actual runs conceded (run prevention)
- bowling_wicket_impact: actual wickets taken minus expected wickets
- bowling_combined_impact: runs-equivalent combined bowling impact
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_WICKET_VALUE_RUNS = 20.0


def compute_batting_impact_residuals(
    df: pd.DataFrame,
    expected_batting_df: pd.DataFrame,
    wicket_value: float = DEFAULT_WICKET_VALUE_RUNS,
) -> pd.DataFrame:
    """Computes delivery-level batting residuals against context-adjusted expectations.

    Args:
        df: Ball-by-ball DataFrame.
        expected_batting_df: Expected batting DataFrame from compute_expected_batting_metrics.
        wicket_value: Runs-equivalent value attributed to a wicket (default 20.0).

    Returns:
        pd.DataFrame: Aligned DataFrame with delivery impact columns:
            - batting_run_impact (float64)
            - batting_dismissal_impact (float64)
            - batting_combined_impact (float64)
            - is_ball_faced (bool)
    """
    extras_type = df["extras_type"].fillna("").astype(str)
    is_legal = df["is_legal_ball"].fillna(False).astype(bool)
    is_ball_faced = is_legal | extras_type.isin(["Overstep", "other"])

    actual_runs = df["runs_scored_on_ball"].fillna(0).astype("float64")
    expected_runs = expected_batting_df["expected_batter_runs"].astype("float64")

    # Dismissal
    is_team_wkt = df["is_team_wicket"].fillna(False).astype(bool)
    dismissed_id = df["dismissed_player_id"].fillna(-999).astype("int64")
    striker_id = df["striker_id"].fillna(-888).astype("int64")
    is_striker_wkt = (is_team_wkt & (dismissed_id == striker_id)).astype("float64")
    if "is_retired_hurt" in df.columns:
        is_striker_wkt = is_striker_wkt * (~df["is_retired_hurt"].fillna(False).astype(bool)).astype("float64")

    exp_wkt_risk = expected_batting_df["expected_batter_dismissal_risk"].astype("float64")

    # Run impact: only for balls faced by the batter; 0 on wides (batter didn't face)
    run_impact = np.where(is_ball_faced, actual_runs - expected_runs, 0.0)

    # Dismissal impact: (expected_risk - actual_dismissal)
    # Positive when batter survives (gain = exp_wkt_risk); negative when out (loss = -(1 - exp_wkt_risk))
    dismissal_impact = np.where(is_ball_faced, exp_wkt_risk - is_striker_wkt, 0.0)

    # Combined run impact in runs-equivalent units
    combined_impact = run_impact + (wicket_value * dismissal_impact)

    return pd.DataFrame({
        "batting_run_impact": np.round(run_impact, 4),
        "batting_dismissal_impact": np.round(dismissal_impact, 4),
        "batting_combined_impact": np.round(combined_impact, 4),
        "is_ball_faced": is_ball_faced,
    }, index=df.index)


def compute_bowling_impact_residuals(
    df: pd.DataFrame,
    expected_bowling_df: pd.DataFrame,
    wicket_value: float = DEFAULT_WICKET_VALUE_RUNS,
) -> pd.DataFrame:
    """Computes delivery-level bowling residuals against context-adjusted expectations.

    Args:
        df: Ball-by-ball DataFrame.
        expected_bowling_df: Expected bowling DataFrame from compute_expected_bowling_metrics.
        wicket_value: Runs-equivalent value attributed to a wicket (default 20.0).

    Returns:
        pd.DataFrame: Aligned DataFrame with delivery impact columns:
            - bowling_run_impact (float64, positive indicates run prevention)
            - bowling_wicket_impact (float64, positive indicates wicket taken)
            - bowling_combined_impact (float64, positive indicates overall excellence)
            - is_legal_ball (bool)
    """
    is_legal = df["is_legal_ball"].fillna(False).astype(bool)

    actual_runs = df["runs_charged_to_bowler_on_ball"].fillna(0).astype("float64")
    expected_runs = expected_bowling_df["expected_bowler_conceded_runs"].astype("float64")

    actual_wkt = df["is_bowler_wicket"].fillna(False).astype("float64")
    expected_wkt = expected_bowling_df["expected_bowler_wickets"].astype("float64")

    # Run impact: expected conceded minus actual conceded (positive = run prevention)
    run_impact = np.where(is_legal, expected_runs - actual_runs, 0.0)

    # Wicket impact: actual bowler wickets minus expected wickets
    wicket_impact = np.where(is_legal, actual_wkt - expected_wkt, 0.0)

    # Combined bowling impact in runs-equivalent units
    combined_impact = run_impact + (wicket_value * wicket_impact)

    return pd.DataFrame({
        "bowling_run_impact": np.round(run_impact, 4),
        "bowling_wicket_impact": np.round(wicket_impact, 4),
        "bowling_combined_impact": np.round(combined_impact, 4),
        "is_legal_ball": is_legal,
    }, index=df.index)

