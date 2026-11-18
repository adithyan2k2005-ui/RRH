"""Unit tests for player baselines and pressure uplift in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.performance.player_baselines import compute_player_pressure_vs_ordinary


class TestPlayerBaselinesUnit:
    """Verifies within-player ordinary baselines, pressure uplift, and prior fallback."""

    @pytest.fixture
    def synthetic_residuals_df(self):
        """Constructs synthetic batting deliveries with HP and ordinary residuals."""
        # Batter 101: 20 HP balls (combined impact +1.0 per ball), 30 Ord balls (combined impact +0.2 per ball)
        # Expected uplift: 1.0 - 0.2 = +0.80
        # Batter 102: 20 HP balls (combined impact -0.5 per ball), 30 Ord balls (combined impact +0.5 per ball)
        # Expected uplift: -0.5 - 0.5 = -1.00
        # Batter 103: 20 HP balls (impact +0.4 per ball), 5 Ord balls (insufficient ord -> population prior)
        b101_hp = pd.DataFrame({
            "match_id": [1] * 20, "striker_id": [101] * 20, "striker_name": ["Player A"] * 20,
            "batting_pressure_class": ["HIGH_PRESSURE"] * 20, "is_ball_faced": [True] * 20,
            "batting_run_impact": [1.0] * 20, "batting_combined_impact": [1.0] * 20,
        })
        b101_ord = pd.DataFrame({
            "match_id": [2] * 30, "striker_id": [101] * 30, "striker_name": ["Player A"] * 30,
            "batting_pressure_class": ["LOW_PRESSURE"] * 30, "is_ball_faced": [True] * 30,
            "batting_run_impact": [0.2] * 30, "batting_combined_impact": [0.2] * 30,
        })

        b102_hp = pd.DataFrame({
            "match_id": [3] * 20, "striker_id": [102] * 20, "striker_name": ["Player B"] * 20,
            "batting_pressure_class": ["HIGH_PRESSURE"] * 20, "is_ball_faced": [True] * 20,
            "batting_run_impact": [-0.5] * 20, "batting_combined_impact": [-0.5] * 20,
        })
        b102_ord = pd.DataFrame({
            "match_id": [4] * 30, "striker_id": [102] * 30, "striker_name": ["Player B"] * 30,
            "batting_pressure_class": ["LOW_PRESSURE"] * 30, "is_ball_faced": [True] * 30,
            "batting_run_impact": [0.5] * 30, "batting_combined_impact": [0.5] * 30,
        })

        b103_hp = pd.DataFrame({
            "match_id": [5] * 20, "striker_id": [103] * 20, "striker_name": ["Player C"] * 20,
            "batting_pressure_class": ["HIGH_PRESSURE"] * 20, "is_ball_faced": [True] * 20,
            "batting_run_impact": [0.4] * 20, "batting_combined_impact": [0.4] * 20,
        })
        b103_ord = pd.DataFrame({
            "match_id": [6] * 5, "striker_id": [103] * 5, "striker_name": ["Player C"] * 5,
            "batting_pressure_class": ["LOW_PRESSURE"] * 5, "is_ball_faced": [True] * 5,
            "batting_run_impact": [1.5] * 5, "batting_combined_impact": [1.5] * 5,
        })

        bat_deliv = pd.concat([b101_hp, b101_ord, b102_hp, b102_ord, b103_hp, b103_ord], ignore_index=True)

        # Minimal dummy bowling deliveries to satisfy function signature
        bowl_deliv = pd.DataFrame({
            "match_id": [1, 2], "bowler_id": [501, 501], "bowler_name": ["Bowler X", "Bowler X"],
            "bowling_pressure_class": ["HIGH_PRESSURE", "LOW_PRESSURE"], "is_legal_ball": [True, True],
            "bowling_run_impact": [0.5, 0.1], "bowling_combined_impact": [0.5, 0.1],
        })

        return bat_deliv, bowl_deliv

    def test_pressure_uplift_calculation(self, synthetic_residuals_df):
        """Verifies uplift is positive for clutch improvers and negative for pressure chokers."""
        bat_deliv, bowl_deliv = synthetic_residuals_df
        b_base, _ = compute_player_pressure_vs_ordinary(bat_deliv, bowl_deliv)

        # Player A: HP impact 1.0, Ord impact 0.2 -> uplift = +0.80
        assert b_base.loc[101, "batting_pressure_uplift"] == pytest.approx(0.80, abs=0.01)

        # Player B: HP impact -0.5, Ord impact 0.5 -> uplift = -1.00
        assert b_base.loc[102, "batting_pressure_uplift"] == pytest.approx(-1.00, abs=0.01)

    def test_insufficient_ordinary_sample_uses_population_prior(self, synthetic_residuals_df):
        """Players with fewer than 15 ordinary balls use population prior for baseline."""
        bat_deliv, bowl_deliv = synthetic_residuals_df
        b_base, _ = compute_player_pressure_vs_ordinary(bat_deliv, bowl_deliv)

        # Player C only has 5 ordinary balls (< 15)
        # Population ord mean from data:
        # Total ord balls = 30*0.2 + 30*0.5 + 5*1.5 = 6.0 + 15.0 + 7.5 = 28.5 / 65 balls = 0.4385
        # Uplift = 0.4 - 0.4385 = -0.0385 (instead of 0.4 - 1.5 = -1.1)
        assert b_base.loc[103, "batting_pressure_uplift"] == pytest.approx(0.4 - (28.5 / 65), abs=0.02)

