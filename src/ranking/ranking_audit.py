"""Ranking Audit and Traceability Module for SupeRR Selector Analytics.

Performs micro-to-macro reconciliation: directly recomputes all delivery-level
and match-level metrics for the Top 10 Batters and Top 10 Bowlers to verify 100%
mathematical consistency with the generated ranking tables.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def audit_batter_metrics(
    top_10_batters: pd.DataFrame,
    bat_perf_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Audits each top 10 batter against raw ball-by-ball performance records."""
    audit_results = []

    for _, row in top_10_batters.iterrows():
        p_id = int(row["striker_id"] if "striker_id" in row else row["player_id"])
        name = str(row["player_name"])

        p_balls = bat_perf_df[bat_perf_df["striker_id"] == p_id].copy()
        hp_balls = p_balls[
            (p_balls["batting_pressure_class"] == "HIGH_PRESSURE") & (p_balls["is_ball_faced"] == True)
        ].copy()

        # Micro counts
        recomputed_hp_balls = len(hp_balls)
        recomputed_hp_matches = hp_balls["match_id"].nunique()
        recomputed_hp_runs = int(hp_balls["batter_runs"].sum())

        # Stored counts
        stored_hp_balls = int(row.get("pressure_balls_faced", row.get("hp_balls", 0)))
        stored_hp_matches = int(row.get("pressure_matches", row.get("hp_matches", 0)))
        stored_hp_runs = int(row.get("pressure_runs", row.get("hp_batter_runs", 0)))

        balls_match = recomputed_hp_balls == stored_hp_balls
        matches_match = recomputed_hp_matches == stored_hp_matches
        runs_match = recomputed_hp_runs == stored_hp_runs

        audit_results.append({
            "player_id": p_id,
            "player_name": name,
            "recomputed_hp_balls": recomputed_hp_balls,
            "stored_hp_balls": stored_hp_balls,
            "balls_match": balls_match,
            "recomputed_hp_matches": recomputed_hp_matches,
            "stored_hp_matches": stored_hp_matches,
            "matches_match": matches_match,
            "recomputed_hp_runs": recomputed_hp_runs,
            "stored_hp_runs": stored_hp_runs,
            "runs_match": runs_match,
            "audit_passed": bool(balls_match and matches_match and runs_match),
        })

    return audit_results


def audit_bowler_metrics(
    top_10_bowlers: pd.DataFrame,
    bowl_perf_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Audits each top 10 bowler against raw ball-by-ball performance records."""
    audit_results = []

    for _, row in top_10_bowlers.iterrows():
        p_id = int(row["bowler_id"] if "bowler_id" in row else row["player_id"])
        name = str(row["player_name"])

        p_balls = bowl_perf_df[bowl_perf_df["bowler_id"] == p_id].copy()
        hp_all = p_balls[p_balls["bowling_pressure_class"] == "HIGH_PRESSURE"].copy()
        hp_legal = hp_all[hp_all["is_legal_ball"] == True].copy()

        # Micro counts
        recomputed_hp_legal_balls = len(hp_legal)
        recomputed_hp_matches = hp_all["match_id"].nunique()
        recomputed_hp_runs = int(hp_all["bowler_runs_conceded"].sum())
        recomputed_hp_wickets = int(hp_all["is_bowler_wicket"].sum())

        # Stored counts
        stored_hp_balls = int(row.get("pressure_legal_balls", row.get("hp_balls", 0)))
        stored_hp_matches = int(row.get("pressure_matches", row.get("hp_matches", 0)))
        stored_hp_runs = int(row.get("pressure_runs_conceded", row.get("hp_runs_conceded", 0)))
        stored_hp_wickets = int(row.get("pressure_wickets", row.get("hp_bowler_wickets", 0)))

        balls_match = recomputed_hp_legal_balls == stored_hp_balls
        matches_match = recomputed_hp_matches == stored_hp_matches
        runs_match = recomputed_hp_runs == stored_hp_runs
        wickets_match = recomputed_hp_wickets == stored_hp_wickets

        audit_results.append({
            "player_id": p_id,
            "player_name": name,
            "recomputed_hp_balls": recomputed_hp_legal_balls,
            "stored_hp_balls": stored_hp_balls,
            "balls_match": balls_match,
            "recomputed_hp_matches": recomputed_hp_matches,
            "stored_hp_matches": stored_hp_matches,
            "matches_match": matches_match,
            "recomputed_hp_runs": recomputed_hp_runs,
            "stored_hp_runs": stored_hp_runs,
            "runs_match": runs_match,
            "recomputed_hp_wickets": recomputed_hp_wickets,
            "stored_hp_wickets": stored_hp_wickets,
            "wickets_match": wickets_match,
            "audit_passed": bool(balls_match and matches_match and runs_match and wickets_match),
        })

    return audit_results
