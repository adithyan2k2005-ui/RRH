"""Phase 6 Automated Submission Integrity and Verification Tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pymupdf
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = PROJECT_ROOT / "submission"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def test_submission_files_exist():
    """Verifies that all required final submission deliverables exist."""
    required = [
        SUBMISSION_DIR / "methodology_report.pdf",
        SUBMISSION_DIR / "methodology_report.md",
        SUBMISSION_DIR / "top_10_batters.csv",
        SUBMISSION_DIR / "top_10_bowlers.csv",
        SUBMISSION_DIR / "submission_selections.md",
        SUBMISSION_DIR / "submission_validation.md",
        SUBMISSION_DIR / "evidence_manifest.md",
        SUBMISSION_DIR / "superr_selector_round1_submission.zip",
    ]
    for path in required:
        assert path.exists(), f"Required submission file missing: {path}"
        assert path.stat().st_size > 0, f"File is empty: {path}"


def test_pdf_document_integrity_and_pages():
    """Verifies that the PDF opens, has expected page count and non-empty pages."""
    pdf_path = SUBMISSION_DIR / "methodology_report.pdf"
    doc = pymupdf.open(str(pdf_path))

    assert len(doc) >= 6, f"Expected comprehensive PDF, found {len(doc)} pages"
    for i, page in enumerate(doc):
        text = page.get_text()
        assert len(text.strip()) > 100, f"Page {i+1} has insufficient text content"

    doc.close()


def test_pdf_contains_all_20_players_and_17_sections():
    """Verifies that all 20 selected players and all 17 numbered sections are present in the PDF."""
    pdf_path = SUBMISSION_DIR / "methodology_report.pdf"
    doc = pymupdf.open(str(pdf_path))
    normalized_text = " ".join(" ".join(page.get_text().split()) for page in doc)
    doc.close()

    # Batters
    batters = [
        "Vipraj Nigam", "Towhid Hridoy", "Matthew Wade", "Ibrahim Zadran",
        "Ravindra Jadeja", "David Willey", "Sikandar Raza", "Rinku Singh",
        "Namboori Tilak Varma", "Joshua Clarkson",
    ]
    for name in batters:
        assert name in normalized_text, f"Selected batter {name} missing from PDF text"

    # Bowlers
    bowlers = [
        "Manimaran Siddharth", "Muhammad Khan", "Abbas Afridi", "Benjamin Sears",
        "Brydon Carse", "Junaid Siddique", "Dushan Hemantha", "Naveen ul Haq",
        "Pieter Willem Mulder", "Saqib Mahmood",
    ]
    for name in bowlers:
        assert name in normalized_text, f"Selected bowler {name} missing from PDF text"

    # Sections 1 to 17
    for s in range(1, 18):
        assert f"{s}." in normalized_text, f"Methodology Section {s} missing from PDF"


def test_cross_file_ranking_consistency():
    """Verifies byte-level and semantic consistency between outputs and submission files."""
    out_bat = pd.read_csv(OUTPUTS_DIR / "top_10_batters.csv")
    sub_bat = pd.read_csv(SUBMISSION_DIR / "top_10_batters.csv")
    pd.testing.assert_frame_equal(out_bat, sub_bat)

    out_bowl = pd.read_csv(OUTPUTS_DIR / "top_10_bowlers.csv")
    sub_bowl = pd.read_csv(SUBMISSION_DIR / "top_10_bowlers.csv")
    pd.testing.assert_frame_equal(out_bowl, sub_bowl)

    # Check rank order and score monotonicity
    assert list(sub_bat["rank"]) == list(range(1, 11))
    assert list(sub_bowl["rank"]) == list(range(1, 11))
    assert (sub_bat["reliability_score"].diff().dropna() <= 0).all()
    assert (sub_bowl["reliability_score"].diff().dropna() <= 0).all()


def test_submission_zip_archive_validity():
    """Verifies that the submission ZIP archive is valid and contains required entries."""
    zip_path = SUBMISSION_DIR / "superr_selector_round1_submission.zip"
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        expected = [
            "methodology_report.pdf",
            "methodology_report.md",
            "top_10_batters.csv",
            "top_10_bowlers.csv",
            "submission_selections.md",
            "submission_validation.md",
            "evidence_manifest.md",
        ]
        for name in expected:
            assert name in namelist, f"Archive missing expected entry: {name}"

