#!/usr/bin/env python3
"""Phase 2 Pipeline Execution Script for SupeRR Selector Analytics.

Executes the complete Phase 2 workflow:
1. Load validated Phase 1 processed Parquet datasets
2. Reconstruct chronological delivery ordering
3. Classify legal deliveries, granular runs, and dismissals
4. Build innings context and chase targets
5. Reconstruct pre-delivery match states with zero future data leakage
6. Execute comprehensive validation and reconciliation audits
7. Save output dataset to data/processed/match_states.parquet
8. Generate Phase 2 summary and validation reports

Usage:
    python scripts/run_phase2.py
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

import pandas as pd

from src.features.match_state import reconstruct_match_states
from src.validation.validate_match_state import (
    generate_phase2_reports,
    generate_unresolved_cases_csv,
    validate_reconstructed_states,
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


def run_phase2_pipeline(project_root: Path = PROJECT_ROOT) -> int:
    """Orchestrates Phase 2 match state reconstruction.

    Args:
        project_root: Path to superr-selector-analytics directory.

    Returns:
        int: 0 on success, non-zero on failure.
    """
    start_time = time.time()
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports" / "phase2"
    log_file = reports_dir / "phase2_execution.log"

    setup_logging(log_file)
    logger = logging.getLogger("run_phase2")
    logger.info("=== STARTING SUPERR SELECTOR SEASON 2 - PHASE 2 PIPELINE ===")
    logger.info("Project Root: %s", project_root)

    try:
        # Step 1: Load Validated Phase 1 Datasets
        logger.info("--- Step 1: Loading Phase 1 Parquet Datasets ---")
        bbb_path = processed_dir / "ball_by_ball.parquet"
        matches_path = processed_dir / "matches.parquet"
        comps_path = processed_dir / "competitions.parquet"

        for p in [bbb_path, matches_path, comps_path]:
            if not p.exists():
                raise FileNotFoundError(
                    f"Required Phase 1 processed dataset missing: {p}. "
                    f"Please run `python scripts/run_phase1.py` first."
                )

        bbb_df = pd.read_parquet(bbb_path)
        matches_df = pd.read_parquet(matches_path)
        comps_df = pd.read_parquet(comps_path)

        logger.info("Loaded ball_by_ball: %d rows, %d cols", len(bbb_df), len(bbb_df.columns))
        logger.info("Loaded matches: %d rows, %d cols", len(matches_df), len(matches_df.columns))
        logger.info("Loaded competitions: %d rows, %d cols", len(comps_df), len(comps_df.columns))

        # Step 2: Reconstruct Pre-Delivery Match States
        logger.info("--- Step 2: Executing Match State Reconstruction ---")
        states_df = reconstruct_match_states(bbb_df, matches_df, comps_df)

        # Step 3: Validate Reconstructed States and Audit Leakage
        logger.info("--- Step 3: Validating Reconstructed States & Auditing Leakage ---")
        metrics = validate_reconstructed_states(states_df, matches_df)

        # Check for critical leakage violations
        if metrics["leakage_score_violations"] > 0 or metrics["leakage_wickets_violations"] > 0:
            raise RuntimeError(
                f"CRITICAL LEAKAGE FAILURE: Detected {metrics['leakage_score_violations']} score "
                f"and {metrics['leakage_wickets_violations']} wicket leakage violations!"
            )

        # Step 4: Export Standardized Parquet Dataset
        logger.info("--- Step 4: Exporting match_states.parquet ---")
        output_parquet = processed_dir / "match_states.parquet"
        states_df.to_parquet(output_parquet, engine="pyarrow", index=False)
        logger.info(
            "Saved match_states.parquet: %d rows, %d cols (%d bytes)",
            len(states_df),
            len(states_df.columns),
            output_parquet.stat().st_size,
        )

        # Step 5: Generate Phase 2 Reports and Artifacts
        logger.info("--- Step 5: Generating Phase 2 Reports ---")
        summary_path = reports_dir / "reconstruction_summary.md"
        validation_path = reports_dir / "reconstruction_validation.md"
        generate_phase2_reports(states_df, matches_df, metrics, summary_path, validation_path)

        unresolved_path = reports_dir / "unresolved_cases.csv"
        generate_unresolved_cases_csv(states_df, matches_df, unresolved_path)

        elapsed = time.time() - start_time
        logger.info("=== PHASE 2 PIPELINE COMPLETED SUCCESSFULLY IN %.2f SECONDS ===", elapsed)
        return 0

    except Exception as err:
        logger.exception("CRITICAL ERROR during Phase 2 pipeline execution: %s", err)
        return 1


if __name__ == "__main__":
    exit_code = run_phase2_pipeline()
    sys.exit(exit_code)

