"""Final Rankings Validation Quality Gates for SupeRR Selector Analytics.

Executes a 16-point comprehensive automated verification checklist on generated
ranking CSV outputs and candidate pools before submission sign-off.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def validate_rankings_checklist(
    output_dir: Path,
) -> Tuple[bool, List[Dict[str, str]]]:
    """Validates the 16-point quality gate for Phase 5 rankings.

    Args:
        output_dir: Directory containing ranking CSVs (outputs/).

    Returns:
        Tuple of (all_passed: bool, checklist_results: list of checks).
    """
    logger.info("Executing 16-point quality gate checklist on %s...", output_dir)
    results = []

    def add_check(gate_num: int, description: str, passed: bool, details: str = "") -> None:
        status = "PASSED" if passed else "FAILED"
        results.append({
            "gate": f"Gate {gate_num:02d}",
            "description": description,
            "status": status,
            "details": details,
        })
        if not passed:
            logger.error("Check FAILED - %s: %s", description, details)
        else:
            logger.info("Check PASSED - %s", description)

    # File paths
    top_bat_path = output_dir / "top_10_batters.csv"
    top_bowl_path = output_dir / "top_10_bowlers.csv"
    full_bat_path = output_dir / "full_batting_rankings.csv"
    full_bowl_path = output_dir / "full_bowling_rankings.csv"

    # 1. Top 10 Batters exists
    passed = top_bat_path.exists()
    add_check(1, "Top 10 Batters CSV exists", passed, str(top_bat_path))
    top_bat = pd.read_csv(top_bat_path) if passed else None

    # 2. Top 10 Batters row count
    if top_bat is not None:
        passed = len(top_bat) == 10
        add_check(2, "Top 10 Batters exactly 10 rows", passed, f"Count = {len(top_bat)}")
    else:
        add_check(2, "Top 10 Batters exactly 10 rows", False, "File missing")

    # 3. Top 10 Batters sequential ranks
    if top_bat is not None:
        passed = list(top_bat["rank"]) == list(range(1, 11))
        add_check(3, "Top 10 Batters rank 1-10 sequential", passed, f"Ranks: {list(top_bat['rank'])}")
    else:
        add_check(3, "Top 10 Batters rank 1-10 sequential", False, "File missing")

    # 4. Top 10 Batters distinct player IDs
    if top_bat is not None:
        passed = top_bat["player_id"].nunique() == 10
        add_check(4, "Top 10 Batters distinct player IDs", passed, f"Unique = {top_bat['player_id'].nunique()}")
    else:
        add_check(4, "Top 10 Batters distinct player IDs", False, "File missing")

    # 5. Top 10 Batters all eligible
    if top_bat is not None:
        passed = (top_bat["eligibility_status"] == "ELIGIBLE").all()
        add_check(5, "Top 10 Batters all ELIGIBLE", passed, f"Statuses: {top_bat['eligibility_status'].unique()}")
    else:
        add_check(5, "Top 10 Batters all ELIGIBLE", False, "File missing")

    # 6. Top 10 Batters descending scores
    if top_bat is not None:
        scores = list(top_bat["reliability_score"])
        passed = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        add_check(6, "Top 10 Batters reliability score descending", passed, f"Scores: {scores}")
    else:
        add_check(6, "Top 10 Batters reliability score descending", False, "File missing")

    # 7. Top 10 Batters no null values
    if top_bat is not None:
        passed = not top_bat.isnull().any().any()
        add_check(7, "Top 10 Batters zero null values", passed, f"Null count: {top_bat.isnull().sum().to_dict()}")
    else:
        add_check(7, "Top 10 Batters zero null values", False, "File missing")

    # 8. Top 10 Bowlers exists
    passed = top_bowl_path.exists()
    add_check(8, "Top 10 Bowlers CSV exists", passed, str(top_bowl_path))
    top_bowl = pd.read_csv(top_bowl_path) if passed else None

    # 9. Top 10 Bowlers row count
    if top_bowl is not None:
        passed = len(top_bowl) == 10
        add_check(9, "Top 10 Bowlers exactly 10 rows", passed, f"Count = {len(top_bowl)}")
    else:
        add_check(9, "Top 10 Bowlers exactly 10 rows", False, "File missing")

    # 10. Top 10 Bowlers sequential ranks
    if top_bowl is not None:
        passed = list(top_bowl["rank"]) == list(range(1, 11))
        add_check(10, "Top 10 Bowlers rank 1-10 sequential", passed, f"Ranks: {list(top_bowl['rank'])}")
    else:
        add_check(10, "Top 10 Bowlers rank 1-10 sequential", False, "File missing")

    # 11. Top 10 Bowlers distinct player IDs
    if top_bowl is not None:
        passed = top_bowl["player_id"].nunique() == 10
        add_check(11, "Top 10 Bowlers distinct player IDs", passed, f"Unique = {top_bowl['player_id'].nunique()}")
    else:
        add_check(11, "Top 10 Bowlers distinct player IDs", False, "File missing")

    # 12. Top 10 Bowlers all eligible
    if top_bowl is not None:
        passed = (top_bowl["eligibility_status"] == "ELIGIBLE").all()
        add_check(12, "Top 10 Bowlers all ELIGIBLE", passed, f"Statuses: {top_bowl['eligibility_status'].unique()}")
    else:
        add_check(12, "Top 10 Bowlers all ELIGIBLE", False, "File missing")

    # 13. Top 10 Bowlers descending scores
    if top_bowl is not None:
        scores = list(top_bowl["reliability_score"])
        passed = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        add_check(13, "Top 10 Bowlers reliability score descending", passed, f"Scores: {scores}")
    else:
        add_check(13, "Top 10 Bowlers reliability score descending", False, "File missing")

    # 14. Top 10 Bowlers no null values
    if top_bowl is not None:
        passed = not top_bowl.isnull().any().any()
        add_check(14, "Top 10 Bowlers zero null values", passed, f"Null count: {top_bowl.isnull().sum().to_dict()}")
    else:
        add_check(14, "Top 10 Bowlers zero null values", False, "File missing")

    # 15. Full Batting Rankings integrity
    passed = full_bat_path.exists()
    if passed:
        full_bat = pd.read_csv(full_bat_path)
        scores = list(full_bat["reliability_score"])
        desc_ok = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        uniq_ok = full_bat["player_id"].nunique() == len(full_bat)
        passed = desc_ok and uniq_ok and len(full_bat) >= 10
        add_check(15, "Full Batting Rankings integrity", passed, f"Total candidates: {len(full_bat)}")
    else:
        add_check(15, "Full Batting Rankings integrity", False, "File missing")

    # 16. Full Bowling Rankings integrity
    passed = full_bowl_path.exists()
    if passed:
        full_bowl = pd.read_csv(full_bowl_path)
        scores = list(full_bowl["reliability_score"])
        desc_ok = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        uniq_ok = full_bowl["player_id"].nunique() == len(full_bowl)
        passed = desc_ok and uniq_ok and len(full_bowl) >= 10
        add_check(16, "Full Bowling Rankings integrity", passed, f"Total candidates: {len(full_bowl)}")
    else:
        add_check(16, "Full Bowling Rankings integrity", False, "File missing")

    all_passed = all(r["status"] == "PASSED" for r in results)
    return all_passed, results

