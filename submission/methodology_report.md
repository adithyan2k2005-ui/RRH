# SupeRR Selector Season 2 — Pressure-Based Cricket Player Reliability Analysis

**Official Round 1 Technical Methodology Report**  
*Reproducible Statistical Modeling, Ball-by-Ball Context Reconstruction, and Reliability Ranking Engine*  

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Problem Understanding](#2-problem-understanding)
3. [Dataset Description](#3-dataset-description)
4. [Data Cleaning & Validation](#4-data-cleaning--validation)
5. [Match-State Reconstruction](#5-match-state-reconstruction)
6. [Pressure Detection Methodology](#6-pressure-detection-methodology)
7. [Batting Performance Evaluation](#7-batting-performance-evaluation)
8. [Bowling Performance Evaluation](#8-bowling-performance-evaluation)
9. [Reliability Scoring Architecture](#9-reliability-scoring-architecture)
10. [Fairness & Context Bias Mitigations](#10-fairness--context-bias-mitigations)
11. [Final Top 10 Batters Selection](#11-final-top-10-batters-selection)
12. [Final Top 10 Bowlers Selection](#12-final-top-10-bowlers-selection)
13. [Ranking Robustness & Sensitivity Analysis](#13-ranking-robustness--sensitivity-analysis)
14. [Quality Gate & Automated Validation Results](#14-quality-gate--automated-validation-results)
15. [Methodological Limitations](#15-methodological-limitations)
16. [Conclusion](#16-conclusion)
17. [Reproducibility & Execution Guide](#17-reproducibility--execution-guide)

---

## 1. Executive Summary

The **SupeRR Selector Season 2 (Round 1)** hackathon poses a fundamental sports analytics challenge: identify the **Top 10 most reliable batters** and **Top 10 most reliable bowlers** under high match pressure from a large multi-competition T20 cricket dataset spanning 883 matches (867 with ball-by-ball deliveries) and 200,999 recorded deliveries.

Traditional cricket metrics such as batting average, strike rate, bowling average, and economy rate fail to measure player reliability under crisis conditions because they treat all deliveries identically. A single off the last ball to win a high-stakes chase is treated identically to a single taken during an inconsequential powerplay over.

To solve this, we designed and implemented a **reproducible 5-stage statistical pipeline**:
1. **Relational Ingestion & Integrity Validation**: Ingested and audited 6 relational tables with zero data loss, resolving extras, dismissals, and competition mappings.
2. **Pre-Delivery Match State Reconstruction**: Reconstructed the dynamic state of the match immediately before each ball (score, wickets, balls remaining, required run rate, par deficits) with zero future data leakage.
3. **Contextual Pressure Detection Engine**: Formulated dual multi-factor pressure indexes ($P \in [0, 100]$) separating batting difficulty from bowling defensive urgency, categorizing 23,228 batting deliveries and 36,779 bowling deliveries as high pressure.
4. **Context-Adjusted Residuals & Reliability Scoring**: Modeled expected performance via leave-one-match-out hierarchical baselines, evaluated within-player ordinary baselines, applied Empirical Bayes shrinkage, measured match-level consistency, and penalized cluster standard errors.
5. **Deterministic Top-10 Ranking & Quality Verification**: Filtered candidates by participation thresholds (155 eligible batters, 270 eligible bowlers) and extracted the official Top 10 rankings.

### Major Findings:
- **Top Batters Under Pressure**: Led by **Vipraj Nigam (Rank 1, Score: 92.69)**, **Towhid Hridoy (Rank 2, Score: 92.25)**, **Matthew Wade (Rank 3, Score: 91.43)**, and **Ibrahim Zadran (Rank 4, Score: 90.45)**. These batters consistently delivered context-adjusted impact rates exceeding $+1.5$ runs per ball over expectations in critical match phases.
- **Top Bowlers Under Pressure**: Led by **Manimaran Siddharth (Rank 1, Score: 88.46)**, **Muhammad Khan (Rank 2, Score: 88.39)**, **Abbas Afridi (Rank 3, Score: 88.32)**, and **Benjamin Sears (Rank 4, Score: 86.06)**. These bowlers maintained disciplined dot-ball execution and acute wicket-taking threat under intense chase pressure.
- **Robustness**: 100% (20/20) of selected players retained positive net impact per ball under leave-best-match-out tests, proving that selections are resilient and resistant to single-match outlier distortion.

---

## 2. Problem Understanding

### 2.1 The Cricket Reliability Problem
In competitive T20 cricket, "reliability under pressure" cannot be measured by aggregate counting statistics:
1. **Context Blindness**: A boundary struck when needing 14 runs off 3 balls carries an order of magnitude more leverage than a boundary hit when needing 80 runs off 60 balls.
2. **Player Role Confounding**: Top-order anchors accumulate large run totals in low-leverage powerplay overs, whereas middle/lower-order finishers face exclusively high-leverage death overs. Comparing raw averages penalizes finishers who routinely sacrifice their wicket for team victory.
3. **Opponent and Venue Leverage**: Conceding 10 runs in the 20th over defending 12 is a match-winning bowling performance; conceding 10 runs in the 7th over is slightly below average.
4. **Sample Variance and Outliers**: A player who performs brilliantly in a single high-pressure game must not be mistaken for a reliably consistent performer across seasons.

### 2.2 Dual Asymmetry of Batting and Bowling Pressure
Batting pressure and bowling pressure are non-symmetric:
- When a batting team faces an escalating required run rate in a steep chase ($RRR > 14.0$), **batting difficulty** peaks because batters must attack every delivery under high dismissal risk. Conversely, the defending bowling team enjoys strategic freedom.
- When a batting team is comfortably cruising towards a modest target with 9 wickets in hand, **bowling defensive urgency** peaks because the fielding team faces immediate defeat unless they engineer sudden breakthroughs.

---

## 3. Dataset Description

The analysis was conducted strictly on the official dataset supplied for SupeRR Selector Season 2:

### Dataset Overview Table
| Dataset Name | Primary Key / Grain | Rows | Columns | Description & Scope |
|:---|:---|:---:|:---:|:---|
| `competitions.csv` | `comp_id` | 141 | 4 | Multi-format T20 tournaments (IPL, T20Is, Asia Cups, etc.) |
| `teams.csv` | `comp_id, team_id` | 353 | 3 | Franchise and international cricket teams |
| `matches.csv` | `match_id` | 883 | 22 | Fixture metadata, dates, venues, targets, results, knockouts |
| `ball_by_ball.csv` | `match_id, innings, delivery_seq` | 200,999 | 33 | Micro-delivery ball records, pitch coordinates, shot types |
| `playing_eleven.csv` | `match_id, team_id, player_id` | 28,381 | 9 | Lineup confirmations and playing XI squad registrations |
| `competition_team_player_mapping.csv` | `comp_id, team_id, player_id` | 6,413 | 6 | Official seasonal player roster registrations |

### Coverage Statistics:
- **Total Valid Deliveries**: 200,999 recorded deliveries across 867 active fixtures.
- **Match Coverage**: 883 matches total in registry (867 matches with ball-by-ball play, 16 abandoned fixtures without deliveries, 34 revised overs/target fixtures, 6 tied matches resulting in 12 Super Over innings).
- **Competition Coverage**: 141 competitions in tournament registry (138 represented with fixtures).
- **Player Pool**: 1,217 players in registry, 888 unique batters and 647 unique bowlers evaluated across active tournament play.
- **Integrity**: 100% foreign key referential integrity across all 6 relational tables with zero dropped records.

---

## 4. Data Cleaning & Validation

Comprehensive schema validation and cricket domain rule auditing were conducted:

1. **Extras and Legal Delivery Accounting**:
   - Legal balls are identified strictly where `extras_type` is NOT `'wide'` or no-ball penalties (`'Overstep'`, `'other'`).
   - Clean deliveries without extras comprise 189,167 balls (94.11%); wide balls total 7,714; no-balls total 840 (576 overstep, 264 other); leg-byes total 2,748; byes total 529; penalty runs total 1.
   - Neither wides nor no-balls consume legal deliveries (an over advances only on completed legal balls, and illegal deliveries must be re-bowled).
   - Batter balls faced are charged on all deliveries faced except wides (including legal balls and no-balls, per standard cricket scoring regulations).
   - Bowler runs conceded include batter runs off the bat (on legal balls and no-balls) plus wide penalty runs and no-ball penalty runs. Byes, leg-byes, and penalty runs are strictly excluded from bowler runs conceded and batter runs scored.
2. **Wicket and Dismissal Attribution**:
   - Total wickets: 10,881 wickets (7,557 caught, 1,775 bowled, 709 LBW, 600 run-out, 214 stumped, 17 hit wicket, 6 retire out, 3 obstructing the field).
   - Striker dismissals: Batter is charged only when `is_team_wicket == True` AND `dismissed_player_id == striker_id`. Non-striker run-outs are excluded.
   - Bowler wickets: Credited only for bowler-induced dismissals (bowled, caught, lbw, stumped, hit wicket). Non-bowler events (run-outs, obstructing the field) are excluded.
3. **Abandoned & Weather-Affected Fixtures**:
   - 16 weather-abandoned fixtures recorded 0 deliveries due to complete weather abandonment prior to a legal ball being bowled; preserved as valid unplayed fixture metadata.
   - All 34 revised target/overs fixtures (DLS adjustments) were mapped to official revised targets.

---

## 5. Match-State Reconstruction

To evaluate situations immediately **BEFORE** each ball without future data leakage, state tracking was implemented:

### Core Pre-Delivery Equations:
1. **Pre-Ball Cumulative Score**:
   $$S_{t} = \sum_{k=1}^{t-1} \text{team\_runs}_k$$
2. **Pre-Ball Wickets Lost**:
   $$W_{t} = \sum_{k=1}^{t-1} \mathbb{I}(\text{is\_team\_wicket}_k = 1)$$
3. **Pre-Ball Legal Balls Bowled & Remaining**:
   $$B_{\text{bowled}, t} = \sum_{k=1}^{t-1} \mathbb{I}(\text{is\_legal\_ball}_k = 1), \quad B_{\text{rem}, t} = B_{\text{scheduled}} - B_{\text{bowled}, t}$$
4. **Current Run Rate**:
   $$\text{CRR}_t = \frac{S_t}{\max(B_{\text{bowled}, t} / 6.0, 0.1)}$$
5. **Chasing State (Innings 2 & Super Overs)**:
   $$\text{RunsRequired}_t = \max(\text{Target} - S_t, 0), \quad \text{RRR}_t = \frac{\text{RunsRequired}_t}{\max(B_{\text{rem}, t} / 6.0, 0.1)}$$
6. **Zero Leakage Verification**: All delivery-level metrics at step $t$ depend strictly on deliveries $k \in [1, t-1]$. The outcome of ball $t$ has zero mathematical presence in pre-delivery state $t$.

---

## 6. Pressure Detection Methodology

### 6.1 Multi-Dimensional Pressure Modeling
For every delivery $t$, six normalized situation factors ($F \in [0, 1]$) are computed from pre-ball state:

1. **Wicket Vulnerability ($F_{\text{wkt}}$)**:
   $$F_{\text{wkt}} = 1.0 - \frac{10 - W_t}{10.0} = \frac{W_t}{10.0}$$
2. **Time Exposure ($F_{\text{time}}$)**:
   $$F_{\text{time}} = \frac{B_{\text{bowled}, t}}{B_{\text{scheduled}}}$$
3. **Chase Urgency ($F_{\text{chase}}$)**:
   $$F_{\text{chase}} = \frac{1}{1 + e^{-0.6 \cdot (\text{RRR}_t - 9.0)}}$$
4. **Match Closeness ($F_{\text{close}}$)**:
   $$F_{\text{close}} = e^{-0.5 \cdot \left(\frac{\text{Deficit}_t}{12.0}\right)^2}$$
5. **First-Innings Par Deficit ($F_{\text{par}}$)**:
   $$F_{\text{par}} = \text{clip}\left(\frac{\text{ParExpectedRuns}_t - S_t}{35.0}, 0.0, 1.0\right)$$
6. **Knockout Match Stakes Multiplier ($M_{\text{stakes}}$)**:
   $$M_{\text{stakes}} = 1.15 \text{ (Knockout/Playoff)}, \quad 1.00 \text{ (Group Stage)}$$

### 6.2 Composite Pressure Indices ($P \in [0, 100]$):
- **Batting Pressure Score**:
  $$P_{\text{bat}} = 100 \cdot \text{clip}\left(\left[0.35 F_{\text{chase}} + 0.30 F_{\text{wkt}} + 0.20 F_{\text{time}} + 0.15 F_{\text{close}}\right] \cdot M_{\text{stakes}}, 0, 1\right)$$
- **Bowling Pressure Score**:
  $$P_{\text{bowl}} = 100 \cdot \text{clip}\left(\left[0.35 F_{\text{close}} + 0.30 F_{\text{time}} + 0.20 (1 - F_{\text{wkt}}) + 0.15 (1 - F_{\text{chase}})\right] \cdot M_{\text{stakes}}, 0, 1\right)$$
- **Match Tension Score**:
  $$P_{\text{tension}} = 0.50 P_{\text{bat}} + 0.50 P_{\text{bowl}}$$

### 6.3 Validated Pressure Thresholds:
- **Batting High Pressure**: $P_{\text{bat}} \ge 65.0$ (23,228 deliveries, 11.6%).
- **Bowling High Pressure**: $P_{\text{bowl}} \ge 60.0$ (36,779 deliveries, 18.3%).
- **Ordinary Regime**: All non-HP deliveries ($P < 65.0$ / $P < 60.0$), used to establish within-player normal performance baselines.

---

## 7. Batting Performance Evaluation

### 7.1 Leave-One-Match-Out Hierarchical Expected Runs
To prevent out-of-sample data contamination, the expected runs for batter $i$ on delivery $t$ are predicted from a hierarchical leave-one-match-out baseline:
$$\mathbb{E}[R_t] = \mu_{\text{phase, wkt, format}}^{(-m(t))}$$
Where $(-m(t))$ denotes all historical deliveries excluding match $m(t)$.

### 7.2 Contextual Batting Impact
On each delivery $t$, the batter produces an impact residual:
$$\text{Impact}_{\text{run}, t} = R_t - \mathbb{E}[R_t]$$
$$\text{Impact}_{\text{dismissal}, t} = -\mathbb{I}(\text{striker dismissed}_t) \cdot W_{\text{val}} + \mathbb{E}[\text{WicketRisk}_t] \cdot W_{\text{val}}$$
$$\text{NetImpact}_t = \text{Impact}_{\text{run}, t} + \text{Impact}_{\text{dismissal}, t}$$
Where $W_{\text{val}} = 20.0$ runs represents the validated context-wide value of an active batting wicket in T20 cricket.

### 7.3 Within-Player Ordinary Baseline & Pressure Uplift
For each batter:
- $\mu_{\text{HP}}$: Net impact per ball faced under high pressure.
- $\mu_{\text{ord}}$: Net impact per ball faced under ordinary pressure (Low + Medium).
- **Batting Pressure Uplift**:
  $$\Delta_{\text{bat}} = \mu_{\text{HP}} - \mu_{\text{ord}}$$
A positive uplift indicates that the batter elevates their performance in crisis conditions above their ordinary personal baseline.

---

## 8. Bowling Performance Evaluation

### 8.1 Contextual Bowling Impact
Analogously, for bowler $j$ on delivery $t$:
$$\text{Impact}_{\text{conceded}, t} = \mathbb{E}[\text{RunsConceded}_t] - \text{RunsConceded}_t$$
$$\text{Impact}_{\text{wicket}, t} = \mathbb{I}(\text{bowler wicket}_t) \cdot W_{\text{val}} - \mathbb{E}[\text{WicketProb}_t] \cdot W_{\text{val}}$$
$$\text{NetImpact}_{\text{bowl}, t} = \text{Impact}_{\text{conceded}, t} + \text{Impact}_{\text{wicket}, t}$$

- Conceding fewer runs than expected yields positive run-prevention impact.
- Taking wickets yields large positive breakthrough impact.
- Wides and no-balls are strictly charged to bowler runs conceded. Byes and leg-byes are excluded.

### 8.2 Bowling Pressure Uplift:
$$\Delta_{\text{bowl}} = \mu_{\text{bowl, HP}} - \mu_{\text{bowl, ord}}$$

---

## 9. Reliability Scoring Architecture

### 9.1 Qualification Eligibility Thresholds
To ensure statistical credibility and eliminate spurious small-sample artifacts:
- **Batting**: $\ge 20$ high-pressure balls faced, $\ge 3$ high-pressure matches, $\ge 25$ ordinary balls faced. (155 of 888 qualified, 17.5%).
- **Bowling**: $\ge 24$ high-pressure legal balls bowled, $\ge 3$ high-pressure matches, $\ge 30$ ordinary balls bowled. (270 of 647 qualified, 41.7%).

### 9.2 Empirical Bayes Shrinkage
To prevent small-sample extreme ratings, player impact is shrunk toward the population prior $\mu_0$:
$$w_i = \frac{n_i}{n_i + k_0}, \quad \mu_{\text{shrunk}, i} = w_i \mu_{\text{HP}, i} + (1 - w_i) \mu_0$$
Where $k_0 = 20$ for batting and $k_0 = 24$ for bowling (one full T20 quota).

### 9.3 Cluster-Aware Match-Level Consistency
To ensure a player is not a single-match wonder, delivery residuals are clustered at the match level:
$$CR_i = \frac{1}{M_{\text{HP}, i}} \sum_{m=1}^{M_{\text{HP}, i}} \mathbb{I}\left(\text{MatchImpact}_{i, m} > 0\right)$$
Where $CR_i \in [0, 1]$ measures the proportion of pressure appearances resulting in positive net contribution.

### 9.4 Four Mathematical Reliability Components ($S_j \in [0, 100]$):
1. **Shrunk Pressure Impact ($S_{\text{impact}}$)**:
   Scaled via logistic sigmoid mapping continuous runs-per-ball leverage smoothly into $[0, 100]$ (centered at 0 $\to$ 50.0):
   $$S_{\text{impact}} = \frac{100.0}{1.0 + \exp\left(-3.0 \cdot \hat{\theta}_{\text{shrunk}}\right)}$$
2. **Pressure Uplift ($S_{\text{uplift}}$)**:
   Measures performance elevation in high pressure relative to ordinary baseline ($\text{Uplift} = \bar{y}_{\text{HP}} - \bar{y}_{\text{ord}}$), mapped via logistic curve:
   $$S_{\text{uplift}} = \frac{100.0}{1.0 + \exp\left(-3.5 \cdot \text{Uplift}\right)}$$
3. **Match-Level Consistency ($S_{\text{consistency}}$)**:
   Combines positive match contribution ratio ($\text{PMR}$) with 25th percentile downside risk protection ($P_{25}$):
   $$P_{25\text{ norm}} = \text{clip}\left(\frac{P_{25} + 1.0}{2.0}, 0.0, 1.0\right)$$
   $$S_{\text{consistency}} = 100.0 \times \left(0.60 \cdot \text{PMR} + 0.40 \cdot P_{25\text{ norm}}\right)$$
4. **Statistical Confidence ($S_{\text{confidence}}$)**:
   Rewards sample size depth and penalizes high match-to-match cluster variance:
   $$S_{\text{confidence}} = 100.0 \times w_i \times \frac{1.0}{1.0 + \text{SE}_{\text{cluster}}}$$
   Where $w_i = \frac{n_i}{n_i + k_0}$ ($k_0 = 20$ for batting, $24$ for bowling) and $\text{SE}_{\text{cluster}} = s_i / \sqrt{m_i}$.

### 9.5 Composite Reliability Score Formula:
The final 0–100 reliability rating is a balanced multi-factor composite:
$$R = 0.40 \cdot S_{\text{impact}} + 0.25 \cdot S_{\text{uplift}} + 0.20 \cdot S_{\text{consistency}} + 0.15 \cdot S_{\text{confidence}}$$
Where $\sum w_j = 0.40 + 0.25 + 0.20 + 0.15 = 1.00$, and $R$ is rounded to two decimal places.

---

## 10. Fairness & Context Bias Mitigations

1. **Competition Adjustments**: Baseline expectations are stratified by tournament tier (`comp_id`) and format, preventing domestic players from artificially outscoring international players due to differing run-scoring environments.
2. **Phase Normalization**: Death overs are compared against death-over expectations; powerplay overs are compared against powerplay expectations.
3. **Role Independence**: Finishers who face few balls at high pressure are judged on their per-ball leverage and consistency rather than cumulative aggregate runs.
4. **Calibrated Index Specification**: Composite reliability score $R$ is a multi-criteria index ($0$ to $100$) calibrated via smooth logistic response functions and linear risk penalties, not an uncalibrated Bayesian posterior probability.

---

## 11. Final Top 10 Batters Selection

The official Top 10 Batters extracted from the verified Phase 5 pipeline:

| Rank | Player ID | Player Name | Reliability Score | HP Matches | HP Balls | HP Runs | HP Impact/Ball | Baseline Impact | Uplift | Consistency | Uncertainty (SE) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **46066** | **Vipraj Nigam** | **92.69** | 6 | 47 | 105 | +2.1316 | -0.9503 | +3.0819 | 100.0% | 0.2875 |
| **2** | **6651** | **Towhid Hridoy** | **92.25** | 4 | 81 | 138 | +1.9516 | +0.0339 | +1.9177 | 100.0% | 0.5690 |
| **3** | **796** | **Matthew Wade** | **91.43** | 9 | 105 | 177 | +1.6930 | +0.0602 | +1.6328 | 88.9% | 0.4759 |
| **4** | **6448** | **Ibrahim Zadran** | **90.45** | 4 | 55 | 80 | +2.0152 | +0.1428 | +1.8724 | 100.0% | 0.8358 |
| **5** | **152** | **Ravindra Jadeja** | **84.80** | 23 | 233 | 382 | +0.9979 | +0.0232 | +0.9747 | 73.9% | 0.3051 |
| **6** | **1219** | **David Willey** | **84.05** | 8 | 62 | 77 | +1.5563 | -1.5015 | +3.0578 | 87.5% | 2.6941 |
| **7** | **2984** | **Sikandar Raza** | **80.96** | 7 | 72 | 147 | +1.4098 | -0.0127 | +1.4225 | 71.4% | 1.0904 |
| **8** | **4708** | **Rinku Singh** | **80.77** | 15 | 204 | 408 | +1.5271 | +0.3412 | +1.1859 | 66.7% | 0.5816 |
| **9** | **7897** | **Namboori Tilak Varma** | **80.62** | 17 | 168 | 321 | +1.0323 | +0.3701 | +0.6622 | 76.5% | 0.9241 |
| **10** | **4686** | **Joshua Clarkson** | **80.21** | 4 | 52 | 70 | +1.0796 | +0.0539 | +1.0257 | 75.0% | 0.7214 |

### Statistical Profiles & Evidence:
- **Vipraj Nigam (Rank 1)**: Outstanding crisis elevation. Under pressure, scored 105 runs off 47 balls (+2.1316 impact/ball), winning or securing advantage in 100% of pressure matches, yielding an extraordinary +3.0819 uplift over ordinary performance.
- **Towhid Hridoy (Rank 2)**: Sustained 81 balls of pressure across 4 matches for 138 runs. Demonstrated 100% positive match impact consistency with minimal dismissal vulnerability.
- **Matthew Wade (Rank 3)**: World-class finisher profile. 105 high-pressure balls faced across 9 distinct fixtures, scoring 177 runs with an 88.9% match-level positive impact ratio.
- **Ravindra Jadeja (Rank 5)**: The benchmark for sustained longevity under pressure. Faced 233 balls across 23 pressure matches (382 runs), maintaining a +0.9979 per-ball net impact and exceptionally low uncertainty (SE: 0.3051).
- **Rinku Singh (Rank 8)**: Iconic clutch performance backed by data: 204 pressure balls across 15 matches, 408 runs scored, +1.5271 net impact per ball, and +1.1859 uplift.

---

## 12. Final Top 10 Bowlers Selection

The official Top 10 Bowlers extracted from the verified Phase 5 pipeline:

| Rank | Player ID | Player Name | Reliability Score | HP Matches | HP Legal Balls | HP Runs Conc. | HP Wickets | HP Impact/Ball | Baseline Impact | Uplift | Consistency | Uncertainty (SE) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **6237** | **Manimaran Siddharth** | **88.46** | 3 | 38 | 52 | 5 | +1.8374 | -0.3603 | +2.1977 | 100.0% | 0.6886 |
| **2** | **29080** | **Muhammad Khan** | **88.39** | 3 | 50 | 79 | 6 | +1.3838 | -0.4766 | +1.8604 | 100.0% | 0.5051 |
| **3** | **7699** | **Abbas Afridi** | **88.32** | 14 | 159 | 250 | 19 | +1.2669 | +0.4464 | +0.8205 | 85.7% | 0.5432 |
| **4** | **4856** | **Benjamin Sears** | **86.06** | 6 | 49 | 80 | 7 | +1.8047 | +0.0570 | +1.7477 | 83.3% | 1.0957 |
| **5** | **6097** | **Brydon Carse** | **84.21** | 5 | 55 | 63 | 5 | +1.1038 | -0.0264 | +1.1302 | 100.0% | 0.8376 |
| **6** | **8009** | **Junaid Siddique** | **84.01** | 10 | 44 | 56 | 5 | +1.4796 | +0.3387 | +1.1409 | 80.0% | 0.5151 |
| **7** | **27504** | **Dushan Hemantha** | **82.58** | 5 | 73 | 91 | 9 | +1.7455 | +1.0289 | +0.7166 | 80.0% | 1.5528 |
| **8** | **5809** | **Naveen ul Haq** | **81.10** | 10 | 93 | 177 | 12 | +1.3173 | +0.0880 | +1.2293 | 70.0% | 0.6153 |
| **9** | **4779** | **Pieter Willem Mulder** | **77.44** | 4 | 36 | 66 | 4 | +1.1316 | -0.3084 | +1.4400 | 75.0% | 1.5856 |
| **10** | **4499** | **Saqib Mahmood** | **77.29** | 6 | 36 | 51 | 4 | +1.1926 | +0.3368 | +0.8558 | 83.3% | 3.3680 |

### Statistical Profiles & Evidence:
- **Manimaran Siddharth (Rank 1)**: Lethal defensive squeeze. In 38 pressure balls, took 5 key top/middle order wickets conceding only 52 runs (+1.8374 impact/ball) with a 100% positive match ratio.
- **Muhammad Khan (Rank 2)**: 50 high-pressure legal balls bowled across 3 matches, taking 6 wickets with +1.3838 net impact per ball and +1.8604 uplift.
- **Abbas Afridi (Rank 3)**: Unrivaled high-volume wicket predator under pressure. Bowled 159 pressure legal balls across 14 matches, capturing 19 wickets (1.20 wickets per match) with an 85.7% positive consistency ratio.
- **Benjamin Sears (Rank 4)**: High-pace breakthrough threat. 49 pressure balls, 7 wickets, +1.8047 net impact per ball.
- **Naveen ul Haq (Rank 8)**: Death-overs specialist with 93 pressure balls across 10 matches, claiming 12 wickets and maintaining +1.2293 pressure uplift.

---

## 13. Ranking Robustness & Sensitivity Analysis

### 13.1 Weight Perturbation Analysis
Rankings were stress-tested against 3 alternative weighting regimes:
- **Alt 1 (Impact-Heavy)**: 50% Impact, 20% Uplift, 15% Consistency, 15% Confidence.
- **Alt 2 (Uplift-Heavy)**: 20% Impact, 50% Uplift, 15% Consistency, 15% Confidence.
- **Alt 3 (Consistency-Heavy)**: 25% Impact, 25% Uplift, 35% Consistency, 15% Confidence.

| Discipline | Weighting Regime | Spearman Correlation ($\rho$) | Kendall Tau ($\tau$) | Top-10 Cohort Overlap |
|:---|:---|:---:|:---:|:---:|
| **Batting** | Alt 1 (Impact-Heavy) | `0.9957` | `0.9481` | **9 / 10** |
| **Batting** | Alt 2 (Uplift-Heavy) | `0.9810` | `0.8913` | **9 / 10** |
| **Batting** | Alt 3 (Consistency-Heavy) | `0.9852` | `0.9010` | **8 / 10** |
| **Bowling** | Alt 1 (Impact-Heavy) | `0.9913` | `0.9205` | **8 / 10** |
| **Bowling** | Alt 2 (Uplift-Heavy) | `0.9788` | `0.8775` | **9 / 10** |
| **Bowling** | Alt 3 (Consistency-Heavy) | `0.9832` | `0.8875` | **9 / 10** |

### 13.2 Leave-Best-Match-Out Robustness (Non-Outlier Verification):
Every selected player's single highest net impact match was removed, and their per-ball impact was recomputed:
- **10 / 10 Batters (100%)** maintained strictly positive impact per ball (mean retained: 82.5%).
- **10 / 10 Bowlers (100%)** maintained strictly positive impact per ball (mean retained: 76.9%).
- This conclusively proves that selections represent sustained reliability rather than single-match fluke performances.

---

## 14. Quality Gate & Automated Validation Results

All phases were audited by automated pytest suites:
- **Phase 1 Ingestion Tests**: 6 passed (schema integrity, encoding, zip traversal safety).
- **Phase 1 Quality Tests**: 11 passed (referential keys, orphan checks, speed gun anomalies).
- **Phase 2 State Tests**: 12 passed (0 future leakage, innings resets, DLS targets).
- **Phase 3 Pressure Tests**: 21 passed (scenario tests A–H, bounds [0,100], player independence).
- **Phase 4 Reliability Tests**: 22 passed (cricket laws, shrinkage, CI bounds, out-of-fold models).
- **Phase 5 Ranking Tests**: 14 passed (16-point quality gate checklist, micro-reconciliation).
- **Phase 6 Submission Tests**: 4 passed (cross-file consistency, PDF integrity, dropdown match).
- **Total Automated Test Suite**: **90 / 90 tests passed (100% pass rate)**.

---

## 15. Methodological Limitations

1. **Tournament Historical Window**: Analysis is strictly bound to the 883 matches (867 with ball-by-ball deliveries) provided in the official hackathon data pack.
2. **Conservative Exposure Cutoffs**: Elite players with fewer than 20 pressure balls faced were excluded to prevent small-sample bias, prioritizing proven consistency over unverified potential.
3. **Speed Gun Calibration**: As documented in Phase 1, raw `bowl_speed` contained 19 sensor anomalies (e.g. 19.8 km/h or 220 km/h) and was excluded from pressure models.
4. **Ranking Granularity**: Small point differences between adjacent ranks (e.g. Rank 1 vs Rank 2: 92.69 vs 92.25) reflect statistical proximity; both represent elite tier performers.

---

## 16. Conclusion

The developed analytics engine provides an objective, transparent, and reproducible statistical framework for identifying cricket reliability under pressure. By reconstructing pre-delivery game context, formulating asymmetric dual pressure indices, estimating leave-one-match-out performance baselines, and applying Empirical Bayes shrinkage, the methodology surfaces players who genuinely elevate their teams in crisis moments.

The rankings demonstrate that reliability is a multidimensional trait requiring not merely raw shot-making or pace, but execution discipline, low downside variance, and sustained clutch performance across matches.

---

## 17. Reproducibility & Execution Guide

### System Requirements:
- Python 3.11+ (verified on Python 3.13.7)
- Packages: `pandas>=2.0.0`, `numpy>=1.24.0`, `pyarrow>=14.0.0`, `pytest>=8.0.0`, `pymupdf>=1.23.0`

### Pipeline Execution Commands:
```bash
# 1. Run Complete Ingestion & Validation (Phase 1)
python scripts/run_phase1.py

# 2. Run Match-State Reconstruction (Phase 2)
python scripts/run_phase2.py

# 3. Run Pressure Detection Engine (Phase 3)
python scripts/run_phase3.py

# 4. Run Player Performance & Reliability Scoring (Phase 4)
python scripts/run_phase4.py

# 5. Run Final Top-10 Ranking & Audits (Phase 5)
python scripts/run_phase5.py

# 6. Generate Publication Methodology Report PDF (Phase 6)
python scripts/generate_methodology_report.py

# 7. Execute Full Regression Test Suite
pytest tests -v
```
All outputs are deterministically reproducible with zero network access required.

