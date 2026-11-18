"""Unit Tests for Ranking Eligibility Audit and Gating."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ranking.eligibility_audit import generate_eligibility_audit
from src.ranking.ranking_engine import generate_rankings


def test_ranking_excludes_ineligible_candidates():
    """Verifies that INELIGIBLE candidates are strictly excluded from rankings regardless of high score."""
    bat_df = pd.DataFrame({
        "striker_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 999],
        "eligibility_status": ["ELIGIBLE"] * 10 + ["INELIGIBLE_HP_BALLS"],
        "reliability_score": [80.0] * 10 + [99.9],  # High score but ineligible
        "shrunk_hp_combined_impact": [1.0] * 11,
        "positive_match_ratio": [0.8] * 11,
        "hp_matches": [5] * 11,
    })
    bowl_df = pd.DataFrame({
        "bowler_id": range(15),
        "eligibility_status": ["ELIGIBLE"] * 15,
        "reliability_score": [75.0] * 15,
        "shrunk_hp_combined_impact": [1.0] * 15,
        "positive_match_ratio": [0.8] * 15,
        "hp_matches": [5] * 15,
    })

    rankings = generate_rankings(bat_df, bowl_df, top_n=10)
    top_batters = rankings["top_10_batters"]

    assert 999 not in top_batters["striker_id"].values
    assert len(top_batters) == 10
    assert (top_batters["eligibility_status"] == "ELIGIBLE").all()


def test_generate_eligibility_audit_flags():
    """Verifies eligibility audit accurately records boolean threshold flags."""
    bat_df = pd.DataFrame({
        "striker_id": [101, 102],
        "player_name": ["Batter A", "Batter B"],
        "hp_balls": [25, 15],
        "hp_matches": [4, 2],
        "ord_balls": [30, 20],
        "eligibility_status": ["ELIGIBLE", "INSUFFICIENT_HP_BALLS"],
        "reliability_score": [85.0, 60.0],
    })
    bowl_df = pd.DataFrame({
        "bowler_id": [201],
        "player_name": ["Bowler A"],
        "hp_balls": [20],  # Bowler threshold is 24
        "hp_matches": [3],
        "ord_balls": [35],
        "eligibility_status": ["INSUFFICIENT_HP_BALLS"],
        "reliability_score": [70.0],
    })

    audit_df = generate_eligibility_audit(bat_df, bowl_df)

    assert len(audit_df) == 3
    row_a = audit_df[audit_df["player_id"] == 101].iloc[0]
    assert row_a["meets_hp_balls"] is True or row_a["meets_hp_balls"] == 1
    assert row_a["meets_hp_matches"] is True or row_a["meets_hp_matches"] == 1
    assert row_a["meets_ord_balls"] is True or row_a["meets_ord_balls"] == 1

    row_b = audit_df[audit_df["player_id"] == 102].iloc[0]
    assert row_b["meets_hp_balls"] is False or row_b["meets_hp_balls"] == 0

    row_bowl = audit_df[audit_df["player_id"] == 201].iloc[0]
    assert row_bowl["meets_hp_balls"] is False or row_bowl["meets_hp_balls"] == 0  # 20 < 24

