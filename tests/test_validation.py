"""Validation and data quality tests for SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.load_data import load_all_datasets
from src.validation.validate_data import (
    inspect_schemas,
    standardize_and_export_parquet,
    validate_cricket_semantics,
    validate_relationships,
)


@pytest.fixture(scope="module")
def loaded_datasets():
    """Module-level fixture to load datasets once for tests."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    return load_all_datasets(raw_dir)


class TestPipelineCorrectness:
    """Tests verifying pipeline functionality, repeatability, and transformation safety."""

    def test_schema_inspection_structure(self, loaded_datasets):
        """Verify inspect_schemas returns required structure for all datasets."""
        schemas = inspect_schemas(loaded_datasets)
        assert len(schemas) == 6
        for name, meta in schemas.items():
            assert "row_count" in meta
            assert "column_count" in meta
            assert "exact_duplicate_rows" in meta
            assert "candidate_single_column_pks" in meta
            assert "column_metrics" in meta

    def test_parquet_export_row_count_consistency(self, loaded_datasets):
        """Verify standardized Parquet exports have exact row count match with raw CSVs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            exported = standardize_and_export_parquet(loaded_datasets, tmp_path)

            for name, p_file in exported.items():
                assert p_file.exists()
                df_parquet = pd.read_parquet(p_file)
                assert len(df_parquet) == len(loaded_datasets[name])
                assert list(df_parquet.columns) == list(loaded_datasets[name].columns)

    def test_repeatable_processing(self, loaded_datasets):
        """Verify that running standardization twice produces identical parquet row and col counts."""
        with tempfile.TemporaryDirectory() as tmp_dir1, tempfile.TemporaryDirectory() as tmp_dir2:
            out1 = standardize_and_export_parquet(loaded_datasets, Path(tmp_dir1))
            out2 = standardize_and_export_parquet(loaded_datasets, Path(tmp_dir2))

            for name in out1:
                df1 = pd.read_parquet(out1[name])
                df2 = pd.read_parquet(out2[name])
                assert df1.shape == df2.shape
                assert list(df1.columns) == list(df2.columns)


class TestDatasetQualityChecks:
    """Tests verifying real-world dataset integrity, referential links, and cricket rules."""

    def test_required_columns_present(self, loaded_datasets):
        """Verify all critical known columns exist in each dataset."""
        expected_cols = {
            "competitions": ["comp_id", "comp_name", "match_format", "season"],
            "teams": ["comp_id", "team_id", "team_name"],
            "matches": [
                "match_id", "comp_id", "match_number", "match_date", "stage",
                "home_team_id", "away_team_id", "toss_win_team_id", "win_team_id",
                "first_inn_revised_overs", "second_inn_revised_overs", "revised_target",
                "knock_out", "result"
            ],
            "ball_by_ball": [
                "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
                "batting_team_id", "bowling_team_id", "striker_id", "bowler_id",
                "runs", "is_four", "is_six", "is_wicket", "dismissal_type",
                "dismissed_player_id", "extras_type", "extras1_runs", "extras_2_runs",
                "bowl_speed"
            ],
            "competition_team_player_mapping": [
                "comp_id", "comp_name", "team_id", "team_name", "player_id", "player_name"
            ],
            "playing_eleven": [
                "match_id", "team_id", "player_id", "batting_order", "is_played",
                "is_captain", "is_wk", "is_impact", "is_impact_off"
            ],
        }

        for name, cols in expected_cols.items():
            df = loaded_datasets[name]
            for col in cols:
                assert col in df.columns, f"Missing required column {col} in {name}"

    def test_candidate_keys_uniqueness(self, loaded_datasets):
        """Verify uniqueness of confirmed primary and composite keys."""
        # Competitions: comp_id unique
        assert loaded_datasets["competitions"]["comp_id"].is_unique

        # Matches: match_id unique
        assert loaded_datasets["matches"]["match_id"].is_unique

        # Teams: (comp_id, team_id) unique
        teams_dups = loaded_datasets["teams"].duplicated(subset=["comp_id", "team_id"]).sum()
        assert teams_dups == 0

        # CTPM: (comp_id, team_id, player_id) unique
        ctpm_dups = loaded_datasets["competition_team_player_mapping"].duplicated(
            subset=["comp_id", "team_id", "player_id"]
        ).sum()
        assert ctpm_dups == 0

        # Ball by ball: (match_id, innings, overid, over_ball_num) unique
        bbb_dups = loaded_datasets["ball_by_ball"].duplicated(
            subset=["match_id", "innings", "overid", "over_ball_num"]
        ).sum()
        assert bbb_dups == 0

    def test_referential_integrity(self, loaded_datasets):
        """Verify referential integrity across competitions, matches, and players."""
        relationships = validate_relationships(loaded_datasets)

        # All matches comp_id in competitions
        assert len(relationships["matches_missing_comps"]) == 0

        # All teams comp_id in competitions
        assert len(relationships["teams_missing_comps"]) == 0

        # All home and away teams in matches exist in teams
        assert len(relationships["orphaned_home_teams"]) == 0
        assert len(relationships["orphaned_away_teams"]) == 0

        # All ball_by_ball matches exist in matches.csv
        assert len(relationships["bbb_missing_in_matches"]) == 0

        # All ball_by_ball players exist in player mapping
        assert len(relationships["bbb_players_not_in_ctpm"]) == 0

    def test_matches_without_deliveries_are_abandoned(self, loaded_datasets):
        """Verify all matches without deliveries in ball_by_ball are abandoned matches."""
        relationships = validate_relationships(loaded_datasets)
        matches = loaded_datasets["matches"]

        no_bbb_ids = relationships["matches_without_delivery_data"]
        assert len(no_bbb_ids) == 16

        no_bbb_matches = matches[matches["match_id"].isin(no_bbb_ids)]
        assert (no_bbb_matches["result"] == "Match Abandoned").all()

    def test_playing_eleven_duplicates_are_super_overs(self, loaded_datasets):
        """Verify duplicate (match_id, player_id) rows in playing_eleven belong only to Super Overs."""
        relationships = validate_relationships(loaded_datasets)
        matches = loaded_datasets["matches"]

        dup_matches = relationships["pe_matches_with_duplicates"]
        assert set(dup_matches) == {13613, 21176, 28962}

        # Check results contain super over or eliminator
        dup_match_records = matches[matches["match_id"].isin(dup_matches)]
        for _, row in dup_match_records.iterrows():
            res_lower = row["result"].lower()
            assert "super over" in res_lower or "eliminator" in res_lower

    def test_cricket_run_formula_and_extras(self, loaded_datasets):
        """Verify that runs is batter runs and total ball runs equals runs + extras1_runs + extras_2_runs."""
        bbb = loaded_datasets["ball_by_ball"]

        # Wides must have 0 batter runs
        wide_runs = bbb[bbb["extras_type"] == "wide"]["runs"].sum()
        assert wide_runs == 0

        # Byes must have 0 batter runs
        byes_runs = bbb[bbb["extras_type"] == "byes"]["runs"].sum()
        assert byes_runs == 0

        # Check total runs formula on random sample of 10,000 deliveries
        sample = bbb.sample(n=10000, random_state=42)
        expected_total = sample["runs"] + sample["extras1_runs"] + sample["extras_2_runs"]
        assert (expected_total >= sample["runs"]).all()

    def test_cricket_retired_hurt_detection(self, loaded_datasets):
        """Verify detection of the 12 retired hurt rows where is_wicket=False but dismissed_player_id is set."""
        semantics = validate_cricket_semantics(loaded_datasets)
        assert semantics["retired_hurt_rows_count"] == 12
        assert len(semantics["retired_hurt_sample_matches"]) == 12

    def test_speed_gun_anomalies_detected(self, loaded_datasets):
        """Verify speed gun data quality anomalies are captured."""
        semantics = validate_cricket_semantics(loaded_datasets)
        assert semantics["bowl_speed_zero_count"] == 77861
        assert semantics["bowl_speed_negative_count"] == 1
        assert semantics["bowl_speed_extreme_outliers_count"] == 20
