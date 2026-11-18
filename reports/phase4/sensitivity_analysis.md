# SupeRR Selector Season 2 — Phase 4 Sensitivity Analysis Report

## 1. Wicket Value Sensitivity ($W_{\text{val}}$)
Tested impact of varying wicket run values across $W_{\text{val}} \in \{0, 10, 15, 20, 25\}$:
- At $W_{\text{val}} = 0$ (pure run impact): Top reliable batters are dominated purely by high strike rates without penalizing dismissals.
- At $W_{\text{val}} = 20$ (baseline empirical): Balances boundary striking with wicket preservation, matching T20 death overs wicket economics (19.7 runs/wicket).
- Spearman rank correlation between $W_{\text{val}}=15$ and $W_{\text{val}}=25$ top-15 batters exceeds 0.94, demonstrating robust stability.

---

## 2. Eligibility Threshold Sensitivity
| Batting Threshold ($HP_{\text{balls}} / HP_{\text{matches}}$) | Qualified Batters | % of Batters |
| :--- | :--- | :--- |
| 15 balls / 2 matches | 197 | 22.2% |
| **20 balls / 3 matches (Default)** | **155** | **17.5%** |
| 25 balls / 3 matches | 149 | 16.8% |
| 30 balls / 4 matches | 129 | 14.5% |

| Bowling Threshold ($HP_{\text{balls}} / HP_{\text{matches}}$) | Qualified Bowlers | % of Bowlers |
| :--- | :--- | :--- |
| 18 balls / 3 matches | 280 | 43.3% |
| **24 balls / 3 matches (Default)** | **270** | **41.7%** |
| 30 balls / 4 matches | 238 | 36.8% |

Threshold choice maintains a competitive, statistically sound candidate pool while filtering 1-over flukes.
