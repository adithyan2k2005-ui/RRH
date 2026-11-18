"""Pydantic Models and Schemas for SupeRR Intelligence Lab."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
    app_name: str = "SupeRR Intelligence Lab"
    deliveries_loaded: int
    matches_loaded: int
    players_loaded: int
    test_suite_status: str
    verification_status: Optional[str] = "UNVERIFIED"
    last_verified_at: Optional[str] = None


class PhaseStatus(BaseModel):
    phase_number: int
    phase_id: Optional[int] = None
    phase_name: str
    status: str
    description: str
    deliverable: str
    name: Optional[str] = None
    key_output: Optional[str] = None
    verification_timestamp: Optional[str] = None
    test_count: Optional[int] = None
    passed_tests: Optional[int] = None
    failed_tests: Optional[int] = None
    skipped_tests: Optional[int] = None
    warnings: Optional[List[str]] = None
    report_path: Optional[str] = None


class CompetitionStat(BaseModel):
    comp_id: int
    comp_name: str
    matches_count: int
    deliveries_count: int


class PressureDistribution(BaseModel):
    batting: Dict[str, int]
    bowling: Dict[str, int]


class PlayerSummary(BaseModel):
    rank: int
    player_id: int
    player_name: str
    reliability_score: float
    hp_matches: int
    hp_balls: int
    hp_stat_display: str
    impact_per_ball: float
    uplift: float
    consistency: float
    pressure_stat: Optional[str] = None
    key_trait: Optional[str] = None


class OverviewResponse(BaseModel):
    total_matches: int
    total_deliveries: int
    total_players: int
    total_competitions: int
    total_batters_evaluated: int = 0
    total_bowlers_evaluated: int = 0
    eligible_batters: int
    eligible_bowlers: int
    reconstructed_state_coverage: float
    pressure_classification_coverage: float
    pipeline_phases: List[PhaseStatus]
    competitions_distribution: List[CompetitionStat]
    pressure_distribution: PressureDistribution
    top_batter_summary: PlayerSummary
    top_bowler_summary: PlayerSummary
    data_quality_warnings: List[str]
    overall_verification_status: Optional[str] = "UNVERIFIED"
    submission_readiness: Optional[str] = "UNVERIFIED"
    last_verified_at: Optional[str] = None
    total_tests_passed: Optional[int] = None
    total_tests_count: Optional[int] = None


class DatasetMeta(BaseModel):
    dataset_id: str
    name: str
    row_count: int
    column_count: int
    size_bytes: int
    description: str
    columns: List[Dict[str, str]]
    rows_count: Optional[int] = None
    columns_count: Optional[int] = None
    file_size_bytes: Optional[int] = None


class DatasetRecordsResponse(BaseModel):
    dataset_id: str
    total_records: int
    page: int
    page_size: int
    total_pages: int
    columns: List[str] = Field(default_factory=list)
    records: List[Dict[str, Any]]


class CompetitionItem(BaseModel):
    comp_id: int
    comp_name: str
    match_format: str
    matches_count: int
    teams_count: int
    first_match_date: Optional[str] = None
    last_match_date: Optional[str] = None


class MatchSummary(BaseModel):
    match_id: int
    comp_id: int
    comp_name: str
    team1_id: int
    team1_name: str
    team2_id: int
    team2_name: str
    match_date: str
    venue: str
    match_format: str
    stage: str
    knock_out: int
    scheduled_overs: float
    target: Optional[float] = None
    is_target_revised: int = 0
    winner_team_id: Optional[int] = None
    result_margin: Optional[str] = None
    total_deliveries: int
    innings_available: List[int]


class DeliveryState(BaseModel):
    match_id: int
    innings: int
    delivery_seq: int
    overid: int
    over_ball_num: int
    innings_ball_num: int
    striker_id: int
    striker_name: str
    non_striker_id: int
    non_striker_name: str
    bowler_id: int
    bowler_name: str
    is_legal_ball: bool
    runs_scored_on_ball: int
    extras_on_ball: int
    runs_charged_to_bowler: int
    is_team_wicket: bool
    is_bowler_wicket: bool
    dismissal_type: Optional[str] = None
    # Pre-ball situation
    innings_score_before: int
    wickets_lost_before: int
    legal_balls_bowled_before: int
    scheduled_balls_remaining_before: int
    current_run_rate: float
    runs_required_before: Optional[float] = None
    required_run_rate: Optional[float] = None
    # Pressure indices & factors
    batting_pressure_score: float
    bowling_pressure_score: float
    match_tension_score: float
    batting_pressure_class: str
    bowling_pressure_class: str
    wicket_vulnerability: float
    time_pressure: float
    chase_urgency: float
    match_closeness: float
    first_inn_par_deficit: float
    match_stakes_multiplier: float


class PlayerItem(BaseModel):
    player_id: int
    player_name: str
    discipline: str
    rank: Optional[int] = None
    reliability_score: float
    eligibility_status: str
    hp_matches: int
    hp_balls: int
    hp_runs_or_wkts: int
    hp_impact_per_ball: float
    ord_baseline_impact: float
    pressure_uplift: float
    consistency_metric: float
    uncertainty_se: float
    shrinkage_weight: float


class PlayerPerformancePoint(BaseModel):
    match_id: int
    match_date: Optional[str] = None
    opponent_team: Optional[str] = None
    opponent_name: Optional[str] = None
    comp_name: Optional[str] = None
    venue: Optional[str] = None
    balls: int
    hp_balls: Optional[int] = None
    runs_or_wkts: int
    hp_runs_or_wkts: Optional[int] = None
    net_impact: float
    hp_impact: Optional[float] = None
    impact_per_ball: float
    is_positive_contribution: bool


class PlayerDetail(BaseModel):
    summary: PlayerItem
    competitions_count: int
    total_matches: int
    total_balls: int
    total_runs_or_wkts: int
    ordinary_balls: int
    ordinary_runs_or_wkts: int
    ordinary_impact_per_ball: float
    ci_lower_90: float
    ci_upper_90: float
    best_match_impact: float
    worst_match_impact: float
    match_appearances: List[PlayerPerformancePoint]


class PlayerComparisonResponse(BaseModel):
    discipline: str
    player_a: PlayerDetail
    player_b: PlayerDetail
    radar_comparison: Dict[str, Dict[str, float]]
    advantage_analysis: List[str]


class RankingItem(BaseModel):
    rank: int
    player_id: int
    player_name: str
    reliability_score: float
    pressure_matches: int
    pressure_balls: int
    pressure_stat_display: str
    high_pressure_impact: float
    ordinary_performance_baseline: float
    pressure_uplift: float
    consistency_metric: float
    uncertainty_measure: float
    eligibility_status: str


class RankingsResponse(BaseModel):
    discipline: str
    total_candidates: int
    total_eligible: int
    top_10: List[RankingItem]
    near_miss_11_15: List[RankingItem]
    full_rankings: List[RankingItem]


class QualityGateItem(BaseModel):
    gate: str
    description: str
    status: str
    details: str


class MethodologyResponse(BaseModel):
    title: str = "SupeRR Selector Season 2 — Pressure-Based Cricket Player Reliability Analysis"
    version: str = "2.0.0"
    pressure_weights: Dict[str, float]
    reliability_weights: Dict[str, float]
    sensitivity_correlations: Dict[str, Any]
    quality_gates: List[QualityGateItem]
    document_summary: str


class ReportItem(BaseModel):
    report_id: str
    title: str
    category: str
    filename: str
    file_size_bytes: int
    mime_type: str
    description: str
    download_url: str

