"""Player Reliability Model Module for SupeRR Selector Analytics.

Implements the multi-dimensional player reliability scoring system:
R_raw = 0.40 * S_impact + 0.25 * S_uplift + 0.20 * S_consistency + 0.15 * S_confidence

Strictly bounds scores in [0, 100] using transparent mathematical scaling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

from .scoring_spec import RELIABILITY_WEIGHTS, LOGISTIC_SLOPES, CONSISTENCY_WEIGHTS

logger = logging.getLogger(__name__)

DEFAULT_RELIABILITY_WEIGHTS: Dict[str, float] = RELIABILITY_WEIGHTS


def compute_batter_reliability_scores(
    metrics_df: pd.DataFrame,
    weights_config: Dict[str, float] | None = None,
) -> pd.DataFrame:
    """Computes transparent, composite 0-100 reliability ratings for batters.

    Args:
        metrics_df: Aggregated batter metrics DataFrame with eligibility, baselines,
            consistency, and uncertainty features.
        weights_config: Optional custom weights configuration.

    Returns:
        pd.DataFrame: DataFrame with normalized score components and reliability_score.
    """
    logger.info("Computing batter reliability ratings for %d players.", len(metrics_df))
    cfg = weights_config or DEFAULT_RELIABILITY_WEIGHTS

    w_imp = cfg["weight_impact"]
    w_upl = cfg["weight_uplift"]
    w_con = cfg["weight_consistency"]
    w_cnf = cfg["weight_confidence"]

    # Component 1: Shrunk impact (runs per ball above expectation)
    # Centered at 0 -> 50.0; +0.50 rpb -> ~81.8; -0.50 rpb -> ~18.2
    shrunk_impact = metrics_df["shrunk_hp_combined_impact"].fillna(0.0).values
    s_impact = 100.0 / (1.0 + np.exp(-3.0 * shrunk_impact))

    # Component 2: Pressure uplift (HP impact minus ordinary baseline)
    # Centered at 0 -> 50.0; +0.30 rpb -> ~74.1; -0.30 rpb -> ~25.9
    uplift = metrics_df["batting_pressure_uplift"].fillna(0.0).values
    s_uplift = 100.0 / (1.0 + np.exp(-3.5 * uplift))

    # Component 3: Match consistency (positive match ratio & downside protection)
    pos_ratio = metrics_df["positive_match_ratio"].fillna(0.0).values
    p25 = metrics_df["worst_quartile_match_impact"].fillna(0.0).values
    # Downside score: p25 in [-1.0, 1.0] scaled to [0, 1]
    p25_norm = np.clip((p25 + 1.0) / 2.0, 0.0, 1.0)
    s_consistency = 100.0 * (0.60 * pos_ratio + 0.40 * p25_norm)

    # Component 4: Statistical confidence (shrinkage weight * low standard error)
    shrink_w = metrics_df["shrinkage_weight"].fillna(0.0).values
    se = np.maximum(0.0, metrics_df["cluster_se"].fillna(1.0).values)
    s_confidence = 100.0 * shrink_w * (1.0 / (1.0 + se))

    # Composite reliability rating
    composite = (
        w_imp * s_impact
        + w_upl * s_uplift
        + w_con * s_consistency
        + w_cnf * s_confidence
    )
    composite = np.clip(composite, 0.0, 100.0)

    # Ineligible players receive NaN for reliability_score
    is_eligible = (metrics_df["eligibility_status"] == "ELIGIBLE").values
    final_score = np.where(is_eligible, np.round(composite, 2), np.nan)

    res_df = pd.DataFrame({
        "score_impact_component": np.round(s_impact, 2),
        "score_uplift_component": np.round(s_uplift, 2),
        "score_consistency_component": np.round(s_consistency, 2),
        "score_confidence_component": np.round(s_confidence, 2),
        "reliability_score": final_score,
    }, index=metrics_df.index)

    return res_df


def compute_bowler_reliability_scores(
    metrics_df: pd.DataFrame,
    weights_config: Dict[str, float] | None = None,
) -> pd.DataFrame:
    """Computes transparent, composite 0-100 reliability ratings for bowlers.

    Args:
        metrics_df: Aggregated bowler metrics DataFrame with eligibility, baselines,
            consistency, and uncertainty features.
        weights_config: Optional custom weights configuration.

    Returns:
        pd.DataFrame: DataFrame with normalized score components and reliability_score.
    """
    logger.info("Computing bowler reliability ratings for %d players.", len(metrics_df))
    cfg = weights_config or DEFAULT_RELIABILITY_WEIGHTS

    w_imp = cfg["weight_impact"]
    w_upl = cfg["weight_uplift"]
    w_con = cfg["weight_consistency"]
    w_cnf = cfg["weight_confidence"]

    # Component 1: Shrunk impact (runs per ball prevented/gained above expectation)
    shrunk_impact = metrics_df["shrunk_hp_combined_impact"].fillna(0.0).values
    s_impact = 100.0 / (1.0 + np.exp(-3.0 * shrunk_impact))

    # Component 2: Pressure uplift
    uplift = metrics_df["bowling_pressure_uplift"].fillna(0.0).values
    s_uplift = 100.0 / (1.0 + np.exp(-3.5 * uplift))

    # Component 3: Match consistency
    pos_ratio = metrics_df["positive_match_ratio"].fillna(0.0).values
    p25 = metrics_df["worst_quartile_match_impact"].fillna(0.0).values
    p25_norm = np.clip((p25 + 1.0) / 2.0, 0.0, 1.0)
    s_consistency = 100.0 * (0.60 * pos_ratio + 0.40 * p25_norm)

    # Component 4: Statistical confidence
    shrink_w = metrics_df["shrinkage_weight"].fillna(0.0).values
    se = np.maximum(0.0, metrics_df["cluster_se"].fillna(1.0).values)
    s_confidence = 100.0 * shrink_w * (1.0 / (1.0 + se))

    # Composite reliability rating
    composite = (
        w_imp * s_impact
        + w_upl * s_uplift
        + w_con * s_consistency
        + w_cnf * s_confidence
    )
    composite = np.clip(composite, 0.0, 100.0)

    is_eligible = (metrics_df["eligibility_status"] == "ELIGIBLE").values
    final_score = np.where(is_eligible, np.round(composite, 2), np.nan)

    res_df = pd.DataFrame({
        "score_impact_component": np.round(s_impact, 2),
        "score_uplift_component": np.round(s_uplift, 2),
        "score_consistency_component": np.round(s_consistency, 2),
        "score_confidence_component": np.round(s_confidence, 2),
        "reliability_score": final_score,
    }, index=metrics_df.index)

    return res_df

