"""Unit tests for batting metrics and cricket scoring semantics in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.performance.batting_metrics import compute_delivery_batting_flags, compute_player_batting_aggregate


class TestBattingMetricsUnit:
    """Verifies cricket laws for batting balls faced, runs, boundaries, and dismissals."""

    @pytest.fixture
    def synthetic_batting_deliveries(self):
        """Constructs synthetic deliveries with tricky cricket edge cases."""
        return pd.DataFrame({
            "match_id": [1, 1, 1, 1, 1, 1, 1, 1],
            "innings": [1, 1, 1, 1, 1, 1, 1, 1],
            "comp_id": [10, 10, 10, 10, 10, 10, 10, 10],
            "striker_id": [101, 101, 101, 101, 101, 102, 101, 101],
            "striker_name": ["Batter A", "Batter A", "Batter A", "Batter A", "Batter A", "Batter B", "Batter A", "Batter A"],
            "non_striker_id": [102, 102, 102, 102, 102, 101, 102, 102],
            "is_legal_ball": [True, False, False, True, True, True, True, True],
            "extras_type": [pd.NA, "wide", "Overstep", "legbyes", "byes", pd.NA, pd.NA, pd.NA],
            "runs_scored_on_ball": [1, 0, 4, 0, 0, 0, 6, 0],
            "is_four": [0, 0, 1, 0, 0, 0, 0, 0],
            "is_six": [0, 0, 0, 0, 0, 0, 1, 0],
            "is_team_wicket": [False, False, False, False, False, True, False, True],
            # Delivery 5 (row 5): non-striker run out (dismissed 101 while 102 is striker)
            # Delivery 7 (row 7): striker dismissed (dismissed 101 while 101 is striker)
            "dismissed_player_id": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 101, pd.NA, 101],
            "batting_pressure_class": [
                "LOW_PRESSURE", "LOW_PRESSURE", "HIGH_PRESSURE", "LOW_PRESSURE",
                "LOW_PRESSURE", "HIGH_PRESSURE", "HIGH_PRESSURE", "HIGH_PRESSURE",
            ],
        })

    def test_wides_do_not_count_as_balls_faced(self, synthetic_batting_deliveries):
        """Wides must not increment balls faced by the batter."""
        flags = compute_delivery_batting_flags(synthetic_batting_deliveries)
        # Ball 1 (row 1) is wide
        assert not flags.loc[1, "is_ball_faced"]

    def test_noballs_count_as_balls_faced(self, synthetic_batting_deliveries):
        """No-balls (Overstep / other) must increment balls faced by the batter."""
        flags = compute_delivery_batting_flags(synthetic_batting_deliveries)
        # Ball 2 (row 2) is Overstep
        assert flags.loc[2, "is_ball_faced"]

    def test_batter_runs_exclude_extras(self, synthetic_batting_deliveries):
        """Byes, leg-byes, and wides give 0 batter runs."""
        flags = compute_delivery_batting_flags(synthetic_batting_deliveries)
        assert flags.loc[1, "batter_runs"] == 0  # wide
        assert flags.loc[3, "batter_runs"] == 0  # legbyes
        assert flags.loc[4, "batter_runs"] == 0  # byes
        assert flags.loc[2, "batter_runs"] == 4  # hit 4 off no-ball

    def test_non_striker_run_out_not_charged_to_striker(self, synthetic_batting_deliveries):
        """When the non-striker is run out, striker must not be credited with a dismissal."""
        flags = compute_delivery_batting_flags(synthetic_batting_deliveries)
        # Row 5: Striker is 102, dismissed is 101 (non-striker).
        # Striker 102 is NOT dismissed
        assert not flags.loc[5, "is_striker_dismissed"]
        # Row 7: Striker is 101, dismissed is 101. Striker 101 IS dismissed
        assert flags.loc[7, "is_striker_dismissed"]

    def test_player_batting_aggregation_accuracy(self, synthetic_batting_deliveries):
        """Verifies player-level aggregation produces correct strike rates and dismissal counts."""
        player_df = compute_player_batting_aggregate(synthetic_batting_deliveries)
        assert 101 in player_df.index
        p101 = player_df.loc[101]

        # Batter A (101): faced rows 0, 2, 3, 4, 6, 7 = 6 balls faced (row 1 wide excluded)
        assert p101["total_balls_faced"] == 6
        # Runs: 1 (row 0) + 4 (row 2) + 0 (row 3) + 0 (row 4) + 6 (row 6) + 0 (row 7) = 11 runs
        assert p101["total_batter_runs"] == 11
        # Strike rate: 11 / 6 * 100 = 183.33
        assert p101["batting_strike_rate"] == pytest.approx(183.33, abs=0.01)
        # Dismissals: only row 7 = 1 dismissal
        assert p101["total_striker_dismissals"] == 1
        assert p101["batting_average"] == pytest.approx(11.0, abs=0.01)

        # High pressure for 101: rows 2 (4 runs, Overstep), 6 (6 runs), 7 (0 runs, dismissed)
        # Total HP balls: 3 balls, 10 runs, 1 dismissal -> HP SR = 10 / 3 * 100 = 333.33
        assert p101["hp_balls_faced"] == 3
        assert p101["hp_batter_runs"] == 10
        assert p101["hp_striker_dismissals"] == 1
        assert p101["hp_strike_rate"] == pytest.approx(333.33, abs=0.01)

