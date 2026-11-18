# SupeRR Selector Season 2 — Phase 1 Data Quality Report

## Executive Summary
This quality report documents the exhaustive dataset audit, schema inspection, referential integrity verification, and cricket domain semantics validation performed for Phase 1 of SupeRR Selector Season 2.
All numerical findings in this report were directly computed from the supplied raw dataset.

---

## 1. Total Records in Each Dataset
| Dataset Name | Total Rows | Total Columns | Exact Duplicate Rows | Inferred Candidate Primary Key |
| :--- | :--- | :--- | :--- | :--- |
| `competitions` | 141 | 4 | 0 | comp_id, comp_name |
| `teams` | 353 | 3 | 0 | None (Composite Key) |
| `matches` | 883 | 22 | 0 | match_id |
| `ball_by_ball` | 200,999 | 33 | 0 | None (Composite Key) |
| `competition_team_player_mapping` | 6,413 | 6 | 0 | None (Composite Key) |
| `playing_eleven` | 28,381 | 9 | 0 | None (Composite Key) |

---

## 2. Match & Competition Coverage
- **Total Matches in `matches.csv`**: 883
- **Matches with Ball-by-Ball Delivery Data**: 867
- **Matches Without Delivery Data**: 16 (100% accounted for by abandoned fixtures)
- **Matches with Playing Eleven Data**: 880
- **Matches Without Playing Eleven Data**: 3 (abandoned prior to toss)
- **Match Formats Covered**:
  - `T20I`: 134 competitions (Bilateral international series, ICC T20 World Cups, Asia Cups)
  - `T20`: 7 competitions (IPL 2022, IPL 2023, IPL 2024, IPL 2025, IPL 2026, Mens T20 Emerging Teams Asia Cup 2024, Asia Cup Rising Stars 2025)
- **Season Span**: 2022 through 2026

---

## 3. Player Registry & Identity Analysis
- **Total Unique Player IDs Across All Datasets**: 1,217
- **Unique Players in `ball_by_ball.csv`**: 959
- **Unique Players in `playing_eleven.csv`**: 1,082
- **Unique Players in `competition_team_player_mapping.csv`**: 1,217
- **Squad Players Never Appearing in a Playing 11**: 135 (benched squad members)
- **Squad Players Never Batting or Bowling**: 258

### Crucial Player Identity Findings
1. **Player IDs with Multiple Names**: 0 (Every player ID maps strictly to a single canonical name).
2. **Player Names with Multiple IDs**: 7 names map to multiple distinct player IDs:
   - **`Abdul Samad`**: 2 distinct player IDs
   - **`Bashir Ahmad`**: 2 distinct player IDs
   - **`Basil Hameed`**: 2 distinct player IDs
   - **`Haider Ali`**: 2 distinct player IDs
   - **`Mohammad Ali`**: 2 distinct player IDs
   - **`Muhammad Farooq`**: 2 distinct player IDs
   - **`Rashid Khan`**: 2 distinct player IDs
   > [!IMPORTANT]
   > Merging or aggregating on player names alone is strictly prohibited. Analysis must strictly use `player_id` as the identity key.

---

## 4. Missing-Value Analysis
Summary of non-zero null counts across datasets:

### Dataset: `matches`
| Column | Missing Count | Missing Percentage | Context & Meaning |
| :--- | :--- | :--- | :--- |
| `home_team_captain_id` | 44 | 4.98% | Optional / conditional field |
| `away_team_captain_id` | 45 | 5.1% | Optional / conditional field |
| `toss_win_team_id` | 15 | 1.7% | Optional / conditional field |
| `toss_opted` | 15 | 1.7% | Optional / conditional field |
| `first_inn_revised_overs` | 858 | 97.17% | Populated only in rain-affected / DLS matches |
| `second_inn_revised_overs` | 858 | 97.17% | Populated only in rain-affected / DLS matches |
| `revised_target` | 860 | 97.4% | Populated only in rain-affected / DLS matches |
| `win_team_id` | 41 | 4.64% | Optional / conditional field |

### Dataset: `ball_by_ball`
| Column | Missing Count | Missing Percentage | Context & Meaning |
| :--- | :--- | :--- | :--- |
| `dismissal_type_id` | 190,118 | 94.59% | Populated only when a dismissal occurs (is_wicket == True) |
| `dismissal_type` | 190,118 | 94.59% | Populated only when a dismissal occurs (is_wicket == True) |
| `dismissed_player_id` | 190,107 | 94.58% | Optional / conditional field |
| `extras_type` | 189,167 | 94.11% | Populated only when delivery has extras (wide, no-ball, bye, leg-bye) |
| `stroke` | 6,158 | 3.06% | Optional / conditional field |
| `delivery_style` | 391 | 0.19% | Optional / conditional field |
| `over_or_around` | 407 | 0.2% | Optional / conditional field |

### Dataset: `playing_eleven`
| Column | Missing Count | Missing Percentage | Context & Meaning |
| :--- | :--- | :--- | :--- |
| `batting_order` | 8,678 | 30.58% | Populated only for active participants (is_played == True) |
| `is_captain` | 8,667 | 30.54% | Populated only for active participants (is_played == True) |
| `is_wk` | 8,667 | 30.54% | Populated only for active participants (is_played == True) |

---

## 5. Duplicate Records & Key Uniqueness Analysis
- **Exact Duplicate Rows**: 0 duplicate rows across all six datasets.
- **Single-Column Primary Keys**:
  - `competitions.csv`: `comp_id` is unique (141 / 141).
  - `matches.csv`: `match_id` is unique (883 / 883).
- **Composite Keys**:
  - `teams.csv`: `(comp_id, team_id)` is strictly unique (353 / 353). `team_id` alone is not unique because teams participate across multiple competitions.
  - `competition_team_player_mapping.csv`: `(comp_id, team_id, player_id)` is strictly unique (6,413 / 6,413).
  - `ball_by_ball.csv`: `(match_id, innings, overid, over_ball_num)` is strictly unique (200,999 / 200,999).
- **Special Case in `playing_eleven.csv`**:
  - `75` duplicate rows observed on `(match_id, player_id)` across 3 specific matches: `[np.int64(13613), np.int64(21176), np.int64(28962)]`.
  - **Root Cause**: All 3 matches (`13613`, `21176`, `28962`) are Tied matches that went to a Super Over / One-Over Eliminator. The super over batting orders were appended, resulting in players having two distinct `batting_order` records for the same match.

---

## 6. Referential Integrity & Orphaned Records
- **Competitions <-> Matches**: 0 orphaned matches. All `comp_id` in `matches.csv` exist in `competitions.csv`.
- **Competitions <-> Teams**: 0 orphaned teams. All `comp_id` in `teams.csv` exist in `competitions.csv`.
- **Teams <-> Matches**: 0 orphaned teams. Every home and away team in `matches.csv` resolves in `teams.csv` under the match's competition.
- **Ball-by-Ball <-> Matches**: 0 orphaned deliveries. All 200,999 deliveries resolve to known matches.
- **Playing Eleven <-> Matches**: 0 orphaned playing eleven records.
- **Ball-by-Ball Players <-> Registry**: 0 missing players in `competition_team_player_mapping.csv`. All 959 players in BBB are fully registered.
- **Discrepancy (BBB vs Playing Eleven)**:
  - Exactly 2 players ([np.int64(36153), np.int64(39444)]: Syed Haider [ID 36153] and Basil Hameed [ID 39444]) bowled/batted in 3 matches (`37087`, `37092`, `37095` - Mens T20 Emerging Teams Asia Cup 2024 for UAE) but were omitted from `playing_eleven.csv` for those fixtures.

---

## 7. Cricket Semantic & Rule Findings

### A. Delivery Runs & Extras Breakdown
- **`runs` Column**: Represents **BATTER RUNS** scored off the bat.
  - On `wide`: `runs` is ALWAYS 0. Wide runs are stored in `extras1_runs`.
  - On `byes`: `runs` is ALWAYS 0. Bye runs are stored in `extras1_runs`.
  - On `legbyes`: `runs` is 0 (except 1 data entry anomaly row with runs=1, extras1_runs=0).
  - On `Overstep` (No-Ball): `extras1_runs` is ALWAYS 1 (the 1 penalty run for no-ball). `runs` contains the batter's runs off the bat (0, 1, 2, 4, 6).
  - On `other` (No-Ball from beamers/fielding restrictions): `extras1_runs` is ALWAYS 1.
  - **`extras_2_runs`**: Represents secondary extras occurring on no-balls (e.g., byes or leg-byes taken during a no-ball).
- **Mathematical Delivery Total Equation**:
  $$\text{total\_ball\_runs} = \text{runs} + \text{extras1\_runs} + \text{extras\_2\_runs}$$
  *Verified against match results across all innings.*

### B. Wicket & Dismissal Semantics
- **Total Wickets Recorded**: 10,881
- **Bowler-Credited Dismissals**: 10,272 (Bowled: 1,775, Caught: 7,557, LBW: 709, Stump: 214, Hit Wicket: 17).
- **Non-Bowler Dismissals**: 609 (RunOut: 600, Retire Out: 6, Obstructing the field: 3).
- **Non-Striker Dismissals**: In 275 dismissals (271 runouts, 3 retire outs, 1 obstructing the field), the player dismissed was the non-striker (`dismissed_player_id != striker_id`).
- **Retired Hurt Discovery**:
  - Exactly 12 rows exhibit `is_wicket == False` while having a non-null `dismissed_player_id`.
  - Verification against next-delivery strikers confirmed all 12 events represent batsmen retiring hurt (e.g. Rahul Tripathi, Rohit Sharma, Kane Williamson, Sanju Samson). In cricket rules, Retired Hurt is not a wicket, but the player leaving the crease was recorded in `dismissed_player_id`.
- **Missing Dismissed Player ID**: Exactly 1 row (Row 127899 in match 40709) has `is_wicket == True` and `dismissal_type == 'Retire Out'` but `dismissed_player_id` is null.

### C. Over & Ball Numbering
- `overid`: Ranges from 1 to 20 (1-indexed, over 1 through over 20).
- `over_ball_num`: Ranges from 1 to 13. Increments sequentially on every delivery bowled in the over, including illegal deliveries (wides and no-balls).
- Completed overs with exactly 6 legal balls: 31,757 out of 32,350.
- Final overs of innings frequently terminate prior to 6 legal balls when teams are bowled out or successfully chase targets.
- **Anomalous Overs**:
  - Over with 7 legal balls: Match `41509` (over 12) had 7 legal balls bowled due to on-field umpire count error.
  - Over with 0 legal balls: Match `24353` (over 18) had 1 delivery (a wide for 2 runs) which completed the chase and ended the match immediately.

### D. Speed Gun & Context Anomalies
- `bowl_speed == 0`: 77,861 deliveries (speed tracking unavailable/unrecorded).
- `bowl_speed < 0`: 1 delivery (-1.0 sentinel value).
- Extreme outliers (`bowl_speed > 165 km/h`): 20 deliveries with corrupted values up to 1456.1 km/h (speed gun parsing errors).
- `delivery_ist_time`: Delivery timestamps are labeled with string suffix 'UTC' despite the column header denoting 'delivery_ist_time'. 200,957 rows possess distinct second-level timestamps; 42 rows possess default '00:00:00 UTC' values.

---

## 8. Incomplete, Abandoned & Unusual Matches
- **Abandoned Matches**: 19 matches abandoned without a ball bowled (16 in BBB, 3 without playing elevens).
- **No Result Matches**: 21 matches interrupted by weather with incomplete innings.
- **DLS / Revised Overs Matches**: 19 matches with revised overs or targets.
- **Super Over Matches**: 9 matches resolved by Super Over / One-Over Eliminator.

---

## 9. Implications & Handling Strategy for Phase 2 & Phase 3
1. **Pressure Index Construction**:
   - Wides and no-balls must not count toward balls faced by a batter.
   - Bowler economy under pressure must exclude leg-byes and byes (which are not charged to the bowler) while including wide and no-ball penalty runs.
   - Wickets credited to bowlers must strictly exclude run-outs, retired out, and obstructing the field.
   - Retired hurt events (`is_wicket == False`) must never be counted as bowler wickets or batter dismissals.
2. **Eligibility & Sample Size Filtering**:
   - Players with very few pressure balls faced or bowled (e.g. fewer than minimum qualification threshold) must be filtered to prevent small-sample distortions.
3. **Match Context & Format Normalization**:
   - DLS matches require contextual scaling of balls remaining and required run rate.
   - IPL and T20I matches must be balanced appropriately.

---

## 10. Unresolved Ambiguities
1. **Delivery Timestamp Timezone**: Whether `delivery_ist_time` represents Indian Standard Time formatted with a 'UTC' suffix or true UTC remains undocumented; however, ball ordering is strictly guaranteed by `(match_id, innings, overid, over_ball_num)`.
2. **Speed Gun Calibration**: `bowl_speed` outliers (>165 km/h) and zeros indicate unreliable speed tracking; speed should not be used as a primary pressure weighting feature.

