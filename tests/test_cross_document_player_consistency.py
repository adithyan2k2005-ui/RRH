"""Automated Cross-Document Player-Identity Consistency Test Suite.

Verifies:
1. Exact 1-to-1 alignment between player_id, player_name, and reliability_score across:
   - outputs/top_10_batters.csv and outputs/top_10_bowlers.csv
   - submission/top_10_batters.csv and submission/top_10_bowlers.csv
   - submission/submission_selections.md
   - submission/methodology_report.md
   - submission/methodology_report.pdf
   - data/processed/competition_team_player_mapping.parquet
   - data/processed/player_batting_metrics.parquet & player_bowling_metrics.parquet
2. Rejection / failure if a valid score is paired with an incorrect player name.
3. Verification that no famous player names are incorrectly substituted for the actual qualified players.
"""

from pathlib import Path
import pandas as pd
import pytest
import fitz  # PyMuPDF

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
SUBMISSION_DIR = REPO_ROOT / "submission"
DATA_PROC = REPO_ROOT / "data" / "processed"

# The authoritative ground-truth Top 10 Batters (Phase 5 verified)
EXPECTED_BATTERS = [
    (1, 46066, "Vipraj Nigam", 92.69),
    (2, 6651, "Towhid Hridoy", 92.25),
    (3, 796, "Matthew Wade", 91.43),
    (4, 6448, "Ibrahim Zadran", 90.45),
    (5, 152, "Ravindra Jadeja", 84.80),
    (6, 1219, "David Willey", 84.05),
    (7, 2984, "Sikandar Raza", 80.96),
    (8, 4708, "Rinku Singh", 80.77),
    (9, 7897, "Namboori Tilak Varma", 80.62),
    (10, 4686, "Joshua Clarkson", 80.21),
]

# The authoritative ground-truth Top 10 Bowlers (Phase 5 verified)
EXPECTED_BOWLERS = [
    (1, 6237, "Manimaran Siddharth", 88.46),
    (2, 29080, "Muhammad Khan", 88.39),
    (3, 7699, "Abbas Afridi", 88.32),
    (4, 4856, "Benjamin Sears", 86.06),
    (5, 6097, "Brydon Carse", 84.21),
    (6, 8009, "Junaid Siddique", 84.01),
    (7, 27504, "Dushan Hemantha", 82.58),
    (8, 5809, "Naveen ul Haq", 81.10),
    (9, 4779, "Pieter Willem Mulder", 77.44),
    (10, 4499, "Saqib Mahmood", 77.29),
]

# Known incorrect substitution pairings that must NEVER appear
INVALID_SUBSTITUTIONS = [
    ("Nicholas Pooran", 92.25),
    ("Tristan Stubbs", 91.43),
    ("Heinrich Klaasen", 90.45),
    ("Jasprit Bumrah", 88.39),
    ("Sunil Narine", 88.32),
    ("Rashid Khan", 86.06),
]


def test_top_batters_csv_ground_truth():
    """Verify outputs/top_10_batters.csv matches expected ground truth exactly."""
    df = pd.read_csv(OUTPUTS_DIR / "top_10_batters.csv")
    assert len(df) == 10, f"Expected 10 rows, got {len(df)}"
    for rank, p_id, name, score in EXPECTED_BATTERS:
        row = df[df["rank"] == rank]
        assert len(row) == 1, f"Rank {rank} missing"
        assert int(row.iloc[0]["player_id"]) == p_id, f"Rank {rank} ID mismatch"
        assert row.iloc[0]["player_name"] == name, f"Rank {rank} Name mismatch"
        assert abs(float(row.iloc[0]["reliability_score"]) - score) < 1e-2, f"Rank {rank} Score mismatch"


def test_top_bowlers_csv_ground_truth():
    """Verify outputs/top_10_bowlers.csv matches expected ground truth exactly."""
    df = pd.read_csv(OUTPUTS_DIR / "top_10_bowlers.csv")
    assert len(df) == 10, f"Expected 10 rows, got {len(df)}"
    for rank, p_id, name, score in EXPECTED_BOWLERS:
        row = df[df["rank"] == rank]
        assert len(row) == 1, f"Rank {rank} missing"
        assert int(row.iloc[0]["player_id"]) == p_id, f"Rank {rank} ID mismatch"
        assert row.iloc[0]["player_name"] == name, f"Rank {rank} Name mismatch"
        assert abs(float(row.iloc[0]["reliability_score"]) - score) < 1e-2, f"Rank {rank} Score mismatch"


def test_player_mapping_integrity():
    """Verify that player IDs in rankings map to their actual legal names in relational mapping."""
    map_df = pd.read_parquet(DATA_PROC / "competition_team_player_mapping.parquet")
    
    for _, p_id, expected_name, _ in EXPECTED_BATTERS + EXPECTED_BOWLERS:
        names = map_df[map_df["player_id"] == p_id]["player_name"].unique()
        assert len(names) > 0, f"Player ID {p_id} not found in player mapping table"
        assert expected_name in names, f"Player ID {p_id} mapped to {names}, expected '{expected_name}'"


def test_methodology_markdown_player_consistency():
    """Verify that methodology_report.md contains all 20 correct names and NO invalid substitutions."""
    md_path = SUBMISSION_DIR / "methodology_report.md"
    assert md_path.exists(), "submission/methodology_report.md missing"
    text = md_path.read_text(encoding="utf-8")
    
    # 1. All 20 correct players must appear
    for _, p_id, name, _ in EXPECTED_BATTERS + EXPECTED_BOWLERS:
        assert name in text, f"Player '{name}' missing from methodology_report.md"
        assert str(p_id) in text, f"Player ID {p_id} ({name}) missing from methodology_report.md"
    
    # 2. None of the invalid celebrity substitutions may appear associated with top scores
    for name, score in INVALID_SUBSTITUTIONS:
        # Check that e.g. "Nicholas Pooran (Rank 2, Score: 92.25)" is NOT present
        pattern_check = f"{name} (Rank"
        assert pattern_check not in text, f"Found invalid rank attribution for {name} in methodology_report.md"
        # Check that score is not attributed to the wrong name
        score_str = f"{score:.2f}"
        assert f"{name} (Rank 2, Score: {score_str})" not in text
        assert f"{name} (Rank 3, Score: {score_str})" not in text
        assert f"{name} (Rank 4, Score: {score_str})" not in text


def test_submission_selections_markdown_consistency():
    """Verify submission_selections.md lists the exact 20 players in exact rank order."""
    sel_path = SUBMISSION_DIR / "submission_selections.md"
    assert sel_path.exists(), "submission/submission_selections.md missing"
    text = sel_path.read_text(encoding="utf-8")
    
    for rank, p_id, name, score in EXPECTED_BATTERS:
        expected_line = f"Rank {rank}: {name} — {p_id} (Reliability Score: {score:.2f})"
        assert expected_line in text, f"Missing or mismatched line in submission_selections.md: '{expected_line}'"

    for rank, p_id, name, score in EXPECTED_BOWLERS:
        expected_line = f"Rank {rank}: {name} — {p_id} (Reliability Score: {score:.2f})"
        assert expected_line in text, f"Missing or mismatched line in submission_selections.md: '{expected_line}'"


def test_methodology_pdf_player_consistency():
    """Verify that methodology_report.pdf contains all 20 correct names and no swapped identities."""
    pdf_path = SUBMISSION_DIR / "methodology_report.pdf"
    assert pdf_path.exists(), "submission/methodology_report.pdf missing"
    
    doc = fitz.open(str(pdf_path))
    full_pdf_text = ""
    for page in doc:
        full_pdf_text += page.get_text()
    
    # All 20 players must appear in PDF text
    for _, _, name, _ in EXPECTED_BATTERS + EXPECTED_BOWLERS:
        assert name in full_pdf_text, f"Player '{name}' not found in methodology_report.pdf text"
    
    # Check that invalid substitution pairings are NOT in the PDF
    for name, score in INVALID_SUBSTITUTIONS:
        assert f"{name} ({score:.2f})" not in full_pdf_text, f"Invalid pairing {name} ({score:.2f}) found in PDF"


def test_cricket_rules_explanation_accuracy():
    """Verify that documentation correctly states that no-balls and wides do NOT consume legal balls."""
    md_text = (SUBMISSION_DIR / "methodology_report.md").read_text(encoding="utf-8")
    
    # Verify accurate explanation is present
    assert "Neither wides nor no-balls consume legal deliveries" in md_text, \
        "methodology_report.md missing accurate rule explanation"
    
    # Verify incorrect statement is absent
    assert "No-balls consume legal balls for the team and batter" not in md_text, \
        "methodology_report.md still contains incorrect statement that no-balls consume legal balls"


def test_reject_wrong_player_score_assignment():
    """Explicitly verify that a validation function fails when a wrong name is paired with a valid score."""
    def validate_pairing(claimed_name: str, score: float, role: str) -> bool:
        expected_list = EXPECTED_BATTERS if role == "batting" else EXPECTED_BOWLERS
        for _, _, exp_name, exp_score in expected_list:
            if abs(score - exp_score) < 1e-2:
                return claimed_name == exp_name
        return False

    # Positive test
    assert validate_pairing("Towhid Hridoy", 92.25, "batting") is True
    assert validate_pairing("Muhammad Khan", 88.39, "bowling") is True

    # Negative test: Same score assigned to famous star MUST FAIL
    assert validate_pairing("Nicholas Pooran", 92.25, "batting") is False
    assert validate_pairing("Jasprit Bumrah", 88.39, "bowling") is False
    assert validate_pairing("Sunil Narine", 88.32, "bowling") is False
    assert validate_pairing("Rashid Khan", 86.06, "bowling") is False
