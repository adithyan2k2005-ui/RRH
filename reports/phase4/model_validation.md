# SupeRR Selector Season 2 — Phase 4 Model Validation Report

## 1. Domain Scoring Semantics Audit
- **Wides excluded from balls faced**: True (PASSED)
- **No-balls counted as balls faced**: True (PASSED)
- **Batter runs strictly exclude extras**: True (PASSED)
- **Striker dismissals correctly isolated**: True (10606 strikers out of 10881 team wickets)
- **Byes & leg-byes excluded from bowler runs**: False (PASSED)
- **Wides debited to bowler**: True (PASSED)
- **Run-outs excluded from bowler wickets**: True (PASSED)

---

## 2. Reliability Ratings Distribution
### Batters (Eligible n=155):
- Mean Score: 46.93
- Median Score: 48.64
- Range: [0.0, 100.0] Compliant: True
- Ineligible Gating: True
- Confidence Intervals Valid: True

### Bowlers (Eligible n=270):
- Mean Score: 44.23
- Median Score: 43.9
- Range: [0.0, 100.0] Compliant: True
- Ineligible Gating: True
- Confidence Intervals Valid: True
