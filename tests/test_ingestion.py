"""Ingestion and loading tests for SupeRR Selector Analytics."""

from __future__ import annotations

import io
from pathlib import Path
import sys
import tempfile
import zipfile

import pandas as pd
import pytest

# Derive project root and insert into sys.path before package imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.load_data import (
    EXPECTED_CSV_FILES,
    extract_raw_dataset,
    find_hackathon_zip,
    inspect_zip_contents,
    load_all_datasets,
    load_csv,
)


class TestIngestionPipeline:
    """Pipeline correctness tests for data ingestion."""

    def test_find_hackathon_zip_finds_valid_archive(self):
        """Verify find_hackathon_zip locates the archive containing expected CSVs."""
        zip_path = find_hackathon_zip([PROJECT_ROOT, PROJECT_ROOT.parent])
        assert zip_path.exists()
        assert zip_path.suffix.lower() == ".zip"

    def test_inspect_zip_contents_filters_system_files(self):
        """Verify inspect_zip_contents ignores __MACOSX and .DS_Store."""
        zip_path = find_hackathon_zip([PROJECT_ROOT, PROJECT_ROOT.parent])
        contents = inspect_zip_contents(zip_path)

        for filename in contents:
            assert not filename.startswith("__MACOSX")
            assert not filename.endswith("/")
            assert ".DS_Store" not in filename
            assert not Path(filename).name.startswith("._")

        base_names = {entry["basename"] for entry in contents.values()}
        assert EXPECTED_CSV_FILES.issubset(base_names)

    def test_extract_prevents_zip_traversal(self):
        """Verify extract_raw_dataset blocks zip slip attacks attempting directory traversal."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            malicious_zip = tmp_path / "malicious.zip"
            target_out = tmp_path / "extracted"

            # Create a zip with an entry trying to traverse upwards
            with zipfile.ZipFile(malicious_zip, "w") as zf:
                zf.writestr("../../evil.txt", "malicious payload")
                for expected in EXPECTED_CSV_FILES:
                    zf.writestr(expected, "col1,col2\n1,2\n")

            with pytest.raises(ValueError, match="Attempted zip path traversal"):
                extract_raw_dataset(malicious_zip, target_out)

    def test_load_csv_missing_file_raises_error(self):
        """Verify load_csv raises FileNotFoundError when given non-existent path."""
        non_existent = PROJECT_ROOT / "data" / "raw" / "non_existent_dataset.csv"
        with pytest.raises(FileNotFoundError):
            load_csv(non_existent)

    def test_load_all_datasets_preserves_row_counts(self):
        """Verify all six datasets load with complete record counts."""
        raw_dir = PROJECT_ROOT / "data" / "raw"
        datasets = load_all_datasets(raw_dir)

        assert set(datasets.keys()) == {
            "competitions",
            "teams",
            "matches",
            "ball_by_ball",
            "competition_team_player_mapping",
            "playing_eleven",
        }

        # Exact expected raw counts verified from dataset
        assert len(datasets["competitions"]) == 141
        assert len(datasets["teams"]) == 353
        assert len(datasets["matches"]) == 883
        assert len(datasets["ball_by_ball"]) == 200999
        assert len(datasets["competition_team_player_mapping"]) == 6413
        assert len(datasets["playing_eleven"]) == 28381

    def test_raw_files_unmodified_preservation(self):
        """Verify raw CSV files exist and have non-zero size."""
        raw_dir = PROJECT_ROOT / "data" / "raw"
        for fname in EXPECTED_CSV_FILES:
            fpath = raw_dir / fname
            assert fpath.exists(), f"Raw file {fname} is missing"
            assert fpath.stat().st_size > 0, f"Raw file {fname} is empty"
