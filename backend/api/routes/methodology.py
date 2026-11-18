"""Methodology and Formulations API Routes."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends

from backend.api.schemas.models import MethodologyResponse, QualityGateItem
from backend.api.services.data_loader import AnalyticsDataStore, get_datastore
from src.validation.validate_final_rankings import validate_rankings_checklist

router = APIRouter(prefix="/methodology", tags=["Methodology"])


@router.get("", response_model=MethodologyResponse)
def get_methodology(store: AnalyticsDataStore = Depends(get_datastore)) -> MethodologyResponse:
    """Returns official mathematical formulas, factor weights, and validation results."""
    from backend.api.services.data_loader import OUTPUTS_DIR
    _, results = validate_rankings_checklist(OUTPUTS_DIR)

    q_items = [
        QualityGateItem(
            gate=r["gate"],
            description=r["description"],
            status=r["status"],
            details=r["details"],
        )
        for r in results
    ]

    return MethodologyResponse(
        title="SupeRR Selector Season 2 — Pressure-Based Cricket Player Reliability Analysis",
        version="2.0.0",
        pressure_weights={
            "batting_chase_urgency": 0.35,
            "batting_wicket_vulnerability": 0.30,
            "batting_time_pressure": 0.20,
            "batting_match_closeness": 0.15,
            "bowling_match_closeness": 0.35,
            "bowling_time_pressure": 0.30,
            "bowling_wickets_remaining": 0.20,
            "bowling_chase_urgency_inverted": 0.15,
            "knockout_stakes_multiplier": 1.15,
        },
        reliability_weights={
            "high_pressure_impact": 0.40,
            "pressure_uplift_over_ordinary": 0.25,
            "cluster_aware_match_consistency": 0.20,
            "sample_confidence_weight": 0.15,
        },
        sensitivity_correlations={
            "batting_alt1_impact_heavy": {"spearman_rho": 0.9957, "top10_overlap": "9/10"},
            "batting_alt2_uplift_heavy": {"spearman_rho": 0.9810, "top10_overlap": "9/10"},
            "batting_alt3_consistency_heavy": {"spearman_rho": 0.9852, "top10_overlap": "8/10"},
            "bowling_alt1_impact_heavy": {"spearman_rho": 0.9913, "top10_overlap": "8/10"},
            "bowling_alt2_uplift_heavy": {"spearman_rho": 0.9788, "top10_overlap": "9/10"},
            "bowling_alt3_consistency_heavy": {"spearman_rho": 0.9832, "top10_overlap": "9/10"},
        },
        quality_gates=q_items,
        document_summary=(
            "A 5-stage analytical system measuring cricket performance under high match leverage. "
            "Reconstructs dynamic pre-delivery states with zero future leakage, separates batting difficulty "
            "from bowling urgency, evaluates out-of-fold expectations, and applies Empirical Bayes shrinkage."
        ),
    )

