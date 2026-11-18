# Critical Repair 1 — Initial Findings: Formula Discrepancy & Mathematical Audit

**Project**: `superr-selector-analytics`  
**Phase**: Critical Repair 1 — Reliability Formula & Methodology Reconciliation  
**Auditor**: Independent Cricket Data Science & Verification Specialist  
**Date**: November 18, 2026  
**Status**: **ROOT CAUSE CONFIRMED — CODE VERIFIED AS GROUND TRUTH**  

---

## 1. Problem Identification

During audit of the final hackathon submission materials, an explicit contradiction was detected between the implemented scoring algorithm in Python and the mathematical description in the methodology documentation:

### Code Implementation (`src/reliability/reliability_model.py`):
```python
DEFAULT_RELIABILITY_WEIGHTS = {
    "weight_impact": 0.40,
    "weight_uplift": 0.25,
    "weight_consistency": 0.20,
    "weight_confidence": 0.15,
}

# Component 1: Logistic scaling of shrunk impact
s_impact = 100.0 / (1.0 + np.exp(-3.0 * shrunk_impact))

# Component 2: Logistic scaling of pressure uplift
s_uplift = 100.0 / (1.0 + np.exp(-3.5 * uplift))

# Component 3: Match consistency (60% positive match ratio + 40% downside floor)
s_consistency = 100.0 * (0.60 * pos_ratio + 0.40 * p25_norm)

# Component 4: Statistical confidence (shrinkage weight * inverted cluster standard error)
s_confidence = 100.0 * shrink_w * (1.0 / (1.0 + se))

# Composite score:
composite = 0.40 * s_impact + 0.25 * s_uplift + 0.20 * s_consistency + 0.15 * s_confidence
```

### Documentation Formulation (`scripts/generate_methodology_report.py` & `submission/methodology_report.md`):
```text
Reliability Score = 0.35 * Pctl(mu_shrunk) + 0.30 * Pctl(Delta_uplift) + 0.20 * Pctl(CR) + 0.15 * Pctl(1 / SE_cluster)
"All components are scaled to percentile ranks ([0, 100]) across the qualified candidate pool."
```

---

## 2. Source Inspection & Provenance Analysis

A systematic trace across all project phases revealed the timeline of this defect:

1. **Phase 4 Design & Implementation**:
   - `reports/phase4/reliability_methodology.md` correctly defined the formula:
     $$R = 0.40 \cdot S_{\text{impact}} + 0.25 \cdot S_{\text{uplift}} + 0.20 \cdot S_{\text{consistency}} + 0.15 \cdot S_{\text{confidence}}$$
   - `src/reliability/reliability_model.py` was implemented with exact weights $\{0.40, 0.25, 0.20, 0.15\}$ and logistic scaling functions ($k=3.0$ for impact, $k=3.5$ for uplift).
   - `scripts/run_phase4.py` evaluated 888 batters and 647 bowlers, applying this model and outputting `player_batting_metrics.parquet` and `player_bowling_metrics.parquet`.

2. **Phase 5 Rankings & Validation**:
   - `src/ranking/ranking_engine.py` generated the official Top 10 rankings (`outputs/top_10_batters.csv`, `outputs/top_10_bowlers.csv`).
   - The scores in the official rankings (e.g. Vipraj Nigam = 92.69, Manimaran Siddharth = 88.46) derive **strictly from the 0.40 / 0.25 / 0.20 / 0.15 model**.

3. **Phase 6 Documentation Desynchronization**:
   - When drafting the final 17-section methodology report in `scripts/generate_methodology_report.py` and `submission/methodology_report.md`, an earlier draft/conceptual formula ($0.35 / 0.30 / 0.20 / 0.15$ with percentile transformations) was accidentally copied into the text instead of querying the authoritative code module.

---

## 3. Mathematical Recomputation Audit Summary

To determine whether the code or the report prose produced the stored rankings, an independent first-principles recomputation was executed on `data/processed/player_batting_metrics.parquet` and `data/processed/player_bowling_metrics.parquet`:

- **Eligible Batters Evaluated**: 155
- **Batters Max Absolute Error**: `0.0000000000` (Exact float match across all 155 players)
- **Eligible Bowlers Evaluated**: 270
- **Bowlers Max Absolute Error**: `0.0000000000` (Exact float match across all 270 players)
- **Rankings Agreement**:
  - Top 10 Batters Player IDs Match: **TRUE** (10/10 exact order match)
  - Top 10 Batters Scores Match: **TRUE** (10/10 exact score match)
  - Top 10 Bowlers Player IDs Match: **TRUE** (10/10 exact order match)
  - Top 10 Bowlers Scores Match: **TRUE** (10/10 exact score match)

### Conclusion:
The code in `src/reliability/reliability_model.py` is the **authoritative, ground-truth engine** that produced all verified data. The report prose in `scripts/generate_methodology_report.py` and `submission/methodology_report.md` represents an erroneous manual transcription that must be corrected to reflect the real, implemented mathematics.
