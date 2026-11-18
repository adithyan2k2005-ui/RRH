"""Eligibility Audit Module for SupeRR Selector Analytics.

Audits all candidates (batters and bowlers) across the dataset against the declared
sample size and competition exposure thresholds. Produces an audit summary DataFrame
and CSV report.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def generate_eligibility_audit(
    player_bat_df: pd.DataFrame,
    player_bowl_df: pd.DataFrame,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Generates an exhaustive eligibility audit table for all batters and bowlers.

    Args:
        player_bat_df: All evaluated batters from Phase 4.
        player_bowl_df: All evaluated bowlers from Phase 4.
        output_path: Optional path to save CSV.

    Returns:
        pd.DataFrame: Audit table for all players.
    """
    logger.info("Generating candidate eligibility audit...")

    records = []

    # 1. Batters
    for _, row in player_bat_df.iterrows():
        hp_balls = int(row.get("hp_balls", 0))
        hp_matches = int(row.get("hp_matches", 0))
        ord_balls = int(row.get("ord_balls", 0))
        status = str(row.get("eligibility_status", "UNKNOWN"))
        score = float(row.get("reliability_score", 0.0))

        records.append({
            "discipline": "BATTING",
            "player_id": int(row["striker_id"]),
            "player_name": str(row["player_name"]),
            "hp_balls": hp_balls,
            "hp_matches": hp_matches,
            "ord_balls": ord_balls,
            "meets_hp_balls": hp_balls >= 20,
            "meets_hp_matches": hp_matches >= 3,
            "meets_ord_balls": ord_balls >= 25,
            "eligibility_status": status,
            "reliability_score": round(score, 2),
        })

    # 2. Bowlers
    for _, row in player_bowl_df.iterrows():
        hp_balls = int(row.get("hp_balls", 0))
        hp_matches = int(row.get("hp_matches", 0))
        ord_balls = int(row.get("ord_balls", 0))
        status = str(row.get("eligibility_status", "UNKNOWN"))
        score = float(row.get("reliability_score", 0.0))

        records.append({
            "discipline": "BOWLING",
            "player_id": int(row["bowler_id"]),
            "player_name": str(row["player_name"]),
            "hp_balls": hp_balls,
            "hp_matches": hp_matches,
            "ord_balls": ord_balls,
            "meets_hp_balls": hp_balls >= 24,
            "meets_hp_matches": hp_matches >= 3,
            "meets_ord_balls": ord_balls >= 30,
            "eligibility_status": status,
            "reliability_score": round(score, 2),
        })

    audit_df = pd.DataFrame(records)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audit_df.to_csv(output_path, index=False)
        logger.info("Saved eligibility audit CSV to %s (%d records).", output_path, len(audit_df))

    return audit_df

