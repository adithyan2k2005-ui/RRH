"""Unit tests for bowling metrics and cricket scoring semantics in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.performance.bowling_metrics import compute_delivery_bowling_flags, compute_player_bowling_aggregate


class TestBowlingMetricsUnit:
    """Verifies cricket laws for bowling legal balls, conceded runs, and credited wickets."""

    @pytest.fixture
    def synthetic_bowling_deliveries(self):
        """Constructs synthetic bowling deliveries with wides, byes, and run-outs."""
        return pd.DataFrame({
            "match_id": [1, 1, 1, 1, 1, 1, 1],
            "innings": [1, 1, 1, 1, 1, 1, 1],
            "comp_id": [10, 10, 10, 10, 10, 10, 10],
            "bowler_id": [501, 501, 501, 501, 501, 501, 501],
            "bowler_name": ["Bowler X", "Bowler X", "Bowler X", "Bowler X", "Bowler X", "Bowler X", "Bowler X"],
            "is_legal_ball": [True, False, True, True, True, True, False],
            "extras_type": [pd.NA, "wide", "legbyes", "byes", pd.NA, pd.NA, "Overstep"],
            # Runs debited to bowler: excludes legbyes and byes, includes wides and overstep penalty
            "runs_charged_to_bowler_on_ball": [0, 1, 0, 0, 4, 0, 1],
            "runs_scored_on_ball": [0, 0, 0, 0, 4, 0, 0],
            "is_four": [0, 0, 0, 0, 1, 0, 0],
            "is_six": [0, 0, 0, 0, 0, 0, 0],
            # Delivery 4 (row 4): Bowled wicket (credited to bowler)
            # Delivery 5 (row 5): RunOut (NOT credited to bowler)
            "is_bowler_wicket": [False, False, False, False, False, True, False],
            "dismissal_type": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, "Caught", "RunOut"],
            "bowling_pressure_class": [
                "LOW_PRESSURE", "LOW_PRESSURE", "LOW_PRESSURE", "LOW_PRESSURE",
                "HIGH_PRESSURE", "HIGH_PRESSURE", "HIGH_PRESSURE",
            ],
        })

    def test_byes_and_legbyes_excluded_from_bowler_runs(self, synthetic_bowling_deliveries):
        """Byes and leg-byes must not be charged to the bowler."""
        flags = compute_delivery_bowling_flags(synthetic_bowling_deliveries)
        # Row 2 (legbyes) and Row 3 (byes)
        assert flags.loc[2, "bowler_runs_conceded"] == 0
        assert flags.loc[3, "bowler_runs_conceded"] == 0

    def test_wides_and_noballs_charged_to_bowler(self, synthetic_bowling_deliveries):
        """Wides and no-balls (Overstep) must be debited to the bowler."""
        flags = compute_delivery_bowling_flags(synthetic_bowling_deliveries)
        # Row 1 (wide = 1 run) and Row 6 (Overstep = 1 run)
        assert flags.loc[1, "bowler_runs_conceded"] == 1
        assert flags.loc[6, "bowler_runs_conceded"] == 1

    def test_runouts_excluded_from_bowler_wickets(self, synthetic_bowling_deliveries):
        """Run-outs must not be counted as a bowler's wicket."""
        flags = compute_delivery_bowling_flags(synthetic_bowling_deliveries)
        assert not flags.loc[6, "is_bowler_wicket"]
        # Caught is credited to bowler
        assert flags.loc[5, "is_bowler_wicket"]

    def test_player_bowling_aggregation_accuracy(self, synthetic_bowling_deliveries):
        """Verifies player-level aggregation produces correct economy and overs."""
        player_df = compute_player_bowling_aggregate(synthetic_bowling_deliveries)
        assert 501 in player_df.index
        p501 = player_df.loc[501]

        # Legal balls: Rows 0, 2, 3, 4, 5 = 5 legal balls (Rows 1 & 6 are wide/overstep)
        assert p501["total_legal_balls_bowled"] == 5
        # Overs: 5 / 6 = 0.83 overs
        assert p501["total_overs"] == pytest.approx(0.83, abs=0.01)

        # Runs conceded: 0 (row 0) + 1 (row 1) + 0 (row 2) + 0 (row 3) + 4 (row 4) + 0 (row 5) + 1 (row 6) = 6 runs
        assert p501["total_runs_conceded"] == 6

        # Economy: 6 runs / (5 / 6 overs) = 7.20 rpo
        assert p501["economy_rate"] == pytest.approx(7.20, abs=0.01)

        # Wickets: 1 wicket (Caught at row 5)
        assert p501["total_bowler_wickets"] == 1

        # HP stats: Rows 4 (4 runs, legal), 5 (0 runs, 1 wkt, legal), 6 (1 run, Overstep/illegal)
        # Legal balls in HP: 2 legal balls
        assert p501["hp_legal_balls"] == 2
        # Runs conceded in HP: 4 + 0 + 1 = 5 runs
        assert p501["hp_runs_conceded"] == 5
        # HP economy: 5 runs / (2 / 6 overs) = 15.00 rpo
        assert p501["hp_economy"] == pytest.approx(15.00, abs=0.01)
        assert p501["hp_bowler_wickets"] == 1

