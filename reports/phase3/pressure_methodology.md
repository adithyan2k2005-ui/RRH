# SupeRR Selector Season 2 — Phase 3 Pressure Methodology Document

## 1. Overview & Conceptual Definition
Cricket match pressure represents the situational difficulty and critical importance of a match state immediately before a delivery is bowled.
Pressure is a property of the match context, strictly independent of the players' identities and their subsequent execution on that ball.

---

## 2. Fundamental Distinction: Batting vs Bowling Pressure
A core domain principle in cricket is that **batting difficulty does NOT equal bowling difficulty**:
- **Batting Pressure** peaks when the required run rate exceeds normal scoring expectations, wickets in hand are few, or the team suffers an early collapse.
- **Bowling Pressure** peaks when the game is tightly contested (wire finish), the batting team is on track or ahead of the rate, and the batting team has wickets in hand to attack.
- **Desperation Asymmetry**: When a team requires 36 runs from 6 balls with 8 wickets down, batting desperation is extreme, but bowling pressure is negligible because the bowler has massive defensive cushion.

---

## 3. Mathematical Formulations

### A. Second Innings (Chase)
1. **Chase Urgency ($U$)**:
   $$U = \frac{1}{1 + e^{-0.45 \times (\text{RRR} - R_{\text{fmt}})}}$$
   where $R_{\text{fmt}}$ is the **format-level global baseline** (T20: 9.21 rpo, T20I: 8.55 rpo).
   The format-level reference is used (not the phase-specific rate) so that an RRR of 10.2 rpo
   is recognised as genuinely difficult even during Death overs where phase norms reach 10.24 rpo.
2. **Wicket Vulnerability ($V$)**:
   $$V = \left(\frac{10 - W_{\text{rem}}}{9}\right)^{1.35}$$
3. **Time Progression ($T$)**:
   $$T = \frac{\text{balls\_bowled}}{\text{scheduled\_balls}}$$
4. **Match Closeness ($C$)**:
   $$C = \exp\left(-\frac{(\text{RRR} - R_{\text{phase}})^2}{2 \times 3.5^2}\right) \times (0.5 + 0.5 T)$$
   where $R_{\text{phase}}$ is the phase-specific baseline (Powerplay 8.68, Middle 8.34, Death 10.24).
5. **Batting Score**:
   $$P_{\text{bat}} = 100 \times \text{clamp}\left((0.45 U + 0.35 V + 0.20 \sqrt{UV}) \times S_{\text{stakes}}, 0, 1\right)$$
6. **Bowling Score**:
   $$P_{\text{bowl}} = 100 \times \text{clamp}\left((0.50 C + 0.30 (1-V) T + 0.20 \max(0, 1-U) T) \times S_{\text{stakes}}, 0, 1\right)$$

### B. First Innings (Target Setting)
1. **Par Deficit ($D_{\text{par}}$)**:
   $$D_{\text{par}} = \frac{1}{1 + e^{0.40 \times (\text{CRR} - R_{\text{phase}})}}$$
2. **Batting Score**:
   $$P_{\text{bat}} = 100 \times \text{clamp}\left((0.45 V + 0.35 D_{\text{par}} + 0.20 \sqrt{VT}) \times S_{\text{stakes}}, 0, 1\right)$$
3. **Bowling Score**:
   $$P_{\text{bowl}} = 100 \times \text{clamp}\left((0.40 (1-D_{\text{par}}) + 0.35 (1-V) + 0.25 T) \times S_{\text{stakes}}, 0, 1\right)$$

---

## 4. Classification Regimes
- `LOW_PRESSURE`: Score < 40.0
- `MEDIUM_PRESSURE`: 40.0 <= Score < 65.0
- `HIGH_PRESSURE`: Score >= 65.0

---

## 5. Zero Future Data Leakage Compliance
- All features rely strictly on states prior to the ball.
- Match outcome is excluded from input features.
- Parquet output is persisted at `data/processed/pressure_states.parquet` for Phase 4.

