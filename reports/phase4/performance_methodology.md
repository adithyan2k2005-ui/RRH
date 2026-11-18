# SupeRR Selector Season 2 — Phase 4 Performance Methodology Document

## 1. Overview & Evaluation Philosophy
Phase 4 implements a three-layer context-adjusted evaluation architecture to evaluate individual cricket player performance under match pressure:
- **Layer A (Context-Adjusted Residuals)**: Evaluates delivery outcomes against out-of-fold historical baseline expectations.
- **Layer B (Within-Player Baselines & Uplift)**: Evaluates each player's high-pressure performance relative to their own ordinary-pressure baseline.
- **Layer C (Consistency & Reliability)**: Evaluates match-level stability, downside protection, and sample-size credibility.

---

## 2. Cricket Scoring Semantics & Rule Enforcement

### Batting Rules:
1. **Balls Faced**: Includes legal balls and no-balls (`Overstep`, `other`), but strictly excludes wides.
2. **Batter Runs**: Excludes all extras (byes, leg-byes, wide penalties, no-ball penalties).
3. **Striker Dismissal**: Strictly charged only when `is_team_wicket == True` AND `dismissed_player_id == striker_id`. Non-striker run-outs are not debited to the striker.
4. **Retired Hurt**: Preserved as not out; never treated as a dismissal.

### Bowling Rules:
1. **Overs Bowled**: Counted strictly from legal deliveries (`total_legal_balls / 6.0`).
2. **Runs Conceded**: Excludes byes and leg-byes; includes wides and no-ball penalty extras.
3. **Bowler Dismissals**: Includes Bowled, Caught, LBW, Stump, Hit Wicket. Excludes RunOut, Retire Out, Obstructing.
4. **Economy Rate**: `runs_conceded / (legal_balls / 6.0)`.

---

## 3. Context-Adjusted Expected Performance Models
Expectations are estimated via **hierarchical leave-one-match-out (LOMO)** aggregation:
$$\hat{\mu}_{-m}(G) = \frac{\sum_{j \in G, m_j \neq m} Y_j}{\sum_{j \in G, m_j \neq m} W_j}$$

- **Hierarchy Levels**:
  - Level 1: `(match_format, bowling_innings_phase, wickets_bucket, is_chase)`
  - Level 2: `(match_format, bowling_innings_phase, wickets_bucket)`
  - Level 3: `(match_format, bowling_innings_phase)`
  - Level 4: `(match_format)`
  - Level 5: Global overall mean
- Minimum supporting balls: 30.

---

## 4. Runs-Equivalent Wicket Conversion
To combine run rate and wicket preservation into a single coherent metric:
$$\text{Combined Batting Impact} = \text{Run Impact} + W_{\text{val}} \times (\text{Dismissal Risk} - \text{Dismissal})$$
$$\text{Combined Bowling Impact} = \text{Run Prevention} + W_{\text{val}} \times (\text{Wicket Taken} - \text{Expected Wicket})$$
Where empirical $W_{\text{val}} = 20.0$ runs (based on average runs per wicket in T20 death and middle phases: 19.7 to 28.3).
