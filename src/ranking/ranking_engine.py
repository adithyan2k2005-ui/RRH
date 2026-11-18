"""Ranking Engine Module for SupeRR Selector Analytics.

Executes candidate eligibility filtering, deterministic tie-breaking,
and extraction of top-10 and full ranking lists for batting and bowling.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import pandas as pd

from .tie_breaking import apply_deterministic_ranking

logger = logging.getLogger(__name__)


def generate_rankings(
    player_bat_df: pd.DataFrame,
    player_bowl_df: pd.DataFrame,
    top_n: int = 10,
) -> Dict[str, pd.DataFrame]:
    """Generates official top-N and full ranking DataFrames for batters and bowlers.

    Args:
        player_bat_df: Evaluated player batting metrics DataFrame.
        player_bowl_df: Evaluated player bowling metrics DataFrame.
        top_n: Number of top candidates to select (default 10).

    Returns:
        Dict[str, pd.DataFrame]:
            - 'top_10_batters': Top N ranked batters.
            - 'full_batting_rankings': All eligible batters ranked.
            - 'top_10_bowlers': Top N ranked bowlers.
            - 'full_bowling_rankings': All eligible bowlers ranked.
    """
    logger.info("Generating rankings: Top %d selection.", top_n)

    # 1. Batting
    b_elig = player_bat_df[player_bat_df["eligibility_status"] == "ELIGIBLE"].copy()
    if len(b_elig) < top_n:
        raise ValueError(f"Insufficient eligible batters: {len(b_elig)} found, {top_n} required.")

    full_bat = apply_deterministic_ranking(b_elig, id_col="striker_id", score_col="reliability_score")
    top_bat = full_bat.head(top_n).copy()

    # 2. Bowling
    bw_elig = player_bowl_df[player_bowl_df["eligibility_status"] == "ELIGIBLE"].copy()
    if len(bw_elig) < top_n:
        raise ValueError(f"Insufficient eligible bowlers: {len(bw_elig)} found, {top_n} required.")

    full_bowl = apply_deterministic_ranking(bw_elig, id_col="bowler_id", score_col="reliability_score")
    top_bowl = full_bowl.head(top_n).copy()

    logger.info(
        "Rankings generated: %d eligible batters (Top %d selected), %d eligible bowlers (Top %d selected).",
        len(full_bat),
        len(top_bat),
        len(full_bowl),
        len(top_bowl),
    )

    return {
        "top_10_batters": top_bat,
        "full_batting_rankings": full_bat,
        "top_10_bowlers": top_bowl,
        "full_bowling_rankings": full_bowl,
    }

