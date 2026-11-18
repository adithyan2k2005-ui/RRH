#!/usr/bin/env python3
"""Phase 1 Pipeline Execution Script for SupeRR Selector Analytics.

Executes the complete Phase 1 workflow:
1. Data extraction & loading from hackathon zip archive
2. Comprehensive schema inspection
3. Relational integrity & cricket domain semantic validation
4. Data type standardization and clean Parquet export
5. Generation of the Phase 1 Data Quality Report

Usage:
    python scripts/run_phase1.py
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.load_data import (
    extract_raw_dataset,
    find_hackathon_zip,
    inspect_zip_contents,
    load_all_datasets,
)
from src.validation.validate_data import (
    generate_data_quality_report,
    inspect_schemas,
    standardize_and_export_parquet,
    validate_cricket_semantics,
    validate_relationships,
)


def setup_logging(log_file: Path) -> None:
    """Configures console and file logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
    )


def run_phase1_pipeline(
    project_root: Path = PROJECT_ROOT,
    zip_path: Path | None = None,
) -> int:
    """Orchestrates Phase 1 data ingestion, validation, and export.

    Args:
        project_root: Path to the superr-selector-analytics directory.
        zip_path: Optional explicit path to the hackathon zip file.

    Returns:
        int: 0 on success, non-zero on critical failure.
    """
    start_time = time.time()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports" / "phase1"
    log_file = reports_dir / "phase1_execution.log"

    setup_logging(log_file)
    logger = logging.getLogger("run_phase1")
    logger.info("=== STARTING SUPERR SELECTOR SEASON 2 - PHASE 1 PIPELINE ===")
    logger.info("Project Root: %s", project_root)

    try:
        # Step 1: Locate Archive
        logger.info("--- Step 1: Locating and Inspecting Dataset Archive ---")
        if zip_path is None:
            zip_path = find_hackathon_zip([project_root, project_root.parent])
        logger.info("Using hackathon archive: %s", zip_path)

        zip_info = inspect_zip_contents(zip_path)
        logger.info("Archive contains %d valid dataset entries.", len(zip_info))

        # Step 2: Safe Extraction
        logger.info("--- Step 2: Extracting Raw Datasets Safely ---")
        extracted_paths = extract_raw_dataset(zip_path, raw_dir)
        logger.info("Extracted %d CSV files to %s", len(extracted_paths), raw_dir)

        # Step 3: Load Datasets
        logger.info("--- Step 3: Loading Datasets into Memory ---")
        datasets = load_all_datasets(raw_dir)
        for name, df in datasets.items():
            logger.info("Loaded '%s': %d rows, %d columns", name, len(df), len(df.columns))

        # Step 4: Schema Inspection
        logger.info("--- Step 4: Inspecting Schemas & Candidate Keys ---")
        schemas = inspect_schemas(datasets)

        # Step 5: Relational Integrity Validation
        logger.info("--- Step 5: Validating Cross-Dataset Relationships ---")
        relationships = validate_relationships(datasets)

        # Step 6: Cricket Domain Semantics Validation
        logger.info("--- Step 6: Validating Cricket Domain Semantics ---")
        semantics = validate_cricket_semantics(datasets)

        # Step 7: Parquet Standardization and Export
        logger.info("--- Step 7: Standardizing Types and Exporting Parquet ---")
        parquet_files = standardize_and_export_parquet(datasets, processed_dir)
        for name, p_path in parquet_files.items():
            logger.info("Parquet ready: %s (%d bytes)", p_path.name, p_path.stat().st_size)

        # Step 8: Quality Report Generation
        logger.info("--- Step 8: Generating Official Data Quality Report ---")
        report_path = reports_dir / "data_quality_report.md"
        generate_data_quality_report(schemas, relationships, semantics, report_path)
        logger.info("Data Quality Report generated at: %s", report_path)

        elapsed = time.time() - start_time
        logger.info("=== PHASE 1 PIPELINE COMPLETED SUCCESSFULLY IN %.2f SECONDS ===", elapsed)
        return 0

    except Exception as err:
        logger.exception("CRITICAL ERROR during Phase 1 pipeline execution: %s", err)
        return 1


if __name__ == "__main__":
    exit_code = run_phase1_pipeline()
    sys.exit(exit_code)

