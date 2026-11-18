"""Bowling Performance Metrics Module for SupeRR Selector Analytics.

Calculates verified cricket conventional bowling statistics and pressure segmentations
using verified scoring semantics:
- Byes and leg-byes are excluded from bowler-conceded runs.
- Wides and no-balls are included in bowler-conceded runs.
- Run-outs are not credited to the bowler.
- Overs are counted strictly from legal deliveries (legal_balls / 6.0).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_delivery_bowling_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Computes delivery-level bowling indicators according to cricket laws.

    Args:
        df: Ball-by-ball match states DataFrame.

    Returns:
        pd.DataFrame: DataFrame of bowling indicator columns aligned with df.index:
            - is_legal_ball (bool)
            - bowler_runs_conceded (int64)
            - is_bowler_wicket (bool)
            - is_bowler_dot_ball (bool)
            - is_boundary_conceded (bool)
    """
    is_legal = df["is_legal_ball"].fillna(False).astype(bool)
    runs_conceded = df["runs_charged_to_bowler_on_ball"].fillna(0).astype("int64")
    is_wkt = df["is_bowler_wicket"].fillna(False).astype(bool)

    is_dot = is_legal & (runs_conceded == 0)

    # Boundaries conceded off bowler
    is_four = (df["is_four"] == 1) | (df["is_four"] is True) | (df["runs_scored_on_ball"] == 4)
    is_six = (df["is_six"] == 1) | (df["is_six"] is True) | (df["runs_scored_on_ball"] == 6)
    is_boundary = is_legal & (is_four | is_six)

    return pd.DataFrame({
        "is_legal_ball": is_legal,
        "bowler_runs_conceded": runs_conceded,
        "is_bowler_wicket": is_wkt,
        "is_bowler_dot_ball": is_dot,
        "is_boundary_conceded": is_boundary,
    }, index=df.index)


def compute_player_bowling_aggregate(
    df: pd.DataFrame,
    bowling_flags: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggregates bowling metrics to the player level across overall, HP, and ordinary regimes.

    Args:
        df: Ball-by-ball DataFrame containing match and player identifiers.
        bowling_flags: Precomputed bowling flags (or None to compute inline).

    Returns:
        pd.DataFrame: Player-level bowling statistics indexed by bowler_id.
    """
    if bowling_flags is None:
        bowling_flags = compute_delivery_bowling_flags(df)

    work = df[["match_id", "innings", "comp_id", "bowler_id", "bowler_name", "bowling_pressure_class"]].copy()
    for col in bowling_flags.columns:
        work[col] = bowling_flags[col]

    work["innings_key"] = work["match_id"].astype(str) + "__" + work["innings"].astype(str)
    work["is_hp"] = work["bowling_pressure_class"] == "HIGH_PRESSURE"
    work["is_ord"] = work["bowling_pressure_class"] != "HIGH_PRESSURE"
    work["is_lp"] = work["bowling_pressure_class"] == "LOW_PRESSURE"

    # Group by bowler_id
    grouped = work.groupby("bowler_id")

    player_names = grouped["bowler_name"].first()
    comp_counts = grouped["comp_id"].nunique()
    total_matches = grouped["match_id"].nunique()
    total_innings = grouped["innings_key"].nunique()

    total_legal_balls = grouped["is_legal_ball"].sum()
    total_overs = np.round(total_legal_balls / 6.0, 2)
    total_runs_conceded = grouped["bowler_runs_conceded"].sum()
    total_wickets = grouped["is_bowler_wicket"].sum()
    total_dots = grouped["is_bowler_dot_ball"].sum()
    total_boundaries = grouped["is_boundary_conceded"].sum()

    economy_rate = np.where(
        total_legal_balls > 0,
        np.round(total_runs_conceded / (total_legal_balls / 6.0), 2),
        np.nan,
    )
    dot_pct = np.where(
        total_legal_balls > 0,
        np.round(100.0 * total_dots / total_legal_balls, 2),
        np.nan,
    )
    bowling_sr = np.where(
        total_wickets > 0,
        np.round(total_legal_balls / total_wickets, 2),
        np.nan,
    )
    bowling_avg = np.where(
        total_wickets > 0,
        np.round(total_runs_conceded / total_wickets, 2),
        np.nan,
    )

    # HP stats
    hp_work = work[work["is_hp"]]
    hp_grouped = hp_work.groupby("bowler_id")

    hp_balls = hp_grouped["is_legal_ball"].sum()
    hp_runs = hp_grouped["bowler_runs_conceded"].sum()
    hp_wickets = hp_grouped["is_bowler_wicket"].sum()
    hp_dots = hp_grouped["is_bowler_dot_ball"].sum()
    hp_matches = hp_grouped["match_id"].nunique()

    # Ordinary stats (non-HP)
    ord_work = work[work["is_ord"]]
    ord_grouped = ord_work.groupby("bowler_id")

    ord_balls = ord_grouped["is_legal_ball"].sum()
    ord_runs = ord_grouped["bowler_runs_conceded"].sum()
    ord_wickets = ord_grouped["is_bowler_wicket"].sum()
    ord_matches = ord_grouped["match_id"].nunique()

    # LP stats
    lp_work = work[work["is_lp"]]
    lp_grouped = lp_work.groupby("bowler_id")

    lp_balls = lp_grouped["is_legal_ball"].sum()
    lp_runs = lp_grouped["bowler_runs_conceded"].sum()
    lp_wickets = lp_grouped["is_bowler_wicket"].sum()
    lp_matches = lp_grouped["match_id"].nunique()

    player_df = pd.DataFrame({
        "bowler_id": player_names.index,
        "player_name": player_names.values,
        "competitions_represented": comp_counts.values,
        "total_matches": total_matches.values,
        "total_innings": total_innings.values,
        "total_legal_balls_bowled": total_legal_balls.values,
        "total_overs": total_overs.values,
        "total_runs_conceded": total_runs_conceded.values,
        "total_bowler_wickets": total_wickets.values,
        "total_dot_balls_bowled": total_dots.values,
        "dot_ball_pct": dot_pct,
        "total_boundaries_conceded": total_boundaries.values,
        "economy_rate": economy_rate,
        "bowling_strike_rate": bowling_sr,
        "bowling_average": bowling_avg,
    }, index=player_names.index)

    all_idx = player_df.index
    player_df["hp_legal_balls"] = hp_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_runs_conceded"] = hp_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_bowler_wickets"] = hp_wickets.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_dot_balls"] = hp_dots.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_matches"] = hp_matches.reindex(all_idx, fill_value=0).astype("int64")

    player_df["hp_economy"] = np.where(
        player_df["hp_legal_balls"] > 0,
        np.round(player_df["hp_runs_conceded"] / (player_df["hp_legal_balls"] / 6.0), 2),
        np.nan,
    )
    player_df["hp_bowling_strike_rate"] = np.where(
        player_df["hp_bowler_wickets"] > 0,
        np.round(player_df["hp_legal_balls"] / player_df["hp_bowler_wickets"], 2),
        np.nan,
    )

    player_df["ord_legal_balls"] = ord_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_runs_conceded"] = ord_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_bowler_wickets"] = ord_wickets.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_matches"] = ord_matches.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_economy"] = np.where(
        player_df["ord_legal_balls"] > 0,
        np.round(player_df["ord_runs_conceded"] / (player_df["ord_legal_balls"] / 6.0), 2),
        np.nan,
    )

    player_df["lp_legal_balls"] = lp_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_runs_conceded"] = lp_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_bowler_wickets"] = lp_wickets.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_matches"] = lp_matches.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_economy"] = np.where(
        player_df["lp_legal_balls"] > 0,
        np.round(player_df["lp_runs_conceded"] / (player_df["lp_legal_balls"] / 6.0), 2),
        np.nan,
    )

    return player_df

