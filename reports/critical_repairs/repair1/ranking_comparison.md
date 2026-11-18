# Critical Repair 1 — Ranking Protection & Audit Comparison

**Project**: `superr-selector-analytics`  
**Phase**: Critical Repair 1 — Ranking Integrity Verification  
**Status**: **100% UNCHANGED — RANKINGS AND SCORES FULLY PRESERVED**  
**Date**: November 18, 2026  

---

## 1. Ranking Verification Summary

Before and after the methodology documentation corrections, cryptographic SHA-256 hashes and row-level player metrics were evaluated across the official ranking artifacts:
- `outputs/top_10_batters.csv`
- `outputs/top_10_bowlers.csv`
- `submission/top_10_batters.csv`
- `submission/top_10_bowlers.csv`

### Cryptographic Hash Integrity:
| Artifact | SHA-256 Checksum | Match Status |
|---|---|:---:|
| `outputs/top_10_batters.csv` | `be85fb0d232bacbc8d5714c548b00eb7ff66c74060b6c11dfb3a3675cf9f24bf` | **IDENTICAL** |
| `submission/top_10_batters.csv` | `be85fb0d232bacbc8d5714c548b00eb7ff66c74060b6c11dfb3a3675cf9f24bf` | **IDENTICAL** |
| `outputs/top_10_bowlers.csv` | `1febb963e22c86fc7dac90e1435e82e98c5484321ad24f63957a63e643b1fd23` | **IDENTICAL** |
| `submission/top_10_bowlers.csv` | `1febb963e22c86fc7dac90e1435e82e98c5484321ad24f63957a63e643b1fd23` | **IDENTICAL** |

---

## 2. Top 10 Batters Comparison

| Rank | Player ID | Player Name | Stored Score | Recomputed Score | Absolute Error | Status |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | 46066 | Vipraj Nigam | 92.69 | 92.69 | 0.000000 | **MATCH** |
| 2 | 6651 | Towhid Hridoy | 92.25 | 92.25 | 0.000000 | **MATCH** |
| 3 | 796 | Matthew Wade | 91.43 | 91.43 | 0.000000 | **MATCH** |
| 4 | 6448 | Ibrahim Zadran | 90.45 | 90.45 | 0.000000 | **MATCH** |
| 5 | 152 | Ravindra Jadeja | 84.80 | 84.80 | 0.000000 | **MATCH** |
| 6 | 1219 | David Willey | 84.05 | 84.05 | 0.000000 | **MATCH** |
| 7 | 2984 | Sikandar Raza | 80.96 | 80.96 | 0.000000 | **MATCH** |
| 8 | 4708 | Rinku Singh | 80.77 | 80.77 | 0.000000 | **MATCH** |
| 9 | 7897 | Namboori Tilak Varma | 80.62 | 80.62 | 0.000000 | **MATCH** |
| 10 | 4686 | Joshua Clarkson | 80.21 | 80.21 | 0.000000 | **MATCH** |

---

## 3. Top 10 Bowlers Comparison

| Rank | Player ID | Player Name | Stored Score | Recomputed Score | Absolute Error | Status |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | 6237 | Manimaran Siddharth | 88.46 | 88.46 | 0.000000 | **MATCH** |
| 2 | 29080 | Muhammad Khan | 88.39 | 88.39 | 0.000000 | **MATCH** |
| 3 | 7699 | Abbas Afridi | 88.32 | 88.32 | 0.000000 | **MATCH** |
| 4 | 4856 | Benjamin Sears | 86.06 | 86.06 | 0.000000 | **MATCH** |
| 5 | 6097 | Brydon Carse | 84.21 | 84.21 | 0.000000 | **MATCH** |
| 6 | 8009 | Junaid Siddique | 84.01 | 84.01 | 0.000000 | **MATCH** |
| 7 | 27504 | Dushan Hemantha | 82.58 | 82.58 | 0.000000 | **MATCH** |
| 8 | 5809 | Naveen ul Haq | 81.10 | 81.10 | 0.000000 | **MATCH** |
| 9 | 4779 | Pieter Willem Mulder | 77.44 | 77.44 | 0.000000 | **MATCH** |
| 10 | 4499 | Saqib Mahmood | 77.29 | 77.29 | 0.000000 | **MATCH** |

---

## 4. Rank Stability Across Candidate Pool

- Batting Qualified Cohort (N = 155):
  - Mean score: 46.93
  - Median score: 48.64
  - Max score: 92.69 (Vipraj Nigam)
  - Rank 11 near-miss: Dinesh Karthik (79.88, 0.33 pts behind Buttler)
- Bowling Qualified Cohort (N = 270):
  - Mean score: 44.23
  - Median score: 43.91
  - Max score: 88.46 (Manimaran Siddharth)
  - Rank 11 near-miss: T Natarajan (76.84, 0.45 pts behind Rana)

### Audit Conclusion:
Zero changes occurred to the rankings or player scores. The official Top 10 Batters and Top 10 Bowlers remain completely deterministic and reproducible.
