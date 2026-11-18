/**
 * Type-safe API Client for SupeRR Intelligence Lab backend.
 */

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  deliveries_loaded: number;
  matches_loaded: number;
  players_loaded: number;
  test_suite_status: string;
  verification_status?: string;
  last_verified_at?: string;
}

export interface CompetitionStat {
  comp_id: number;
  comp_name: string;
  matches_count: number;
  deliveries_count: number;
}

export interface PipelinePhase {
  phase_number: number;
  phase_name: string;
  status: string;
  description: string;
  deliverable: string;
  name?: string;
  key_output?: string;
  verified_metric?: string;
  verification_timestamp?: string;
  test_count?: number;
  passed_tests?: number;
  failed_tests?: number;
  skipped_tests?: number;
  warnings?: string[];
  report_path?: string;
}

export interface PlayerTopSummary {
  rank: number;
  player_id: number;
  player_name: string;
  reliability_score: number;
  hp_matches: number;
  hp_balls: number;
  hp_stat_display: string;
  impact_per_ball: number;
  uplift: number;
  consistency: number;
  pressure_stat?: string;
  key_trait?: string;
}

export interface OverviewResponse {
  app_name?: string;
  version?: string;
  total_matches: number;
  total_deliveries: number;
  total_players: number;
  total_competitions: number;
  total_batters_evaluated: number;
  total_bowlers_evaluated: number;
  eligible_batters: number;
  eligible_bowlers: number;
  reconstructed_state_coverage: number;
  pressure_classification_coverage: number;
  pipeline_phases: PipelinePhase[];
  competitions_distribution: CompetitionStat[];
  pressure_distribution: {
    batting: Record<string, number>;
    bowling: Record<string, number>;
  };
  top_batter_summary: PlayerTopSummary;
  top_bowler_summary: PlayerTopSummary;
  data_quality_warnings: string[];
  overall_verification_status?: string;
  submission_readiness?: string;
  last_verified_at?: string;
  total_tests_passed?: number;
  total_tests_count?: number;
}

export interface DatasetColumnMeta {
  name: string;
  type: string;
}

export interface DatasetMeta {
  dataset_id: string;
  name: string;
  description: string;
  format?: string;
  rows_count?: number;
  row_count?: number;
  columns_count?: number;
  column_count?: number;
  file_size_bytes?: number;
  size_bytes?: number;
  columns: (string | DatasetColumnMeta)[];
}

export interface DatasetRecordsResponse {
  dataset_id: string;
  name?: string;
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  columns?: string[];
  records: Record<string, any>[];
}

export interface CompetitionItem {
  comp_id: number;
  comp_name: string;
  match_format: string;
  matches_count: number;
  teams_count: number;
  first_match_date?: string | null;
  last_match_date?: string | null;
}

export interface MatchSummary {
  match_id: number;
  comp_id: number;
  comp_name: string;
  team1_id: number;
  team1_name: string;
  team2_id: number;
  team2_name: string;
  match_date: string;
  venue: string;
  match_format: string;
  stage: string;
  knock_out: number;
  scheduled_overs: number;
  target?: number | null;
  is_target_revised: number;
  winner_team_id?: number | null;
  result_margin?: string | null;
  total_deliveries: number;
  innings_available: number[];
}

export interface DeliveryState {
  match_id: number;
  innings: number;
  delivery_seq: number;
  overid: number;
  over_ball_num: number;
  innings_ball_num: number;
  striker_id: number;
  striker_name: string;
  non_striker_id: number;
  non_striker_name: string;
  bowler_id: number;
  bowler_name: string;
  is_legal_ball: boolean;
  runs_scored_on_ball: number;
  extras_on_ball: number;
  runs_charged_to_bowler: number;
  is_team_wicket: boolean;
  is_bowler_wicket: boolean;
  dismissal_type?: string | null;
  innings_score_before: number;
  wickets_lost_before: number;
  legal_balls_bowled_before: number;
  scheduled_balls_remaining_before: number;
  current_run_rate: number;
  runs_required_before?: number | null;
  required_run_rate?: number | null;
  batting_pressure_score: number;
  bowling_pressure_score: number;
  match_tension_score: number;
  batting_pressure_class: string;
  bowling_pressure_class: string;
  wicket_vulnerability: number;
  time_pressure: number;
  chase_urgency: number;
  match_closeness: number;
  first_inn_par_deficit: number;
  match_stakes_multiplier: number;
}

export interface PressureTimelinePoint {
  delivery_seq: number;
  innings: number;
  over_label: string;
  batting_pressure: number;
  bowling_pressure: number;
  match_tension: number;
  striker: string;
  bowler: string;
  runs: number;
  is_wicket: boolean;
  score_before: string;
}

export interface MatchPressureTimeline {
  match_id: number;
  innings?: number | null;
  total_deliveries: number;
  pressure_timeline: PressureTimelinePoint[];
}

export interface PlayerItem {
  player_id: number;
  player_name: string;
  discipline: string;
  rank?: number | null;
  reliability_score: number;
  hp_impact_per_ball: number;
  ord_baseline_impact: number;
  pressure_uplift: number;
  consistency_metric: number;
  uncertainty_se: number;
  shrinkage_weight: number;
  total_deliveries: number;
  hp_deliveries: number;
  matches_count: number;
  eligibility_status: string;
}

export interface PlayerPerformancePoint {
  match_id: number;
  match_date: string;
  comp_name?: string;
  opponent_name?: string;
  opponent_team?: string;
  venue?: string;
  hp_balls?: number;
  balls?: number;
  hp_runs_or_wkts?: number;
  runs_or_wkts?: number;
  hp_impact?: number;
  net_impact?: number;
  impact_per_ball?: number;
  is_positive_contribution?: boolean;
}

export interface PlayerDetail {
  summary: PlayerItem;
  competitions_count: number;
  total_matches: number;
  total_balls: number;
  total_runs_or_wkts: number;
  ordinary_balls: number;
  ordinary_runs_or_wkts: number;
  ordinary_impact_per_ball: number;
  ci_lower_90: number;
  ci_upper_90: number;
  best_match_impact: number;
  worst_match_impact: number;
  match_appearances: PlayerPerformancePoint[];
}

export interface PlayerComparisonResponse {
  discipline: string;
  player_a: PlayerDetail;
  player_b: PlayerDetail;
  radar_comparison: Record<string, Record<string, number>>;
  advantage_analysis: string[];
}

export interface RankingItem {
  rank: number;
  player_id: number;
  player_name: string;
  reliability_score: number;
  pressure_matches: number;
  pressure_balls: number;
  pressure_stat_display: string;
  high_pressure_impact: number;
  ordinary_performance_baseline: number;
  pressure_uplift: number;
  consistency_metric: number;
  uncertainty_measure: number;
  eligibility_status: string;
}

export interface RankingsResponse {
  discipline: string;
  total_candidates: number;
  total_eligible: number;
  top_10: RankingItem[];
  near_miss_11_15: RankingItem[];
  full_rankings: RankingItem[];
}

export interface QualityGateItem {
  gate: string;
  description: string;
  status: string;
  details: string;
}

export interface MethodologyResponse {
  title: string;
  version: string;
  pressure_weights: Record<string, number>;
  reliability_weights: Record<string, number>;
  sensitivity_correlations: Record<string, any>;
  quality_gates: QualityGateItem[];
  document_summary: string;
}

export interface ReportItem {
  report_id: string;
  title: string;
  category: string;
  filename: string;
  file_size_bytes: number;
  mime_type: string;
  description: string;
}

const API_BASE = '/api';

async function fetchJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`API error ${resp.status} on ${url}: ${errorText}`);
  }
  return resp.json();
}

/**
 * Runtime schema validator for Overview payload.
 * Guarantees that contract mismatches fail with actionable diagnostic messages
 * rather than allowing invalid data shapes to cause chart rendering crashes.
 */
export function validateOverviewResponse(data: any): OverviewResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('API Contract Violation: /api/overview returned a non-object payload.');
  }
  if (!Array.isArray(data.competitions_distribution)) {
    throw new Error(
      `API Contract Violation: /api/overview expected 'competitions_distribution' to be an Array, received ${typeof data.competitions_distribution}.`
    );
  }
  if (!Array.isArray(data.pipeline_phases)) {
    throw new Error(
      `API Contract Violation: /api/overview expected 'pipeline_phases' to be an Array, received ${typeof data.pipeline_phases}.`
    );
  }
  if (!data.pressure_distribution || typeof data.pressure_distribution !== 'object') {
    throw new Error(
      `API Contract Violation: /api/overview expected 'pressure_distribution' to be an object.`
    );
  }
  if (!data.top_batter_summary || typeof data.top_batter_summary !== 'object') {
    throw new Error(
      `API Contract Violation: /api/overview expected 'top_batter_summary' object.`
    );
  }
  if (!data.top_bowler_summary || typeof data.top_bowler_summary !== 'object') {
    throw new Error(
      `API Contract Violation: /api/overview expected 'top_bowler_summary' object.`
    );
  }
  return data as OverviewResponse;
}

export const api = {
  getHealth: () => fetchJson<HealthResponse>(`${API_BASE}/health`),
  getOverview: async (): Promise<OverviewResponse> => {
    const raw = await fetchJson<any>(`${API_BASE}/overview`);
    return validateOverviewResponse(raw);
  },
  getPipelineStatus: () => fetchJson<PipelinePhase[]>(`${API_BASE}/pipeline/status`),

  // Datasets
  getDatasets: () => fetchJson<DatasetMeta[]>(`${API_BASE}/datasets`),
  getDatasetRecords: (datasetId: string, page = 1, pageSize = 20, search?: string, sortBy?: string, sortOrder = 'asc') => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      sort_order: sortOrder,
    });
    if (search) params.set('search', search);
    if (sortBy) params.set('sort_by', sortBy);
    return fetchJson<DatasetRecordsResponse>(`${API_BASE}/datasets/${datasetId}/records?${params.toString()}`);
  },
  getDatasetExportUrl: (datasetId: string) => `${API_BASE}/datasets/${datasetId}/export`,

  // Competitions & Matches
  getCompetitions: () => fetchJson<CompetitionItem[]>(`${API_BASE}/competitions`),
  getMatches: (compId?: number, stage?: string, knockout?: number, search?: string, limit = 100) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (compId !== undefined) params.set('comp_id', String(compId));
    if (stage) params.set('stage', stage);
    if (knockout !== undefined) params.set('knock_out', String(knockout));
    if (search) params.set('search', search);
    return fetchJson<MatchSummary[]>(`${API_BASE}/matches?${params.toString()}`);
  },
  getMatchDetail: (matchId: number) => fetchJson<MatchSummary>(`${API_BASE}/matches/${matchId}`),
  getMatchDeliveries: (matchId: number, innings?: number) => {
    const q = innings !== undefined ? `?innings=${innings}` : '';
    return fetchJson<DeliveryState[]>(`${API_BASE}/matches/${matchId}/deliveries${q}`);
  },
  getMatchPressureCurve: (matchId: number, innings?: number) => {
    const q = innings !== undefined ? `?innings=${innings}` : '';
    return fetchJson<MatchPressureTimeline>(`${API_BASE}/matches/${matchId}/pressure${q}`);
  },

  // Players
  getPlayers: (discipline = 'batting', eligibility = 'ELIGIBLE', search?: string, limit = 100) => {
    const params = new URLSearchParams({ discipline, eligibility, limit: String(limit) });
    if (search) params.set('search', search);
    return fetchJson<PlayerItem[]>(`${API_BASE}/players?${params.toString()}`);
  },
  getPlayerDetail: (playerId: number, discipline = 'batting') =>
    fetchJson<PlayerDetail>(`${API_BASE}/players/${playerId}?discipline=${discipline}`),
  comparePlayers: (playerAId: number, playerBId: number, discipline = 'batting') =>
    fetchJson<PlayerComparisonResponse>(`${API_BASE}/players/compare?player_a_id=${playerAId}&player_b_id=${playerBId}&discipline=${discipline}`),

  // Rankings
  getBattingRankings: (search?: string, sortBy?: string, sortOrder = 'desc') => {
    const params = new URLSearchParams({ sort_order: sortOrder });
    if (search) params.set('search', search);
    if (sortBy) params.set('sort_by', sortBy);
    return fetchJson<RankingsResponse>(`${API_BASE}/rankings/batting?${params.toString()}`);
  },
  getBowlingRankings: (search?: string, sortBy?: string, sortOrder = 'desc') => {
    const params = new URLSearchParams({ sort_order: sortOrder });
    if (search) params.set('search', search);
    if (sortBy) params.set('sort_by', sortBy);
    return fetchJson<RankingsResponse>(`${API_BASE}/rankings/bowling?${params.toString()}`);
  },
  getRankingsExportUrl: (discipline: 'batting' | 'bowling') => `${API_BASE}/rankings/${discipline}/export`,

  // Methodology & Reports
  getMethodology: () => fetchJson<MethodologyResponse>(`${API_BASE}/methodology`),
  getReports: () => fetchJson<ReportItem[]>(`${API_BASE}/reports`),
  getReportDownloadUrl: (reportId: string) => `${API_BASE}/reports/${reportId}/download`,
};
