"""Overview, Pipeline Analytics, and Verification Routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException

from backend.api.schemas.models import (
    CompetitionStat,
    OverviewResponse,
    PhaseStatus,
    PlayerSummary,
    PressureDistribution,
)
from backend.api.services.data_loader import AnalyticsDataStore, REPORTS_DIR, get_datastore

router = APIRouter(tags=["Overview"])

MANIFEST_PATH = REPORTS_DIR / "verification_manifest.json"


def load_verification_manifest() -> Optional[Dict[str, Any]]:
    """Loads reports/verification_manifest.json safely with error handling."""
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "phases" in data:
            return data
    except Exception:
        pass
    return None


@router.get("/overview", response_model=OverviewResponse)
def get_overview(store: AnalyticsDataStore = Depends(get_datastore)) -> OverviewResponse:
    """Returns high-level summary KPIs, distributions, and dynamic verification statuses."""
    # Competition stats
    comp_counts = store.matches_df["comp_id"].value_counts().to_dict()
    comp_delivs = store.pressure_states_df["comp_id"].value_counts().to_dict()

    comp_stats = []
    for comp_id, match_cnt in comp_counts.items():
        comp_name = store.get_comp_name(int(comp_id))
        deliv_cnt = comp_delivs.get(comp_id, 0)
        comp_stats.append(CompetitionStat(
            comp_id=int(comp_id),
            comp_name=comp_name,
            matches_count=int(match_cnt),
            deliveries_count=int(deliv_cnt),
        ))

    # Pressure distribution
    bat_press = store.pressure_states_df["batting_pressure_class"].value_counts().to_dict()
    bowl_press = store.pressure_states_df["bowling_pressure_class"].value_counts().to_dict()

    # Top batter & bowler summaries
    top_b = store.top_10_batters_df.iloc[0]
    top_bw = store.top_10_bowlers_df.iloc[0]

    top_b_summary = PlayerSummary(
        rank=int(top_b["rank"]),
        player_id=int(top_b["player_id"]),
        player_name=str(top_b["player_name"]),
        reliability_score=float(top_b["reliability_score"]),
        hp_matches=int(top_b["pressure_matches"]),
        hp_balls=int(top_b["pressure_balls_faced"]),
        hp_stat_display=f"{int(top_b['pressure_runs'])} Runs ({int(top_b['pressure_balls_faced'])} HP balls)",
        impact_per_ball=float(top_b["high_pressure_impact"]),
        uplift=float(top_b["pressure_uplift"]),
        consistency=float(top_b["consistency_metric"]),
        pressure_stat=f"{int(top_b['pressure_runs'])} Runs ({int(top_b['pressure_balls_faced'])} HP balls)",
        key_trait=f"Uplift: {float(top_b['pressure_uplift']):+.3f}/ball • Consistency: {float(top_b['consistency_metric']) * 100:.1f}%",
    )

    top_bw_summary = PlayerSummary(
        rank=int(top_bw["rank"]),
        player_id=int(top_bw["player_id"]),
        player_name=str(top_bw["player_name"]),
        reliability_score=float(top_bw["reliability_score"]),
        hp_matches=int(top_bw["pressure_matches"]),
        hp_balls=int(top_bw["pressure_legal_balls"]),
        hp_stat_display=f"{int(top_bw['pressure_wickets'])} Wickets ({int(top_bw['pressure_runs_conceded'])} Runs)",
        impact_per_ball=float(top_bw["high_pressure_impact"]),
        uplift=float(top_bw["pressure_uplift"]),
        consistency=float(top_bw["consistency_metric"]),
        pressure_stat=f"{int(top_bw['pressure_wickets'])} Wickets ({int(top_bw['pressure_runs_conceded'])} Runs)",
        key_trait=f"Uplift: {float(top_bw['pressure_uplift']):+.3f}/ball • Consistency: {float(top_bw['consistency_metric']) * 100:.1f}%",
    )

    # Dynamic pipeline phases from verification manifest
    manifest = load_verification_manifest()

    phase_metadata = [
        (1, "Ingestion & Data Quality", "Relational ingestion of 6 tables, referential integrity check, encoding validation.", "data/processed/*.parquet (6 relational tables)", "reports/phase1/data_quality_report.md"),
        (2, "Match-State Reconstruction", "Chronological delivery ordering, legal ball flags, zero future data leakage pre-ball state.", "data/processed/match_states.parquet (200,999 rows)", "reports/phase2/reconstruction_verification.md"),
        (3, "Pressure Detection Engine", "Dual asymmetric pressure modeling (0-100) separating batting difficulty from bowling urgency.", "data/processed/pressure_states.parquet (77 columns)", "reports/phase3/pressure_model_report.md"),
        (4, "Performance & Reliability Scoring", "Hierarchical leave-one-match-out baselines, Empirical Bayes shrinkage, cluster consistency.", "player_batting_metrics & player_bowling_metrics.parquet", "reports/phase4/reliability_scoring_report.md"),
        (5, "Top-10 Rankings & Verification", "Deterministic tie-breaking, micro-reconciliation, leave-best-match-out robustness.", "outputs/top_10_batters.csv & outputs/top_10_bowlers.csv", "reports/phase5/ranking_evidence.md"),
        (6, "Methodology Report & Packaging", "Official 8-page publication PDF, 17 mandatory sections, submission ZIP archive.", "submission/methodology_report.pdf & submission archive", "submission/submission_validation.md"),
    ]

    pipeline_phases = []
    for p_num, p_name, p_desc, p_deliv, p_rep in phase_metadata:
        if manifest and "phases" in manifest and str(p_num) in manifest["phases"]:
            p_data = manifest["phases"][str(p_num)]
            phase_status = p_data.get("status", "UNVERIFIED")
            ts = p_data.get("execution_timestamp")
            t_cnt = p_data.get("test_count", 0)
            p_pass = p_data.get("passed_tests", 0)
            p_fail = p_data.get("failed_tests", 0)
            p_skip = p_data.get("skipped_tests", 0)
            p_warn = p_data.get("warnings", [])
            rep_path = p_data.get("report_path", p_rep)
        else:
            phase_status = "UNVERIFIED"
            ts = None
            t_cnt = 0
            p_pass = 0
            p_fail = 0
            p_skip = 0
            p_warn = ["Verification manifest missing or unexecuted. Run scripts/verify_project.py."]
            rep_path = p_rep

        pipeline_phases.append(PhaseStatus(
            phase_number=p_num,
            phase_id=p_num,
            phase_name=p_name,
            name=p_name,
            status=phase_status,
            description=p_desc,
            deliverable=p_deliv,
            key_output=p_deliv,
            verification_timestamp=ts,
            test_count=t_cnt,
            passed_tests=p_pass,
            failed_tests=p_fail,
            skipped_tests=p_skip,
            warnings=p_warn,
            report_path=rep_path,
        ))

    warnings = [
        "19 raw speed gun outliers (e.g. 19.8 km/h or 220 km/h) excluded from pressure features to protect model integrity.",
        "34 weather-affected matches with revised DLS targets accounted for with official adjusted par calculations.",
        "6 tied fixtures resulting in 12 Super Over innings reconstructed with zero-leakage state tracking.",
        "16 weather-abandoned matches recorded 0 deliveries; preserved as valid fixture metadata.",
    ]

    overall_v = manifest.get("overall_status", "UNVERIFIED") if manifest else "UNVERIFIED"
    sub_readiness = manifest.get("submission_readiness", "UNVERIFIED") if manifest else "UNVERIFIED"
    last_v = manifest.get("generated_at") if manifest else None
    t_pass = manifest.get("summary", {}).get("passed_tests") if manifest else None
    t_total = manifest.get("summary", {}).get("total_tests") if manifest else None

    return OverviewResponse(
        total_matches=len(store.matches_df),
        total_deliveries=len(store.pressure_states_df),
        total_players=len(store.player_batting_df) + len(store.player_bowling_df),
        total_competitions=len(store.competitions_df),
        total_batters_evaluated=len(store.player_batting_df),
        total_bowlers_evaluated=len(store.player_bowling_df),
        eligible_batters=int((store.player_batting_df["eligibility_status"] == "ELIGIBLE").sum()),
        eligible_bowlers=int((store.player_bowling_df["eligibility_status"] == "ELIGIBLE").sum()),
        reconstructed_state_coverage=100.0,
        pressure_classification_coverage=100.0,
        pipeline_phases=pipeline_phases,
        competitions_distribution=comp_stats,
        pressure_distribution=PressureDistribution(
            batting={k: int(v) for k, v in bat_press.items()},
            bowling={k: int(v) for k, v in bowl_press.items()},
        ),
        top_batter_summary=top_b_summary,
        top_bowler_summary=top_bw_summary,
        data_quality_warnings=warnings,
        overall_verification_status=overall_v,
        submission_readiness=sub_readiness,
        last_verified_at=last_v,
        total_tests_passed=t_pass,
        total_tests_count=t_total,
    )


@router.get("/pipeline/status", response_model=List[PhaseStatus])
def get_pipeline_status(store: AnalyticsDataStore = Depends(get_datastore)) -> List[PhaseStatus]:
    """Returns the verified execution status of all project phases."""
    overview = get_overview(store)
    return overview.pipeline_phases


@router.get("/verification/manifest")
def get_verification_manifest() -> Dict[str, Any]:
    """Returns the authoritative verification manifest."""
    manifest = load_verification_manifest()
    if not manifest:
        return {
            "overall_status": "UNVERIFIED",
            "submission_readiness": "UNVERIFIED",
            "website_readiness": "UNVERIFIED",
            "message": "Verification manifest missing. Run 'python scripts/verify_project.py' to generate.",
        }
    return manifest


@router.get("/verification/submission-gates")
def get_submission_gates() -> Dict[str, Any]:
    """Returns the official submission readiness gates."""
    manifest = load_verification_manifest()
    if not manifest or "submission_gates" not in manifest:
        raise HTTPException(
            status_code=404,
            detail="Submission gates unverified. Run scripts/verify_project.py first."
        )
    return {
        "submission_readiness": manifest.get("submission_readiness", "UNVERIFIED"),
        "gates": manifest["submission_gates"],
        "generated_at": manifest.get("generated_at"),
    }
