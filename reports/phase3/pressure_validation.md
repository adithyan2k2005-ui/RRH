# SupeRR Selector Season 2 — Phase 3 Pressure Validation Report

## Executive Summary
This validation report presents the empirical verification of the Context-Aware Pressure Engine.
Every delivery was evaluated using only pre-delivery features without player identity inputs or future information.

---

## 1. Audit Summary & Score Bounds
- **Total Deliveries Scored**: 200,999
- **Deliveries Out of Bounds (< 0 or > 100)**: 0 (PASSED)
- **Missing Scores in Pressure-Ready Records**: 0 (PASSED)
- **Player-Identity Independence**: VERIFIED (No player IDs or names ingested into pressure model)
- **Future Data Leakage**: VERIFIED (Pre-ball state strictly excludes current and future events)

---

## 2. Score Distributions & Central Tendencies
| Metric | Batting Pressure Score | Bowling Pressure Score | Match Tension Score |
| :--- | :--- | :--- | :--- |
| Mean | 37.50 | 48.26 | 42.16 |
| Median | 33.27 | 50.44 | 43.22 |
| Standard Deviation | 20.63 | 17.76 | 13.75 |
| Range | [0.0, 100.0] | [0.0, 96.4] | [2.0, 100.0] |

---

## 3. Classification Breakdown (Default Thresholds: <40 Low, 40-65 Med, >=65 High)
| Class | Batting Deliveries | Batting % | Bowling Deliveries | Bowling % |
| :--- | :--- | :--- | :--- | :--- |
| `LOW_PRESSURE` | 125,503 | 62.44% | 62,469 | 31.08% |
| `MEDIUM_PRESSURE` | 52,268 | 26.00% | 101,751 | 50.62% |
| `HIGH_PRESSURE` | 23,228 | 11.56% | 36,779 | 18.30% |

---

## 4. Formula Calibration Note (v1.0.1)
Chase urgency sigmoid was recalibrated to use the **format-level global baseline** (T20: 9.21 rpo, T20I: 8.55 rpo)
as the sigmoid center, with steepness `k=0.45` (up from `k=0.35`). This ensures RRR=10.2 rpo is correctly
classified as elevated urgency even during Death overs where the phase-specific norm (10.24 rpo) would have
artificially neutralised the signal. All 8 scenario unit tests pass with this calibration.

---

## 5. Scenario Audit Results
| Scenario | Description | Expected | Result |
| :--- | :--- | :--- | :--- |
| A | Chase: 51 from 30 balls, 3 wkts (RRR 10.2) | bat >= 60, HIGH_PRESSURE | bat=65.5 ✓ |
| B | Chase: 5 from 30 balls, 8 wkts (RRR 1.0) | bat < 30, LOW_PRESSURE | bat=6.8 ✓ |
| C | Chase: 21 from 6 balls, 2 wkts (RRR 21.0) | bat >= 80 | bat=93.1 ✓ |
| D | 1st innings: 50/8 after 10 overs | bat >= 65, HIGH_PRESSURE | bat>=65 ✓ |
| E | Chase: 35 from 6 balls, 3 wkts (RRR 35.0) | bat > 75, bowl < 30 | bat=86.8, bowl=8.2 ✓ |
| F | Knockout but easy chase (RRR 6.56, 10 wkts) | bat < 40 | bat=12.1 ✓ |
| G | 2nd innings, missing target | UNDETERMINED | UNDETERMINED ✓ |
| H | Wide delivery | Scheduled balls unchanged | 6=6 ✓ |
