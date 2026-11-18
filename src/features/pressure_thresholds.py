"""Pressure Classification and Threshold Sensitivity Module for SupeRR Selector Analytics.

Classifies continuous pressure scores into categorical regimes:
- LOW_PRESSURE (< 40.0)
- MEDIUM_PRESSURE (40.0 - 64.99)
- HIGH_PRESSURE (>= 65.0)
- UNDETERMINED (unscoreable or invalid states)

Includes threshold sensitivity evaluation to ensure classification stability.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_LOW_THRESHOLD = 40.0
DEFAULT_HIGH_THRESHOLD = 65.0


def classify_pressure(
    score_series: pd.Series,
    is_pressure_ready: Optional[pd.Series] = None,
    low_thresh: float = DEFAULT_LOW_THRESHOLD,
    high_thresh: float = DEFAULT_HIGH_THRESHOLD,
) -> pd.Series:
    """Classifies a continuous 0-100 pressure score into discrete categories.

    Args:
        score_series: Numeric Series of pressure scores in [0, 100].
        is_pressure_ready: Boolean Series indicating record validity.
        low_thresh: Boundary between LOW_PRESSURE and MEDIUM_PRESSURE.
        high_thresh: Boundary between MEDIUM_PRESSURE and HIGH_PRESSURE.

    Returns:
        pd.Series: Categorical pressure classifications.
    """
    classes = pd.Series("MEDIUM_PRESSURE", index=score_series.index, dtype="string")

    valid_mask = score_series.notnull()
    if is_pressure_ready is not None:
        valid_mask = valid_mask & is_pressure_ready.fillna(False)

    # Classify valid records
    classes.loc[valid_mask & (score_series < low_thresh)] = "LOW_PRESSURE"
    classes.loc[valid_mask & (score_series >= low_thresh) & (score_series < high_thresh)] = "MEDIUM_PRESSURE"
    classes.loc[valid_mask & (score_series >= high_thresh)] = "HIGH_PRESSURE"

    # Undetermined records
    classes.loc[~valid_mask] = "UNDETERMINED"

    return classes


def evaluate_threshold_sensitivity(
    df: pd.DataFrame,
    threshold_pairs: Optional[List[Tuple[float, float]]] = None,
) -> pd.DataFrame:
    """Evaluates classification stability across alternative threshold configurations.

    Args:
        df: DataFrame containing 'batting_pressure_score', 'bowling_pressure_score', 'is_pressure_ready'.
        threshold_pairs: List of (low_thresh, high_thresh) tuples to evaluate.

    Returns:
        pd.DataFrame: Sensitivity comparison table.
    """
    if threshold_pairs is None:
        threshold_pairs = [
            (35.0, 60.0),  # More aggressive high-pressure cutoff
            (40.0, 65.0),  # Baseline / Default
            (45.0, 70.0),  # More conservative high-pressure cutoff
        ]

    results: List[Dict[str, Any]] = []

    for low_t, high_t in threshold_pairs:
        bat_classes = classify_pressure(
            df["batting_pressure_score"], df["is_pressure_ready"], low_t, high_t
        )
        bowl_classes = classify_pressure(
            df["bowling_pressure_score"], df["is_pressure_ready"], low_t, high_t
        )

        n_total = len(df)
        bat_high = int((bat_classes == "HIGH_PRESSURE").sum())
        bat_med = int((bat_classes == "MEDIUM_PRESSURE").sum())
        bat_low = int((bat_classes == "LOW_PRESSURE").sum())

        bowl_high = int((bowl_classes == "HIGH_PRESSURE").sum())
        bowl_med = int((bowl_classes == "MEDIUM_PRESSURE").sum())
        bowl_low = int((bowl_classes == "LOW_PRESSURE").sum())

        results.append({
            "threshold_config": f"Low<{low_t}_High>={high_t}",
            "low_threshold": low_t,
            "high_threshold": high_t,
            "batting_high_count": bat_high,
            "batting_high_pct": round(bat_high / n_total * 100, 2),
            "batting_med_pct": round(bat_med / n_total * 100, 2),
            "batting_low_pct": round(bat_low / n_total * 100, 2),
            "bowling_high_count": bowl_high,
            "bowling_high_pct": round(bowl_high / n_total * 100, 2),
            "bowling_med_pct": round(bowl_med / n_total * 100, 2),
            "bowling_low_pct": round(bowl_low / n_total * 100, 2),
        })

    return pd.DataFrame(results)

