#!/usr/bin/env python3
"""Phase 3 Pipeline Execution Script for SupeRR Selector Analytics.

Executes the complete Phase 3 workflow:
1. Load validated Phase 2 match_states.parquet
2. Fit contextual baselines across formats and phases
3. Compute normalized pre-delivery pressure components
4. Calculate batting, bowling, and match tension scores (0-100)
5. Classify pressure regimes (LOW, MEDIUM, HIGH)
6. Execute comprehensive validation and leakage audits
7. Save output dataset to data/processed/pressure_states.parquet
8. Generate Phase 3 methodology, validation, sensitivity, and scenario reports

Usage:
    python scripts/run_phase3.py
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

from src.features.pressure_baselines import ContextualBaselines
from src.features.pressure_features import calculate_pressure_features
from src.features.pressure_model import compute_pressure_scores
from src.features.pressure_thresholds import classify_pressure
from src.validation.validate_pressure import (
    generate_phase3_reports,
    generate_pressure_audit_examples,
    validate_pressure_scores,
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


def run_phase3_pipeline(project_root: Path = PROJECT_ROOT) -> int:
    """Orchestrates Phase 3 pressure modeling.

    Args:
        project_root: Path to superr-selector-analytics directory.

    Returns:
        int: 0 on success, non-zero on failure.
    """
    start_time = time.time()
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports" / "phase3"
    log_file = reports_dir / "phase3_execution.log"

    setup_logging(log_file)
    logger = logging.getLogger("run_phase3")
    logger.info("=== STARTING SUPERR SELECTOR SEASON 2 - PHASE 3 PIPELINE ===")
    logger.info("Project Root: %s", project_root)

    try:
        # Step 1: Load Phase 2 Match States
        logger.info("--- Step 1: Loading Phase 2 Match States ---")
        states_path = processed_dir / "match_states.parquet"
        if not states_path.exists():
            raise FileNotFoundError(
                f"Required Phase 2 dataset missing: {states_path}. "
                f"Please run `python scripts/run_phase2.py` first."
            )

        states_df = pd.read_parquet(states_path)
        logger.info("Loaded match_states: %d rows, %d cols", len(states_df), len(states_df.columns))

        # Step 2: Fit Contextual Baselines
        logger.info("--- Step 2: Fitting Contextual Baselines ---")
        baselines = ContextualBaselines.fit_from_data(states_df)

        # Step 3: Compute Normalized Pressure Components
        logger.info("--- Step 3: Extracting Pressure Factors ---")
        components_df = calculate_pressure_features(states_df, baselines)

        # Step 4: Calculate Pressure Scores
        logger.info("--- Step 4: Calculating Multi-Dimensional Pressure Scores ---")
        scores_df = compute_pressure_scores(states_df, components_df)

        # Step 5: Classify Pressure Regimes
        logger.info("--- Step 5: Classifying Pressure Regimes ---")
        bat_class = classify_pressure(scores_df["batting_pressure_score"], states_df["is_pressure_ready"])
        bowl_class = classify_pressure(scores_df["bowling_pressure_score"], states_df["is_pressure_ready"])

        # Step 6: Assemble Complete Pressure States Dataset
        logger.info("--- Step 6: Assembling Final Pressure Dataset ---")
        augmented_df = pd.concat([
            states_df,
            components_df,
            scores_df,
            pd.DataFrame({
                "batting_pressure_class": bat_class,
                "bowling_pressure_class": bowl_class,
            }, index=states_df.index)
        ], axis=1)

        # Step 7: Validate Output & Leakage Checks
        logger.info("--- Step 7: Validating Pressure Scores & Bounds ---")
        metrics = validate_pressure_scores(augmented_df)

        if metrics["out_of_bounds_count"] > 0:
            raise ValueError(f"Detected {metrics['out_of_bounds_count']} out-of-bounds pressure scores!")

        # Step 8: Save Parquet Output
        logger.info("--- Step 8: Exporting pressure_states.parquet ---")
        output_parquet = processed_dir / "pressure_states.parquet"
        augmented_df.to_parquet(output_parquet, engine="pyarrow", index=False)
        logger.info(
            "Saved pressure_states.parquet: %d rows, %d cols (%d bytes)",
            len(augmented_df),
            len(augmented_df.columns),
            output_parquet.stat().st_size,
        )

        # Step 9: Generate Reports and Audit Artifacts
        logger.info("--- Step 9: Generating Phase 3 Reports and Tables ---")
        meth_path = reports_dir / "pressure_methodology.md"
        val_path = reports_dir / "pressure_validation.md"
        dist_path = reports_dir / "pressure_distribution.csv"
        sens_path = reports_dir / "pressure_sensitivity.csv"
        generate_phase3_reports(augmented_df, metrics, meth_path, val_path, dist_path, sens_path)

        ex_path = reports_dir / "pressure_examples.csv"
        generate_pressure_audit_examples(augmented_df, ex_path)

        elapsed = time.time() - start_time
        logger.info("=== PHASE 3 PIPELINE COMPLETED SUCCESSFULLY IN %.2f SECONDS ===", elapsed)
        return 0

    except Exception as err:
        logger.exception("CRITICAL ERROR during Phase 3 pipeline execution: %s", err)
        return 1


if __name__ == "__main__":
    exit_code = run_phase3_pipeline()
    sys.exit(exit_code)

