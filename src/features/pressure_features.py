"""Pressure Components and Feature Extraction Module for SupeRR Selector Analytics.

Calculates normalized pre-delivery pressure factors:
- Chase urgency (RRR relative to contextual scoring expectations)
- Wicket vulnerability (non-linear batting resource depletion)
- Time pressure (innings progression towards scheduled end)
- Match closeness (competitiveness / balance around 50-50 wire finish)
- First-innings scoring deficit (run rate relative to par)
- Match stakes (knockout and elimination tournament contexts)
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .pressure_baselines import ContextualBaselines, GLOBAL_FORMAT_BENCHMARKS, GLOBAL_DEFAULT_RUN_RATE

logger = logging.getLogger(__name__)


def calculate_pressure_features(
    states_df: pd.DataFrame,
    baselines: Optional[ContextualBaselines] = None,
) -> pd.DataFrame:
    """Calculates granular normalized pressure factor components for every delivery.

    All features use information strictly available BEFORE the delivery.

    Args:
        states_df: Reconstructed match states DataFrame.
        baselines: Fitted ContextualBaselines instance.

    Returns:
        pd.DataFrame: DataFrame containing the normalized pressure components.
    """
    logger.info("Computing pressure components for %d delivery states.", len(states_df))
    df = states_df.copy()

    # When no baselines are supplied, use global default benchmarks.
    # We deliberately do NOT fit from data here to avoid requiring columns
    # (is_legal_ball, team_runs_on_ball) that may be absent in synthetic test fixtures.
    if baselines is None:
        baselines = ContextualBaselines()

    # 1. Map contextual baseline run rate and support ball counts
    # Vectorized lookup across (match_format, bowling_innings_phase)
    lookup_keys = (
        df["match_format"].fillna("T20").astype(str)
        + "__"
        + df["bowling_innings_phase"].fillna("Middle").astype(str)
    )

    unique_keys = lookup_keys.unique()
    rate_map = {}
    support_map = {}
    for ukey in unique_keys:
        fmt, phs = ukey.split("__")
        r, s = baselines.get_baseline_run_rate(fmt, phs)
        rate_map[ukey] = r
        support_map[ukey] = s

    baseline_rates = lookup_keys.map(rate_map).astype("float64")
    support_counts = lookup_keys.map(support_map).astype("int64")

    # 2a. Format-level baseline for chase urgency sigmoid center.
    # Chase urgency compares RRR against the OVERALL format scoring rate (not the
    # phase-specific rate), so that RRR > format average signals genuine difficulty
    # regardless of which phase the chase is in.
    fmt_series = df["match_format"].fillna("T20").astype(str)
    format_baseline_rates = fmt_series.map(
        lambda f: GLOBAL_FORMAT_BENCHMARKS.get(f, GLOBAL_DEFAULT_RUN_RATE)
    ).astype("float64")

    # 2. Wicket Vulnerability: V_wickets in [0, 1]
    # Wickets remaining ranges from 1 to 10
    w_rem = df["wickets_remaining_before"].clip(1, 10).astype("float64")
    # Non-linear power scaling: 10 in hand -> 0.0; 1 in hand (9 down) -> 1.0
    v_wickets = np.power((10.0 - w_rem) / 9.0, 1.35)

    # 3. Time Pressure: T_time in [0, 1]
    # Proximity to innings conclusion: balls bowled / scheduled balls
    sched_balls = df["scheduled_balls"].clip(lower=6).astype("float64")
    balls_bowled = df["legal_balls_bowled_before"].clip(lower=0).astype("float64")
    t_time = np.clip(balls_bowled / sched_balls, 0.0, 1.0)

    # 4. Chase Urgency: U_chase in [0, 1] (Applicable to Innings 2 and 4)
    # Compares required run rate to the FORMAT-LEVEL global baseline, not the phase baseline.
    # Using the format-level baseline ensures RRR > average scoring rate reflects real difficulty
    # regardless of phase (e.g. RRR=10.2 is hard even in a Death over where phase norms are 10.24).
    is_chase = df["innings"].isin([2, 4]) & df["target"].notnull()
    rrr = df["required_run_rate"].fillna(format_baseline_rates).astype("float64")

    # Logistic sigmoid (k=0.45) centered at format baseline.
    # At RRR == format_base (~9.2 for T20): U ~ 0.5 (neutral)
    # At RRR == 10.2 (T20, 3 wkts):       U ~ 0.61 (elevated)
    # At RRR >= 18.0:                       U ~ 0.98+ (extreme)
    # At RRR == 1.0 (comfortable):          U ~ 0.03 (very low)
    chase_urgency_raw = 1.0 / (1.0 + np.exp(-0.45 * (rrr - format_baseline_rates)))
    # Where balls remaining == 0: if target still needed, urgency = 1.0; else 0.0
    zero_balls_mask = (df["scheduled_balls_remaining_before"] == 0) & is_chase
    runs_needed = df["runs_required_before"].fillna(0).astype("int64")
    chase_urgency = np.where(
        zero_balls_mask,
        np.where(runs_needed > 0, 1.0, 0.0),
        chase_urgency_raw,
    )
    # Mask out non-chase innings
    chase_urgency = np.where(is_chase, chase_urgency, np.nan)

    # 5. Match Closeness / Balance: C_closeness in [0, 1] (Chase context)
    # Closeness peaks when RRR is near baseline rate and balls remaining are low
    rrr_diff = rrr - baseline_rates
    closeness_gaussian = np.exp(-(rrr_diff ** 2) / (2.0 * (3.5 ** 2)))
    # Proximity amplifier: matches become closer / higher tension deeper into the chase
    closeness_amplifier = 0.5 + 0.5 * t_time
    c_closeness = np.where(is_chase, np.clip(closeness_gaussian * closeness_amplifier, 0.0, 1.0), np.nan)

    # 6. First-Innings Par Deficit: D_par in [0, 1] (Innings 1 and 3)
    # Evaluates whether the batting team is falling behind competitive par
    crr = df["current_run_rate"].fillna(baseline_rates).astype("float64")
    # Logistic function: CRR < par -> D_par > 0.5 (deficit / pressure); CRR > par -> D_par < 0.5
    d_par_raw = 1.0 / (1.0 + np.exp(0.40 * (crr - baseline_rates)))
    is_first_inn = df["innings"].isin([1, 3])
    d_par = np.where(is_first_inn, d_par_raw, np.nan)

    # 7. Match Stakes Multiplier: S_stakes in [1.0, 1.15]
    # Knockout matches receive a modest contextual boost without distorting normal play
    stage = df["stage"].fillna("League").astype(str)
    is_ko = (df["knock_out"] == 1) | stage.isin(["Final", "Semi Final", "Qualifier", "Eliminator"])
    is_playoff = stage.isin(["Super 4", "Super 8"])

    s_stakes = np.where(is_ko, 1.15, np.where(is_playoff, 1.08, 1.00))

    components_df = pd.DataFrame({
        "baseline_expected_rate": baseline_rates,
        "baseline_support_balls": support_counts,
        "wicket_vulnerability": v_wickets,
        "time_pressure": t_time,
        "chase_urgency": chase_urgency,
        "match_closeness": c_closeness,
        "first_inn_par_deficit": d_par,
        "match_stakes_multiplier": s_stakes,
    }, index=df.index)

    return components_df

