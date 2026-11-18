"""Innings Context and Target Determination Module for SupeRR Selector Analytics.

Calculates scheduled overs, scheduled legal balls, target scores (standard vs DLS revised),
and match-level environmental context without future data leakage.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_match_innings_context(
    matches_df: pd.DataFrame,
    bbb_df: pd.DataFrame,
) -> pd.DataFrame:
    """Builds an authoritative lookup table of scheduled balls and targets per (match_id, innings).

    Args:
        matches_df: Clean matches metadata DataFrame.
        bbb_df: Ball-by-ball DataFrame containing 'runs', 'extras1_runs', 'extras_2_runs'.

    Returns:
        pd.DataFrame: Table keyed by ['match_id', 'innings'] with scheduled overs, balls,
                      target, is_target_revised, and is_shortened_match.
    """
    logger.info("Computing innings context and targets across matches.")

    # Calculate actual final innings scores from BBB deliveries
    # (Note: Innings 1 total is known before Innings 2 begins, preserving causality)
    bbb_calc = bbb_df.copy()
    bbb_calc["total_ball_runs"] = (
        bbb_calc["runs"].fillna(0)
        + bbb_calc["extras1_runs"].fillna(0)
        + bbb_calc["extras_2_runs"].fillna(0)
    )
    inn_totals = (
        bbb_calc.groupby(["match_id", "innings"])["total_ball_runs"]
        .sum()
        .unstack(level="innings")
    )

    # Unique match-innings pairs present in BBB
    match_innings_pairs = (
        bbb_df[["match_id", "innings"]].drop_duplicates().sort_values(by=["match_id", "innings"])
    )

    # Merge matches metadata
    m_cols = [
        "match_id",
        "comp_id",
        "match_date",
        "stage",
        "knock_out",
        "first_inn_revised_overs",
        "second_inn_revised_overs",
        "revised_target",
        "result",
    ]
    available_m_cols = [c for c in m_cols if c in matches_df.columns]
    merged = match_innings_pairs.merge(
        matches_df[available_m_cols], on="match_id", how="left"
    )

    scheduled_balls_list = []
    scheduled_overs_list = []
    target_list = []
    is_target_revised_list = []
    is_shortened_list = []

    for _, row in merged.iterrows():
        mid = row["match_id"]
        inn = row["innings"]
        rev_target = row.get("revised_target", None)
        first_rev_overs = row.get("first_inn_revised_overs", None)
        second_rev_overs = row.get("second_inn_revised_overs", None)

        # 1. Super Overs (Innings 3 & 4)
        if inn in [3, 4]:
            s_balls = 6
            s_overs = 1.0
            is_short = False

            if inn == 3:
                target = pd.NA
                is_rev = False
            else:  # Innings 4 (Super Over Chase)
                inn3_tot = inn_totals.loc[mid, 3] if mid in inn_totals.index and 3 in inn_totals.columns and not pd.isna(inn_totals.loc[mid, 3]) else None
                target = int(inn3_tot + 1) if inn3_tot is not None else pd.NA
                is_rev = False

        # 2. Innings 1 (Normal Match)
        elif inn == 1:
            if pd.notna(first_rev_overs):
                # Verified: first_inn_revised_overs contains SCHEDULED BALLS (e.g. 54 = 9 overs)
                s_balls = int(first_rev_overs)
                s_overs = float(first_rev_overs) / 6.0
                is_short = s_balls < 120
            else:
                s_balls = 120
                s_overs = 20.0
                is_short = False

            target = pd.NA
            is_rev = False

        # 3. Innings 2 (The Chase)
        elif inn == 2:
            if pd.notna(second_rev_overs):
                s_balls = int(second_rev_overs)
                s_overs = float(second_rev_overs) / 6.0
                is_short = s_balls < 120
            elif pd.notna(first_rev_overs):
                s_balls = int(first_rev_overs)
                s_overs = float(first_rev_overs) / 6.0
                is_short = s_balls < 120
            else:
                s_balls = 120
                s_overs = 20.0
                is_short = False

            # Target determination for Innings 2
            if pd.notna(rev_target):
                target = int(rev_target)
                is_rev = True
            else:
                inn1_tot = inn_totals.loc[mid, 1] if mid in inn_totals.index and 1 in inn_totals.columns and not pd.isna(inn_totals.loc[mid, 1]) else None
                target = int(inn1_tot + 1) if inn1_tot is not None else pd.NA
                is_rev = False

        else:
            s_balls = 120
            s_overs = 20.0
            target = pd.NA
            is_rev = False
            is_short = False

        scheduled_balls_list.append(s_balls)
        scheduled_overs_list.append(s_overs)
        target_list.append(target)
        is_target_revised_list.append(is_rev)
        is_shortened_list.append(is_short)

    merged["scheduled_balls"] = pd.Series(scheduled_balls_list, dtype="int64")
    merged["scheduled_overs"] = pd.Series(scheduled_overs_list, dtype="float64")
    merged["target"] = pd.Series(target_list, dtype="Int64")
    merged["is_target_revised"] = pd.Series(is_target_revised_list, dtype="bool")
    merged["is_shortened_match"] = pd.Series(is_shortened_list, dtype="bool")

    logger.info(
        "Innings context built for %d match-innings. Shortened: %d, Revised targets: %d",
        len(merged),
        int(merged["is_shortened_match"].sum()),
        int(merged["is_target_revised"].sum()),
    )
    return merged

