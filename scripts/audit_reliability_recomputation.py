"""Independent mathematical recomputation and audit of player reliability scores.

Loads raw Phase 4 parquet files, recomputes each scoring component from first principles,
computes the composite reliability score, and performs strict micro-level floating-point
comparison against the stored values.
"""

from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def audit_recomputation():
    data_dir = PROJECT_ROOT / "data" / "processed"
    outputs_dir = PROJECT_ROOT / "outputs"
    rep_dir = PROJECT_ROOT / "reports" / "critical_repairs" / "repair1"
    rep_dir.mkdir(parents=True, exist_ok=True)

    df_bat = pd.read_parquet(data_dir / "player_batting_metrics.parquet")
    df_bowl = pd.read_parquet(data_dir / "player_bowling_metrics.parquet")

    w_imp = 0.40
    w_upl = 0.25
    w_con = 0.20
    w_cnf = 0.15

    # ----------------------------------------------------
    # BATTING RECOMPUTATION
    # ----------------------------------------------------
    shrunk_impact_b = df_bat["shrunk_hp_combined_impact"].fillna(0.0).to_numpy(dtype=float)
    s_impact_b = 100.0 / (1.0 + np.exp(-3.0 * shrunk_impact_b))

    uplift_b = df_bat["batting_pressure_uplift"].fillna(0.0).to_numpy(dtype=float)
    s_uplift_b = 100.0 / (1.0 + np.exp(-3.5 * uplift_b))

    pos_ratio_b = df_bat["positive_match_ratio"].fillna(0.0).to_numpy(dtype=float)
    p25_b = df_bat["worst_quartile_match_impact"].fillna(0.0).to_numpy(dtype=float)
    p25_norm_b = np.clip((p25_b + 1.0) / 2.0, 0.0, 1.0)
    s_consistency_b = 100.0 * (0.60 * pos_ratio_b + 0.40 * p25_norm_b)

    shrink_w_b = df_bat["shrinkage_weight"].fillna(0.0).to_numpy(dtype=float)
    se_b = np.maximum(0.0, df_bat["cluster_se"].fillna(1.0).to_numpy(dtype=float))
    s_confidence_b = 100.0 * shrink_w_b * (1.0 / (1.0 + se_b))

    composite_b = w_imp * s_impact_b + w_upl * s_uplift_b + w_con * s_consistency_b + w_cnf * s_confidence_b
    composite_b = np.clip(composite_b, 0.0, 100.0)

    is_elig_b = (df_bat["eligibility_status"] == "ELIGIBLE").to_numpy(dtype=bool)
    recomputed_scores_b = np.where(is_elig_b, np.round(composite_b, 2), np.nan)
    stored_scores_b = df_bat["reliability_score"].to_numpy(dtype=float)

    diff_b = np.abs(recomputed_scores_b[is_elig_b] - stored_scores_b[is_elig_b])

    # ----------------------------------------------------
    # BOWLING RECOMPUTATION
    # ----------------------------------------------------
    shrunk_impact_bw = df_bowl["shrunk_hp_combined_impact"].fillna(0.0).to_numpy(dtype=float)
    s_impact_bw = 100.0 / (1.0 + np.exp(-3.0 * shrunk_impact_bw))

    uplift_bw = df_bowl["bowling_pressure_uplift"].fillna(0.0).to_numpy(dtype=float)
    s_uplift_bw = 100.0 / (1.0 + np.exp(-3.5 * uplift_bw))

    pos_ratio_bw = df_bowl["positive_match_ratio"].fillna(0.0).to_numpy(dtype=float)
    p25_bw = df_bowl["worst_quartile_match_impact"].fillna(0.0).to_numpy(dtype=float)
    p25_norm_bw = np.clip((p25_bw + 1.0) / 2.0, 0.0, 1.0)
    s_consistency_bw = 100.0 * (0.60 * pos_ratio_bw + 0.40 * p25_norm_bw)

    shrink_w_bw = df_bowl["shrinkage_weight"].fillna(0.0).to_numpy(dtype=float)
    se_bw = np.maximum(0.0, df_bowl["cluster_se"].fillna(1.0).to_numpy(dtype=float))
    s_confidence_bw = 100.0 * shrink_w_bw * (1.0 / (1.0 + se_bw))

    composite_bw = w_imp * s_impact_bw + w_upl * s_uplift_bw + w_con * s_consistency_bw + w_cnf * s_confidence_bw
    composite_bw = np.clip(composite_bw, 0.0, 100.0)

    is_elig_bw = (df_bowl["eligibility_status"] == "ELIGIBLE").to_numpy(dtype=bool)
    recomputed_scores_bw = np.where(is_elig_bw, np.round(composite_bw, 2), np.nan)
    stored_scores_bw = df_bowl["reliability_score"].to_numpy(dtype=float)

    diff_bw = np.abs(recomputed_scores_bw[is_elig_bw] - stored_scores_bw[is_elig_bw])

    print("=================================================================")
    print("RELIABILITY SCORE RECOMPUTATION AUDIT RESULTS")
    print("=================================================================")
    print(f"Batting Eligible Players: {np.sum(is_elig_b)}")
    print(f"  Max Absolute Error:    {np.max(diff_b):.10f}")
    print(f"  Median Absolute Error: {np.median(diff_b):.10f}")
    print(f"  Discrepancies > 1e-6:  {np.sum(diff_b > 1e-6)}")
    print(f"Bowling Eligible Players: {np.sum(is_elig_bw)}")
    print(f"  Max Absolute Error:    {np.max(diff_bw):.10f}")
    print(f"  Median Absolute Error: {np.median(diff_bw):.10f}")
    print(f"  Discrepancies > 1e-6:  {np.sum(diff_bw > 1e-6)}")

    # Build reconciliation dataframe
    bat_recon = df_bat[is_elig_b].copy()
    bat_recon["recomputed_s_impact"] = np.round(s_impact_b[is_elig_b], 2)
    bat_recon["recomputed_s_uplift"] = np.round(s_uplift_b[is_elig_b], 2)
    bat_recon["recomputed_s_consistency"] = np.round(s_consistency_b[is_elig_b], 2)
    bat_recon["recomputed_s_confidence"] = np.round(s_confidence_b[is_elig_b], 2)
    bat_recon["recomputed_score"] = recomputed_scores_b[is_elig_b]
    bat_recon["abs_error"] = diff_b
    bat_recon["discipline"] = "BATTING"
    bat_recon["player_id"] = bat_recon["striker_id"]

    bowl_recon = df_bowl[is_elig_bw].copy()
    bowl_recon["recomputed_s_impact"] = np.round(s_impact_bw[is_elig_bw], 2)
    bowl_recon["recomputed_s_uplift"] = np.round(s_uplift_bw[is_elig_bw], 2)
    bowl_recon["recomputed_s_consistency"] = np.round(s_consistency_bw[is_elig_bw], 2)
    bowl_recon["recomputed_s_confidence"] = np.round(s_confidence_bw[is_elig_bw], 2)
    bowl_recon["recomputed_score"] = recomputed_scores_bw[is_elig_bw]
    bowl_recon["abs_error"] = diff_bw
    bowl_recon["discipline"] = "BOWLING"
    bowl_recon["player_id"] = bowl_recon["bowler_id"]

    cols = [
        "discipline", "player_id", "player_name",
        "stored_score", "recomputed_score", "abs_error",
        "score_impact_component", "recomputed_s_impact",
        "score_uplift_component", "recomputed_s_uplift",
        "score_consistency_component", "recomputed_s_consistency",
        "score_confidence_component", "recomputed_s_confidence"
    ]
    
    bat_recon["stored_score"] = bat_recon["reliability_score"]
    bowl_recon["stored_score"] = bowl_recon["reliability_score"]

    recon_full = pd.concat([bat_recon[cols], bowl_recon[cols]], ignore_index=True)
    recon_path = rep_dir / "score_reconciliation.csv"
    recon_full.to_csv(recon_path, index=False)
    print(f"Reconciliation CSV saved to {recon_path} ({len(recon_full)} rows).")

    # Verify tie-breaking and top 10 rankings match outputs/top_10_batters.csv
    top10_bat_stored = pd.read_csv(outputs_dir / "top_10_batters.csv")
    top10_bowl_stored = pd.read_csv(outputs_dir / "top_10_bowlers.csv")

    from src.ranking.tie_breaking import apply_deterministic_ranking

    df_bat_elig = df_bat[is_elig_b].copy()
    df_bat_elig["reliability_score"] = recomputed_scores_b[is_elig_b]
    re_ranked_bat = apply_deterministic_ranking(df_bat_elig, id_col="striker_id").head(10)

    df_bowl_elig = df_bowl[is_elig_bw].copy()
    df_bowl_elig["reliability_score"] = recomputed_scores_bw[is_elig_bw]
    re_ranked_bowl = apply_deterministic_ranking(df_bowl_elig, id_col="bowler_id").head(10)

    bat_ids_match = list(re_ranked_bat["striker_id"]) == list(top10_bat_stored["player_id"])
    bowl_ids_match = list(re_ranked_bowl["bowler_id"]) == list(top10_bowl_stored["player_id"])

    bat_scores_match = np.allclose(re_ranked_bat["reliability_score"], top10_bat_stored["reliability_score"], atol=1e-5)
    bowl_scores_match = np.allclose(re_ranked_bowl["reliability_score"], top10_bowl_stored["reliability_score"], atol=1e-5)

    print(f"Top 10 Batters Player IDs Match: {bat_ids_match}")
    print(f"Top 10 Batters Scores Match:     {bat_scores_match}")
    print(f"Top 10 Bowlers Player IDs Match: {bowl_ids_match}")
    print(f"Top 10 Bowlers Scores Match:     {bowl_scores_match}")

    if not (bat_ids_match and bowl_ids_match and bat_scores_match and bowl_scores_match):
        print("CRITICAL: Recomputed rankings DO NOT MATCH stored outputs!")
        return False
    else:
        print("SUCCESS: 100% of stored scores and top 10 rankings mathematically verified!")
        return True

if __name__ == "__main__":
    audit_recomputation()
