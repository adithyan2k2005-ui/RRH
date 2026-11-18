"""Context-Aware Cricket Pressure Model for SupeRR Selector Analytics.

Implements the multi-dimensional pressure engine calculating:
- batting_pressure_score (0-100)
- bowling_pressure_score (0-100)
- match_tension_score (0-100)

Strictly separates batting difficulty from bowling defensive urgency, distinguishes
first-innings target setting from chase dynamics, and guarantees zero future data leakage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default model weight configuration
DEFAULT_PRESSURE_WEIGHTS: Dict[str, Any] = {
    "version": "1.0.0",
    # Second Innings (Chase) Batting Weights
    "chase_bat_urgency_w": 0.45,
    "chase_bat_wickets_w": 0.35,
    "chase_bat_interaction_w": 0.20,
    # Second Innings (Chase) Bowling Weights
    "chase_bowl_closeness_w": 0.50,
    "chase_bowl_wickets_in_hand_w": 0.30,
    "chase_bowl_comfortable_chase_w": 0.20,
    # Second Innings Match Tension Weights
    "chase_tension_closeness_w": 0.60,
    "chase_tension_time_w": 0.25,
    "chase_tension_wickets_w": 0.15,
    # First Innings Batting Weights
    "first_bat_wickets_w": 0.45,
    "first_bat_par_deficit_w": 0.35,
    "first_bat_interaction_w": 0.20,
    # First Innings Bowling Weights
    "first_bowl_opposition_runrate_w": 0.40,
    "first_bowl_opposition_wickets_w": 0.35,
    "first_bowl_time_w": 0.25,
}


def compute_pressure_scores(
    states_df: pd.DataFrame,
    components_df: pd.DataFrame,
    weights_config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Calculates batting pressure, bowling pressure, and match tension scores in [0, 100].

    Args:
        states_df: Reconstructed match states DataFrame.
        components_df: Normalized pressure components DataFrame.
        weights_config: Optional dictionary of model weights.

    Returns:
        pd.DataFrame: DataFrame containing:
            - batting_pressure_score (float, 0-100)
            - bowling_pressure_score (float, 0-100)
            - match_tension_score (float, 0-100)
            - pressure_model_version (string)
    """
    logger.info("Computing pressure scores for %d deliveries.", len(states_df))
    cfg = weights_config or DEFAULT_PRESSURE_WEIGHTS
    version = str(cfg.get("version", "1.0.0"))

    is_chase = states_df["innings"].isin([2, 4]) & states_df["target"].notnull()
    is_first_inn = ~is_chase

    # Extract normalized components
    u_chase = components_df["chase_urgency"].fillna(0.0).values
    v_wickets = components_df["wicket_vulnerability"].fillna(0.0).values
    t_time = components_df["time_pressure"].fillna(0.0).values
    c_closeness = components_df["match_closeness"].fillna(0.0).values
    d_par = components_df["first_inn_par_deficit"].fillna(0.0).values
    s_stakes = components_df["match_stakes_multiplier"].fillna(1.0).values

    # Pre-allocate output arrays
    batting_pressure = np.zeros(len(states_df), dtype="float64")
    bowling_pressure = np.zeros(len(states_df), dtype="float64")
    match_tension = np.zeros(len(states_df), dtype="float64")

    # -------------------------------------------------------------
    # 1. SECOND INNINGS / CHASE CALCULATIONS
    # -------------------------------------------------------------
    chase_indices = np.where(is_chase)[0]
    if len(chase_indices) > 0:
        u = u_chase[chase_indices]
        v = v_wickets[chase_indices]
        t = t_time[chase_indices]
        c = c_closeness[chase_indices]
        s = s_stakes[chase_indices]

        # Batting Pressure in Chase:
        # Driven by high required rate, fewer wickets in hand, and interaction
        bat_raw = (
            cfg["chase_bat_urgency_w"] * u
            + cfg["chase_bat_wickets_w"] * v
            + cfg["chase_bat_interaction_w"] * np.sqrt(u * v)
        )
        batting_pressure[chase_indices] = np.clip(bat_raw * s * 100.0, 0.0, 100.0)

        # Bowling Pressure in Chase:
        # Driven by match closeness (game on the line), batting team having wickets in hand,
        # and death overs defending a tight total. Low when batting team is doomed.
        bowl_raw = (
            cfg["chase_bowl_closeness_w"] * c
            + cfg["chase_bowl_wickets_in_hand_w"] * (1.0 - v) * t
            + cfg["chase_bowl_comfortable_chase_w"] * np.maximum(0.0, 1.0 - u) * t
        )
        bowling_pressure[chase_indices] = np.clip(bowl_raw * s * 100.0, 0.0, 100.0)

        # Match Tension in Chase:
        # Reflects overall balance and closeness of contest
        tension_raw = (
            cfg["chase_tension_closeness_w"] * c
            + cfg["chase_tension_time_w"] * t * (1.0 - np.abs(u - 0.5) * 2.0)
            + cfg["chase_tension_wickets_w"] * v
        )
        match_tension[chase_indices] = np.clip(tension_raw * s * 100.0, 0.0, 100.0)

    # -------------------------------------------------------------
    # 2. FIRST INNINGS CALCULATIONS (Target Setting)
    # -------------------------------------------------------------
    first_inn_indices = np.where(is_first_inn)[0]
    if len(first_inn_indices) > 0:
        v = v_wickets[first_inn_indices]
        d = d_par[first_inn_indices]
        t = t_time[first_inn_indices]
        s = s_stakes[first_inn_indices]

        # Batting Pressure in 1st Innings:
        # Driven by wicket collapses, scoring below par, and death acceleration
        bat_raw_first = (
            cfg["first_bat_wickets_w"] * v
            + cfg["first_bat_par_deficit_w"] * d
            + cfg["first_bat_interaction_w"] * np.sqrt(v * t)
        )
        batting_pressure[first_inn_indices] = np.clip(bat_raw_first * s * 100.0, 0.0, 100.0)

        # Bowling Pressure in 1st Innings:
        # Driven by batting team scoring heavily (1 - d), wickets remaining (1 - v), and death phase (t)
        bowl_raw_first = (
            cfg["first_bowl_opposition_runrate_w"] * (1.0 - d)
            + cfg["first_bowl_opposition_wickets_w"] * (1.0 - v)
            + cfg["first_bowl_time_w"] * t
        )
        bowling_pressure[first_inn_indices] = np.clip(bowl_raw_first * s * 100.0, 0.0, 100.0)

        # Match Tension in 1st Innings: Balanced combination of competitive demands
        tension_raw_first = 0.50 * batting_pressure[first_inn_indices] + 0.50 * bowling_pressure[first_inn_indices]
        match_tension[first_inn_indices] = np.clip(tension_raw_first, 0.0, 100.0)

    scores_df = pd.DataFrame({
        "batting_pressure_score": np.round(batting_pressure, 2),
        "bowling_pressure_score": np.round(bowling_pressure, 2),
        "match_tension_score": np.round(match_tension, 2),
        "pressure_model_version": version,
    }, index=states_df.index)

    return scores_df

