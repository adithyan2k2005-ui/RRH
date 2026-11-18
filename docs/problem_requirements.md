# SupeRR Selector Season 2 — Round 1 Problem Requirements

## 1. Executive Summary & Challenge Overview
*Source: Official Round 1 Problem Statement PDF (`Round 1 Problem Statement _ SupeRR Selector Season 2.docx.pdf`)*

The objective of Round 1 is to build a data-driven statistical analytics system that identifies and distinguishes cricket players (both batters and bowlers) who consistently rise to the occasion in high-pressure match situations from those whose performances dip under pressure.

The system must measure how players perform under pressure compared to their baseline/usual performance levels, and use these findings to rank the players who deliver most reliably when it matters most.

---

## 2. Core Problem Definition: What Counts as Pressure?
The problem statement explicitly delegates the formal definition of pressure to the participant, while specifying key guiding signals and constraints:

- **Participant Responsibility**: Participants must choose their own approach, justify why their definition is meaningful, and demonstrate quantitatively how it separates pressure situations from ordinary match conditions.
- **Batting and Bowling Scope**: The method and pressure framework must work across both batting and bowling disciplines.
- **Match-Context Indicators Suggested in Problem Statement**:
  - Required run rate (chasing context)
  - Wickets in hand (loss of wickets, batting collapse)
  - Balls remaining (overs/balls left in an innings or match)
  - Stage of an innings (e.g., Powerplay, Middle, Death overs)
  - Closeness of the contest (margin of runs or wickets required)
  - Other relevant match-context signals (e.g., tournament phase, knockout status, revised targets)

---

## 3. Dataset Scope & Boundaries
The challenge provides historical Indian Premier League (IPL) and Men's T20 International (T20I) match records from 2022 onwards:

1. **Ball-by-Ball Data (`ball_by_ball.csv`)**: Delivery-level match records capturing runs, extras, wickets, bowler/batter actions, and delivery context.
2. **Supporting Context Files**:
   - `competitions.csv`: Tournaments and series covering IPL and T20I (2022–2026 seasons).
   - `teams.csv`: Competition-specific team mappings.
   - `matches.csv`: Match-level metadata including venues, toss, revised overs/targets, knockouts, and outcomes.
   - `playing_eleven.csv`: Squad selections, designated roles (captain, wicketkeeper), impact players, and batting order.
   - `competition_team_player_mapping.csv`: Canonical player and squad registry across competitions.

**Constraint**: All rankings and analytical claims must be derived directly and reproducibly from the supplied dataset. External reputation or subjective opinions cannot be substituted for data-driven evidence.

---

## 4. Submission Requirements & Deliverables

The official challenge requires two mandatory components:

### Component 01: Player Rankings (Selected on Unstop)
- Two separate, ordered Top-10 lists submitted via dropdown fields:
  1. **Top 10 Batters Under Pressure** (Rank 1 through Rank 10)
  2. **Top 10 Bowlers Under Pressure** (Rank 1 through Rank 10)
- **Rules**:
  - Rank 1 represents the highest-rated player under pressure in each respective category.
  - Players must be strictly distinct within each list (no duplicates allowed within the same Top 10).
  - The dropdown selections must match exactly the rankings presented and justified in the methodology report.

### Component 02: Methodology Report (Document Upload)
A comprehensive, transparent report explaining the analytical framework and selections. The report must explicitly cover:
1. **Pressure Definition**: The specific match situations and indicators utilized, and the justification for selecting them.
2. **Performance Measurement**: Batting and bowling performance metrics, calculation of baseline performance, and the rating/scoring logic.
3. **Fair Comparisons**: Methodology for handling sample sizes, player eligibility thresholds, varying match contexts, and combining IPL and T20I data.
4. **Evidence for Top 10**: Quantitative evidence, comparisons, tables, and charts supporting both the selection of players and their specific rank order.
5. **Reliability & Limitations**: Consistency checks across different matches and seasons, and identification of areas where the model may be less certain or have wider confidence bounds.
6. **Reproducibility**: The methodology must be sufficiently transparent and rigorous for an independent evaluator to reproduce the results.

### Component 03: Optional Journey Sharing
- Completely optional: photos, screenshots, or a 30–60 second video summarizing the experience, approach, or an interesting insight.
- The document explicitly states: *This is completely optional and will not affect the evaluation of your submission.*

---

## 5. Explicit Constraints & Phase Boundaries

1. **Phase 1 Focus**:
   - Establish reproducible ingestion and validation pipelines.
   - Conduct thorough schema inspection, referential integrity verification, and cricket data semantics analysis.
   - Standardize cleaned Parquet outputs and generate automated test suites.
   - **Do NOT** compute pressure scores, rank players, or construct predictive models in Phase 1.
2. **Reproducibility & Integrity**:
   - No fabrication of data, metrics, or missing events.
   - No silent dropping of anomalous or unparseable records.
   - No assumptions without verified evidence from the supplied data.

