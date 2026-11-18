"""Deterministic Tie-Breaking and Sorting Module for SupeRR Selector Analytics.

Implements the declared multi-tier deterministic sorting policy:
1. Primary: Validated composite reliability score (descending).
2. Secondary: Shrunk high-pressure combined impact (descending).
3. Tertiary: Cluster-aware positive match ratio (descending).
4. Quaternary: Qualifying pressure matches count (descending).
5. Final Fallback: Stable unique player identifier (ascending).
"""

from __future__ import annotations

import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def apply_deterministic_ranking(
    df: pd.DataFrame,
    id_col: str,
    score_col: str = "reliability_score",
) -> pd.DataFrame:
    """Sorts candidate players deterministically and assigns sequential 1-based ranks.

    Args:
        df: Filtered DataFrame of eligible candidates.
        id_col: 'striker_id' for batters, 'bowler_id' for bowlers.
        score_col: Primary ranking score column name.

    Returns:
        pd.DataFrame: Deterministically ordered DataFrame with 'rank' column (1, 2, ...).
    """
    logger.info("Applying deterministic ranking for %d eligible candidates on %s.", len(df), id_col)

    sort_cols: List[str] = [score_col]
    ascending_flags: List[bool] = [False]

    if "shrunk_hp_combined_impact" in df.columns:
        sort_cols.append("shrunk_hp_combined_impact")
        ascending_flags.append(False)

    if "positive_match_ratio" in df.columns:
        sort_cols.append("positive_match_ratio")
        ascending_flags.append(False)

    if "hp_matches" in df.columns:
        sort_cols.append("hp_matches")
        ascending_flags.append(False)

    # Deterministic final fallback: Player ID ascending
    sort_cols.append(id_col)
    ascending_flags.append(True)

    sorted_df = df.sort_values(by=sort_cols, ascending=ascending_flags).copy()
    sorted_df["rank"] = range(1, len(sorted_df) + 1)

    return sorted_df

