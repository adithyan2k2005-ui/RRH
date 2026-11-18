# SupeRR Selector Season 2 — Statistical Analytics Engine

A reproducible statistical analytics and quality assurance engine built for **SupeRR Selector Season 2 (Round 1)**.

- **Phase 1**: Ingestion, schema audit, relational integrity, cricket domain semantics validation, and standardized Parquet dataset generation.
- **Phase 2**: Ball-by-ball chronological delivery ordering, legal delivery classification, granular run and wicket attribution, innings context, and pre-delivery match state reconstruction with strict zero future data leakage.
- **Phase 3**: Context-aware pressure detection engine. Computes `batting_pressure_score`, `bowling_pressure_score`, and `match_tension_score` (all 0–100) for every delivery using only pre-ball match state. Separates batting difficulty from bowling defensive urgency. Outputs `data/processed/pressure_states.parquet` (200,999 rows × 77 cols).
- **Phase 4**: Context-adjusted player performance and reliability scoring. Estimates leave-one-match-out hierarchical expectations, computes performance residuals, evaluates within-player ordinary baselines and pressure uplift, measures match-level consistency and downside risk, applies Empirical Bayes shrinkage, enforces sample-size eligibility, and outputs composite 0–100 player reliability ratings. Outputs `batting_performance.parquet`, `bowling_performance.parquet`, `player_batting_metrics.parquet` (888 batters, 155 eligible), and `player_bowling_metrics.parquet` (647 bowlers, 270 eligible).
- **Phase 5**: Final top-10 player ranking, deterministic tie-breaking, micro-to-macro delivery reconciliation, stability sensitivity audits, and submission preparation. Generates official submission CSVs and reference selections.

---

## 1. Project Architecture

```
superr-selector-analytics/
    data/
        raw/                    # Unmodified raw CSV source files and problem statement PDF
        processed/              # Clean Parquet datasets and reconstructed match states
            ball_by_ball.parquet
            competitions.parquet
            competition_team_player_mapping.parquet
            matches.parquet
            match_states.parquet    # Phase 2 reconstructed pre-delivery states
            playing_eleven.parquet
            pressure_states.parquet         # Phase 3 pressure-annotated delivery states (77 cols)
            batting_performance.parquet     # Phase 4 delivery batting residuals & expectations
            bowling_performance.parquet     # Phase 4 delivery bowling residuals & expectations
            player_batting_metrics.parquet  # Phase 4 player-level batting reliability (888 batters)
            player_bowling_metrics.parquet  # Phase 4 player-level bowling reliability (647 bowlers)
            teams.parquet
    outputs/
        top_10_batters.csv          # Official Top 10 Batters ranking output
        top_10_bowlers.csv          # Official Top 10 Bowlers ranking output
        full_batting_rankings.csv   # Complete ranked pool of all 155 eligible batters
        full_bowling_rankings.csv   # Complete ranked pool of all 270 eligible bowlers
        submission_selections.md    # Formatted player dropdown matching reference
    src/
        __init__.py
        ingestion/
            __init__.py
            load_data.py        # Safe zip detection, traversal-proof extraction, encoding-safe CSV loading
        validation/
            __init__.py
            validate_data.py           # Schema inspection, relational integrity, cricket domain semantics
            validate_match_state.py    # Phase 2 match state audit, reconciliation, and reporting
            validate_pressure.py       # Phase 3 pressure score bounds, distribution, and scenario audit
            validate_player_metrics.py # Phase 4 player performance & reliability audits
            validate_final_rankings.py # Phase 5 16-point quality gate checklist validator
        features/
            __init__.py
            delivery_order.py   # Chronological ordering and sequence validation
            cricket_rules.py    # Legal ball detection, granular runs, dismissals, phases
            innings_context.py  # Scheduled overs, balls, standard and DLS chase targets
            match_state.py      # Core pre-delivery state reconstruction engine
            pressure_baselines.py  # Hierarchical contextual scoring rate baselines
            pressure_features.py   # Normalized pressure factor components (6 factors)
            pressure_model.py      # Multi-dimensional pressure score calculator
            pressure_thresholds.py # Pressure classification and threshold sensitivity
        performance/
            __init__.py
            batting_metrics.py     # Conventional batting stats, boundaries, striker dismissals
            bowling_metrics.py     # Conventional bowling stats, economy, bowler wickets
            expected_performance.py # Hierarchical leave-one-match-out expected models
            contextual_impact.py   # Runs-equivalent impact residuals and wicket attribution
            player_baselines.py    # Within-player ordinary baselines and pressure uplift
        reliability/
            __init__.py
            consistency.py         # Cluster-aware match-level consistency & downside protection
            uncertainty.py         # Empirical Bayes shrinkage and confidence intervals
            eligibility.py         # Sample-size qualification criteria and reason logging
            reliability_model.py   # Multi-dimensional 0-100 player reliability ratings
        ranking/
            __init__.py
            tie_breaking.py        # Multi-tier deterministic sorting and tie resolution
            ranking_engine.py      # Top-N filtering, ranking generation, candidate slicing
            submission_formatter.py # Standardized CSV export and dropdown markdown formatting
            eligibility_audit.py   # Complete dataset candidate audit (1,535 records)
            ranking_stability.py   # Weight sensitivity & leave-best-match-out robustness
            ranking_audit.py       # Micro-to-macro delivery reconciliation audit
    tests/
        test_ingestion.py              # Phase 1 ingestion unit tests (6 tests)
        test_validation.py             # Phase 1 schema & data quality tests (11 tests)
        test_delivery_order.py         # Phase 2 delivery ordering unit tests (5 tests)
        test_cricket_rules.py          # Phase 2 cricket rules unit tests (4 tests)
        test_match_state.py            # Phase 2 match state & zero-leakage unit tests (3 tests)
        test_match_state_integration.py # Phase 2 integration tests on real data (4 tests)
        test_pressure_features.py      # Phase 3 pressure factor unit tests (5 tests)
        test_pressure_model.py         # Phase 3 scenario A–H scenario tests (8 tests)
        test_pressure_leakage.py       # Phase 3 leakage & player-independence tests (3 tests)
        test_pressure_integration.py   # Phase 3 integration on 200,999 real deliveries (5 tests)
        test_batting_metrics.py        # Phase 4 batting laws, balls faced, striker dismissals (5 tests)
        test_bowling_metrics.py        # Phase 4 bowling laws, byes excluded, bowler wickets (4 tests)
        test_expected_performance.py   # Phase 4 leave-one-match-out out-of-fold validation (2 tests)
        test_player_baselines.py       # Phase 4 within-player baselines & pressure uplift (2 tests)
        test_consistency.py            # Phase 4 match-level consistency & downside risk (2 tests)
        test_reliability.py            # Phase 4 shrinkage, CI ordering, score bounds (3 tests)
        test_phase4_integration.py     # Phase 4 end-to-end integration on 200,999 deliveries (4 tests)
        test_ranking_engine.py         # Phase 5 deterministic sorting & tie-breaking (3 tests)
        test_ranking_eligibility.py    # Phase 5 eligibility filtering & audit flags (2 tests)
        test_ranking_integrity.py      # Phase 5 output schemas & column formatting (2 tests)
        test_ranking_stability.py      # Phase 5 Spearman & Kendall rank correlations (2 tests)
        test_phase5_integration.py     # Phase 5 16-point quality gates & integration (5 tests)
    reports/
        phase1/
            data_quality_report.md  # Official Phase 1 data quality audit report
            phase1_execution.log    # Phase 1 execution log
        phase2/
            reconstruction_summary.md    # Phase 2 methodology and state definitions
            reconstruction_validation.md # Phase 2 reconciliation and leakage audit
            unresolved_cases.csv         # Machine-readable log of anomalies and edge cases
            phase2_execution.log         # Phase 2 execution log
        phase3/
            pressure_methodology.md      # Phase 3 pressure model mathematical specification
            pressure_validation.md       # Phase 3 score bounds, distributions, classification audit
            pressure_distribution.csv    # Score distribution statistics by format and innings
            pressure_sensitivity.csv     # Threshold sensitivity analysis (±5 around defaults)
            pressure_examples.csv        # Annotated scenario audit examples (6 key situations)
        phase4/
            performance_methodology.md   # Phase 4 LOMO expectations & impact methodology
            reliability_methodology.md   # Phase 4 shrinkage, consistency & composite formulas
            player_coverage.md           # Phase 4 player sample distributions & eligibility rates
            model_validation.md          # Phase 4 scoring semantics audit & CI checks
            sensitivity_analysis.md      # Phase 4 wicket values & threshold sensitivity
        phase5/
            ranking_evidence.md          # Phase 5 exhaustive statistical profiles of all 20 players
            ranking_validation.md        # Phase 5 16-point checklist results & micro-reconciliation
            ranking_sensitivity.md       # Phase 5 weight sensitivity & leave-best-match-out analysis
            selection_boundary.md        # Phase 5 Rank 10 vs Ranks 11–15 boundary comparison
            eligibility_audit.csv        # Phase 5 audit table of all 1,535 evaluated players
    docs/
        problem_requirements.md # Exact official Round 1 requirements and constraints
        data_dictionary.md      # Comprehensive data dictionary for all 6 datasets
    scripts/
        run_phase1.py           # Phase 1 runner script
        run_phase2.py           # Phase 2 runner script
        run_phase3.py           # Phase 3 pressure engine runner script
        run_phase4.py           # Phase 4 player performance & reliability runner script
        run_phase5.py           # Phase 5 master ranking, audit, and reporting runner script
    requirements.txt            # Python dependency specifications
    README.md                   # Project documentation
    pytest.ini                  # Pytest configuration
    .gitignore                  # Source control ignore rules
```
    requirements.txt            # Python dependency specifications
    README.md                   # Project documentation
    pytest.ini                  # Pytest configuration
    .gitignore                  # Source control ignore rules
```

---

## 2. Environment Setup & Technology Stack

The project requires **Python 3.11+** and the following dependencies:
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `pyarrow>=14.0.0`
- `pytest>=8.0.0`
- `pymupdf>=1.23.0`

### Installation
Run the following from the project root:

```bash
pip install -r requirements.txt
```

---

## 3. Pipeline Execution

### Execute Phase 1 Pipeline (Ingestion & Schema Validation):
```bash
python scripts/run_phase1.py
```
*Executes archive extraction, raw loading, schema profiling, type standardization, and generates `reports/phase1/data_quality_report.md`.*

### Execute Phase 2 Pipeline (Match-State Reconstruction):
```bash
python scripts/run_phase2.py
```
*Executes delivery sequencing, legal ball identification, pre-delivery cumulative scoring and wickets, chase context calculation, zero-leakage audits, writes `data/processed/match_states.parquet`, and generates `reports/phase2/` summaries.*

### Execute Phase 3 Pipeline (Pressure Detection Engine):
```bash
python scripts/run_phase3.py
```
*Fits contextual scoring baselines, computes 6 pressure factor components, scores every delivery, classifies regimes, validates bounds and player independence, writes `data/processed/pressure_states.parquet`, and generates 5 artifacts in `reports/phase3/`.*

### Execute Phase 4 Pipeline (Player Performance & Reliability Scoring):
```bash
python scripts/run_phase4.py
```
*Estimates leave-one-match-out hierarchical expectations, computes delivery residuals, constructs within-player ordinary baselines and pressure uplift, measures match-level consistency, applies Empirical Bayes shrinkage, enforces qualification rules, outputs 4 parquet datasets in `data/processed/`, and generates 5 markdown reports in `reports/phase4/`.*

---

## 4. Automated Testing

The complete test suite comprises **76 automated tests** across all four phases, covering unit logic, domain rules, cricket scenarios, leakage audits, within-player baselines, consistency, shrinkage, and end-to-end integration on 200,999 actual tournament deliveries.

**Current Status: `76 passed` — 100% pass rate.**

### Run Complete Test Suite:
```bash
pytest tests -v
```

### Run Phase 4 Tests:
```bash
pytest tests/test_batting_metrics.py tests/test_bowling_metrics.py tests/test_expected_performance.py tests/test_player_baselines.py tests/test_consistency.py tests/test_reliability.py tests/test_phase4_integration.py -v
```

**Current Status: `54 passed` — 100% pass rate.**

### Run Complete Test Suite:
```bash
pytest tests -v
```

### Run Phase 1 Tests:
```bash
pytest tests/test_ingestion.py tests/test_validation.py -v
```

### Run Phase 2 Tests:
```bash
pytest tests/test_delivery_order.py tests/test_cricket_rules.py tests/test_match_state.py tests/test_match_state_integration.py -v
```

### Run Phase 3 Tests:
```bash
pytest tests/test_pressure_features.py tests/test_pressure_model.py tests/test_pressure_leakage.py tests/test_pressure_integration.py -v
```

---

## 5. Phase 2 Reconstructed Pre-Delivery Features

In `data/processed/match_states.parquet`, every delivery includes the exact match situation immediately **BEFORE** the ball was bowled:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `innings_score_before` | `int64` | Cumulative team score strictly before the delivery (first ball = 0). |
| `wickets_lost_before` | `int64` | Cumulative team dismissals before the delivery (first ball = 0). |
| `wickets_remaining_before` | `int64` | Wickets in hand before the delivery (`10 - wickets_lost_before`). |
| `legal_balls_bowled_before` | `int64` | Count of legal deliveries bowled in the innings before this ball. |
| `scheduled_balls` | `int64` | Total scheduled legal deliveries (120 in full match, 6 in super over, revised in shortened). |
| `scheduled_balls_remaining_before` | `int64` | Remaining scheduled legal balls (`max(0, scheduled_balls - legal_balls_bowled_before)`). |
| `current_run_rate` | `Float64` | Current scoring rate (`6.0 * score / legal_balls_bowled`; `<NA>` when 0 legal balls). |
| `target` | `Int64` | Target runs to win in the chase (Innings 2 & 4; `<NA>` in 1st innings). |
| `runs_required_before` | `Int64` | Runs required to win before this delivery (`max(0, target - score_before)`). |
| `required_run_rate` | `Float64` | Required run rate (`6.0 * runs_required / scheduled_balls_remaining`). |
| `bowling_innings_phase` | `string` | Match phase: `'Powerplay'` (overs 1-6), `'Middle'` (7-15), `'Death'` (16-20), `'SuperOver'`. |
| `is_legal_ball` | `bool` | True if delivery is legal; False if wide, overstep, or other no-ball. |
| `team_runs_on_ball` | `int64` | Total runs added to team score on this delivery (`runs + extras1 + extras2`). |
| `runs_charged_to_bowler_on_ball` | `int64` | Runs debited to bowler (excludes byes/leg-byes; includes wides & no-ball penalties). |
| `is_bowler_wicket` | `bool` | True if dismissal is credited to bowler (Bowled, Caught, LBW, Stump, Hit Wicket). |
| `is_target_revised` | `bool` | True if target was set via DLS / revised overs. |
| `is_shortened_match` | `bool` | True if scheduled overs < 20. |
| `reconstruction_status` | `string` | Quality status: `'VALID'`, `'WARNING'`, or `'BLOCKED'`. |
| `is_pressure_ready` | `bool` | True if record is verified for Phase 3 pressure modeling. |

---

## 6. Phase 3 Pressure Score Features

In `data/processed/pressure_states.parquet` (200,999 rows × 77 cols), every delivery additionally carries:

| Feature Name | Range | Description |
| :--- | :--- | :--- |
| `batting_pressure_score` | 0–100 | Situational difficulty facing the batting side. Driven by RRR vs format baseline (chase) or CRR vs par with collapse risk (1st innings). |
| `bowling_pressure_score` | 0–100 | Defensive urgency facing the bowling side. Peaks in wire-finish scenarios; low when batting team is effectively beaten. |
| `match_tension_score` | 0–100 | Combined contest balance reflecting overall match closeness. |
| `batting_pressure_class` | categorical | `LOW_PRESSURE` (<40), `MEDIUM_PRESSURE` (40–65), `HIGH_PRESSURE` (≥65), `UNDETERMINED`. |
| `bowling_pressure_class` | categorical | Same classification applied to bowling pressure. |
| `baseline_expected_rate` | float | Contextual scoring rate baseline (rpo) for the delivery's format & phase. |
| `wicket_vulnerability` | 0–1 | Non-linear wickets-in-hand depletion factor. |
| `time_pressure` | 0–1 | Innings progression as a fraction of scheduled balls. |
| `chase_urgency` | 0–1 or NaN | RRR difficulty relative to format-level global baseline (2nd innings only). |
| `match_closeness` | 0–1 or NaN | Gaussian proximity to par; amplified as the chase deepens (2nd innings only). |
| `first_inn_par_deficit` | 0–1 or NaN | Batting team's scoring rate relative to competitive par (1st innings only). |
| `match_stakes_multiplier` | 1.00–1.15 | Knockout/playoff context weight (Finals: 1.15, Super 4/8: 1.08, League: 1.00). |

### Score Distributions (200,999 deliveries):
| Metric | Batting | Bowling | Match Tension |
| :--- | :--- | :--- | :--- |
| Mean | ~37.2 | ~48.4 | ~42.6 |
| Median | ~33.1 | ~50.5 | ~43.4 |
| HIGH_PRESSURE % | ~11% | ~19% | — |

---

## 7. Audit & Reconciliation Summary

- **Total Deliveries Reconstructed**: 200,999 (100% of raw deliveries accounted for).
- **Zero Future Data Leakage**:
  - Ball 1 score violations: **0**
  - Ball 1 wicket violations: **0**
  - Ball 1 legal ball violations: **0**
  - Cumulative score mismatches: **0**
- **Reconciliation Against Match Outcomes**:
  - 703 standard matches reconciled against result margins with **0 discrepancies**.
  - All 34 revised target/overs matches accounted for.
  - 12 Super Over innings (6 matches) fully reconciled.
- **Unresolved Cases**: 62 edge cases documented in `reports/phase2/unresolved_cases.csv` (12 retired hurt cases, 24 weather-shortened fixtures, 19 speed gun outliers, 3 super over playing XI duplicates, 3 squad registration omissions, 1 zero-legal-ball winning wide over).
- **Phase 3 Pressure Validation**:
  - Deliveries out of bounds [0,100]: **0**
  - NaN scores in pressure-ready records: **0**
  - Player-identity independence: **VERIFIED**
  - Future data leakage: **VERIFIED**

---

## 8. Phase 4 Performance & Reliability Scoring

In Phase 4, player performance is evaluated against out-of-fold contextual expectations and within-player ordinary baselines:

### Datasets Generated:
- `data/processed/batting_performance.parquet` (200,999 rows × 91 cols)
- `data/processed/bowling_performance.parquet` (200,999 rows × 88 cols)
- `data/processed/player_batting_metrics.parquet` (888 batters, 155 qualified)
- `data/processed/player_bowling_metrics.parquet` (647 bowlers, 270 qualified)

### Evaluation Architecture:
- **Layer A (Context-Adjusted Residuals)**:
  - Batter runs vs leave-one-match-out hierarchical expected runs.
  - Bowler runs conceded vs leave-one-match-out expected runs.
  - Dismissals vs expected dismissal risk ($W_{\text{val}} = 20.0$ runs).
- **Layer B (Within-Player Baselines & Uplift)**:
  - High-pressure impact vs ordinary baseline (LOW + MEDIUM pressure).
  - Empirical Bayes shrinkage ($k_0 = 20$ for batting, $k_0 = 24$ for bowling).
- **Layer C (Consistency & Reliability)**:
  - Match-level clustering preventing single-game domination.
  - Downside protection (25th percentile match impact).
  - Positive match ratio (% pressure matches with positive net impact).
  - Multi-dimensional composite rating ($R \in [0, 100]$):
    $$R = 0.40 \cdot S_{\text{impact}} + 0.25 \cdot S_{\text{uplift}} + 0.20 \cdot S_{\text{consistency}} + 0.15 \cdot S_{\text{confidence}}$$

### Score Distributions (Eligible Players):
| Discipline | Evaluated | Qualified | Mean Score | Median Score | Range |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Batting** | 888 | 155 (17.5%) | 46.93 | 48.64 | [7.08, 92.69] |
| **Bowling** | 647 | 270 (41.7%) | 44.23 | 43.91 | [6.51, 88.46] |

---

## 9. Phase 5 Final Top-10 Player Ranking & Submission Preparation

In Phase 5, official candidate rankings and Top-10 selections are extracted deterministically from the validated Phase 4 reliability outputs:

### Official Submission Selections:

#### Top 10 Batters Under Pressure:
| Rank | Player ID | Player Name | Reliability Score | HP Matches | HP Balls | HP Runs | Impact/Ball | Baseline | Uplift | Consistency |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 46066 | Vipraj Nigam | **92.69** | 6 | 47 | 105 | +2.1316 | -0.9503 | +3.0819 | 100.0% |
| 2 | 6651 | Towhid Hridoy | **92.25** | 4 | 81 | 138 | +1.9516 | +0.0339 | +1.9177 | 100.0% |
| 3 | 796 | Matthew Wade | **91.43** | 9 | 105 | 177 | +1.6930 | +0.0602 | +1.6328 | 88.9% |
| 4 | 6448 | Ibrahim Zadran | **90.45** | 4 | 55 | 80 | +2.0152 | +0.1428 | +1.8724 | 100.0% |
| 5 | 152 | Ravindra Jadeja | **84.80** | 23 | 233 | 382 | +0.9979 | +0.0232 | +0.9747 | 73.9% |
| 6 | 1219 | David Willey | **84.05** | 8 | 62 | 77 | +1.5563 | -1.5015 | +3.0578 | 87.5% |
| 7 | 2984 | Sikandar Raza | **80.96** | 7 | 72 | 147 | +1.4098 | -0.0127 | +1.4225 | 71.4% |
| 8 | 4708 | Rinku Singh | **80.77** | 15 | 204 | 408 | +1.5271 | +0.3412 | +1.1859 | 66.7% |
| 9 | 7897 | Namboori Tilak Varma | **80.62** | 17 | 168 | 321 | +1.0323 | +0.3701 | +0.6622 | 76.5% |
| 10 | 4686 | Joshua Clarkson | **80.21** | 4 | 52 | 70 | +1.0796 | +0.0539 | +1.0257 | 75.0% |

#### Top 10 Bowlers Under Pressure:
| Rank | Player ID | Player Name | Reliability Score | HP Matches | HP Legal Balls | HP Runs Conc. | HP Wickets | Impact/Ball | Baseline | Uplift | Consistency |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 6237 | Manimaran Siddharth | **88.46** | 3 | 38 | 52 | 5 | +1.8374 | -0.3603 | +2.1977 | 100.0% |
| 2 | 29080 | Muhammad Khan | **88.39** | 3 | 50 | 79 | 6 | +1.3838 | -0.4766 | +1.8604 | 100.0% |
| 3 | 7699 | Abbas Afridi | **88.32** | 14 | 159 | 250 | 19 | +1.2669 | +0.4464 | +0.8205 | 85.7% |
| 4 | 4856 | Benjamin Sears | **86.06** | 6 | 49 | 80 | 7 | +1.8047 | +0.0570 | +1.7477 | 83.3% |
| 5 | 6097 | Brydon Carse | **84.21** | 5 | 55 | 63 | 5 | +1.1038 | -0.0264 | +1.1302 | 100.0% |
| 6 | 8009 | Junaid Siddique | **84.01** | 10 | 44 | 56 | 5 | +1.4796 | +0.3387 | +1.1409 | 80.0% |
| 7 | 27504 | Dushan Hemantha | **82.58** | 5 | 73 | 91 | 9 | +1.7455 | +1.0289 | +0.7166 | 80.0% |
| 8 | 5809 | Naveen ul Haq | **81.10** | 10 | 93 | 177 | 12 | +1.3173 | +0.0880 | +1.2293 | 70.0% |
| 9 | 4779 | Pieter Willem Mulder | **77.44** | 4 | 36 | 66 | 4 | +1.1316 | -0.3084 | +1.4400 | 75.0% |
| 10 | 4499 | Saqib Mahmood | **77.29** | 6 | 36 | 51 | 4 | +1.1926 | +0.3368 | +0.8558 | 83.3% |

### Verification & Robustness Highlights:
- **16-Point Automated Quality Gate Checklist**: **16 / 16 PASSED** (`outputs/top_10_batters.csv`, `outputs/top_10_bowlers.csv`, full ranking files, unique IDs, 1-10 sequence, ELIGIBLE status, non-increasing scores, zero nulls).
- **Micro-to-Macro Reconciliation Audit**: **100% Agreement** between ball-by-ball delivery micro-records and macro-level ranking metrics for all 20 players.
- **Sensitivity & Stability**:
  - Weight sensitivity rank correlations: Spearman $\rho \ge 0.978$, Kendall $\tau \ge 0.877$, Top-10 cohort overlap 80%–90%.
  - Leave-best-match-out test: **100% (20/20) of top players retain strictly positive net impact** upon removal of their single best match, confirming resistance to single-match distortion.

---

## 10. Phase 6 Final Methodology Report & Submission Package

In Phase 6, the final submission package was compiled, verified, and packaged for official submission to **SupeRR Selector Season 2 — Round 1**:

### Submission Deliverables:
- **Methodology Report (PDF)**: `submission/methodology_report.pdf` (8 pages, publication-quality A4 document with running headers/footers, dynamic pagination, and 6 embedded statistical figures).
- **Methodology Source (Markdown)**: `submission/methodology_report.md` (Self-contained technical specification covering all 17 sections).
- **Official Top 10 Batters Dataset**: `submission/top_10_batters.csv` (10 rows, matching Phase 5).
- **Official Top 10 Bowlers Dataset**: `submission/top_10_bowlers.csv` (10 rows, matching Phase 5).
- **Unstop Dropdown Reference**: `submission/submission_selections.md` (Player name, ID, and score reference for manual portal selection).
- **Independent Quality Audit**: `submission/submission_validation.md` (Exhaustive compliance checklist and readiness audit).
- **Traceability Manifest**: `submission/evidence_manifest.md` (End-to-end mapping of all tables, charts, and equations to source code and data).
- **Submission ZIP Archive**: `submission/superr_selector_round1_submission.zip` (1.05 MB clean submission package).

### Verification & Test Suite Status:
- **Automated Regression Suite**: **95 / 95 tests passing (100% pass rate)**.
- **Cross-File Parity**: Verified byte-level and hash-level consistency between ranking outputs, submission files, and report contents.
- **Submission Readiness**: **PASS** (Ready for immediate manual submission on the Unstop portal).

### Pipeline Execution Guide:
```bash
# Full Pipeline Execution Sequence
python scripts/run_phase1.py              # Ingestion & Schema Quality
python scripts/run_phase2.py              # Pre-Delivery Match-State Reconstruction
python scripts/run_phase3.py              # Contextual Pressure Detection Engine
python scripts/run_phase4.py              # Context-Adjusted Performance & Reliability
python scripts/run_phase5.py              # Deterministic Rankings & Audits
python scripts/generate_methodology_report.py # Publication PDF Report Generation
pytest tests -v                           # 95 Automated Quality Gate Tests
```
