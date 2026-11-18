"""Sample-Size Fairness and Player Eligibility Module for SupeRR Selector Analytics.

Defines statistically justified qualification thresholds to prevent small-sample distortions:
- Batters must have faced at least min_hp_balls across min_hp_matches, with min_ord_balls baseline.
- Bowlers must have bowled at least min_hp_balls across min_hp_matches, with min_ord_balls baseline.
- Every evaluated player receives an explicit status and documented reason.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_BATTER_ELIGIBILITY_CONFIG: Dict[str, Any] = {
    "min_hp_balls": 20,
    "min_hp_matches": 3,
    "min_ord_balls": 25,
}

DEFAULT_BOWLER_ELIGIBILITY_CONFIG: Dict[str, Any] = {
    "min_hp_balls": 24,
    "min_hp_matches": 3,
    "min_ord_balls": 30,
}


def classify_batter_eligibility(
    player_df: pd.DataFrame,
    min_hp_balls: int = 20,
    min_hp_matches: int = 3,
    min_ord_balls: int = 25,
) -> pd.DataFrame:
    """Evaluates batter eligibility against sample-size adequacy criteria.

    Args:
        player_df: DataFrame containing hp_balls, hp_matches, ord_balls columns.
        min_hp_balls: Minimum high-pressure deliveries faced.
        min_hp_matches: Minimum distinct matches with high-pressure exposure.
        min_ord_balls: Minimum ordinary-pressure deliveries for baseline reliability.

    Returns:
        pd.DataFrame: DataFrame with eligibility_status and eligibility_reason columns.
    """
    hp_b = player_df["hp_balls"].fillna(0).astype("int64")
    hp_m = player_df["hp_matches"].fillna(0).astype("int64")
    ord_b = player_df["ord_balls"].fillna(0).astype("int64")

    fail_hp_balls = hp_b < min_hp_balls
    fail_hp_matches = hp_m < min_hp_matches
    fail_ord_balls = ord_b < min_ord_balls

    is_eligible = ~(fail_hp_balls | fail_hp_matches | fail_ord_balls)

    reasons = []
    for f_b, f_m, f_o in zip(fail_hp_balls, fail_hp_matches, fail_ord_balls):
        issues = []
        if f_b:
            issues.append(f"INSUFFICIENT_HP_BALLS (<{min_hp_balls})")
        if f_m:
            issues.append(f"INSUFFICIENT_HP_MATCHES (<{min_hp_matches})")
        if f_o:
            issues.append(f"INSUFFICIENT_ORD_BALLS (<{min_ord_balls})")

        if not issues:
            reasons.append("QUALIFIED")
        else:
            reasons.append("; ".join(issues))

    status = pd.Series(
        ["ELIGIBLE" if e else "INELIGIBLE" for e in is_eligible],
        index=player_df.index,
        dtype="string",
    )
    reason_series = pd.Series(reasons, index=player_df.index, dtype="string")

    return pd.DataFrame({
        "eligibility_status": status,
        "eligibility_reason": reason_series,
    }, index=player_df.index)


def classify_bowler_eligibility(
    player_df: pd.DataFrame,
    min_hp_balls: int = 24,
    min_hp_matches: int = 3,
    min_ord_balls: int = 30,
) -> pd.DataFrame:
    """Evaluates bowler eligibility against sample-size adequacy criteria.

    Args:
        player_df: DataFrame containing hp_balls, hp_matches, ord_balls columns.
        min_hp_balls: Minimum high-pressure legal deliveries bowled.
        min_hp_matches: Minimum distinct matches with high-pressure bowling.
        min_ord_balls: Minimum ordinary-pressure legal deliveries for baseline.

    Returns:
        pd.DataFrame: DataFrame with eligibility_status and eligibility_reason columns.
    """
    hp_b = player_df["hp_balls"].fillna(0).astype("int64")
    hp_m = player_df["hp_matches"].fillna(0).astype("int64")
    ord_b = player_df["ord_balls"].fillna(0).astype("int64")

    fail_hp_balls = hp_b < min_hp_balls
    fail_hp_matches = hp_m < min_hp_matches
    fail_ord_balls = ord_b < min_ord_balls

    is_eligible = ~(fail_hp_balls | fail_hp_matches | fail_ord_balls)

    reasons = []
    for f_b, f_m, f_o in zip(fail_hp_balls, fail_hp_matches, fail_ord_balls):
        issues = []
        if f_b:
            issues.append(f"INSUFFICIENT_HP_BALLS (<{min_hp_balls})")
        if f_m:
            issues.append(f"INSUFFICIENT_HP_MATCHES (<{min_hp_matches})")
        if f_o:
            issues.append(f"INSUFFICIENT_ORD_BALLS (<{min_ord_balls})")

        if not issues:
            reasons.append("QUALIFIED")
        else:
            reasons.append("; ".join(issues))

    status = pd.Series(
        ["ELIGIBLE" if e else "INELIGIBLE" for e in is_eligible],
        index=player_df.index,
        dtype="string",
    )
    reason_series = pd.Series(reasons, index=player_df.index, dtype="string")

    return pd.DataFrame({
        "eligibility_status": status,
        "eligibility_reason": reason_series,
    }, index=player_df.index)

