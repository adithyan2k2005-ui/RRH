# Phase 5: Ranking Stability & Sensitivity Analysis Report

## 1. Weight Sensitivity Perturbation Analysis

We evaluated ranking robustness across three alternative weighting regimes:
- **Alt 1 (Impact-Heavy)**: 50% Impact, 20% Uplift, 15% Consistency, 15% Sample Size.
- **Alt 2 (Uplift-Heavy)**: 20% Impact, 50% Uplift, 15% Consistency, 15% Sample Size.
- **Alt 3 (Consistency-Heavy)**: 25% Impact, 25% Uplift, 35% Consistency, 15% Sample Size.

### Batting Weight Sensitivity Results

| Weighting Regime | Spearman Rank Correlation (ρ) | Kendall Tau Correlation (τ) | Top-10 Cohort Overlap |
|:---|:---:|:---:|:---:|
| alt1_impact_heavy | `0.9957` | `0.9481` | **9/10** |
| alt2_uplift_heavy | `0.9810` | `0.8913` | **9/10** |
| alt3_consistency_heavy | `0.9852` | `0.9010` | **8/10** |

### Bowling Weight Sensitivity Results

| Weighting Regime | Spearman Rank Correlation (ρ) | Kendall Tau Correlation (τ) | Top-10 Cohort Overlap |
|:---|:---:|:---:|:---:|
| alt1_impact_heavy | `0.9913` | `0.9205` | **8/10** |
| alt2_uplift_heavy | `0.9788` | `0.8775` | **9/10** |
| alt3_consistency_heavy | `0.9832` | `0.8875` | **9/10** |

## 2. Leave-Best-Match-Out Robustness (Non-Outlier Verification)

To guarantee that candidates are genuinely reliable across matches rather than single-match outliers, each player's single highest net impact match was excluded and their per-ball impact was recalculated.

### Batters Leave-Best-Match-Out

| Rank | Player ID | Player Name | HP Matches | Original Impact/Ball | Ex-Best Impact/Ball | Retained % | Remains Positive? |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | 46066 | Vipraj Nigam | 6 | +2.1316 | +1.9034 | 89.3% | **True** |
| 2 | 6651 | Towhid Hridoy | 4 | +1.9516 | +1.5670 | 80.3% | **True** |
| 3 | 796 | Matthew Wade | 9 | +1.6930 | +1.4729 | 87.0% | **True** |
| 4 | 6448 | Ibrahim Zadran | 4 | +2.0152 | +2.7300 | 135.5% | **True** |
| 5 | 152 | Ravindra Jadeja | 23 | +0.9979 | +0.8957 | 89.8% | **True** |
| 6 | 1219 | David Willey | 8 | +1.5563 | +1.2837 | 82.5% | **True** |
| 7 | 2984 | Sikandar Raza | 7 | +1.4098 | +0.6484 | 46.0% | **True** |
| 8 | 4708 | Rinku Singh | 15 | +1.5271 | +1.3669 | 89.5% | **True** |
| 9 | 7897 | Namboori Tilak Varma | 17 | +1.0323 | +0.7966 | 77.2% | **True** |
| 10 | 4686 | Joshua Clarkson | 4 | +1.0796 | +0.4042 | 37.4% | **True** |

### Bowlers Leave-Best-Match-Out

| Rank | Player ID | Player Name | HP Matches | Original Impact/Ball | Ex-Best Impact/Ball | Retained % | Remains Positive? |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | 6237 | Manimaran Siddharth | 3 | +1.8374 | +1.1995 | 65.3% | **True** |
| 2 | 29080 | Muhammad Khan | 3 | +1.3838 | +1.0352 | 74.8% | **True** |
| 3 | 7699 | Abbas Afridi | 14 | +1.2669 | +1.1514 | 90.9% | **True** |
| 4 | 4856 | Benjamin Sears | 6 | +1.8047 | +1.5816 | 87.6% | **True** |
| 5 | 6097 | Brydon Carse | 5 | +1.1038 | +1.0112 | 91.6% | **True** |
| 6 | 8009 | Junaid Siddique | 10 | +1.4796 | +1.2134 | 82.0% | **True** |
| 7 | 27504 | Dushan Hemantha | 5 | +1.7455 | +1.3047 | 74.7% | **True** |
| 8 | 5809 | Naveen ul Haq | 10 | +1.3173 | +0.7602 | 57.7% | **True** |
| 9 | 4779 | Pieter Willem Mulder | 4 | +1.1316 | +1.4592 | 128.9% | **True** |
| 10 | 4499 | Saqib Mahmood | 6 | +1.1926 | +0.2074 | 17.4% | **True** |
