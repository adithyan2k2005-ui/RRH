"""Unit tests for cluster-aware match consistency and downside risk in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.reliability.consistency import compute_match_level_consistency


class TestConsistencyUnit:
    """Verifies match-level clustering, positive match ratios, and downside risk metrics."""

    @pytest.fixture
    def synthetic_match_impacts(self):
        """Constructs synthetic deliveries across multiple matches for two distinct profiles.

        Player 201 (Consistent):
        - Match 1: 10 balls, net impact +5.0 (per ball +0.5)
        - Match 2: 10 balls, net impact +3.0 (per ball +0.3)
        - Match 3: 10 balls, net impact +4.0 (per ball +0.4)
        - Match 4: 10 balls, net impact +2.0 (per ball +0.2)
        Total 4 matches, 100% positive match ratio!

        Player 202 (One-Hit Wonder):
        - Match 1: 20 balls, net impact +30.0 (per ball +1.5, giant outlier match)
        - Match 2: 10 balls, net impact -5.0 (per ball -0.5)
        - Match 3: 10 balls, net impact -8.0 (per ball -0.8)
        - Match 4: 10 balls, net impact -6.0 (per ball -0.6)
        Total 4 matches, only 25% positive match ratio!
        """
        rows = []
        # Player 201
        for m_id, imp in [(1, 0.5), (2, 0.3), (3, 0.4), (4, 0.2)]:
            for _ in range(10):
                rows.append({"match_id": m_id, "striker_id": 201, "impact": imp, "is_hp": True, "faced": True})

        # Player 202
        for _ in range(20):
            rows.append({"match_id": 1, "striker_id": 202, "impact": 1.5, "is_hp": True, "faced": True})
        for m_id, imp in [(2, -0.5), (3, -0.8), (4, -0.6)]:
            for _ in range(10):
                rows.append({"match_id": m_id, "striker_id": 202, "impact": imp, "is_hp": True, "faced": True})

        return pd.DataFrame(rows)

    def test_positive_match_ratio_distinguishes_consistent_from_outlier(self, synthetic_match_impacts):
        """Consistent player achieves 1.0 positive match ratio; one-hit wonder gets 0.25."""
        cons = compute_match_level_consistency(
            synthetic_match_impacts,
            player_id_col="striker_id",
            impact_col="impact",
            pressure_mask=synthetic_match_impacts["is_hp"],
            exposure_mask=synthetic_match_impacts["faced"],
        )

        p201 = cons.loc[201]
        p202 = cons.loc[202]

        assert p201["positive_match_ratio"] == 1.00
        assert p202["positive_match_ratio"] == 0.25

    def test_downside_protection_reflects_tail_risk(self, synthetic_match_impacts):
        """Worst-quartile match impact protects against players with catastrophic downside."""
        cons = compute_match_level_consistency(
            synthetic_match_impacts,
            player_id_col="striker_id",
            impact_col="impact",
            pressure_mask=synthetic_match_impacts["is_hp"],
            exposure_mask=synthetic_match_impacts["faced"],
        )

        # Player 201 worst-quartile match impact is positive (+0.275)
        assert cons.loc[201, "worst_quartile_match_impact"] > 0.0

        # Player 202 worst-quartile match impact is heavily negative (-0.65)
        assert cons.loc[202, "worst_quartile_match_impact"] < 0.0

