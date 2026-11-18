"""Match State Reconstruction Engine for SupeRR Selector Analytics.

Reconstructs the precise ball-by-ball match situation immediately BEFORE each delivery.
Ensures zero future data leakage, vectorized performance, and full audit traceability.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .cricket_rules import (
    calculate_delivery_runs,
    classify_wickets,
    determine_bowling_phase,
    is_legal_delivery,
)
from .delivery_order import validate_and_sort_deliveries
from .innings_context import build_match_innings_context

logger = logging.getLogger(__name__)


def reconstruct_match_states(
    bbb_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    comps_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Reconstructs the pre-delivery match state for every delivery in the dataset.

    All pre-delivery metrics (score, wickets lost, legal balls bowled, runs required, run rates)
    strictly exclude outcomes from the current delivery, ensuring ZERO future data leakage.

    Args:
        bbb_df: Clean raw/processed ball_by_ball DataFrame.
        matches_df: Clean raw/processed matches DataFrame.
        comps_df: Optional competitions DataFrame for format lookup.

    Returns:
        pd.DataFrame: Augmented DataFrame with all required pre-delivery state variables.
    """
    logger.info("Starting ball-by-ball match state reconstruction on %d records.", len(bbb_df))

    # Step 1: Delivery Order Reconstruction & Validation
    ordered_df, order_anomalies = validate_and_sort_deliveries(bbb_df)

    # Step 2: Legal Ball Detection
    ordered_df["is_legal_ball"] = is_legal_delivery(ordered_df["extras_type"])

    # Step 3: Granular Run Breakdown
    runs_df = calculate_delivery_runs(ordered_df)
    for col in runs_df.columns:
        ordered_df[col] = runs_df[col]

    # Step 4: Wicket Classification
    wickets_df = classify_wickets(ordered_df)
    for col in wickets_df.columns:
        ordered_df[col] = wickets_df[col]

    # Step 5: Bowling Phase
    ordered_df["bowling_innings_phase"] = determine_bowling_phase(
        ordered_df["overid"], ordered_df["innings"]
    )

    # Step 6: Innings Context and Target Mapping
    innings_context = build_match_innings_context(matches_df, ordered_df)
    context_cols = [
        "match_id",
        "innings",
        "comp_id",
        "stage",
        "knock_out",
        "scheduled_balls",
        "scheduled_overs",
        "target",
        "is_target_revised",
        "is_shortened_match",
    ]
    available_ctx_cols = [c for c in context_cols if c in innings_context.columns]
    merged_df = ordered_df.merge(
        innings_context[available_ctx_cols],
        on=["match_id", "innings"],
        how="left",
    )

    # Add match format if comps_df is supplied
    if comps_df is not None and "comp_id" in merged_df.columns and "match_format" in comps_df.columns:
        format_map = comps_df.set_index("comp_id")["match_format"].to_dict()
        merged_df["match_format"] = merged_df["comp_id"].map(format_map).astype("string")
    elif "match_format" not in merged_df.columns:
        merged_df["match_format"] = "T20"  # Fallback default

    # Step 7: Vectorized Cumulative Pre-Delivery Match State Calculations
    # Note: Pre-delivery value = cumulative_sum_to_current_ball - current_ball_value
    group_keys = ["match_id", "innings"]

    # 7.1 Innings score before delivery
    cum_team_runs = merged_df.groupby(group_keys)["team_runs_on_ball"].cumsum()
    merged_df["innings_score_before"] = (
        cum_team_runs - merged_df["team_runs_on_ball"]
    ).astype("int64")

    # 7.2 Wickets lost and remaining before delivery
    cum_wickets = merged_df.groupby(group_keys)["is_team_wicket"].cumsum()
    merged_df["wickets_lost_before"] = (
        cum_wickets - merged_df["is_team_wicket"].astype(int)
    ).astype("int64")
    merged_df["wickets_remaining_before"] = (10 - merged_df["wickets_lost_before"]).astype("int64")

    # 7.3 Legal balls bowled and remaining before delivery
    cum_legal = merged_df.groupby(group_keys)["is_legal_ball"].cumsum()
    merged_df["legal_balls_bowled_before"] = (
        cum_legal - merged_df["is_legal_ball"].astype(int)
    ).astype("int64")

    # Scheduled balls remaining before delivery
    merged_df["scheduled_balls_remaining_before"] = np.maximum(
        0, merged_df["scheduled_balls"] - merged_df["legal_balls_bowled_before"]
    ).astype("int64")

    # 7.4 Current Run Rate before delivery: 6 * score / legal_balls
    # (Avoid division by zero: return NA when no legal ball has been bowled yet)
    has_legal_balls = merged_df["legal_balls_bowled_before"] > 0
    crr_vals = np.where(
        has_legal_balls,
        (6.0 * merged_df["innings_score_before"]) / merged_df["legal_balls_bowled_before"],
        np.nan,
    )
    merged_df["current_run_rate"] = pd.Series(crr_vals, index=merged_df.index, dtype="Float64")

    # 7.5 Chase State: Runs required and Required Run Rate
    # Applies to Innings 2 and Innings 4 when a valid target is known
    has_target = merged_df["target"].notnull()
    runs_req_vals = np.where(
        has_target,
        np.maximum(0, merged_df["target"] - merged_df["innings_score_before"]),
        np.nan,
    )
    merged_df["runs_required_before"] = pd.Series(runs_req_vals, index=merged_df.index, dtype="Int64")

    # Required run rate: 6 * runs_required / scheduled_balls_remaining
    # (Avoid division by zero when balls_remaining == 0 or target is null)
    has_balls_remaining = merged_df["scheduled_balls_remaining_before"] > 0
    rrr_condition = has_target & has_balls_remaining
    rrr_vals = np.where(
        rrr_condition,
        (6.0 * merged_df["runs_required_before"].astype("float64"))
        / merged_df["scheduled_balls_remaining_before"],
        np.nan,
    )
    merged_df["required_run_rate"] = pd.Series(rrr_vals, index=merged_df.index, dtype="Float64")

    # Step 8: Quality Status and Phase 3 Eligibility Flags
    # Classify reconstruction status
    status = pd.Series("VALID", index=merged_df.index, dtype="string")
    pressure_ready = pd.Series(True, index=merged_df.index, dtype="bool")

    # Warnings for shortened matches, revised targets, or retired hurt events
    warning_mask = (
        merged_df["is_shortened_match"]
        | merged_df["is_target_revised"]
        | merged_df["is_retired_hurt"]
    )
    status.loc[warning_mask] = "WARNING"

    # Flag records where legal balls bowled exceed scheduled balls (e.g. umpire count errors)
    over_scheduled_mask = (
        merged_df["legal_balls_bowled_before"] > merged_df["scheduled_balls"]
    )
    status.loc[over_scheduled_mask] = "WARNING"

    # Blocked: Innings 2 where target cannot be determined (e.g. abandoned fixture)
    blocked_mask = (merged_df["innings"] == 2) & merged_df["target"].isnull()
    status.loc[blocked_mask] = "BLOCKED"
    pressure_ready.loc[blocked_mask] = False

    merged_df["reconstruction_status"] = status
    merged_df["is_pressure_ready"] = pressure_ready

    logger.info(
        "Match state reconstruction completed successfully. Total: %d, Valid: %d, Warnings: %d, Blocked: %d",
        len(merged_df),
        int((status == "VALID").sum()),
        int((status == "WARNING").sum()),
        int((status == "BLOCKED").sum()),
    )

    return merged_df

