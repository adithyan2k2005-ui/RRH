# Critical Repair 2 — Corrected Dataset Statistics & Coverage Reconciliation

**Project**: `superr-selector-analytics`  
**Phase**: Critical Repair 2 — Dataset Integrity & Source Statistics Reconciliation  
**Auditor**: Senior Cricket Data Engineer & Dataset Quality Auditor  
**Date**: November 18, 2026  
**Status**: **SOURCE TRUTH RECONCILED — ZERO RECORD LOSS OR DATASET DRIFT**  

---

## 1. Executive Summary & Root Cause Confirmation

A confirmed discrepancy existed between the actual data processed by the analytical engine and the dataset narrative recorded in earlier project documentation:
- Earlier archived reports (`submission/submission_validation.md`, `submission/methodology_report.md`, and `scripts/generate_methodology_report.py`) stated:
  - `competitions.csv`: **6 rows**
  - `teams.csv`: **51 rows**
  - `matches.csv`: **744 rows**
  - `playing_eleven.csv`: **16,368 rows**
  - `competition_team_player_mapping.csv`: **2,752 rows**
- In reality, the official hackathon archive `6af458274c1e8_data_pack.zip` and the ingested datasets contain:
  - `competitions.csv`: **141 rows** (4 columns)
  - `teams.csv`: **353 rows** (3 columns)
  - `matches.csv`: **883 rows** (22 columns)
  - `ball_by_ball.csv`: **200,999 rows** (33 columns)
  - `competition_team_player_mapping.csv`: **6,413 rows** (6 columns)
  - `playing_eleven.csv`: **28,381 rows** (9 columns)

### Root Cause Analysis:
The discrepancy was an artifact of Phase 6 manual documentation authoring. The underlying analytical pipeline (`scripts/run_phase1.py` through `scripts/run_phase5.py`) correctly ingested and processed all **883 matches, 141 competitions, 353 teams, and 200,999 deliveries** as recorded in `reports/phase1/data_quality_report.md`. However, during Phase 6 report generation, a generic boilerplate draft containing mock counts (6 competitions, 51 teams, 744 matches) was copied into the report narrative instead of dynamically pulling from the validated source manifest.

---

## 2. Source-to-Processed Data Reconciliation

Every processed Parquet table in `data/processed/` corresponds **1-to-1 with zero row loss, zero row additions, and zero join multiplication** to the raw CSVs extracted from `6af458274c1e8_data_pack.zip`:

| Dataset Table | Raw File (`data/raw/`) | Raw Rows | Raw Cols | Processed File (`data/processed/`) | Proc Rows | Proc Cols | Traceability & Integrity Status |
|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|
| **Competitions** | `competitions.csv` | 141 | 4 | `competitions.parquet` | 141 | 4 | **EXACT 1-TO-1 MATCH (0 loss)** |
| **Teams** | `teams.csv` | 353 | 3 | `teams.parquet` | 353 | 3 | **EXACT 1-TO-1 MATCH (0 loss)** |
| **Matches** | `matches.csv` | 883 | 22 | `matches.parquet` | 883 | 22 | **EXACT 1-TO-1 MATCH (0 loss)** |
| **Ball-by-Ball** | `ball_by_ball.csv` | 200,999 | 33 | `ball_by_ball.parquet` | 200,999 | 33 | **EXACT 1-TO-1 MATCH (0 loss)** |
| **Player Mapping** | `competition_team_player_mapping.csv` | 6,413 | 6 | `competition_team_player_mapping.parquet` | 6,413 | 6 | **EXACT 1-TO-1 MATCH (0 loss)** |
| **Playing XI** | `playing_eleven.csv` | 28,381 | 9 | `playing_eleven.parquet` | 28,381 | 9 | **EXACT 1-TO-1 MATCH (0 loss)** |

---

## 3. Pipeline Analysis Coverage Breakdown

To eliminate confusion between full source records and analytical subsets, all stages of the pipeline have been measured:

### 3.1 Match Coverage
* **A. Total Supplied Matches in Registry**: **883 matches** (spanning 2022 to 2026 across 138 competition IDs).
* **B. Matches with Ball-by-Ball Delivery Data**: **867 matches**.
* **C. Matches Without Deliveries**: **16 matches** (100% accounted for by abandoned fixtures where no ball was bowled due to rain/outfield).
* **D. Matches with Valid Reconstructed States**: **867 matches** (100% coverage of all deliveries).
* **E. Matches Eligible for Pressure Modelling**: **867 matches** (zero dropped fixtures).
* **F. Matches Contributing to Final Rankings**: **492 matches** (the distinct match appearances of all 425 qualified batters and bowlers).

### 3.2 Competition Coverage
* **All Competitions in Registry**: **141 competitions** (134 T20I tournaments/series, 7 domestic T20 leagues).
* **Competitions Represented in Fixtures (`matches.csv`)**: **138 competitions**.
* **Competitions with Zero Fixtures**: **3 competitions** (IDs: 2724, 2726, 2727 — present in tournament registry without scheduled matches in this data pack).
* **Competitions Represented in Ball-by-Ball Deliveries**: **138 competitions**.

### 3.3 Player Registry & Exposure Funnel
* **Total Registered Player IDs (`competition_team_player_mapping.csv`)**: **1,217 players**.
* **Players Appearing in Confirmed Playing XI (`playing_eleven.csv`)**: **1,082 players** (135 registered squad members were benched).
* **Players Observed in Active Ball-by-Ball Play**: **959 players** (striker, non-striker, or bowler).
* **Total Evaluated Batters Pool**: **888 batters** (71 players appeared only as bowlers or fielders).
* **Qualified Batters Meeting Minimum Sample Size**: **155 batters** ($\ge 20$ HP balls, $\ge 3$ HP matches, $\ge 25$ ord balls).
* **Total Evaluated Bowlers Pool**: **647 bowlers**.
* **Qualified Bowlers Meeting Minimum Sample Size**: **270 bowlers** ($\ge 24$ HP legal balls, $\ge 3$ HP matches, $\ge 30$ ord balls).
* **Final Official Selection**: Exactly **10 Batters** and **10 Bowlers**.

---

## 4. Cricket Semantics & Data Quality Reconciliation

A full domain semantics audit of the 200,999 delivery records verified the following breakdown:

### Delivery Types & Extras Breakdown:
* **Clean Deliveries (No extras)**: 189,167 balls (94.11%)
* **Wides (`extras_type == 'wide'`)**: 7,714 balls (3.84%)
* **Leg-byes (`extras_type == 'legbyes'`)**: 2,748 balls (1.37%)
* **No-balls (`extras_type.isin(['Overstep', 'other'])`)**: 840 balls (0.42%) — 576 Overstep, 264 other
* **Byes (`extras_type == 'byes'`)**: 529 balls (0.26%)
* **Penalties (`extras_type == 'Penalty'`)**: 1 ball (0.00%)
* **Total**: **200,999 deliveries (100.0%)**

### Dismissal & Wicket Accounting:
* **Total Wickets (`is_wicket == 1`)**: **10,881 wickets**
  - Caught: 7,557
  - Bowled: 1,775
  - LBW: 709
  - Run Out: 600
  - Stumped: 214
  - Hit Wicket: 17
  - Retire Out: 6
  - Obstructing the field: 3
* **Striker Dismissal Semantics**: Striker is charged only when `is_team_wicket == True` AND `dismissed_player_id == striker_id`. Non-striker run-outs are excluded.
* **Bowler Wicket Semantics**: Credited strictly for bowler-induced dismissals (bowled, caught, lbw, stumped, hit-wicket). Run-outs and obstructing the field are excluded.

### Match Conditions & Curtailed Fixtures:
* **Super Overs**: 38 deliveries across 6 tied matches (all designated `innings > 2` and modeled with zero future leakage).
* **Revised Target Fixtures**: 23 matches with explicit revised targets (34 matches with revised overs or targets under DLS).
* **Weather-Abandoned Fixtures with 0 Deliveries**: Exactly 16 fixtures.

---

## 5. Machine-Readable Audit Outputs

The following authoritative files have been generated in `reports/critical_repairs/repair2/`:
1. `source_manifest.json` — Exhaustive inventory of all 6 raw CSV files with SHA-256 hashes, sizes, schemas, nulls, and duplicate counts.
2. `dataset_reconciliation.csv` — Exact 1-to-1 table reconciliation confirming zero record loss and zero join multiplication.
3. `analysis_coverage.json` — Stage-by-stage coverage metrics across matches, competitions, teams, players, and deliveries.
4. `exclusions_audit.csv` — Explicit accounting for every excluded match (16 abandoned fixtures), competition (3 empty registry entries), and ineligible player (733 batters, 377 bowlers).
