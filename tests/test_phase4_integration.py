"""Integration tests for Phase 4 player performance and reliability pipeline on real tournament data."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module")
def phase4_outputs():
    """Loads Phase 4 generated parquet datasets."""
    proc_dir = PROJECT_ROOT / "data" / "processed"
    bat_deliv = pd.read_parquet(proc_dir / "batting_performance.parquet")
    bowl_deliv = pd.read_parquet(proc_dir / "bowling_performance.parquet")
    player_bat = pd.read_parquet(proc_dir / "player_batting_metrics.parquet")
    player_bowl = pd.read_parquet(proc_dir / "player_bowling_metrics.parquet")
    return {
        "bat_deliv": bat_deliv,
        "bowl_deliv": bowl_deliv,
        "player_bat": player_bat,
        "player_bowl": player_bowl,
    }


class TestPhase4Integration:
    """Verifies end-to-end Phase 4 outputs on full real-world tournament dataset."""

    def test_parquet_row_and_column_integrity(self, phase4_outputs):
        """Verifies row counts and required column presence across all 4 generated datasets."""
        bat_deliv = phase4_outputs["bat_deliv"]
        bowl_deliv = phase4_outputs["bowl_deliv"]
        player_bat = phase4_outputs["player_bat"]
        player_bowl = phase4_outputs["player_bowl"]

        assert len(bat_deliv) == 200999
        assert len(bowl_deliv) == 200999
        assert len(player_bat) == 888
        assert len(player_bowl) == 647

        required_player_cols = [
            "player_name", "hp_balls", "hp_matches", "ord_balls",
            "hp_combined_impact_per_ball", "batting_pressure_uplift",
            "positive_match_ratio", "shrunk_hp_combined_impact",
            "reliability_score", "eligibility_status", "eligibility_reason",
        ]
        for c in required_player_cols:
            assert c in player_bat.columns, f"Missing batting col: {c}"

        required_bowler_cols = [
            "player_name", "hp_legal_balls", "hp_matches", "ord_balls",
            "hp_combined_impact_per_ball", "bowling_pressure_uplift",
            "positive_match_ratio", "shrunk_hp_combined_impact",
            "reliability_score", "eligibility_status", "eligibility_reason",
        ]
        for c in required_bowler_cols:
            assert c in player_bowl.columns, f"Missing bowling col: {c}"

    def test_eligible_player_counts_and_score_bounds(self, phase4_outputs):
        """Verifies eligible player counts match expected criteria and scores are in [0, 100]."""
        player_bat = phase4_outputs["player_bat"]
        player_bowl = phase4_outputs["player_bowl"]

        elig_bat = player_bat[player_bat["eligibility_status"] == "ELIGIBLE"]
        elig_bowl = player_bowl[player_bowl["eligibility_status"] == "ELIGIBLE"]

        assert len(elig_bat) == 155
        assert len(elig_bowl) == 270

        # No NaNs for eligible
        assert elig_bat["reliability_score"].notnull().all()
        assert elig_bowl["reliability_score"].notnull().all()

        # In bounds [0, 100]
        assert (elig_bat["reliability_score"] >= 0.0).all() and (elig_bat["reliability_score"] <= 100.0).all()
        assert (elig_bowl["reliability_score"] >= 0.0).all() and (elig_bowl["reliability_score"] <= 100.0).all()

        # Ineligible are NaN
        inelig_bat = player_bat[player_bat["eligibility_status"] != "ELIGIBLE"]
        assert inelig_bat["reliability_score"].isna().all()

    def test_cricket_rules_hold_on_real_data(self, phase4_outputs):
        """Verifies cricket laws hold strictly on the real dataset."""
        bat_deliv = phase4_outputs["bat_deliv"]
        bowl_deliv = phase4_outputs["bowl_deliv"]

        # 1. Wides not counted as balls faced by batter
        wides = bat_deliv[bat_deliv["extras_type"] == "wide"]
        assert wides["is_ball_faced"].sum() == 0

        # 2. No-balls counted as balls faced by batter
        noballs = bat_deliv[bat_deliv["extras_type"].isin(["Overstep", "other"])]
        assert noballs["is_ball_faced"].all()

        # 3. Byes and legbyes excluded from bowler runs (0 charged to bowler)
        byes = bowl_deliv[bowl_deliv["extras_type"].isin(["byes", "legbyes"])]
        assert (byes["runs_charged_to_bowler_on_ball"] == 0).all()

    def test_all_reports_exist_and_substantive(self):
        """Verifies all 5 Phase 4 reports exist in reports/phase4/ and are substantive."""
        rep_dir = PROJECT_ROOT / "reports" / "phase4"
        expected_reports = [
            "performance_methodology.md",
            "reliability_methodology.md",
            "player_coverage.md",
            "model_validation.md",
            "sensitivity_analysis.md",
        ]
        for rep in expected_reports:
            p = rep_dir / rep
            assert p.exists(), f"Missing report: {p}"
            assert p.stat().st_size > 500, f"Report {rep} is too short"
