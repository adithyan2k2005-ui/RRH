"""Unit tests for delivery order reconstruction in SupeRR Selector Analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.delivery_order import validate_and_sort_deliveries


class TestDeliveryOrderUnit:
    """Unit tests using synthetic cricket sequences to verify delivery ordering logic."""

    def test_normal_consecutive_deliveries_ordering(self):
        """Verify standard 6-ball over is sequenced sequentially from 1 to 6."""
        data = pd.DataFrame({
            "match_id": [1] * 6,
            "innings": [1] * 6,
            "overid": [1] * 6,
            "over_ball_num": [1, 2, 3, 4, 5, 6],
            "innings_ball_num": [1, 2, 3, 4, 5, 6],
        })

        sorted_df, anomalies = validate_and_sort_deliveries(data)

        assert len(sorted_df) == 6
        assert len(anomalies) == 0
        assert list(sorted_df["delivery_seq"]) == [1, 2, 3, 4, 5, 6]

    def test_deliveries_with_wides_and_no_balls(self):
        """Verify delivery sequence advances sequentially across wides and no-balls."""
        # Over with wide on ball 2 and no-ball on ball 4 (8 deliveries total)
        data = pd.DataFrame({
            "match_id": [10] * 8,
            "innings": [1] * 8,
            "overid": [1] * 8,
            "over_ball_num": [1, 2, 3, 4, 5, 6, 7, 8],
            "innings_ball_num": [1, 2, 3, 4, 5, 6, 7, 8],
        })

        sorted_df, anomalies = validate_and_sort_deliveries(data)

        assert len(sorted_df) == 8
        assert len(anomalies) == 0
        assert list(sorted_df["delivery_seq"]) == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_shuffled_deliveries_reordered_chronologically(self):
        """Verify that shuffled input deliveries are sorted deterministically."""
        data = pd.DataFrame({
            "match_id": [1, 1, 1, 1],
            "innings": [1, 1, 1, 1],
            "overid": [2, 1, 1, 2],
            "over_ball_num": [1, 2, 1, 2],
            "innings_ball_num": [7, 2, 1, 8],
        })

        sorted_df, _ = validate_and_sort_deliveries(data)

        # Expected order: (over 1 ball 1), (over 1 ball 2), (over 2 ball 1), (over 2 ball 2)
        assert list(sorted_df["overid"]) == [1, 1, 2, 2]
        assert list(sorted_df["over_ball_num"]) == [1, 2, 1, 2]
        assert list(sorted_df["delivery_seq"]) == [1, 2, 3, 4]

    def test_detect_duplicate_delivery_identifiers(self):
        """Verify that duplicate (match_id, innings, overid, over_ball_num) keys are flagged."""
        data = pd.DataFrame({
            "match_id": [1, 1, 1],
            "innings": [1, 1, 1],
            "overid": [1, 1, 1],
            "over_ball_num": [1, 1, 2],  # Duplicate on ball 1
            "innings_ball_num": [1, 1, 2],
        })

        sorted_df, anomalies = validate_and_sort_deliveries(data)

        assert len(anomalies) > 0

    def test_missing_required_keys_raises_key_error(self):
        """Verify KeyError is raised if a required ordering key is missing."""
        invalid_data = pd.DataFrame({
            "match_id": [1, 1],
            "innings": [1, 1],
            # Missing overid, over_ball_num
        })

        with pytest.raises(KeyError, match="Missing required ordering key"):
            validate_and_sort_deliveries(invalid_data)

