"""Cricket Domain Rules and Event Classification Module for SupeRR Selector Analytics.

Implements verified cricket rules for delivery legality, run attribution (batter vs team vs bowler),
dismissal classification (bowler credited vs team wickets), and bowling innings phase detection.
"""

from __future__ import annotations

import logging
from typing import Set

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Modes of dismissal credited directly to the bowler in standard cricket scoring
BOWLER_CREDITED_DISMISSALS: Set[str] = {
    "Bowled",
    "Caught",
    "LBW",
    "Stump",
    "Hit Wicket",
}

# Modes of dismissal not credited to the bowler
NON_BOWLER_DISMISSALS: Set[str] = {
    "RunOut",
    "Retire Out",
    "Obstructing the field",
    "Obstracting the field",  # Known data spelling variation
}

# Illegal delivery extras types
ILLEGAL_EXTRAS_TYPES: Set[str] = {"wide", "Overstep", "other"}


def is_legal_delivery(extras_type: pd.Series) -> pd.Series:
    """Identifies whether each delivery counts as a legal ball in cricket.

    Wide deliveries and no-balls (Overstep / other) are illegal deliveries and
    do not consume a legal ball. Byes, leg-byes, penalty runs, and unassisted deliveries
    count as legal deliveries.

    Args:
        extras_type: Series of extras_type strings (or null).

    Returns:
        pd.Series: Boolean Series where True indicates a legal delivery.
    """
    return ~extras_type.isin(ILLEGAL_EXTRAS_TYPES)


def calculate_delivery_runs(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates granular run attributions for batter, extras, team, and bowler.

    - runs_scored_on_ball: Batter runs off the bat (from 'runs').
    - extras_on_ball: Total extra runs ('extras1_runs' + 'extras_2_runs').
    - team_runs_on_ball: Total runs added to team innings score.
    - runs_charged_to_bowler_on_ball: Runs debited against bowler's analysis
      (includes off-the-bat runs, wides, and no-ball penalty runs; excludes byes/leg-byes).

    Args:
        df: DataFrame containing 'runs', 'extras_type', 'extras1_runs', 'extras_2_runs'.

    Returns:
        pd.DataFrame: DataFrame containing the four calculated run columns.
    """
    runs = df["runs"].fillna(0).astype("int64")
    extras1 = df["extras1_runs"].fillna(0).astype("int64")
    extras2 = df["extras_2_runs"].fillna(0).astype("int64")
    extras_type = df["extras_type"]

    team_runs = runs + extras1 + extras2
    total_extras = extras1 + extras2

    # Bowler charged runs:
    # 1. Wides: extras1_runs (wide runs debited to bowler)
    # 2. No-balls (Overstep / other): batter runs + 1 penalty run (extras1_runs)
    # 3. Byes / Leg-byes / Penalty: 0 runs debited to bowler
    # 4. Standard legal deliveries: batter runs
    bowler_runs = pd.Series(0, index=df.index, dtype="int64")

    # Wides
    wide_mask = extras_type == "wide"
    bowler_runs.loc[wide_mask] = extras1.loc[wide_mask]

    # No-balls (Overstep or other)
    noball_mask = extras_type.isin(["Overstep", "other"])
    bowler_runs.loc[noball_mask] = (runs.loc[noball_mask] + extras1.loc[noball_mask])

    # Standard legal deliveries (extras_type is null)
    standard_mask = extras_type.isnull()
    bowler_runs.loc[standard_mask] = runs.loc[standard_mask]

    # Byes, legbyes, penalty: remains 0 (correct cricket rule: byes/legbyes are not conceded by bowler)

    return pd.DataFrame({
        "runs_scored_on_ball": runs,
        "extras_on_ball": total_extras,
        "team_runs_on_ball": team_runs,
        "runs_charged_to_bowler_on_ball": bowler_runs,
    })


def classify_wickets(df: pd.DataFrame) -> pd.DataFrame:
    """Classifies dismissals into team wickets, bowler-credited wickets, and retired hurt.

    Args:
        df: DataFrame containing 'is_wicket', 'dismissal_type', 'dismissed_player_id'.

    Returns:
        pd.DataFrame: DataFrame with 'is_team_wicket', 'is_bowler_wicket', 'is_retired_hurt'.
    """
    is_wicket_raw = df["is_wicket"].fillna(False).astype(bool)
    dismissal_type = df["dismissal_type"].fillna("")

    # Team wicket: fall of a wicket (all dismissal types)
    is_team_wicket = is_wicket_raw

    # Bowler credited wicket: Bowled, Caught, LBW, Stump, Hit Wicket
    is_bowler_wicket = is_wicket_raw & dismissal_type.isin(BOWLER_CREDITED_DISMISSALS)

    # Retired hurt: is_wicket == False but dismissed_player_id is populated
    has_dismissed_id = df["dismissed_player_id"].notnull()
    is_retired_hurt = (~is_wicket_raw) & has_dismissed_id

    return pd.DataFrame({
        "is_team_wicket": is_team_wicket,
        "is_bowler_wicket": is_bowler_wicket,
        "is_retired_hurt": is_retired_hurt,
    })


def determine_bowling_phase(overid: pd.Series, innings: pd.Series) -> pd.Series:
    """Determines the standard T20 match phase for each delivery.

    - SuperOver: Innings 3 or 4
    - Powerplay: Overs 1 to 6
    - Middle: Overs 7 to 15
    - Death: Overs 16 to 20

    Args:
        overid: Over number Series (1-indexed: 1..20).
        innings: Innings number Series (1, 2, 3, 4).

    Returns:
        pd.Series: Categorical phase strings.
    """
    phase = pd.Series("Middle", index=overid.index, dtype="string")

    # Super Overs
    super_mask = innings.isin([3, 4])
    phase.loc[super_mask] = "SuperOver"

    # Standard overs
    non_super = ~super_mask
    phase.loc[non_super & (overid >= 1) & (overid <= 6)] = "Powerplay"
    phase.loc[non_super & (overid >= 7) & (overid <= 15)] = "Middle"
    phase.loc[non_super & (overid >= 16) & (overid <= 20)] = "Death"

    return phase

