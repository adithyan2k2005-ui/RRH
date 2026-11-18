"""Match-Level Consistency and Downside Risk Module for SupeRR Selector Analytics.

Computes cluster-aware match-level consistency metrics to prevent individual
unusually long innings from dominating reliability assessments:
- Match-level grouping of delivery residuals
- Mean and median match-level impact per ball
- Match-to-match standard deviation
- Proportion of pressure matches with positive net impact
- Worst-quartile (25th percentile) match impact for downside protection
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_match_level_consistency(
    delivery_df: pd.DataFrame,
    player_id_col: str,
    impact_col: str,
    pressure_mask: pd.Series,
    exposure_mask: pd.Series,
) -> pd.DataFrame:
    """Computes cluster-aware match-level consistency metrics for players under pressure.

    Args:
        delivery_df: Ball-by-ball DataFrame containing match_id and player_id_col.
        player_id_col: 'striker_id' for batters, 'bowler_id' for bowlers.
        impact_col: Column name containing the residual impact metric.
        pressure_mask: Boolean Series indicating high pressure deliveries.
        exposure_mask: Boolean Series indicating valid exposure (ball faced / legal ball).

    Returns:
        pd.DataFrame: Player-level consistency metrics indexed by player_id.
    """
    logger.info("Computing match-level consistency metrics for %s.", player_id_col)

    valid_mask = pressure_mask & exposure_mask
    sub_df = delivery_df[valid_mask].copy()

    if len(sub_df) == 0:
        return pd.DataFrame(columns=[
            player_id_col,
            "hp_matches_count",
            "mean_match_impact",
            "median_match_impact",
            "match_impact_std",
            "positive_match_ratio",
            "worst_quartile_match_impact",
        ])

    # 1. Match-level aggregation per player
    match_agg = sub_df.groupby([player_id_col, "match_id"]).agg(
        match_tot_impact=(impact_col, "sum"),
        match_balls=(impact_col, "count"),
    ).reset_index()

    # Per-ball impact within that specific match
    match_agg["match_per_ball_impact"] = match_agg["match_tot_impact"] / match_agg["match_balls"]

    # 2. Player-level consistency across matches
    all_players = delivery_df[exposure_mask].groupby(player_id_col)["match_id"].nunique().index

    def agg_player_consistency(group: pd.DataFrame) -> pd.Series:
        impacts = group["match_per_ball_impact"].values
        n_m = len(impacts)
        mean_val = float(np.mean(impacts)) if n_m > 0 else np.nan
        med_val = float(np.median(impacts)) if n_m > 0 else np.nan
        std_val = float(np.std(impacts, ddof=1)) if n_m > 1 else 0.0
        pos_ratio = float(np.mean(impacts > 0.0)) if n_m > 0 else 0.0
        p25_val = float(np.percentile(impacts, 25)) if n_m >= 4 else (float(np.min(impacts)) if n_m > 0 else np.nan)

        return pd.Series({
            "hp_matches_count": n_m,
            "mean_match_impact": np.round(mean_val, 4),
            "median_match_impact": np.round(med_val, 4),
            "match_impact_std": np.round(std_val, 4),
            "positive_match_ratio": np.round(pos_ratio, 4),
            "worst_quartile_match_impact": np.round(p25_val, 4),
        })

    player_consistency = match_agg.groupby(player_id_col).apply(
        agg_player_consistency,
        include_groups=False,
    )

    # Reindex across all players who appeared
    res_df = player_consistency.reindex(all_players)
    res_df[player_id_col] = res_df.index
    res_df["hp_matches_count"] = res_df["hp_matches_count"].fillna(0).astype("int64")
    res_df["positive_match_ratio"] = res_df["positive_match_ratio"].fillna(0.0)

    return res_df

