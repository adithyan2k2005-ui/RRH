# SupeRR Selector Season 2 — Phase 4 Reliability Methodology Document

## 1. Reliability Conceptual Definition
Reliability measures how consistently and convincingly an individual player performs above expectation across repeated high-pressure matches.

$$R = 0.40 \cdot S_{\text{impact}} + 0.25 \cdot S_{\text{uplift}} + 0.20 \cdot S_{\text{consistency}} + 0.15 \cdot S_{\text{confidence}}$$

---

## 2. Mathematical Components

### A. Shrunk Pressure Impact ($S_{\text{impact}}$)
Empirical Bayes shrinkage pulls observed sample mean impact toward the population prior:
$$w_i = \frac{n_i}{n_i + k_0}, \quad \hat{\theta}_{\text{shrunk}} = w_i \bar{y}_{i, \text{HP}} + (1 - w_i) \mu_{\text{pop}}$$
- Batting $k_0 = 20.0$ balls; Bowling $k_0 = 24.0$ balls.
- Component score: $S_{\text{impact}} = \frac{100}{1 + e^{-3.0 \cdot \hat{\theta}_{\text{shrunk}}}}$

### B. Pressure Uplift ($S_{\text{uplift}}$)
Difference between high-pressure performance and within-player ordinary baseline:
$$\text{Uplift} = \bar{y}_{i, \text{HP}} - \bar{y}_{i, \text{ord}}$$
- Component score: $S_{\text{uplift}} = \frac{100}{1 + e^{-3.5 \cdot \text{Uplift}}}$$

### C. Match-Level Consistency ($S_{\text{consistency}}$)
Protects against single-match outliers and evaluates downside performance:
$$S_{\text{consistency}} = 100 \times (0.60 \cdot \text{Positive Match Ratio} + 0.40 \cdot \text{Downside Protection})$$

### D. Statistical Confidence ($S_{\text{confidence}}$)
Rewards sample depth and low match-to-match cluster error:
$$S_{\text{confidence}} = 100 \times w_i \times \frac{1}{1 + \text{SE}_i}$$
Where $\text{SE}_i = s_i / \sqrt{m_i}$.
