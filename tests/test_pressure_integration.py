"""Integration tests for Phase 3 pressure engine on full real-world tournament dataset."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.pressure_baselines import ContextualBaselines
from src.features.pressure_features import calculate_pressure_features
from src.features.pressure_model import compute_pressure_scores
from src.features.pressure_thresholds import classify_pressure


@pytest.fixture(scope="module")
def pressure_data():
    """Loads actual generated Phase 3 pressure states dataset."""
    p = PROJECT_ROOT / "data" / "processed" / "pressure_states.parquet"
    assert p.exists(), f"Missing required Phase 3 output: {p}"
    return pd.read_parquet(p)


class TestPressureIntegration:
    """End-to-end integration tests on actual tournament match data."""

    def test_full_dataset_row_and_column_integrity(self, pressure_data):
        """Verify pressure_states.parquet preserves all 200,999 deliveries and adds required features."""
        assert len(pressure_data) == 200999

        required_features = [
            "baseline_expected_rate",
            "wicket_vulnerability",
            "time_pressure",
            "batting_pressure_score",
            "bowling_pressure_score",
            "match_tension_score",
            "batting_pressure_class",
            "bowling_pressure_class",
            "pressure_model_version",
        ]
        for feat in required_features:
            assert feat in pressure_data.columns, f"Missing feature: {feat}"

    def test_scores_bounds_and_no_nans(self, pressure_data):
        """Verify all pressure scores are strictly in [0, 100] and contain no NaNs."""
        bat = pressure_data["batting_pressure_score"]
        bowl = pressure_data["bowling_pressure_score"]
        tension = pressure_data["match_tension_score"]

        assert bat.notnull().all(), "Found NaNs in batting_pressure_score"
        assert bowl.notnull().all(), "Found NaNs in bowling_pressure_score"
        assert tension.notnull().all(), "Found NaNs in match_tension_score"

        assert (bat >= 0.0).all() and (bat <= 100.0).all()
        assert (bowl >= 0.0).all() and (bowl <= 100.0).all()
        assert (tension >= 0.0).all() and (tension <= 100.0).all()

    def test_deterministic_scoring(self, pressure_data):
        """Verify running scoring twice on the same input produces bitwise identical results."""
        states_sample = pressure_data.sample(n=1000, random_state=42)

        baselines = ContextualBaselines.fit_from_data(pressure_data)
        comp1 = calculate_pressure_features(states_sample, baselines)
        score1 = compute_pressure_scores(states_sample, comp1)

        comp2 = calculate_pressure_features(states_sample, baselines)
        score2 = compute_pressure_scores(states_sample, comp2)

        pd.testing.assert_frame_equal(score1, score2)

    def test_classification_categories_valid(self, pressure_data):
        """Verify only allowed categorical pressure regimes appear."""
        valid_classes = {"LOW_PRESSURE", "MEDIUM_PRESSURE", "HIGH_PRESSURE", "UNDETERMINED"}

        bat_classes = set(pressure_data["batting_pressure_class"].unique())
        bowl_classes = set(pressure_data["bowling_pressure_class"].unique())

        assert bat_classes.issubset(valid_classes)
        assert bowl_classes.issubset(valid_classes)

        # High pressure must represent a meaningful subset (e.g. 5% - 30%)
        bat_high_pct = (pressure_data["batting_pressure_class"] == "HIGH_PRESSURE").sum() / len(pressure_data)
        assert 0.05 <= bat_high_pct <= 0.30

    def test_phase3_reports_and_artifacts_exist(self):
        """Verify all required markdown reports and CSV artifacts were generated."""
        rep_dir = PROJECT_ROOT / "reports" / "phase3"
        assert (rep_dir / "pressure_methodology.md").exists()
        assert (rep_dir / "pressure_validation.md").exists()
        assert (rep_dir / "pressure_distribution.csv").exists()
        assert (rep_dir / "pressure_sensitivity.csv").exists()
        assert (rep_dir / "pressure_examples.csv").exists()

