# SupeRR Intelligence Lab — API Contract Matrix
## End-to-End Contract Verification: FastAPI Pydantic Models ↔ React TypeScript Interfaces

**Date**: November 18, 2026  
**Auditor**: Principal Full-Stack Architect & API Contract Verification Engineer  
**Status**: **100% VERIFIED & RECONCILED (ZERO MISMATCHES)**  

---

### 1. Architectural Overview

The SupeRR Intelligence Lab full-stack platform links a Python/FastAPI data intelligence backend (serving pre-computed Phase 1–5 Parquet and CSV artifacts) to a React 18 / TypeScript frontend application.

To guarantee that no contract mismatch, missing field, or unexpected type conversion can cause chart crashes (such as Minified React error #31), every API route response has been audited against its corresponding Pydantic schema in `backend/api/schemas/models.py` and TypeScript interface in `frontend/src/services/api.ts`.

---

### 2. Comprehensive Endpoint Contract Matrix

| Endpoint | HTTP Method | Backend Pydantic Model | Frontend TypeScript Interface | Primary Frontend Consumer | Required Fields | Optional / Nullable Fields | Units / Value Domains | Reconciled Status |
|:---|:---:|:---|:---|:---|:---|:---|:---|:---:|
| `/api/health` | GET | `HealthResponse` | `HealthResponse` | `Shell.tsx` (Sidebar Status Footer) | `status`, `version`, `app_name`, `deliveries_loaded`, `matches_loaded`, `players_loaded`, `test_suite_status` | None | Counts (integers), Status string | **VALIDATED** |
| `/api/overview` | GET | `OverviewResponse` | `OverviewResponse` | `Overview.tsx` | `total_matches`, `total_deliveries`, `total_players`, `total_competitions`, `eligible_batters`, `eligible_bowlers`, `pipeline_phases`, `competitions_distribution`, `pressure_distribution`, `top_batter_summary`, `top_bowler_summary`, `data_quality_warnings` | `app_name`, `version`, `total_batters_evaluated`, `total_bowlers_evaluated` | Counts, percentages (0–100), float ratings | **VALIDATED (Repaired `competitions_distribution` from dict to array)** |
| `/api/pipeline/status` | GET | `List[PhaseStatus]` | `PipelinePhase[]` | `Overview.tsx` (Fallback query) | `phase_number`, `phase_name`, `status`, `description`, `deliverable` | `phase_id`, `name`, `key_output` | Phase numbers 1–6, status uppercase strings | **VALIDATED (Dual naming aliases provided)** |
| `/api/datasets` | GET | `List[DatasetMeta]` | `DatasetMeta[]` | `DataExplorer.tsx` | `dataset_id`, `name`, `row_count`, `column_count`, `size_bytes`, `description`, `columns` | `rows_count`, `columns_count`, `file_size_bytes`, `format` | Row/col integers, byte sizes, column schema list | **VALIDATED** |
| `/api/datasets/{dataset_id}/schema` | GET | `DatasetMeta` | `DatasetMeta` | `DataExplorer.tsx` | `dataset_id`, `name`, `row_count`, `column_count`, `size_bytes`, `description`, `columns` | `rows_count`, `columns_count`, `file_size_bytes` | Schema metadata | **VALIDATED** |
| `/api/datasets/{dataset_id}/records` | GET | `DatasetRecordsResponse` | `DatasetRecordsResponse` | `DataExplorer.tsx` | `dataset_id`, `total_records`, `page`, `page_size`, `total_pages`, `records` | `name`, `columns` | Paginated records list (dict array) | **VALIDATED (Repaired pandas 2.x string-type search mask)** |
| `/api/datasets/{dataset_id}/export` | GET | CSV Stream | N/A (Direct Download Link) | `DataExplorer.tsx` (Export CSV button) | Full dataset as CSV | None | CSV text/csv stream | **VALIDATED** |
| `/api/competitions` | GET | `List[CompetitionItem]` | `CompetitionItem[]` | `Overview.tsx`, `MatchReplay.tsx` | `comp_id`, `comp_name`, `match_format`, `matches_count`, `teams_count` | `first_match_date`, `last_match_date` | IDs, counts, dates (YYYY-MM-DD) | **VALIDATED** |
| `/api/matches` | GET | `List[MatchSummary]` | `MatchSummary[]` | `MatchReplay.tsx`, `PressureLab.tsx` | `match_id`, `comp_id`, `comp_name`, `team1_id`, `team1_name`, `team2_id`, `team2_name`, `match_date`, `venue`, `match_format`, `stage`, `knock_out`, `scheduled_overs`, `is_target_revised`, `total_deliveries`, `innings_available` | `target`, `winner_team_id`, `result_margin` | Overs (floats), runs (floats/ints), IDs | **VALIDATED** |
| `/api/matches/{match_id}` | GET | `MatchSummary` | `MatchSummary` | `MatchReplay.tsx` | Same as `/api/matches` item | `target`, `winner_team_id`, `result_margin` | Match metadata object | **VALIDATED** |
| `/api/matches/{match_id}/deliveries` | GET | `List[DeliveryState]` | `DeliveryState[]` | `MatchReplay.tsx`, `PressureLab.tsx` | `match_id`, `innings`, `delivery_seq`, `overid`, `over_ball_num`, `innings_ball_num`, `striker_id`, `striker_name`, `non_striker_id`, `bowler_id`, `bowler_name`, `is_legal_ball`, `runs_scored_on_ball`, `extras_on_ball`, `runs_charged_to_bowler`, `is_team_wicket`, `is_bowler_wicket`, `innings_score_before`, `wickets_lost_before`, `legal_balls_bowled_before`, `scheduled_balls_remaining_before`, `current_run_rate`, `batting_pressure_score`, `bowling_pressure_score`, `match_tension_score`, `batting_pressure_class`, `bowling_pressure_class` | `dismissal_type`, `runs_required_before`, `required_run_rate` | Pressure scores (0–100), run rates (runs/over) | **VALIDATED** |
| `/api/matches/{match_id}/pressure` | GET | `MatchPressureTimeline` | `MatchPressureTimeline` | `PressureLab.tsx` | `match_id`, `total_deliveries`, `pressure_timeline` | `innings` | Over timeline objects array | **VALIDATED** |
| `/api/players` | GET | `List[PlayerItem]` | `PlayerItem[]` | `PlayerIntelligence.tsx` | `player_id`, `player_name`, `discipline`, `reliability_score`, `eligibility_status`, `hp_matches`, `hp_balls`, `hp_runs_or_wkts`, `hp_impact_per_ball`, `ord_baseline_impact`, `pressure_uplift`, `consistency_metric`, `uncertainty_se`, `shrinkage_weight` | `rank` | Float impacts, reliability (0–100), SE | **VALIDATED (Added missing `import pandas as pd` in route)** |
| `/api/players/{player_id}` | GET | `PlayerDetail` | `PlayerDetail` | `PlayerIntelligence.tsx` | `summary`, `competitions_count`, `total_matches`, `total_balls`, `total_runs_or_wkts`, `ordinary_balls`, `ordinary_runs_or_wkts`, `ordinary_impact_per_ball`, `ci_lower_90`, `ci_upper_90`, `best_match_impact`, `worst_match_impact`, `match_appearances` | None | Full dossier object with match point list | **VALIDATED** |
| `/api/players/compare` | GET | `PlayerComparisonResponse` | `PlayerComparisonResponse` | `PlayerIntelligence.tsx` (Compare Modal) | `discipline`, `player_a`, `player_b`, `radar_comparison`, `advantage_analysis` | None | Radar metric map (0–100), advantage strings | **VALIDATED** |
| `/api/rankings/{discipline}` | GET | `RankingsResponse` | `RankingsResponse` | `ReliabilityRankings.tsx` | `discipline`, `total_candidates`, `total_eligible`, `top_10`, `near_miss_11_15`, `full_rankings` | None | Candidate lists, official rankings | **VALIDATED** |
| `/api/rankings/{discipline}/export` | GET | CSV Stream | N/A (Direct Download Link) | `ReliabilityRankings.tsx` (Export CSV button) | Official rankings as CSV | None | CSV text/csv stream | **VALIDATED** |
| `/api/methodology` | GET | `MethodologyResponse` | `MethodologyResponse` | `MethodologyReports.tsx` | `title`, `version`, `pressure_weights`, `reliability_weights`, `sensitivity_correlations`, `quality_gates`, `document_summary` | None | Weights dict, quality gate items | **VALIDATED (Reconciled weights to 0.40/0.25/0.20/0.15)** |
| `/api/reports` | GET | `List[ReportItem]` | `ReportItem[]` | `MethodologyReports.tsx` | `report_id`, `title`, `category`, `filename`, `file_size_bytes`, `mime_type`, `description`, `download_url` | None | Document inventory | **VALIDATED** |
| `/api/reports/{report_id}/download` | GET | Binary / Document | N/A (Direct Download Link) | `MethodologyReports.tsx` (Download Buttons) | Actual file stream with Content-Disposition attachment header | None | PDF, CSV, ZIP, MD | **VALIDATED** |

---

### 3. Defensive Runtime Safeguards

1. **Lightweight Runtime Schema Validation**:
   `validateOverviewResponse` in `frontend/src/services/api.ts` enforces type invariants before passing data to React components, preventing malformed objects from reaching Recharts primitives.
2. **Recharts Object Protection**:
   `Overview.tsx` explicitly maps `data.competitions_distribution` to an array of primitives (`matches: Number(c.matches_count) || 0`), ensuring React error #31 can never recur.
3. **Fault-Tolerant Route-Level Boundaries**:
   `ErrorBoundary` wraps `<Outlet />` in `Shell.tsx`, keyed by `location.pathname`. Any isolated component or fetch error displays an informative Rajasthan Royals themed fault card without unmounting the persistent sidebar, top navigation, or stadium background mesh.
