"""Comprehensive Statistical Reliability and Methodology Audit Tests.

Verifies:
1. Correct scoring weights matching the authoritative specification (0.40, 0.25, 0.20, 0.15).
2. Scoring weights strictly summing to 1.00.
3. Correct mathematical component definitions (logistic slopes, consistency ratios, shrinkage k0).
4. Correct batting and bowling reliability calculation across synthetic test cases.
5. Exact 100% numerical reproducibility of all stored eligible player reliability scores.
6. Deterministic tie-breaking and rank ordering.
7. PDF & documentation methodology agreement with authoritative code configuration.
8. Robust handling of missing, zero, or edge-case inputs.
9. Uncertainty and Empirical Bayes shrinkage calculations.
10. Exact preservation of previous valid official outputs (hashes and Top 10 members).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.reliability.scoring_spec import (
    RELIABILITY_WEIGHTS,
    SHRINKAGE_K0,
    LOGISTIC_SLOPES,
    CONSISTENCY_WEIGHTS,
    ELIGIBILITY_THRESHOLDS,
    FORMULA_STRINGS,
)
from src.reliability.reliability_model import (
    DEFAULT_RELIABILITY_WEIGHTS,
    compute_batter_reliability_scores,
    compute_bowler_reliability_scores,
)
from src.reliability.uncertainty import (
    apply_empirical_bayes_shrinkage,
    compute_confidence_intervals,
)
from src.ranking.tie_breaking import apply_deterministic_ranking

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Test 1 & 2: Weights verification & summation to 1.0
# ---------------------------------------------------------------------------
def test_scoring_weights_exact_and_sum_to_one():
    """Test 1 & 2: Authoritative weights equal {0.40, 0.25, 0.20, 0.15} and sum to 1.0."""
    assert RELIABILITY_WEIGHTS["weight_impact"] == 0.40
    assert RELIABILITY_WEIGHTS["weight_uplift"] == 0.25
    assert RELIABILITY_WEIGHTS["weight_consistency"] == 0.20
    assert RELIABILITY_WEIGHTS["weight_confidence"] == 0.15
    assert DEFAULT_RELIABILITY_WEIGHTS == RELIABILITY_WEIGHTS

    total_weight = sum(RELIABILITY_WEIGHTS.values())
    assert pytest.approx(total_weight, abs=1e-12) == 1.00


# ---------------------------------------------------------------------------
# Test 3: Correct component definitions and parameters
# ---------------------------------------------------------------------------
def test_component_definitions_and_parameters():
    """Test 3: Validates parameter constants across all 4 components."""
    assert SHRINKAGE_K0["batting"] == 20.0
    assert SHRINKAGE_K0["bowling"] == 24.0
    assert LOGISTIC_SLOPES["impact"] == 3.0
    assert LOGISTIC_SLOPES["uplift"] == 3.5
    assert CONSISTENCY_WEIGHTS["positive_match_ratio"] == 0.60
    assert CONSISTENCY_WEIGHTS["downside_protection"] == 0.40
    assert ELIGIBILITY_THRESHOLDS["batting"]["min_hp_balls"] == 20
    assert ELIGIBILITY_THRESHOLDS["bowling"]["min_hp_balls"] == 24


# ---------------------------------------------------------------------------
# Test 4: Correct batting and bowling scoring behavior
# ---------------------------------------------------------------------------
def test_synthetic_scoring_computation():
    """Test 4: Verifies synthetic player scoring matches theoretical expectations."""
    # Perfectly neutral player: impact=0, uplift=0, PMR=0.5, p25=0.0, shrink_w=1.0, se=1.0
    # S_impact = 50.0, S_uplift = 50.0, S_consistency = 50.0, S_confidence = 50.0 -> Score = 50.0
    synth_df = pd.DataFrame({
        "shrunk_hp_combined_impact": [0.0],
        "batting_pressure_uplift": [0.0],
        "bowling_pressure_uplift": [0.0],
        "positive_match_ratio": [0.5],
        "worst_quartile_match_impact": [0.0],
        "shrinkage_weight": [1.0],
        "cluster_se": [1.0],
        "eligibility_status": ["ELIGIBLE"],
    })

    bat_res = compute_batter_reliability_scores(synth_df)
    assert bat_res["score_impact_component"].iloc[0] == 50.0
    assert bat_res["score_uplift_component"].iloc[0] == 50.0
    assert bat_res["score_consistency_component"].iloc[0] == 50.0
    assert bat_res["score_confidence_component"].iloc[0] == 50.0
    assert bat_res["reliability_score"].iloc[0] == 50.0

    bowl_res = compute_bowler_reliability_scores(synth_df)
    assert bowl_res["reliability_score"].iloc[0] == 50.0


# ---------------------------------------------------------------------------
# Test 5: 100% Numerical reproducibility of stored scores
# ---------------------------------------------------------------------------
def test_reproducibility_of_stored_scores():
    """Test 5: Recomputes all eligible scores and asserts zero absolute error."""
    df_bat = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_batting_metrics.parquet")
    df_bowl = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_bowling_metrics.parquet")

    # Batters
    bat_elig = df_bat["eligibility_status"].to_numpy() == "ELIGIBLE"
    assert np.sum(bat_elig) == 155
    recomputed_bat = compute_batter_reliability_scores(df_bat)
    bat_diff = np.abs(
        recomputed_bat["reliability_score"].to_numpy(dtype=float)[bat_elig]
        - df_bat["reliability_score"].to_numpy(dtype=float)[bat_elig]
    )
    assert np.max(bat_diff) < 1e-6
    assert np.median(bat_diff) == 0.0

    # Bowlers
    bowl_elig = df_bowl["eligibility_status"].to_numpy() == "ELIGIBLE"
    assert np.sum(bowl_elig) == 270
    recomputed_bowl = compute_bowler_reliability_scores(df_bowl)
    bowl_diff = np.abs(
        recomputed_bowl["reliability_score"].to_numpy(dtype=float)[bowl_elig]
        - df_bowl["reliability_score"].to_numpy(dtype=float)[bowl_elig]
    )
    assert np.max(bowl_diff) < 1e-6
    assert np.median(bowl_diff) == 0.0


# ---------------------------------------------------------------------------
# Test 6: Deterministic tie-breaking and ordering
# ---------------------------------------------------------------------------
def test_deterministic_tie_breaking():
    """Test 6: Verifies multi-tier deterministic sorting preserves expected ordering."""
    test_df = pd.DataFrame({
        "striker_id": [102, 101, 103],
        "reliability_score": [85.50, 85.50, 90.00],
        "shrunk_hp_combined_impact": [1.50, 1.50, 2.00],
        "positive_match_ratio": [0.80, 0.80, 0.90],
        "hp_matches": [5, 5, 6],
    })
    # For identical scores, lower striker_id (101) must rank ahead of higher striker_id (102)
    ranked = apply_deterministic_ranking(test_df, id_col="striker_id")
    assert list(ranked["striker_id"]) == [103, 101, 102]
    assert list(ranked["rank"]) == [1, 2, 3]


# ---------------------------------------------------------------------------
# Test 7: PDF and documentation methodology agreement
# ---------------------------------------------------------------------------
def test_methodology_documentation_agreement():
    """Test 7: Ensures report template and markdown match the 0.40/0.25/0.20/0.15 formula."""
    report_script_text = (PROJECT_ROOT / "scripts" / "generate_methodology_report.py").read_text(encoding="utf-8")
    sub_doc_text = (PROJECT_ROOT / "submission" / "methodology_report.md").read_text(encoding="utf-8")

    # Must contain 0.40, 0.25, 0.20, 0.15
    for text in [report_script_text, sub_doc_text]:
        assert "0.40" in text
        assert "0.25" in text
        assert "0.20" in text
        assert "0.15" in text
        # Must NOT contain the old erroneous formula
        assert "0.35 * Pctl" not in text
        assert "0.35 &times; Pctl" not in text


# ---------------------------------------------------------------------------
# Test 8: Missing or invalid input handling
# ---------------------------------------------------------------------------
def test_missing_and_edge_case_inputs():
    """Test 8: Ensures null values and edge cases gracefully default without crashing."""
    edge_df = pd.DataFrame({
        "shrunk_hp_combined_impact": [np.nan, None],
        "batting_pressure_uplift": [np.nan, None],
        "positive_match_ratio": [np.nan, None],
        "worst_quartile_match_impact": [np.nan, None],
        "shrinkage_weight": [np.nan, None],
        "cluster_se": [np.nan, -0.5],  # Negative SE must clip to >= 0
        "eligibility_status": ["INELIGIBLE", "ELIGIBLE"],
    })

    res = compute_batter_reliability_scores(edge_df)
    # INELIGIBLE player must have NaN reliability_score
    assert pd.isna(res["reliability_score"].iloc[0])
    # ELIGIBLE player must have valid numeric score in [0, 100]
    assert 0.0 <= res["reliability_score"].iloc[1] <= 100.0


# ---------------------------------------------------------------------------
# Test 9: Uncertainty calculations
# ---------------------------------------------------------------------------
def test_uncertainty_and_shrinkage_calculation():
    """Test 9: Verifies Empirical Bayes shrinkage pulling toward prior."""
    means = pd.Series([2.0, -1.0])
    sizes = pd.Series([20.0, 0.0])  # n=20 with k=20 -> w=0.5; n=0 -> w=0.0
    shrunk, weights = apply_empirical_bayes_shrinkage(means, sizes, population_prior=0.0, k_noise=20.0)

    assert pytest.approx(weights.iloc[0], abs=1e-4) == 0.5000
    assert pytest.approx(shrunk.iloc[0], abs=1e-4) == 1.0000  # 0.5 * 2.0 + 0.5 * 0.0
    assert weights.iloc[1] == 0.0
    assert shrunk.iloc[1] == 0.0

    # Confidence interval calculation
    se, lo, hi = compute_confidence_intervals(shrunk, pd.Series([1.0, 1.0]), pd.Series([4.0, 4.0]), confidence_level=0.90)
    # se = s / sqrt(n) = 1.0 / 2.0 = 0.5
    assert pytest.approx(se.iloc[0], abs=1e-4) == 0.5000
    # lower = 1.0 - 1.645 * 0.5 = 1.0 - 0.8225 = 0.1775
    assert pytest.approx(lo.iloc[0], abs=1e-4) == 0.1775


# ---------------------------------------------------------------------------
# Test 10: Preservation of previous valid outputs
# ---------------------------------------------------------------------------
def test_preservation_of_official_rankings():
    """Test 10: Verifies official Top 10 CSVs match verified SHA-256 hashes and order."""
    expected_bat_hash = "be85fb0d232bacbc8d5714c548b00eb7ff66c74060b6c11dfb3a3675cf9f24bf"
    expected_bowl_hash = "1febb963e22c86fc7dac90e1435e82e98c5484321ad24f63957a63e643b1fd23"

    for path_str in ["outputs/top_10_batters.csv", "submission/top_10_batters.csv"]:
        content = (PROJECT_ROOT / path_str).read_bytes()
        assert hashlib.sha256(content).hexdigest() == expected_bat_hash

    for path_str in ["outputs/top_10_bowlers.csv", "submission/top_10_bowlers.csv"]:
        content = (PROJECT_ROOT / path_str).read_bytes()
        assert hashlib.sha256(content).hexdigest() == expected_bowl_hash
