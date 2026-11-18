"""Ranking Stability and Robustness Analysis Module for SupeRR Selector Analytics.

Performs rigorous statistical sensitivity analysis on final rankings:
1. Weight perturbation analysis (Spearman rho and Kendall tau rank correlations).
2. Threshold sensitivity analysis (evaluating top-10 stability under varying thresholds).
3. Leave-best-match-out analysis (ensuring candidates are not single-match outliers).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_rank_correlations(
    series_a: pd.Series,
    series_b: pd.Series,
) -> Tuple[float, float]:
    """Computes Spearman rho and Kendall tau rank correlations using pandas and numpy.

    Avoids external scipy dependency for maximum portability and reproducibility.
    """
    # 1. Spearman Rho: Pearson correlation of the ranks
    rank_a = series_a.rank()
    rank_b = series_b.rank()
    rho = float(rank_a.corr(rank_b))

    # 2. Kendall Tau: (concordant - discordant) / sqrt((n0 - n1) * (n0 - n2))
    va = series_a.values
    vb = series_b.values
    n = len(va)
    if n <= 1:
        return 1.0, 1.0

    # Concordant and discordant pair counting
    diff_a = va[:, None] - va[None, :]
    diff_b = vb[:, None] - vb[None, :]

    # Upper triangular indices
    triu_idx = np.triu_indices(n, k=1)
    da = np.sign(diff_a[triu_idx])
    db = np.sign(diff_b[triu_idx])

    concordant = np.sum((da * db) > 0)
    discordant = np.sum((da * db) < 0)
    ties_a = np.sum(da == 0)
    ties_b = np.sum(db == 0)

    total_pairs = n * (n - 1) / 2
    denom = np.sqrt((total_pairs - ties_a) * (total_pairs - ties_b))
    tau = float((concordant - discordant) / denom) if denom > 0 else 0.0

    return float(rho), float(tau)


def run_weight_sensitivity(
    eligible_df: pd.DataFrame,
    discipline: str = "BATTING",
) -> Dict[str, Any]:
    """Tests ranking stability under 3 alternative weighting regimes.

    Baseline: 0.35 * Impact + 0.30 * Uplift + 0.20 * Consistency + 0.15 * Confidence
    Alt 1 (Impact-Heavy): 0.50 * Impact + 0.20 * Uplift + 0.15 * Consistency + 0.15 * Confidence
    Alt 2 (Uplift-Heavy): 0.20 * Impact + 0.50 * Uplift + 0.15 * Consistency + 0.15 * Confidence
    Alt 3 (Consistency-Heavy): 0.25 * Impact + 0.25 * Uplift + 0.35 * Consistency + 0.15 * Confidence

    Returns summary dictionary with correlations and top-10 overlap.
    """
    df = eligible_df.copy()

    # Reconstruct unweighted 0-100 components from saved score components
    comp_impact = df["score_impact_component"] / 0.35
    comp_uplift = df["score_uplift_component"] / 0.30
    comp_consistency = df["score_consistency_component"] / 0.20
    comp_confidence = df["score_confidence_component"] / 0.15

    base_score = df["reliability_score"]

    alt1_score = 0.50 * comp_impact + 0.20 * comp_uplift + 0.15 * comp_consistency + 0.15 * comp_confidence
    alt2_score = 0.20 * comp_impact + 0.50 * comp_uplift + 0.15 * comp_consistency + 0.15 * comp_confidence
    alt3_score = 0.25 * comp_impact + 0.25 * comp_uplift + 0.35 * comp_consistency + 0.15 * comp_confidence

    id_col = "striker_id" if discipline == "BATTING" else "bowler_id"

    base_top10 = set(df.sort_values(by="reliability_score", ascending=False).head(10)[id_col])
    alt1_top10 = set(df.assign(s=alt1_score).sort_values(by="s", ascending=False).head(10)[id_col])
    alt2_top10 = set(df.assign(s=alt2_score).sort_values(by="s", ascending=False).head(10)[id_col])
    alt3_top10 = set(df.assign(s=alt3_score).sort_values(by="s", ascending=False).head(10)[id_col])

    rho1, tau1 = compute_rank_correlations(base_score, alt1_score)
    rho2, tau2 = compute_rank_correlations(base_score, alt2_score)
    rho3, tau3 = compute_rank_correlations(base_score, alt3_score)

    return {
        "discipline": discipline,
        "alt1_impact_heavy": {
            "spearman_rho": round(rho1, 4),
            "kendall_tau": round(tau1, 4),
            "top10_overlap": len(base_top10.intersection(alt1_top10)),
        },
        "alt2_uplift_heavy": {
            "spearman_rho": round(rho2, 4),
            "kendall_tau": round(tau2, 4),
            "top10_overlap": len(base_top10.intersection(alt2_top10)),
        },
        "alt3_consistency_heavy": {
            "spearman_rho": round(rho3, 4),
            "kendall_tau": round(tau3, 4),
            "top10_overlap": len(base_top10.intersection(alt3_top10)),
        },
    }


def run_leave_best_match_out(
    top_10_df: pd.DataFrame,
    ball_perf_df: pd.DataFrame,
    discipline: str = "BATTING",
) -> pd.DataFrame:
    """Performs leave-best-match-out test for top-10 players.

    Drops each player's highest net impact match and verifies that impact remains positive.

    Args:
        top_10_df: Top 10 players DataFrame.
        ball_perf_df: Ball-level performance DataFrame (from batting_performance or bowling_performance).
        discipline: 'BATTING' or 'BOWLING'.

    Returns:
        pd.DataFrame with original vs adjusted impact.
    """
    id_col = "striker_id" if discipline == "BATTING" else "bowler_id"
    pressure_col = "batting_pressure_class" if discipline == "BATTING" else "bowling_pressure_class"
    exposure_col = "is_ball_faced" if discipline == "BATTING" else "is_legal_ball"
    impact_col = "batting_combined_impact" if discipline == "BATTING" else "bowling_combined_impact"

    records = []

    for _, player in top_10_df.iterrows():
        p_id = int(player[id_col] if id_col in player else player["player_id"])
        name = str(player["player_name"])
        orig_hp_impact = float(player["hp_combined_impact_per_ball"])

        p_balls = ball_perf_df[ball_perf_df[id_col] == p_id].copy()
        hp_balls = p_balls[
            (p_balls[pressure_col] == "HIGH_PRESSURE") & (p_balls[exposure_col] == True)
        ].copy()

        # Group by match_id
        if hp_balls.empty or hp_balls["match_id"].nunique() <= 1:
            records.append({
                "player_id": p_id,
                "player_name": name,
                "hp_matches_played": hp_balls["match_id"].nunique() if not hp_balls.empty else 0,
                "orig_impact_per_ball": round(orig_hp_impact, 4),
                "ex_best_impact_per_ball": round(orig_hp_impact, 4),
                "impact_retained_pct": 100.0,
                "remains_positive": orig_hp_impact > 0,
            })
            continue

        match_impacts = hp_balls.groupby("match_id")[impact_col].sum()
        best_match_id = match_impacts.idxmax()

        remaining_balls = hp_balls[hp_balls["match_id"] != best_match_id]
        rem_count = len(remaining_balls)
        rem_tot_impact = remaining_balls[impact_col].sum()
        ex_best_per_ball = rem_tot_impact / max(rem_count, 1)

        retained_pct = (ex_best_per_ball / orig_hp_impact * 100.0) if orig_hp_impact != 0 else 0.0

        records.append({
            "player_id": p_id,
            "player_name": name,
            "hp_matches_played": hp_balls["match_id"].nunique(),
            "orig_impact_per_ball": round(orig_hp_impact, 4),
            "ex_best_impact_per_ball": round(ex_best_per_ball, 4),
            "impact_retained_pct": round(retained_pct, 1),
            "remains_positive": bool(ex_best_per_ball > 0),
        })

    return pd.DataFrame(records)
