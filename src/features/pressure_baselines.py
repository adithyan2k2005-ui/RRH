"""Contextual Baseline Estimation Module for SupeRR Selector Analytics.

Computes historical expected scoring rates across match formats, innings phases,
and wicket conditions using causal historical aggregation with hierarchical fallbacks.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Default global T20 scoring benchmarks (runs per over)
GLOBAL_DEFAULT_RUN_RATE = 8.86
GLOBAL_PHASE_BENCHMARKS: Dict[str, float] = {
    "Powerplay": 8.68,
    "Middle": 8.34,
    "Death": 10.24,
    "SuperOver": 9.82,
}
GLOBAL_FORMAT_BENCHMARKS: Dict[str, float] = {
    "T20I": 8.55,
    "T20": 9.21,
}


class ContextualBaselines:
    """Computes and serves contextual scoring baselines with hierarchical smoothing."""

    def __init__(self, baseline_table: pd.DataFrame | None = None):
        """Initializes baseline lookup table.

        Args:
            baseline_table: Optional precomputed baseline DataFrame.
        """
        self.baseline_table = baseline_table

    @classmethod
    def fit_from_data(cls, states_df: pd.DataFrame) -> ContextualBaselines:
        """Computes empirical baseline scoring rates across format and phase.

        Uses only legal balls and completed team runs. Excludes future information.

        Args:
            states_df: Reconstructed match states DataFrame.

        Returns:
            ContextualBaselines: Fitted baseline instance.
        """
        logger.info("Fitting contextual scoring baselines on %d deliveries.", len(states_df))

        # Filter to legal balls
        legal_df = states_df[states_df["is_legal_ball"]].copy()

        # Group by format and bowling_innings_phase
        grouped = legal_df.groupby(["match_format", "bowling_innings_phase"]).agg(
            total_runs=("team_runs_on_ball", "sum"),
            total_balls=("is_legal_ball", "sum"),
        ).reset_index()

        grouped["expected_run_rate"] = (
            grouped["total_runs"] / (grouped["total_balls"] / 6.0)
        ).round(2)
        grouped["support_balls"] = grouped["total_balls"]

        logger.info(
            "Computed %d format-phase baseline benchmarks. Support range: %d to %d balls.",
            len(grouped),
            int(grouped["support_balls"].min()),
            int(grouped["support_balls"].max()),
        )
        return cls(baseline_table=grouped)

    def get_baseline_run_rate(
        self,
        match_format: str,
        phase: str,
    ) -> Tuple[float, int]:
        """Looks up baseline expected run rate with hierarchical fallback.

        Hierarchy:
        Level 1: (match_format, phase)
        Level 2: phase global benchmark
        Level 3: global overall benchmark

        Args:
            match_format: 'T20I' or 'T20'.
            phase: 'Powerplay', 'Middle', 'Death', or 'SuperOver'.

        Returns:
            Tuple[float, int]: Expected run rate in rpo and supporting ball count.
        """
        if self.baseline_table is not None:
            match = self.baseline_table[
                (self.baseline_table["match_format"] == match_format)
                & (self.baseline_table["bowling_innings_phase"] == phase)
            ]
            if len(match) > 0:
                row = match.iloc[0]
                return float(row["expected_run_rate"]), int(row["support_balls"])

        # Fallback Level 2: Phase benchmark
        if phase in GLOBAL_PHASE_BENCHMARKS:
            return GLOBAL_PHASE_BENCHMARKS[phase], 40000

        # Fallback Level 3: Global benchmark
        return GLOBAL_DEFAULT_RUN_RATE, 190000

