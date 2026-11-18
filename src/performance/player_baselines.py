"""Within-Player Baselines and Pressure Uplift Module for SupeRR Selector Analytics.

Calculates player-level performance comparisons:
- High-pressure impact (performance under high pressure)
- Ordinary-pressure baseline (performance under normal conditions)
- Pressure uplift (high-pressure impact minus ordinary baseline)
- Baseline uncertainty and sample counts
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_player_pressure_vs_ordinary(
    batting_delivery_df: pd.DataFrame,
    bowling_delivery_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Computes player-level HP vs ordinary performance baselines and uplift.

    Args:
        batting_delivery_df: Ball-by-ball DataFrame merged with batting residuals.
        bowling_delivery_df: Ball-by-ball DataFrame merged with bowling residuals.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (batter_baseline_df, bowler_baseline_df)
    """
    logger.info("Computing within-player pressure vs ordinary baselines.")

    # -------------------------------------------------------------
    # 1. BATTING BASELINES
    # -------------------------------------------------------------
    b_work = batting_delivery_df[batting_delivery_df["is_ball_faced"]].copy()
    b_work["is_hp"] = b_work["batting_pressure_class"] == "HIGH_PRESSURE"
    b_work["is_ord"] = ~b_work["is_hp"]

    # Overall player index
    all_batters = b_work.groupby("striker_id")["striker_name"].first()

    # HP stats per batter
    b_hp = b_work[b_work["is_hp"]].groupby("striker_id")
    hp_bat_count = b_hp["is_ball_faced"].sum()
    hp_bat_matches = b_hp["match_id"].nunique()
    hp_bat_run_impact = b_hp["batting_run_impact"].mean()
    hp_bat_comb_impact = b_hp["batting_combined_impact"].mean()
    hp_bat_std = b_hp["batting_combined_impact"].std()

    # Ordinary stats per batter
    b_ord = b_work[b_work["is_ord"]].groupby("striker_id")
    ord_bat_count = b_ord["is_ball_faced"].sum()
    ord_bat_matches = b_ord["match_id"].nunique()
    ord_bat_run_impact = b_ord["batting_run_impact"].mean()
    ord_bat_comb_impact = b_ord["batting_combined_impact"].mean()
    ord_bat_std = b_ord["batting_combined_impact"].std()

    # Population-level ordinary prior
    pop_ord_bat_comb = b_work[b_work["is_ord"]]["batting_combined_impact"].mean()

    idx_b = all_batters.index
    batter_df = pd.DataFrame({
        "striker_id": idx_b,
        "player_name": all_batters.values,
        "hp_balls": hp_bat_count.reindex(idx_b, fill_value=0).astype("int64"),
        "hp_matches": hp_bat_matches.reindex(idx_b, fill_value=0).astype("int64"),
        "hp_run_impact_per_ball": np.round(hp_bat_run_impact.reindex(idx_b), 4),
        "hp_combined_impact_per_ball": np.round(hp_bat_comb_impact.reindex(idx_b), 4),
        "hp_impact_std": np.round(hp_bat_std.reindex(idx_b), 4),
        "ord_balls": ord_bat_count.reindex(idx_b, fill_value=0).astype("int64"),
        "ord_matches": ord_bat_matches.reindex(idx_b, fill_value=0).astype("int64"),
        "ord_run_impact_per_ball": np.round(ord_bat_run_impact.reindex(idx_b), 4),
        "ord_combined_impact_per_ball": np.round(ord_bat_comb_impact.reindex(idx_b), 4),
        "ord_impact_std": np.round(ord_bat_std.reindex(idx_b), 4),
    }, index=idx_b)

    # Standard error of ordinary baseline: s / sqrt(n)
    batter_df["ord_baseline_se"] = np.where(
        batter_df["ord_balls"] > 1,
        np.round(batter_df["ord_impact_std"] / np.sqrt(batter_df["ord_balls"]), 4),
        np.nan,
    )

    # Effective baseline with population fallback for small ordinary samples (< 15 balls)
    eff_ord_bat = np.where(
        batter_df["ord_balls"] >= 15,
        batter_df["ord_combined_impact_per_ball"],
        pop_ord_bat_comb,
    )
    batter_df["batting_pressure_uplift"] = np.round(
        batter_df["hp_combined_impact_per_ball"] - eff_ord_bat, 4
    )

    # -------------------------------------------------------------
    # 2. BOWLING BASELINES
    # -------------------------------------------------------------
    bw_work = bowling_delivery_df[bowling_delivery_df["is_legal_ball"]].copy()
    bw_work["is_hp"] = bw_work["bowling_pressure_class"] == "HIGH_PRESSURE"
    bw_work["is_ord"] = ~bw_work["is_hp"]

    all_bowlers = bw_work.groupby("bowler_id")["bowler_name"].first()

    # HP stats per bowler
    bw_hp = bw_work[bw_work["is_hp"]].groupby("bowler_id")
    hp_bowl_count = bw_hp["is_legal_ball"].sum()
    hp_bowl_matches = bw_hp["match_id"].nunique()
    hp_bowl_run_impact = bw_hp["bowling_run_impact"].mean()
    hp_bowl_comb_impact = bw_hp["bowling_combined_impact"].mean()
    hp_bowl_std = bw_hp["bowling_combined_impact"].std()

    # Ordinary stats per bowler
    bw_ord = bw_work[bw_work["is_ord"]].groupby("bowler_id")
    ord_bowl_count = bw_ord["is_legal_ball"].sum()
    ord_bowl_matches = bw_ord["match_id"].nunique()
    ord_bowl_run_impact = bw_ord["bowling_run_impact"].mean()
    ord_bowl_comb_impact = bw_ord["bowling_combined_impact"].mean()
    ord_bowl_std = bw_ord["bowling_combined_impact"].std()

    pop_ord_bowl_comb = bw_work[bw_work["is_ord"]]["bowling_combined_impact"].mean()

    idx_bw = all_bowlers.index
    bowler_df = pd.DataFrame({
        "bowler_id": idx_bw,
        "player_name": all_bowlers.values,
        "hp_balls": hp_bowl_count.reindex(idx_bw, fill_value=0).astype("int64"),
        "hp_matches": hp_bowl_matches.reindex(idx_bw, fill_value=0).astype("int64"),
        "hp_run_impact_per_ball": np.round(hp_bowl_run_impact.reindex(idx_bw), 4),
        "hp_combined_impact_per_ball": np.round(hp_bowl_comb_impact.reindex(idx_bw), 4),
        "hp_impact_std": np.round(hp_bowl_std.reindex(idx_bw), 4),
        "ord_balls": ord_bowl_count.reindex(idx_bw, fill_value=0).astype("int64"),
        "ord_matches": ord_bowl_matches.reindex(idx_bw, fill_value=0).astype("int64"),
        "ord_run_impact_per_ball": np.round(ord_bowl_run_impact.reindex(idx_bw), 4),
        "ord_combined_impact_per_ball": np.round(ord_bowl_comb_impact.reindex(idx_bw), 4),
        "ord_impact_std": np.round(ord_bowl_std.reindex(idx_bw), 4),
    }, index=idx_bw)

    bowler_df["ord_baseline_se"] = np.where(
        bowler_df["ord_balls"] > 1,
        np.round(bowler_df["ord_impact_std"] / np.sqrt(bowler_df["ord_balls"]), 4),
        np.nan,
    )

    eff_ord_bowl = np.where(
        bowler_df["ord_balls"] >= 15,
        bowler_df["ord_combined_impact_per_ball"],
        pop_ord_bowl_comb,
    )
    bowler_df["bowling_pressure_uplift"] = np.round(
        bowler_df["hp_combined_impact_per_ball"] - eff_ord_bowl, 4
    )

    return batter_df, bowler_df

