"""Delivery Order Reconstruction Module for SupeRR Selector Analytics.

Reconstructs the strictly chronological sequence of deliveries within each innings,
verifies delivery sequence continuity, detects duplicate identifiers, and flags anomalies.
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def validate_and_sort_deliveries(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sorts deliveries chronologically and verifies sequence integrity.

    Sorts by ['match_id', 'innings', 'overid', 'over_ball_num'], which is mathematically
    equivalent to sorting by ['match_id', 'innings', 'innings_ball_num'].
    Calculates delivery_seq as a continuous 1-indexed delivery sequence within each innings.

    Args:
        df: Input delivery DataFrame (e.g. ball_by_ball).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - Ordered and validated DataFrame with delivery_seq.
            - DataFrame of any detected ordering anomalies or sequence gaps.
    """
    logger.info("Validating and sorting %d delivery records.", len(df))
    sorted_df = df.copy()

    # Ensure required sorting keys exist
    required_keys = ["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
    for k in required_keys:
        if k not in sorted_df.columns:
            raise KeyError(f"Missing required ordering key: {k}")

    # Deterministic chronological sort
    sorted_df = sorted_df.sort_values(
        by=["match_id", "innings", "overid", "over_ball_num"],
        kind="mergesort",
    ).reset_index(drop=False)  # Preserves original row index as 'index'

    # Rename original index to preserve raw record traceability
    if "index" in sorted_df.columns:
        sorted_df = sorted_df.rename(columns={"index": "source_row_index"})

    # Compute 1-indexed delivery sequence within each match innings
    sorted_df["delivery_seq"] = (
        sorted_df.groupby(["match_id", "innings"]).cumcount() + 1
    ).astype("int64")

    # Detect duplicate delivery keys
    dup_mask = sorted_df.duplicated(
        subset=["match_id", "innings", "overid", "over_ball_num"], keep=False
    )
    dup_count = int(dup_mask.sum())
    if dup_count > 0:
        logger.warning("Found %d duplicate delivery keys in dataset!", dup_count)

    # Detect sequence gaps or contradictions against innings_ball_num
    seq_mismatch = sorted_df["delivery_seq"] != sorted_df["innings_ball_num"]
    mismatch_count = int(seq_mismatch.sum())
    if mismatch_count > 0:
        logger.warning(
            "Found %d deliveries where delivery_seq differs from innings_ball_num!",
            mismatch_count,
        )

    anomalies = sorted_df[dup_mask | seq_mismatch]
    logger.info(
        "Delivery ordering completed successfully. Total deliveries: %d, Anomalies: %d",
        len(sorted_df),
        len(anomalies),
    )
    return sorted_df, anomalies

