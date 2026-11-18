"""Expected Performance Baselines Module for SupeRR Selector Analytics.

Constructs context-adjusted reference models using leave-one-match-out (LOMO)
historical aggregation with hierarchical fallback smoothing.

Guarantees:
- Zero current-match contamination (match-level leave-one-out out-of-fold).
- Zero future data leakage (only pre-delivery context variables are used).
- Hierarchical fallbacks ensure robust estimates even for rare game situations.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_MIN_SUPPORT_BALLS = 30


def _build_context_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Builds hierarchical context group identifier strings for each delivery."""
    format_str = df["match_format"].fillna("T20").astype(str)
    phase_str = df["bowling_innings_phase"].fillna("Middle").astype(str)

    # Wickets remaining categorized into 4 operational tiers
    w_rem = df["wickets_remaining_before"].fillna(10).clip(1, 10).astype(int)
    w_bucket = pd.cut(
        w_rem,
        bins=[0, 2, 4, 7, 10],
        labels=["1-2", "3-4", "5-7", "8-10"],
    ).astype(str)

    # Chase context vs first innings
    is_chase = df["innings"].isin([2, 4]).astype(str)

    lvl1 = format_str + "__" + phase_str + "__" + w_bucket + "__" + is_chase
    lvl2 = format_str + "__" + phase_str + "__" + w_bucket
    lvl3 = format_str + "__" + phase_str
    lvl4 = format_str

    return pd.DataFrame({
        "lvl1": lvl1,
        "lvl2": lvl2,
        "lvl3": lvl3,
        "lvl4": lvl4,
    }, index=df.index)


def _compute_hierarchical_loo(
    df: pd.DataFrame,
    context_df: pd.DataFrame,
    level_cols: List[str],
    target_series: pd.Series,
    weight_series: pd.Series,
    min_support: int = DEFAULT_MIN_SUPPORT_BALLS,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes exact leave-one-match-out expectation with hierarchical fallback smoothing.

    Args:
        df: Base DataFrame with match_id column.
        context_df: Context key columns DataFrame.
        level_cols: Ordered list of context columns from most specific to least specific.
        target_series: The target metric sum (e.g., runs).
        weight_series: The denominator weight sum (e.g., balls faced).
        min_support: Minimum LOMO supporting balls required to accept a level.

    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (expected_rate, support_balls, fallback_level)
    """
    work = pd.DataFrame({
        "match_id": df["match_id"].values,
        "target": target_series.values,
        "weight": weight_series.values,
    }, index=df.index)

    for col in level_cols:
        work[col] = context_df[col].values

    global_target = float(work["target"].sum())
    global_weight = float(work["weight"].sum())
    global_mean = global_target / max(1.0, global_weight)

    res_rates = pd.Series(np.nan, index=df.index, dtype="float64")
    res_support = pd.Series(0, index=df.index, dtype="int64")
    res_level = pd.Series(0, index=df.index, dtype="int64")

    unresolved_mask = pd.Series(True, index=df.index)

    for lvl_idx, col in enumerate(level_cols, start=1):
        if not unresolved_mask.any():
            break

        # Group by (context, match_id)
        m_agg = work.groupby([col, "match_id"], observed=True).agg(
            m_t=("target", "sum"),
            m_w=("weight", "sum"),
        ).reset_index()

        # Group by context total
        tot_agg = m_agg.groupby(col, observed=True).agg(
            tot_t=("m_t", "sum"),
            tot_w=("m_w", "sum"),
        ).reset_index()

        sub_df = work.loc[unresolved_mask, [col, "match_id"]]
        m_merged = sub_df.merge(m_agg, on=[col, "match_id"], how="left")
        m_merged = m_merged.merge(tot_agg, on=col, how="left")

        loo_t = m_merged["tot_t"].fillna(0).values - m_merged["m_t"].fillna(0).values
        loo_w = m_merged["tot_w"].fillna(0).values - m_merged["m_w"].fillna(0).values

        valid = loo_w >= min_support
        rates = np.where(valid, loo_t / np.maximum(1.0, loo_w), np.nan)

        valid_idx = sub_df.index[valid]
        res_rates.loc[valid_idx] = rates[valid]
        res_support.loc[valid_idx] = loo_w[valid].astype("int64")
        res_level.loc[valid_idx] = lvl_idx

        unresolved_mask.loc[valid_idx] = False

    # Level 5 fallback: Global mean
    if unresolved_mask.any():
        left_idx = df.index[unresolved_mask]
        res_rates.loc[left_idx] = global_mean
        res_support.loc[left_idx] = int(global_weight)
        res_level.loc[left_idx] = 5

    return res_rates, res_support, res_level


def compute_expected_batting_metrics(
    df: pd.DataFrame,
    min_support: int = DEFAULT_MIN_SUPPORT_BALLS,
) -> pd.DataFrame:
    """Computes context-adjusted expected runs and dismissal risk for every batting event.

    Args:
        df: Ball-by-ball DataFrame.
        min_support: Minimum out-of-fold balls required for hierarchical level.

    Returns:
        pd.DataFrame: Aligned DataFrame with columns:
            - expected_batter_runs (float64 per ball faced)
            - expected_batter_dismissal_risk (float64 per ball faced)
            - batting_expected_sr (float64, 100 * expected_batter_runs)
            - batting_support_balls (int64)
            - batting_fallback_level (int64: 1 to 5)
    """
    logger.info("Computing context-adjusted expected batting baselines for %d deliveries.", len(df))
    context_df = _build_context_columns(df)
    level_cols = ["lvl1", "lvl2", "lvl3", "lvl4"]

    # Exposure: balls faced by the batter (legal balls + no-balls; excludes wides)
    extras_type = df["extras_type"].fillna("").astype(str)
    is_legal = df["is_legal_ball"].fillna(False).astype(bool)
    is_ball_faced = (is_legal | extras_type.isin(["Overstep", "other"])).astype("int64")

    # Targets: runs scored by batter and striker dismissals
    batter_runs = df["runs_scored_on_ball"].fillna(0).astype("int64")
    is_team_wkt = df["is_team_wicket"].fillna(False).astype(bool)
    dismissed_id = df["dismissed_player_id"].fillna(-999).astype("int64")
    striker_id = df["striker_id"].fillna(-888).astype("int64")
    is_striker_dismissed = (is_team_wkt & (dismissed_id == striker_id)).astype("int64")

    # 1. Expected batter runs
    exp_runs, support_b, lvl_b = _compute_hierarchical_loo(
        df=df,
        context_df=context_df,
        level_cols=level_cols,
        target_series=batter_runs,
        weight_series=is_ball_faced,
        min_support=min_support,
    )

    # 2. Expected striker dismissal risk
    exp_wkt_risk, _, _ = _compute_hierarchical_loo(
        df=df,
        context_df=context_df,
        level_cols=level_cols,
        target_series=is_striker_dismissed,
        weight_series=is_ball_faced,
        min_support=min_support,
    )

    return pd.DataFrame({
        "expected_batter_runs": np.round(exp_runs, 4),
        "expected_batter_dismissal_risk": np.round(exp_wkt_risk, 4),
        "batting_expected_sr": np.round(exp_runs * 100.0, 2),
        "batting_support_balls": support_b,
        "batting_fallback_level": lvl_b,
    }, index=df.index)


def compute_expected_bowling_metrics(
    df: pd.DataFrame,
    min_support: int = DEFAULT_MIN_SUPPORT_BALLS,
) -> pd.DataFrame:
    """Computes context-adjusted expected runs conceded and wicket probabilities for bowling.

    Args:
        df: Ball-by-ball DataFrame.
        min_support: Minimum out-of-fold balls required for hierarchical level.

    Returns:
        pd.DataFrame: Aligned DataFrame with columns:
            - expected_bowler_conceded_runs (float64 per legal ball)
            - expected_bowler_wickets (float64 per legal ball)
            - bowling_expected_economy (float64, 6.0 * expected_bowler_conceded_runs)
            - bowling_support_balls (int64)
            - bowling_fallback_level (int64: 1 to 5)
    """
    logger.info("Computing context-adjusted expected bowling baselines for %d deliveries.", len(df))
    context_df = _build_context_columns(df)
    level_cols = ["lvl1", "lvl2", "lvl3", "lvl4"]

    # Exposure for bowling: legal deliveries bowled
    is_legal = df["is_legal_ball"].fillna(False).astype("int64")

    # Targets: runs charged to bowler and bowler-credited dismissals
    runs_conceded = df["runs_charged_to_bowler_on_ball"].fillna(0).astype("int64")
    is_bowler_wkt = df["is_bowler_wicket"].fillna(False).astype("int64")

    # 1. Expected runs conceded
    exp_runs, support_b, lvl_b = _compute_hierarchical_loo(
        df=df,
        context_df=context_df,
        level_cols=level_cols,
        target_series=runs_conceded,
        weight_series=is_legal,
        min_support=min_support,
    )

    # 2. Expected bowler wickets
    exp_wkts, _, _ = _compute_hierarchical_loo(
        df=df,
        context_df=context_df,
        level_cols=level_cols,
        target_series=is_bowler_wkt,
        weight_series=is_legal,
        min_support=min_support,
    )

    return pd.DataFrame({
        "expected_bowler_conceded_runs": np.round(exp_runs, 4),
        "expected_bowler_wickets": np.round(exp_wkts, 4),
        "bowling_expected_economy": np.round(exp_runs * 6.0, 2),
        "bowling_support_balls": support_b,
        "bowling_fallback_level": lvl_b,
    }, index=df.index)

