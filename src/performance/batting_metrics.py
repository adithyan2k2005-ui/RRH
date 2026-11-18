"""Batting Performance Metrics Module for SupeRR Selector Analytics.

Calculates verified cricket conventional batting statistics and pressure segmentations
using verified scoring semantics:
- Wides are excluded from balls faced by the batter.
- No-balls count as balls faced by the batter.
- Byes and leg-byes are excluded from batter runs.
- Non-striker dismissals are not charged to the striker.
- Retired-hurt is not counted as a dismissal.
"""

from __future__ import annotations

import logging
from typing import Set

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NO_BALL_EXTRAS: Set[str] = {"Overstep", "other"}


def compute_delivery_batting_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Computes delivery-level batting indicators according to cricket laws.

    Args:
        df: Ball-by-ball match states DataFrame.

    Returns:
        pd.DataFrame: DataFrame of batting indicator columns aligned with df.index:
            - is_ball_faced (bool)
            - batter_runs (int64)
            - is_boundary_4 (bool)
            - is_boundary_6 (bool)
            - is_dot_ball (bool)
            - is_striker_dismissed (bool)
    """
    extras_type = df["extras_type"].fillna("").astype(str)
    is_legal = df["is_legal_ball"].fillna(False).astype(bool)

    # In cricket, batter faces legal deliveries and no-balls (Overstep / other),
    # but NOT wide balls.
    is_ball_faced = is_legal | extras_type.isin(NO_BALL_EXTRAS)

    # Batter runs strictly exclude extras (runs_scored_on_ball is batter-scored runs)
    batter_runs = df["runs_scored_on_ball"].fillna(0).astype("int64")

    # Boundary deliveries (scored by batter)
    is_four = (df["is_four"] == 1) | (df["is_four"] is True) | (batter_runs == 4)
    is_six = (df["is_six"] == 1) | (df["is_six"] is True) | (batter_runs == 6)

    # Dot balls faced by batter
    is_dot = is_ball_faced & (batter_runs == 0)

    # Striker dismissal: must be a team wicket AND the dismissed player must be the striker
    is_team_wkt = df["is_team_wicket"].fillna(False).astype(bool)
    has_dismissed_id = df["dismissed_player_id"].notnull()
    dismissed_id = df["dismissed_player_id"].fillna(-999).astype("int64")
    striker_id = df["striker_id"].fillna(-888).astype("int64")

    is_striker_dismissed = is_team_wkt & has_dismissed_id & (dismissed_id == striker_id)

    # Exclude retired hurt if flagged
    if "is_retired_hurt" in df.columns:
        is_striker_dismissed = is_striker_dismissed & (~df["is_retired_hurt"].fillna(False).astype(bool))

    return pd.DataFrame({
        "is_ball_faced": is_ball_faced,
        "batter_runs": batter_runs,
        "is_boundary_4": is_four,
        "is_boundary_6": is_six,
        "is_dot_ball": is_dot,
        "is_striker_dismissed": is_striker_dismissed,
    }, index=df.index)


def compute_player_batting_aggregate(
    df: pd.DataFrame,
    batting_flags: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggregates batting metrics to the player level across overall, HP, and ordinary regimes.

    Args:
        df: Ball-by-ball DataFrame containing match and player identifiers.
        batting_flags: Precomputed batting flags (or None to compute inline).

    Returns:
        pd.DataFrame: Player-level batting statistics indexed by striker_id.
    """
    if batting_flags is None:
        batting_flags = compute_delivery_batting_flags(df)

    work = df[["match_id", "innings", "comp_id", "striker_id", "striker_name", "batting_pressure_class"]].copy()
    for col in batting_flags.columns:
        work[col] = batting_flags[col]

    work["innings_key"] = work["match_id"].astype(str) + "__" + work["innings"].astype(str)
    work["is_hp"] = work["batting_pressure_class"] == "HIGH_PRESSURE"
    work["is_ord"] = work["batting_pressure_class"] != "HIGH_PRESSURE"
    work["is_lp"] = work["batting_pressure_class"] == "LOW_PRESSURE"

    # Aggregations by striker_id
    grouped = work.groupby("striker_id")

    # Static player metadata
    player_names = grouped["striker_name"].first()
    comp_counts = grouped["comp_id"].nunique()
    total_matches = grouped["match_id"].nunique()
    total_innings = grouped["innings_key"].nunique()

    # Overall totals
    total_balls_faced = grouped["is_ball_faced"].sum()
    total_batter_runs = grouped["batter_runs"].sum()
    total_fours = grouped["is_boundary_4"].sum()
    total_sixes = grouped["is_boundary_6"].sum()
    total_boundaries = total_fours + total_sixes
    total_dots = grouped["is_dot_ball"].sum()
    total_dismissals = grouped["is_striker_dismissed"].sum()

    batting_avg = np.where(total_dismissals > 0, np.round(total_batter_runs / total_dismissals, 2), np.nan)
    batting_sr = np.where(total_balls_faced > 0, np.round(100.0 * total_batter_runs / total_balls_faced, 2), np.nan)
    dot_pct = np.where(total_balls_faced > 0, np.round(100.0 * total_dots / total_balls_faced, 2), np.nan)

    # High pressure aggregations
    hp_work = work[work["is_hp"]]
    hp_grouped = hp_work.groupby("striker_id")

    hp_balls = hp_grouped["is_ball_faced"].sum()
    hp_runs = hp_grouped["batter_runs"].sum()
    hp_dismissals = hp_grouped["is_striker_dismissed"].sum()
    hp_matches = hp_grouped["match_id"].nunique()

    # Ordinary pressure aggregations (LOW + MEDIUM)
    ord_work = work[work["is_ord"]]
    ord_grouped = ord_work.groupby("striker_id")

    ord_balls = ord_grouped["is_ball_faced"].sum()
    ord_runs = ord_grouped["batter_runs"].sum()
    ord_dismissals = ord_grouped["is_striker_dismissed"].sum()
    ord_matches = ord_grouped["match_id"].nunique()

    # Low pressure only aggregations
    lp_work = work[work["is_lp"]]
    lp_grouped = lp_work.groupby("striker_id")

    lp_balls = lp_grouped["is_ball_faced"].sum()
    lp_runs = lp_grouped["batter_runs"].sum()
    lp_dismissals = lp_grouped["is_striker_dismissed"].sum()
    lp_matches = lp_grouped["match_id"].nunique()

    player_df = pd.DataFrame({
        "striker_id": player_names.index,
        "player_name": player_names.values,
        "competitions_represented": comp_counts.values,
        "total_matches": total_matches.values,
        "total_innings": total_innings.values,
        "total_balls_faced": total_balls_faced.values,
        "total_batter_runs": total_batter_runs.values,
        "total_fours": total_fours.values,
        "total_sixes": total_sixes.values,
        "total_boundaries": total_boundaries.values,
        "total_dot_balls_faced": total_dots.values,
        "dot_ball_pct": dot_pct,
        "total_striker_dismissals": total_dismissals.values,
        "batting_average": batting_avg,
        "batting_strike_rate": batting_sr,
    }, index=player_names.index)

    # Reindex HP, ORD, LP stats to match all players
    all_idx = player_df.index
    player_df["hp_balls_faced"] = hp_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_batter_runs"] = hp_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_striker_dismissals"] = hp_dismissals.reindex(all_idx, fill_value=0).astype("int64")
    player_df["hp_matches"] = hp_matches.reindex(all_idx, fill_value=0).astype("int64")

    player_df["hp_strike_rate"] = np.where(
        player_df["hp_balls_faced"] > 0,
        np.round(100.0 * player_df["hp_batter_runs"] / player_df["hp_balls_faced"], 2),
        np.nan,
    )
    player_df["hp_batting_average"] = np.where(
        player_df["hp_striker_dismissals"] > 0,
        np.round(player_df["hp_batter_runs"] / player_df["hp_striker_dismissals"], 2),
        np.nan,
    )

    player_df["ord_balls_faced"] = ord_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_batter_runs"] = ord_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_striker_dismissals"] = ord_dismissals.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_matches"] = ord_matches.reindex(all_idx, fill_value=0).astype("int64")
    player_df["ord_strike_rate"] = np.where(
        player_df["ord_balls_faced"] > 0,
        np.round(100.0 * player_df["ord_batter_runs"] / player_df["ord_balls_faced"], 2),
        np.nan,
    )

    player_df["lp_balls_faced"] = lp_balls.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_batter_runs"] = lp_runs.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_striker_dismissals"] = lp_dismissals.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_matches"] = lp_matches.reindex(all_idx, fill_value=0).astype("int64")
    player_df["lp_strike_rate"] = np.where(
        player_df["lp_balls_faced"] > 0,
        np.round(100.0 * player_df["lp_batter_runs"] / player_df["lp_balls_faced"], 2),
        np.nan,
    )

    return player_df

