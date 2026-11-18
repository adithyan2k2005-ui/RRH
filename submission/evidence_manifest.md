# SupeRR Selector Season 2 — Evidence Traceability Manifest

This manifest maps every major table, figure, formula, and statistical claim in the final submission report to its authoritative codebase module, processed dataset, validation report, and regression test.

---

## 1. Top 10 Batters Ranking Table
- **Report Location**: Section 11 (Final Top 10 Batters)
- **Primary Source File**: `outputs/top_10_batters.csv` & `submission/top_10_batters.csv`
- **Underlying Dataset**: `data/processed/player_batting_metrics.parquet` (888 evaluated batters, 155 qualified)
- **Micro-Delivery Source**: `data/processed/batting_performance.parquet` (200,999 delivery rows)
- **Generating Code**: `src/ranking/ranking_engine.py`, `src/ranking/submission_formatter.py`
- **Reconciliation Audit**: `reports/phase5/ranking_validation.md` (Gate 01–07, 100% micro-reconciliation)
- **Regression Test**: `tests/test_phase5_integration.py::test_top_10_batters_csv_structure_and_values`

## 2. Top 10 Bowlers Ranking Table
- **Report Location**: Section 12 (Final Top 10 Bowlers)
- **Primary Source File**: `outputs/top_10_bowlers.csv` & `submission/top_10_bowlers.csv`
- **Underlying Dataset**: `data/processed/player_bowling_metrics.parquet` (647 evaluated bowlers, 270 qualified)
- **Micro-Delivery Source**: `data/processed/bowling_performance.parquet` (200,999 delivery rows)
- **Generating Code**: `src/ranking/ranking_engine.py`, `src/ranking/submission_formatter.py`
- **Reconciliation Audit**: `reports/phase5/ranking_validation.md` (Gate 08–14, 100% micro-reconciliation)
- **Regression Test**: `tests/test_phase5_integration.py::test_top_10_bowlers_csv_structure_and_values`

## 3. Pressure State Distributions & Figures 1 & 2
- **Report Location**: Section 6 (Pressure Detection Methodology)
- **Figure 1**: `submission/figures/figure1_batting_pressure_dist.png` (Batting Pressure Classes: Low 125,503 / 62.4%, Med 52,268 / 26.0%, High 23,228 / 11.6%)
- **Figure 2**: `submission/figures/figure2_bowling_pressure_dist.png` (Bowling Pressure Classes: Low 62,469 / 31.1%, Med 101,751 / 50.6%, High 36,779 / 18.3%)
- **Underlying Dataset**: `data/processed/pressure_states.parquet` (200,999 deliveries × 77 columns)
- **Generating Code**: `src/features/pressure_model.py`, `src/reporting/charts.py`
- **Validation Report**: `reports/phase3/pressure_validation.md`, `reports/phase3/pressure_distribution.csv`
- **Regression Test**: `tests/test_pressure_integration.py::test_full_dataset_row_and_column_integrity`

## 4. Top 10 Score Comparisons & Figures 3 & 4
- **Report Location**: Sections 11 & 12
- **Figure 3**: `submission/figures/figure3_top10_batters.png`
- **Figure 4**: `submission/figures/figure4_top10_bowlers.png`
- **Underlying Dataset**: `outputs/top_10_batters.csv`, `outputs/top_10_bowlers.csv`
- **Generating Code**: `src/reporting/charts.py::generate_horizontal_rankings_chart`
- **Validation Report**: `reports/phase5/ranking_evidence.md`

## 5. High Pressure vs Ordinary Baseline & Figure 5
- **Report Location**: Sections 7 & 8 (Performance Evaluations)
- **Figure 5**: `submission/figures/figure5_pressure_vs_baseline.png`
- **Underlying Dataset**: `player_batting_metrics.parquet`, `player_bowling_metrics.parquet`
- **Generating Code**: `src/performance/player_baselines.py`, `src/reporting/charts.py`
- **Validation Report**: `reports/phase4/performance_methodology.md`, `reports/phase4/sensitivity_analysis.md`

## 6. Sensitivity Correlations & Figure 6
- **Report Location**: Section 13 (Ranking Robustness)
- **Figure 6**: `submission/figures/figure6_ranking_robustness.png`
- **Metrics**: Spearman $\rho \ge 0.978$, Kendall $\tau \ge 0.877$, Top-10 Overlap 80%–90% across 3 weighting regimes
- **Leave-Best-Match-Out**: 100% of top players retain positive impact after dropping their single best match
- **Generating Code**: `src/ranking/ranking_stability.py`
- **Validation Report**: `reports/phase5/ranking_sensitivity.md`, `reports/phase5/selection_boundary.md`
- **Regression Test**: `tests/test_ranking_stability.py`, `tests/test_phase5_integration.py`

## 7. Mathematical Formulations Traceability
- **Match-State Pre-Ball Equations**: Implemented in `src/features/match_state.py`, verified in `tests/test_match_state.py` (0 future leakage).
- **Multi-Factor Pressure Index ($P \in [0, 100]$)**: Implemented in `src/features/pressure_model.py`, verified in `tests/test_pressure_model.py`.
- **Hierarchical Leave-One-Match-Out Expectations**: Implemented in `src/performance/expected_performance.py`, verified in `tests/test_expected_performance.py`.
- **Runs-Equivalent Contextual Impact**: Implemented in `src/performance/contextual_impact.py`, verified in `tests/test_cricket_rules.py`.
- **Empirical Bayes Shrinkage**: Implemented in `src/reliability/uncertainty.py`, verified in `tests/test_reliability.py`.
- **Cluster-Aware Consistency**: Implemented in `src/reliability/consistency.py`, verified in `tests/test_consistency.py`.
- **Deterministic 5-Tier Tie-Breaking**: Implemented in `src/ranking/tie_breaking.py`, verified in `tests/test_ranking_engine.py`.

