"""Unit tests for cricket domain rules and event classifications in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.cricket_rules import (
    calculate_delivery_runs,
    classify_wickets,
    determine_bowling_phase,
    is_legal_delivery,
)


class TestCricketRulesUnit:
    """Unit tests for cricket domain rules on delivery legality, runs, and dismissals."""

    def test_legal_delivery_classification(self):
        """Verify legal deliveries are correctly identified and illegal balls flagged."""
        extras = pd.Series([None, "wide", "Overstep", "byes", "legbyes", "other", "Penalty"])
        legal = is_legal_delivery(extras)

        expected = [True, False, False, True, True, False, True]
        assert list(legal) == expected

    def test_run_attribution_batter_vs_extras_vs_bowler(self):
        """Verify runs are correctly partitioned among batter, extras, team, and bowler."""
        df = pd.DataFrame({
            "runs": [0, 4, 1, 0, 0, 6],
            "extras_type": ["wide", None, "Overstep", "byes", "legbyes", None],
            "extras1_runs": [1, 0, 1, 4, 2, 0],
            "extras_2_runs": [0, 0, 0, 0, 0, 0],
        })

        res = calculate_delivery_runs(df)

        # Batter runs: [0, 4, 1, 0, 0, 6]
        assert list(res["runs_scored_on_ball"]) == [0, 4, 1, 0, 0, 6]

        # Extras: [1, 0, 1, 4, 2, 0]
        assert list(res["extras_on_ball"]) == [1, 0, 1, 4, 2, 0]

        # Team runs: [1, 4, 2, 4, 2, 6]
        assert list(res["team_runs_on_ball"]) == [1, 4, 2, 4, 2, 6]

        # Bowler runs:
        # wide: 1, boundary: 4, no-ball (1 off bat + 1 penalty): 2, byes: 0, legbyes: 0, six: 6
        assert list(res["runs_charged_to_bowler_on_ball"]) == [1, 4, 2, 0, 0, 6]

    def test_wicket_classification_bowler_vs_team_vs_retired_hurt(self):
        """Verify bowler-credited dismissals, runouts, and retired hurt cases are distinct."""
        df = pd.DataFrame({
            "is_wicket": [True, True, True, True, False, False],
            "dismissal_type": ["Bowled", "Caught", "RunOut", "Retire Out", None, None],
            "dismissed_player_id": [101, 102, 103, 104, 105, None],
        })

        res = classify_wickets(df)

        # Team wickets: all True except rows 4 and 5
        assert list(res["is_team_wicket"]) == [True, True, True, True, False, False]

        # Bowler wickets: only Bowled and Caught
        assert list(res["is_bowler_wicket"]) == [True, True, False, False, False, False]

        # Retired hurt: row 4 (is_wicket=False, dismissed_player_id=105)
        assert list(res["is_retired_hurt"]) == [False, False, False, False, True, False]

    def test_bowling_phases_classification(self):
        """Verify powerplay, middle, death, and super over phases."""
        overid = pd.Series([1, 6, 7, 15, 16, 20, 1, 1])
        innings = pd.Series([1, 1, 1, 1, 1, 1, 3, 4])

        phases = determine_bowling_phase(overid, innings)

        expected = [
            "Powerplay", "Powerplay", "Middle", "Middle",
            "Death", "Death", "SuperOver", "SuperOver"
        ]
        assert list(phases) == expected

