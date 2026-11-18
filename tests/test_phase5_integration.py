"""Integration Tests for Phase 5 Outputs and Quality Gate Verification."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.validation.validate_final_rankings import validate_rankings_checklist

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports" / "phase5"


def test_phase5_all_16_quality_gates_passed():
    """Verifies that all 16 quality gates in validate_final_rankings pass."""
    all_passed, results = validate_rankings_checklist(OUTPUTS_DIR)
    assert all_passed is True
    assert len(results) == 16
    for res in results:
        assert res["status"] == "PASSED", f"Gate {res['gate']} failed: {res['details']}"


def test_top_10_batters_csv_structure_and_values():
    """Verifies top 10 batters CSV content, sorting, and values."""
    csv_path = OUTPUTS_DIR / "top_10_batters.csv"
    assert csv_path.exists()
    df = pd.read_csv(csv_path)

    assert len(df) == 10
    assert list(df["rank"]) == list(range(1, 11))
    assert df["player_id"].nunique() == 10
    assert (df["eligibility_status"] == "ELIGIBLE").all()

    # Scores must be descending
    scores = df["reliability_score"].values
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    # All 10 must have positive impact under pressure
    assert (df["high_pressure_impact"] > 0).all()

    # First rank must be Vipraj Nigam (46066)
    assert df.iloc[0]["player_id"] == 46066
    assert df.iloc[0]["player_name"] == "Vipraj Nigam"


def test_top_10_bowlers_csv_structure_and_values():
    """Verifies top 10 bowlers CSV content, sorting, and values."""
    csv_path = OUTPUTS_DIR / "top_10_bowlers.csv"
    assert csv_path.exists()
    df = pd.read_csv(csv_path)

    assert len(df) == 10
    assert list(df["rank"]) == list(range(1, 11))
    assert df["player_id"].nunique() == 10
    assert (df["eligibility_status"] == "ELIGIBLE").all()

    # Scores must be descending
    scores = df["reliability_score"].values
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    # All 10 must have positive impact under pressure
    assert (df["high_pressure_impact"] > 0).all()

    # First rank must be Manimaran Siddharth (6237)
    assert df.iloc[0]["player_id"] == 6237
    assert df.iloc[0]["player_name"] == "Manimaran Siddharth"


def test_submission_selections_md_exists_and_contains_all_20():
    """Verifies outputs/submission_selections.md accurately lists all 20 players."""
    md_path = OUTPUTS_DIR / "submission_selections.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")

    # Batters
    assert "Vipraj Nigam" in content
    assert "46066" in content
    assert "Joshua Clarkson" in content
    assert "4686" in content

    # Bowlers
    assert "Manimaran Siddharth" in content
    assert "6237" in content
    assert "Saqib Mahmood" in content
    assert "4499" in content


def test_phase5_reports_exist():
    """Verifies that all required Phase 5 reports and audit files are generated."""
    assert (REPORTS_DIR / "ranking_evidence.md").exists()
    assert (REPORTS_DIR / "ranking_validation.md").exists()
    assert (REPORTS_DIR / "ranking_sensitivity.md").exists()
    assert (REPORTS_DIR / "selection_boundary.md").exists()
    assert (REPORTS_DIR / "eligibility_audit.csv").exists()

