# SupeRR Selector Season 2 — Phase 2 Reconstruction Summary

## 1. Overview & Architecture
Phase 2 reconstructs the precise match state immediately BEFORE each delivery across historical IPL and T20I matches from 2022 to 2026.
The reconstructed dataset provides the foundational state input for the Phase 3 pressure detection engine.

---

## 2. Core Methodological Principles

### A. Delivery Ordering & Sequence Continuity
- Chronological delivery sequence within each innings is established by sorting on `['match_id', 'innings', 'overid', 'over_ball_num']`.
- In this dataset, `innings_ball_num` strictly increments from 1 to N without gaps across all 1,724 innings.
- Original row indices are preserved as `source_row_index` for 100% audit traceability.

### B. Legal Ball Identification
- Wides (`wide`), Oversteps (`Overstep`), and other no-balls (`other`) do NOT consume legal balls.
- Byes (`byes`), leg-byes (`legbyes`), penalty runs (`Penalty`), and unassisted balls count as legal balls.
- `legal_balls_bowled_before` increments only after a legal delivery is completed.

### C. Run Reconstruction & Pre-Ball Scoring
- Batter runs off the bat are strictly preserved in `runs_scored_on_ball` (`runs`).
- Total runs added to the team score on each ball: `team_runs_on_ball = runs + extras1_runs + extras_2_runs`.
- Pre-delivery innings score is computed via shifted cumulative sum: `innings_score_before = cumsum - team_runs_on_ball`.
- Bowler debited runs strictly exclude byes and leg-byes, while including wides and no-ball penalty runs.

### D. Wicket Reconstruction
- `wickets_lost_before` accumulates fall of wickets strictly prior to the delivery.
- `wickets_remaining_before = 10 - wickets_lost_before`.
- Bowler-credited wickets (`Bowled`, `Caught`, `LBW`, `Stump`, `Hit Wicket`) are distinguished from team dismissals (`RunOut`, `Retire Out`, `Obstructing the field`).
- The 12 retired hurt cases are treated as non-dismissals (`is_wicket == False`).

### E. Innings Context & Chase Metrics
- **Scheduled Overs & Balls**: In shortened matches, `first_inn_revised_overs` and `second_inn_revised_overs` record scheduled balls (e.g. 90.0 = 15 overs = 90 balls).
- **Target Determination**:
  - Innings 1 and 3: No target or required run rate.
  - Innings 2: Set to `revised_target` if DLS revised; otherwise set to `innings_1_total + 1`.
  - Innings 4: Set to `innings_3_total + 1` (Super Over chase).
- **Runs Required**: `runs_required_before = max(0, target - innings_score_before)`.
- **Required Run Rate**: `6.0 * runs_required_before / scheduled_balls_remaining_before`.
- **Current Run Rate**: `6.0 * innings_score_before / legal_balls_bowled_before` (missing/NA when legal_balls == 0).

---

## 3. Future Data Leakage Prevention
- Pre-delivery scores, wickets, and legal balls strictly exclude the current ball outcome.
- Chase targets for Innings 2 use only the completed total from Innings 1 or official pre-innings revised targets.
- No end-of-match results or future delivery outcomes are referenced.

---

## 4. Readiness for Phase 3 Pressure Detection
- The reconstructed dataset is saved at `data/processed/match_states.parquet`.
- All 200,999 records contain valid pre-delivery context for pressure modeling in Phase 3 (required run rate, balls remaining, wickets in hand, innings stage).

