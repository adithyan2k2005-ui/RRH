"""Unit Tests for Ranking Engine and Tie-Breaking Modules."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ranking.ranking_engine import generate_rankings
from src.ranking.tie_breaking import apply_deterministic_ranking


def test_apply_deterministic_ranking_tie_break():
    """Verifies that ties in reliability_score are resolved deterministically by secondary tiers."""
    df = pd.DataFrame({
        "striker_id": [102, 101, 103],
        "reliability_score": [85.0, 85.0, 85.0],
        "shrunk_hp_combined_impact": [1.5, 2.0, 1.5],
        "positive_match_ratio": [0.8, 0.8, 0.9],
        "hp_matches": [5, 5, 5],
    })

    ranked = apply_deterministic_ranking(df, id_col="striker_id", score_col="reliability_score")

    assert list(ranked["rank"]) == [1, 2, 3]
    # Player 101 has highest shrunk impact (2.0) -> Rank 1
    assert ranked.iloc[0]["striker_id"] == 101
    # Player 103 has higher consistency (0.9 vs 0.8) -> Rank 2
    assert ranked.iloc[1]["striker_id"] == 103
    # Player 102 -> Rank 3
    assert ranked.iloc[2]["striker_id"] == 102


def test_apply_deterministic_ranking_id_fallback():
    """Verifies that when all metrics tie, player ID ascending is the deterministic fallback."""
    df = pd.DataFrame({
        "bowler_id": [205, 105],
        "reliability_score": [90.0, 90.0],
        "shrunk_hp_combined_impact": [1.5, 1.5],
        "positive_match_ratio": [0.8, 0.8],
        "hp_matches": [4, 4],
    })

    ranked = apply_deterministic_ranking(df, id_col="bowler_id", score_col="reliability_score")
    assert ranked.iloc[0]["bowler_id"] == 105
    assert ranked.iloc[1]["bowler_id"] == 205


def test_generate_rankings_insufficient_candidates():
    """Verifies that ValueError is raised if eligible candidate pool is smaller than top_n."""
    bat_df = pd.DataFrame({
        "striker_id": [1, 2],
        "eligibility_status": ["ELIGIBLE", "ELIGIBLE"],
        "reliability_score": [80.0, 75.0],
    })
    bowl_df = pd.DataFrame({
        "bowler_id": range(15),
        "eligibility_status": ["ELIGIBLE"] * 15,
        "reliability_score": [80.0] * 15,
    })

    with pytest.raises(ValueError, match="Insufficient eligible batters"):
        generate_rankings(bat_df, bowl_df, top_n=10)

