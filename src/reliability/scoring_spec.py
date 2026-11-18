"""Authoritative Scoring Specification for SupeRR Selector Analytics.

Central single source of truth for:
- Reliability component weights
- Shrinkage parameters
- Logistic scaling parameters
- Match consistency weighting
- Eligibility qualification criteria
- Mathematical formula descriptions (for reports and documentation)
"""

from __future__ import annotations

from typing import Any, Dict

# Component weights in composite reliability score
RELIABILITY_WEIGHTS: Dict[str, float] = {
    "weight_impact": 0.40,
    "weight_uplift": 0.25,
    "weight_consistency": 0.20,
    "weight_confidence": 0.15,
}

# Empirical Bayes noise scale parameters (sample units)
SHRINKAGE_K0: Dict[str, float] = {
    "batting": 20.0,  # balls faced
    "bowling": 24.0,  # legal balls bowled
}

# Logistic sigmoid scaling slope constants
LOGISTIC_SLOPES: Dict[str, float] = {
    "impact": 3.0,  # S_impact = 100 / (1 + exp(-3.0 * shrunk_impact))
    "uplift": 3.5,  # S_uplift = 100 / (1 + exp(-3.5 * uplift))
}

# Match-level consistency weights
CONSISTENCY_WEIGHTS: Dict[str, float] = {
    "positive_match_ratio": 0.60,
    "downside_protection": 0.40,
}

# Qualification thresholds for sample-size adequacy
ELIGIBILITY_THRESHOLDS: Dict[str, Dict[str, int]] = {
    "batting": {
        "min_hp_balls": 20,
        "min_hp_matches": 3,
        "min_ord_balls": 25,
    },
    "bowling": {
        "min_hp_balls": 24,
        "min_hp_matches": 3,
        "min_ord_balls": 30,
    },
}

# Mathematical representation strings for documentation & reports
FORMULA_STRINGS: Dict[str, str] = {
    "composite_math": (
        "R = 0.40 \\cdot S_{\\text{impact}} + 0.25 \\cdot S_{\\text{uplift}} + "
        "0.20 \\cdot S_{\\text{consistency}} + 0.15 \\cdot S_{\\text{confidence}}"
    ),
    "composite_html": (
        "Reliability Score = 0.40 &times; S<sub>impact</sub> + 0.25 &times; S<sub>uplift</sub> + "
        "0.20 &times; S<sub>consistency</sub> + 0.15 &times; S<sub>confidence</sub>"
    ),
    "s_impact_math": "S_{\\text{impact}} = \\frac{100}{1 + e^{-3.0 \\cdot \\hat{\\theta}_{\\text{shrunk}}}}",
    "s_uplift_math": "S_{\\text{uplift}} = \\frac{100}{1 + e^{-3.5 \\cdot \\text{Uplift}}}",
    "s_consistency_math": (
        "S_{\\text{consistency}} = 100 \\times (0.60 \\cdot \\text{Positive Match Ratio} + "
        "0.40 \\cdot \\text{Downside Protection})"
    ),
    "s_confidence_math": "S_{\\text{confidence}} = 100 \\times w_i \\times \\frac{1}{1 + \\text{SE}_i}",
}
