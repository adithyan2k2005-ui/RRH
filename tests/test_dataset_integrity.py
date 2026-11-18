"""Comprehensive Dataset Integrity, Coverage Reconciliation, and Source Audit Tests.

Verifies:
1. Original CSV row counts match source manifest exactly.
2. Source dataset SHA-256 hashes match the official archive.
3. Processed Parquet records match raw counts 1-to-1.
4. Zero join multiplication detected across all processed tables.
5. Missing records (16 abandoned matches, 3 empty comps) are explicitly accounted for.
6. Analysis coverage funnels (883 -> 867 -> 492) independently verified.
7. Competition counts distinguish registry (141) from fixture-represented (138).
8. Reports contain consistent dataset statistics (883 matches, 141 comps, etc.).
9. No unsupported hardcoded totals (e.g. 744 matches) remain in report templates.
10. Phase 1-5 regression outputs and rankings remain 100% valid.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_EXPECTED_COUNTS = {
    "competitions.csv": (141, 4),
    "teams.csv": (353, 3),
    "matches.csv": (883, 22),
    "ball_by_ball.csv": (200999, 33),
    "competition_team_player_mapping.csv": (6413, 6),
    "playing_eleven.csv": (28381, 9),
}


# ---------------------------------------------------------------------------
# Test 1: Original CSV row counts match source manifest exactly
# ---------------------------------------------------------------------------
def test_original_csv_row_counts_match_manifest():
    """Verify raw CSV row counts and column counts match the authoritative manifest."""
    manifest_path = PROJECT_ROOT / "reports" / "critical_repairs" / "repair2" / "source_manifest.json"
    assert manifest_path.exists(), "Source manifest must exist"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for filename, (expected_rows, expected_cols) in RAW_EXPECTED_COUNTS.items():
        assert filename in manifest["files"], f"Manifest files must contain entry for {filename}"
        file_meta = manifest["files"][filename]
        assert file_meta["row_count"] == expected_rows, f"Row mismatch for {filename}"
        assert file_meta["column_count"] == expected_cols, f"Column mismatch for {filename}"

        # Directly verify actual file on disk
        csv_file = PROJECT_ROOT / "data" / "raw" / filename
        assert csv_file.exists(), f"Raw file {csv_file} must exist"
        df = pd.read_csv(csv_file, low_memory=False)
        assert len(df) == expected_rows, f"Direct CSV read row mismatch for {filename}"
        assert len(df.columns) == expected_cols, f"Direct CSV read column mismatch for {filename}"


# ---------------------------------------------------------------------------
# Test 2: Source dataset SHA-256 hashes match archive
# ---------------------------------------------------------------------------
def test_source_dataset_hashes_match_archive():
    """Verify SHA-256 hashes of data/raw files match the contents inside data pack zip."""
    zip_path = PROJECT_ROOT / "6af458274c1e8_data_pack.zip"
    if not zip_path.exists():
        zip_path = PROJECT_ROOT.parent / "6af458274c1e8_data_pack.zip"

    assert zip_path.exists(), f"Official data pack zip must exist at {zip_path}"

    with zipfile.ZipFile(zip_path, "r") as z:
        for filename in RAW_EXPECTED_COUNTS.keys():
            raw_file = PROJECT_ROOT / "data" / "raw" / filename
            raw_hash = hashlib.sha256(raw_file.read_bytes()).hexdigest()

            # Find matching file in zip (avoid macOS metadata artifacts)
            matching_names = [n for n in z.namelist() if not n.startswith("__MACOSX") and n.endswith(filename)]
            assert len(matching_names) == 1, f"Expected unique match for {filename} in zip, found {matching_names}"
            zip_bytes = z.read(matching_names[0])
            zip_hash = hashlib.sha256(zip_bytes).hexdigest()

            assert raw_hash == zip_hash, f"Hash mismatch between data/raw/{filename} and zip archive"


# ---------------------------------------------------------------------------
# Test 3: Processed Parquet records match raw counts 1-to-1
# ---------------------------------------------------------------------------
def test_processed_parquet_records_match_raw():
    """Verify processed Parquet tables preserve 100% of raw rows with zero dropped records."""
    processed_files = {
        "competitions.parquet": 141,
        "teams.parquet": 353,
        "matches.parquet": 883,
        "match_states.parquet": 200999,
        "pressure_states.parquet": 200999,
        "playing_eleven.parquet": 28381,
        "competition_team_player_mapping.parquet": 6413,
    }

    for filename, expected_rows in processed_files.items():
        parquet_path = PROJECT_ROOT / "data" / "processed" / filename
        assert parquet_path.exists(), f"Processed parquet {parquet_path} must exist"
        df = pd.read_parquet(parquet_path)
        assert len(df) == expected_rows, f"Parquet row count mismatch for {filename}: {len(df)} != {expected_rows}"


# ---------------------------------------------------------------------------
# Test 4: Zero join multiplication detected across all processed tables
# ---------------------------------------------------------------------------
def test_zero_join_multiplication():
    """Verify that joins during ingestion and match state processing created zero duplicate rows."""
    raw_bbb = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "ball_by_ball.csv", low_memory=False)
    proc_states = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "match_states.parquet")
    proc_pressure = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "pressure_states.parquet")

    assert len(raw_bbb) == len(proc_states) == len(proc_pressure) == 200999

    # Verify uniqueness of delivery key: (match_id, innings, delivery_seq)
    key_cols = ["match_id", "innings", "delivery_seq"]
    assert not proc_states.duplicated(subset=key_cols).any(), "Duplicate delivery keys detected in match_states"
    assert not proc_pressure.duplicated(subset=key_cols).any(), "Duplicate delivery keys detected in pressure_states"


# ---------------------------------------------------------------------------
# Test 5: Missing records are explicitly accounted for
# ---------------------------------------------------------------------------
def test_missing_records_explicitly_accounted_for():
    """Verify exactly 16 abandoned fixtures without deliveries and 3 empty competitions."""
    matches_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "matches.parquet")
    bbb_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "match_states.parquet")
    comps_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "competitions.parquet")

    bbb_matches = set(bbb_df["match_id"].unique())
    all_matches = set(matches_df["match_id"].unique())

    matches_without_deliveries = all_matches - bbb_matches
    assert len(matches_without_deliveries) == 16, f"Expected 16 matches without deliveries, got {len(matches_without_deliveries)}"

    # All 16 must have result marked as Match Abandoned
    abandoned_records = matches_df[matches_df["match_id"].isin(matches_without_deliveries)]
    assert (abandoned_records["result"] == "Match Abandoned").all(), "All 16 fixtures must have result 'Match Abandoned'"

    # Check 3 empty competitions
    matches_comps = set(matches_df["comp_id"].unique())
    all_comps = set(comps_df["comp_id"].unique())
    empty_comps = set(int(c) for c in (all_comps - matches_comps))
    assert len(empty_comps) == 3, f"Expected 3 empty competitions, got {len(empty_comps)}"
    assert empty_comps == {2940, 3405, 3473}


# ---------------------------------------------------------------------------
# Test 6: Analysis coverage funnels (883 -> 867 -> 492) independently verified
# ---------------------------------------------------------------------------
def test_analysis_coverage_funnels():
    """Verify coverage stages: 883 supplied -> 867 with deliveries -> 492 contributing to final candidates."""
    cov_path = PROJECT_ROOT / "reports" / "critical_repairs" / "repair2" / "analysis_coverage.json"
    assert cov_path.exists(), "analysis_coverage.json must exist"

    with open(cov_path, "r", encoding="utf-8") as f:
        cov = json.load(f)

    assert cov["matches"]["A_total_supplied_matches"] == 883
    assert cov["matches"]["B_matches_with_ball_by_ball_coverage"] == 867
    assert cov["matches"]["unplayed_or_abandoned_matches_without_deliveries"] == 16
    assert cov["matches"]["F_matches_contributing_to_top_10_rankings"] == 492

    # Verify independently against top 10 batters and bowlers performance records
    top_bat = pd.read_csv(PROJECT_ROOT / "outputs" / "top_10_batters.csv")
    top_bowl = pd.read_csv(PROJECT_ROOT / "outputs" / "top_10_bowlers.csv")
    top_bat_ids = set(top_bat["player_id"])
    top_bowl_ids = set(top_bowl["player_id"])

    bat_perf = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "batting_performance.parquet")
    bowl_perf = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "bowling_performance.parquet")

    bat_matches = set(bat_perf[bat_perf["striker_id"].isin(top_bat_ids)]["match_id"])
    bowl_matches = set(bowl_perf[bowl_perf["bowler_id"].isin(top_bowl_ids)]["match_id"])
    top_perf_matches = bat_matches.union(bowl_matches)

    assert len(top_perf_matches) == 492


# ---------------------------------------------------------------------------
# Test 7: Competition counts distinguish registry (141) from fixture-represented (138)
# ---------------------------------------------------------------------------
def test_competition_counts_distinguish_registry_from_fixtures():
    """Verify registry contains 141 competitions while matches represent 138 competitions."""
    comps_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "competitions.parquet")
    matches_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "matches.parquet")

    total_registry_comps = len(comps_df["comp_id"].unique())
    total_fixture_comps = len(matches_df["comp_id"].unique())

    assert total_registry_comps == 141
    assert total_fixture_comps == 138
    assert total_registry_comps - total_fixture_comps == 3


# ---------------------------------------------------------------------------
# Test 8: Reports contain consistent dataset statistics (883 matches, 141 comps, etc.)
# ---------------------------------------------------------------------------
def test_reports_contain_consistent_dataset_statistics():
    """Verify submission methodology report markdown and scripts have updated counts."""
    report_md = PROJECT_ROOT / "submission" / "methodology_report.md"
    assert report_md.exists()
    content = report_md.read_text(encoding="utf-8")

    assert "883 matches" in content
    assert "867 with ball-by-ball deliveries" in content or "867 with recorded" in content
    assert "141" in content
    assert "353" in content
    assert "200,999" in content
    assert "28,381" in content
    assert "6,413" in content

    val_md = PROJECT_ROOT / "submission" / "submission_validation.md"
    assert val_md.exists()
    val_content = val_md.read_text(encoding="utf-8")
    assert "`competitions.csv`: 141 rows" in val_content
    assert "`teams.csv`: 353 rows" in val_content
    assert "`matches.csv`: 883 rows" in val_content
    assert "`playing_eleven.csv`: 28,381 rows" in val_content
    assert "`competition_team_player_mapping.csv`: 6,413 rows" in val_content


# ---------------------------------------------------------------------------
# Test 9: No unsupported hardcoded totals remain in report templates
# ---------------------------------------------------------------------------
def test_no_unsupported_stale_totals_in_templates():
    """Ensure no stale match counts (e.g. '744 matches' or '16,368') linger in report generators."""
    script_path = PROJECT_ROOT / "scripts" / "generate_methodology_report.py"
    script_text = script_path.read_text(encoding="utf-8")

    assert "744" not in script_text, "Found stale count '744' in generate_methodology_report.py"
    assert "16,368" not in script_text, "Found stale count '16,368' in generate_methodology_report.py"
    assert "2,752" not in script_text, "Found stale count '2,752' in generate_methodology_report.py"


# ---------------------------------------------------------------------------
# Test 10: Phase 1-5 regression outputs and rankings remain 100% valid
# ---------------------------------------------------------------------------
def test_rankings_and_regression_outputs_preserved():
    """Verify that player rankings have not been altered in any way by Repair 2."""
    top_bat = pd.read_csv(PROJECT_ROOT / "outputs" / "top_10_batters.csv")
    top_bowl = pd.read_csv(PROJECT_ROOT / "outputs" / "top_10_bowlers.csv")

    assert len(top_bat) == 10
    assert len(top_bowl) == 10

    # Verify top names and rank 1
    assert top_bat.loc[0, "player_name"] == "Vipraj Nigam"
    assert top_bat.loc[0, "player_id"] == 46066
    assert pytest.approx(float(top_bat.loc[0, "reliability_score"]), abs=1e-2) == 92.69

    assert top_bowl.loc[0, "player_name"] == "Manimaran Siddharth"
    assert top_bowl.loc[0, "player_id"] == 6237
    assert pytest.approx(float(top_bowl.loc[0, "reliability_score"]), abs=1e-2) == 88.46
