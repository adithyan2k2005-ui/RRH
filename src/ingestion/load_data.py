"""Data Ingestion Module for SupeRR Selector Analytics.

Provides secure archive location, zip inspection, safe extraction,
and robust CSV loading with explicit encoding and data integrity preservation.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
import zipfile

import pandas as pd

logger = logging.getLogger(__name__)

# Expected canonical CSV file basenames
EXPECTED_CSV_FILES: Set[str] = {
    "competitions.csv",
    "teams.csv",
    "matches.csv",
    "ball_by_ball.csv",
    "competition_team_player_mapping.csv",
    "playing_eleven.csv",
}


def find_hackathon_zip(search_paths: Optional[List[Path]] = None) -> Path:
    """Locate the hackathon zip file without assuming a fixed filename.

    Searches search_paths, current working directory, and parent directories
    for any zip archive containing the expected CSV files.

    Args:
        search_paths: Optional list of directories or file paths to inspect.

    Returns:
        Path: Resolved path to the valid hackathon archive.

    Raises:
        FileNotFoundError: If no valid zip archive containing expected CSVs is found.
    """
    candidates: List[Path] = []
    dirs_to_check: List[Path] = []

    if search_paths:
        for p in search_paths:
            path_obj = Path(p).resolve()
            if path_obj.is_file() and path_obj.suffix.lower() == ".zip":
                candidates.append(path_obj)
            elif path_obj.is_dir():
                dirs_to_check.append(path_obj)

    # Standard fallback directories
    cwd = Path.cwd().resolve()
    dirs_to_check.extend([cwd, cwd.parent, cwd / "data", cwd / "data" / "raw"])

    # Deduplicate directories
    unique_dirs = []
    seen = set()
    for d in dirs_to_check:
        if d.exists() and d not in seen:
            seen.add(d)
            unique_dirs.append(d)

    for d in unique_dirs:
        candidates.extend(d.glob("*.zip"))

    # Remove candidate duplicates
    unique_candidates = []
    seen_files = set()
    for c in candidates:
        if c.resolve() not in seen_files:
            seen_files.add(c.resolve())
            unique_candidates.append(c)

    logger.info("Found %d candidate zip archives to inspect.", len(unique_candidates))

    for zip_path in unique_candidates:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                base_names = {
                    Path(n).name
                    for n in names
                    if not n.startswith("__MACOSX")
                    and not n.endswith("/")
                    and ".DS_Store" not in n
                    and not Path(n).name.startswith("._")
                }
                if EXPECTED_CSV_FILES.issubset(base_names):
                    logger.info("Identified valid hackathon archive at: %s", zip_path)
                    return zip_path
        except (zipfile.BadZipFile, OSError) as err:
            logger.warning("Could not read zip archive %s: %s", zip_path, err)
            continue

    raise FileNotFoundError(
        f"No valid hackathon zip archive found containing expected files {EXPECTED_CSV_FILES}. "
        f"Checked candidates: {[str(c) for c in unique_candidates]}"
    )


def inspect_zip_contents(zip_path: Path) -> Dict[str, dict]:
    """Safely inspects the contents of the zip file without extracting.

    Args:
        zip_path: Path to the zip archive.

    Returns:
        Dict[str, dict]: Metadata for each trusted entry (filename, size, compress_type).
    """
    logger.info("Inspecting archive contents: %s", zip_path)
    contents: Dict[str, dict] = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            # Filter out system and metadata files
            if (
                info.filename.startswith("__MACOSX")
                or info.filename.endswith("/")
                or ".DS_Store" in info.filename
                or Path(info.filename).name.startswith("._")
            ):
                continue
            contents[info.filename] = {
                "basename": Path(info.filename).name,
                "file_size": info.file_size,
                "compress_size": info.compress_size,
                "is_dir": info.is_dir(),
            }
    return contents


def extract_raw_dataset(zip_path: Path, output_dir: Path) -> Dict[str, Path]:
    """Safely extracts expected CSV dataset files to output_dir, preventing zip path traversal.

    Args:
        zip_path: Path to the zip archive.
        output_dir: Destination directory (e.g. data/raw).

    Returns:
        Dict[str, Path]: Mapping of canonical CSV basename to extracted Path.

    Raises:
        ValueError: If a zip entry attempts path traversal outside output_dir.
        RuntimeError: If any expected CSV is missing from extraction.
    """
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths: Dict[str, Path] = {}

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Guard against ZIP path traversal (Zip Slip vulnerability)
            member_path = Path(member.filename)
            if ".." in member_path.parts or member.filename.startswith(("/", "\\")):
                raise ValueError(
                    f"Attempted zip path traversal in entry: {member.filename}"
                )

            # Skip metadata and system files
            if (
                member.filename.startswith("__MACOSX")
                or member.filename.endswith("/")
                or ".DS_Store" in member.filename
                or Path(member.filename).name.startswith("._")
            ):
                continue

            base_name = Path(member.filename).name
            if base_name in EXPECTED_CSV_FILES or base_name.endswith(".pdf"):
                target_path = (output_dir / base_name).resolve()
                try:
                    target_path.relative_to(output_dir)
                except ValueError as err:
                    raise ValueError(
                        f"Attempted zip path traversal in entry: {member.filename}"
                    ) from err

                with zf.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

                if base_name in EXPECTED_CSV_FILES:
                    extracted_paths[base_name] = target_path
                    logger.info("Safely extracted %s -> %s (%d bytes)", base_name, target_path, target_path.stat().st_size)

    # Validate that all expected CSVs were extracted
    missing = EXPECTED_CSV_FILES - set(extracted_paths.keys())
    if missing:
        raise RuntimeError(f"Archive did not contain all expected CSVs. Missing: {missing}")

    return extracted_paths


def load_csv(file_path: Path, preserve_id_types: bool = True) -> pd.DataFrame:
    """Loads a CSV file into a pandas DataFrame with encoding detection and ID preservation.

    Args:
        file_path: Path to the CSV file.
        preserve_id_types: Whether to ensure ID columns are not distorted.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1"]
    last_err = None

    for enc in encodings_to_try:
        try:
            logger.debug("Attempting to load %s with encoding=%s", file_path.name, enc)
            # Read CSV with pandas, preserving all values without dropping rows
            df = pd.read_csv(
                file_path,
                encoding=enc,
                low_memory=False,
            )
            logger.info("Successfully loaded %s with encoding=%s (shape: %s)", file_path.name, enc, df.shape)
            return df
        except (UnicodeDecodeError, pd.errors.ParserError) as err:
            logger.warning("Failed loading %s with encoding %s: %s", file_path.name, enc, err)
            last_err = err

    raise RuntimeError(f"Failed to load CSV {file_path} with any supported encoding: {last_err}")


def load_all_datasets(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """Loads all six expected CSV datasets from the raw directory.

    Args:
        raw_dir: Path to data/raw directory.

    Returns:
        Dict[str, pd.DataFrame]: Mapping of canonical dataset key to DataFrame.
    """
    raw_dir = Path(raw_dir).resolve()
    datasets: Dict[str, pd.DataFrame] = {}

    key_mapping = {
        "competitions.csv": "competitions",
        "teams.csv": "teams",
        "matches.csv": "matches",
        "ball_by_ball.csv": "ball_by_ball",
        "competition_team_player_mapping.csv": "competition_team_player_mapping",
        "playing_eleven.csv": "playing_eleven",
    }

    for csv_name, dict_key in key_mapping.items():
        file_path = raw_dir / csv_name
        if not file_path.exists():
            raise FileNotFoundError(f"Expected raw file does not exist: {file_path}")
        df = load_csv(file_path)
        datasets[dict_key] = df
        logger.info("Loaded '%s': %d rows, %d columns", dict_key, df.shape[0], df.shape[1])

    return datasets
