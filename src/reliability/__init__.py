"""Player Reliability and Statistical Uncertainty Module for SupeRR Selector Analytics."""

from __future__ import annotations

from .consistency import compute_match_level_consistency
from .eligibility import (
    classify_batter_eligibility,
    classify_bowler_eligibility,
    DEFAULT_BATTER_ELIGIBILITY_CONFIG,
    DEFAULT_BOWLER_ELIGIBILITY_CONFIG,
)
from .reliability_model import (
    compute_batter_reliability_scores,
    compute_bowler_reliability_scores,
    DEFAULT_RELIABILITY_WEIGHTS,
)
from .uncertainty import apply_empirical_bayes_shrinkage, compute_confidence_intervals

__all__ = [
    "classify_batter_eligibility",
    "classify_bowler_eligibility",
    "DEFAULT_BATTER_ELIGIBILITY_CONFIG",
    "DEFAULT_BOWLER_ELIGIBILITY_CONFIG",
    "compute_match_level_consistency",
    "apply_empirical_bayes_shrinkage",
    "compute_confidence_intervals",
    "compute_batter_reliability_scores",
    "compute_bowler_reliability_scores",
    "DEFAULT_RELIABILITY_WEIGHTS",
]

