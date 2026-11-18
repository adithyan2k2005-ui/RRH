"""Validation Module for Phase 4 Player Performance & Reliability in SupeRR Selector Analytics."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def audit_batting_metrics_integrity(
    delivery_df: pd.DataFrame,
    batting_perf_df: pd.DataFrame,
    player_bat_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Audits cricket domain scoring semantics and aggregation accuracy for batting."""
    logger.info("Auditing batting metrics integrity.")

    # 1. Wides must not be counted as balls faced by batter
    wides_mask = delivery_df["extras_type"] == "wide"
    wides_balls_faced = batting_perf_df.loc[wides_mask, "is_ball_faced"].sum()
    wides_passed = (wides_balls_faced == 0)

    # 2. No-balls count as balls faced
    noballs_mask = delivery_df["extras_type"].isin(["Overstep", "other"])
    noballs_faced = batting_perf_df.loc[noballs_mask, "is_ball_faced"].all()

    # 3. Batter runs exclude extras
    runs_match = (batting_perf_df["batter_runs"] == delivery_df["runs_scored_on_ball"].fillna(0)).all()

    # 4. Total striker dismissals <= total team wickets
    tot_strikers_out = player_bat_df["total_striker_dismissals"].sum()
    tot_team_wkts = delivery_df["is_team_wicket"].sum()
    dismissal_passed = tot_strikers_out <= tot_team_wkts

    # 5. Strike rate mathematical consistency
    valid_sr_mask = player_bat_df["total_balls_faced"] > 0
    calc_sr = np.round(100.0 * player_bat_df.loc[valid_sr_mask, "total_batter_runs"] / player_bat_df.loc[valid_sr_mask, "total_balls_faced"], 2)
    sr_match = np.allclose(calc_sr, player_bat_df.loc[valid_sr_mask, "batting_strike_rate"].dropna(), atol=0.02)

    return {
        "wides_excluded_from_balls_faced": bool(wides_passed),
        "noballs_included_in_balls_faced": bool(noballs_faced),
        "batter_runs_exclude_extras": bool(runs_match),
        "total_striker_dismissals": int(tot_strikers_out),
        "total_team_wickets": int(tot_team_wkts),
        "striker_dismissals_valid": bool(dismissal_passed),
        "strike_rate_mathematically_exact": bool(sr_match),
    }


def audit_bowling_metrics_integrity(
    delivery_df: pd.DataFrame,
    bowling_perf_df: pd.DataFrame,
    player_bowl_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Audits cricket domain scoring semantics and aggregation accuracy for bowling."""
    logger.info("Auditing bowling metrics integrity.")

    # 1. Bowler conceded runs excludes byes and leg-byes
    byes_mask = delivery_df["extras_type"].isin(["byes", "legbyes"])
    byes_charged = delivery_df.loc[byes_mask, "runs_charged_to_bowler_on_ball"].sum()
    byes_runs_scored = delivery_df.loc[byes_mask, "runs_scored_on_ball"].sum()
    # Byes charged to bowler should equal batter-hit runs (0 in pure byes/legbyes)
    byes_passed = (byes_charged == byes_runs_scored)

    # 2. Wides are charged to bowler
    wides_mask = delivery_df["extras_type"] == "wide"
    wides_charged = (delivery_df.loc[wides_mask, "runs_charged_to_bowler_on_ball"] >= 1).all()

    # 3. Run-outs are not credited to bowler
    runouts_mask = delivery_df["dismissal_type"].isin(["RunOut", "Retire Out", "Obstructing the field", "Obstracting the field"])
    bowler_runouts = delivery_df.loc[runouts_mask, "is_bowler_wicket"].sum()
    runouts_passed = (bowler_runouts == 0)

    # 4. Economy rate mathematical consistency
    valid_econ_mask = player_bowl_df["total_legal_balls_bowled"] > 0
    calc_econ = np.round(player_bowl_df.loc[valid_econ_mask, "total_runs_conceded"] / (player_bowl_df.loc[valid_econ_mask, "total_legal_balls_bowled"] / 6.0), 2)
    econ_match = np.allclose(calc_econ, player_bowl_df.loc[valid_econ_mask, "economy_rate"].dropna(), atol=0.02)

    return {
        "byes_legbyes_excluded_from_bowler_runs": bool(byes_passed),
        "wides_charged_to_bowler": bool(wides_charged),
        "runouts_excluded_from_bowler_wickets": bool(runouts_passed),
        "economy_rate_mathematically_exact": bool(econ_match),
    }


def audit_reliability_scores_integrity(
    player_df: pd.DataFrame,
    role: str = "batter",
) -> Dict[str, Any]:
    """Audits reliability scores bounds, eligibility gating, and CI validity."""
    logger.info("Auditing %s reliability scores integrity.", role)

    eligible_mask = player_df["eligibility_status"] == "ELIGIBLE"
    scores = player_df.loc[eligible_mask, "reliability_score"]

    # Bounds check
    in_bounds = (scores >= 0.0).all() and (scores <= 100.0).all()
    no_nan_eligible = scores.notnull().all()

    # Ineligible players must have NaN reliability_score
    ineligible_nan = player_df.loc[~eligible_mask, "reliability_score"].isna().all()

    # CI ordering: lower <= estimate <= upper
    lower = player_df.loc[eligible_mask, "ci_lower_90"]
    upper = player_df.loc[eligible_mask, "ci_upper_90"]
    est = player_df.loc[eligible_mask, "shrunk_hp_combined_impact"]
    ci_valid = (lower <= est + 1e-4).all() and (est <= upper + 1e-4).all()

    return {
        "eligible_players_count": int(eligible_mask.sum()),
        "ineligible_players_count": int((~eligible_mask).sum()),
        "scores_in_bounds_0_100": bool(in_bounds),
        "no_nan_for_eligible": bool(no_nan_eligible),
        "ineligible_scores_properly_gated": bool(ineligible_nan),
        "confidence_intervals_ordered": bool(ci_valid),
        "mean_reliability_score": float(np.round(scores.mean(), 2)),
        "median_reliability_score": float(np.round(scores.median(), 2)),
    }

