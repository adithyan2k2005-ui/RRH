# Final Audit Defect Analysis & Root Cause Determination

**Project:** Rajasthan Royals SupeRR Selector Season 2 — Round 1  
**Audit Timestamp:** 2026-11-18T10:22:24Z  
**Auditors:** Independent Cricket Data Scientist, Technical Documentation Auditor & QA Lead  
**Defect Status:** All Confirmed Defects Identified, Isolated, and Fully Corrected.

---

## 1. Executive Summary

A rigorous, independent review of the `superr-selector-analytics` project uncovered critical inconsistencies that were previously obscured by superficial test assertions (which checked only row counts, file existence, and Rank #1 names). This document logs the root cause, blast radius, and corrective action for each confirmed defect.

---

## 2. Confirmed Defect Register

### Defect 1: Conflicting Player Identities Across Narrative Documents
- **Severity:** P0 (Critical Documentation / Statistical Presentation Defect)
- **Symptom:**
  While the underlying Phase 5 mathematical output files (`outputs/top_10_batters.csv` and `outputs/top_10_bowlers.csv`) correctly computed and ranked Towhid Hridoy (Rank 2), Matthew Wade (Rank 3), Ibrahim Zadran (Rank 4), Muhammad Khan (Rank 2), Abbas Afridi (Rank 3), and Benjamin Sears (Rank 4), earlier drafts and narrative summaries in `submission/methodology_report.md` (lines 43–44) and `reports/critical_repairs/repair1/completion_report.md` assigned those exact scores to famous IPL stars:
  - Batter Rank 2 (Score: 92.25) was mislabeled as **Nicholas Pooran** (actual player: **Towhid Hridoy**, ID 6651).
  - Batter Rank 3 (Score: 91.43) was mislabeled as **Tristan Stubbs** (actual player: **Matthew Wade**, ID 796).
  - Batter Rank 4 (Score: 90.45) was mislabeled as **Heinrich Klaasen** (actual player: **Ibrahim Zadran**, ID 6448).
  - Bowler Rank 2 (Score: 88.39) was mislabeled as **Jasprit Bumrah** (actual player: **Muhammad Khan**, ID 29080).
  - Bowler Rank 3 (Score: 88.32) was mislabeled as **Sunil Narine** (actual player: **Abbas Afridi**, ID 7699).
  - Bowler Rank 4 (Score: 86.06) was mislabeled as **Rashid Khan** (actual player: **Benjamin Sears**, ID 4856).
- **Root Cause:**
  During exploratory research, celebrity names were manually inserted into early markdown summaries as illustrative examples. Subsequent automated verification tests did not validate names against relational mappings and only checked Rank #1 (Vipraj Nigam and M. Siddharth), allowing the narrative text discrepancy to persist undetected.
- **Resolution:**
  Reconciled all narrative sections across `submission/methodology_report.md`, `reports/critical_repairs/repair1/`, `reports/master_verification/`, and `scripts/generate_methodology_report.py`. Added `tests/test_cross_document_player_consistency.py` to enforce strict 1-to-1 parity across all deliverables.

---

### Defect 2: Incorrect Cricket Rule in PDF & Methodology Documentation
- **Severity:** P1 (Cricket Domain Rule Documentation Error)
- **Symptom:**
  `submission/methodology_report.md` (line 95) and `scripts/generate_methodology_report.py` (line 317) stated:
  `"No-balls consume legal balls for the team and batter, but grant penalty extras."`
  This contradicted standard cricket rules (MCC Law 21) and contradicted the project's actual match-state engine (`src/features/cricket_rules.py` and `src/validation/validate_match_state.py`).
- **Root Cause:**
  A typographical error in the documentation text conflated "balls faced by the batter" with "legal balls consumed in the over". In cricket:
  - Wides and no-balls do **NOT** consume legal balls (the fielding team must re-bowl).
  - Batters **ARE** charged with a ball faced on no-balls (since the ball is bowled at them and runs can be scored off the bat), but **NOT** on wides.
  - The actual Python engine in `src/features/cricket_rules.py` correctly identified `ILLEGAL_EXTRAS_TYPES = ('wide', 'Overstep', 'other')` and never advanced the over on illegal balls.
- **Resolution:**
  Updated `submission/methodology_report.md` and `scripts/generate_methodology_report.py` to state the precise cricket laws accurately. Re-rendered `submission/methodology_report.pdf` (8 pages) reflecting the exact rules.

---

### Defect 3: Superficial Automated Verification Checks
- **Severity:** P1 (Test Architecture Gap)
- **Symptom:**
  `scripts/verify_project.py` reported 100% PASS on all gates while missing the player identity swap and rule documentation discrepancy.
- **Root Cause:**
  - `verify_phase5()` checked only `b_df.iloc[0]["player_name"] == "Vipraj Nigam"` (Rank 1 only).
  - `verify_phase6()` checked only `"Vipraj Nigam" in sel_text and "Manimaran Siddharth" in sel_text`.
  - Gate 10 only checked whether the PDF had 8 pages and contained generic words like "pressure".
  - The runner lacked cross-document string validation between narrative paragraphs, tables, CSV outputs, and relational player mappings.
- **Resolution:**
  Upgraded `scripts/verify_project.py` with:
  1. Full 20-player array validation in Phase 5 and Phase 6.
  2. Integration of `tests/test_cross_document_player_consistency.py` into Gate 11.
  3. PDF text stream inspection in Gate 10 verifying the presence of all 20 players and absence of celebrity misattributions.
  4. Explicit assertion that wides and no-balls do not consume legal balls.

---

### Defect 4: Lingering Unrelated Brand Text in Overview Component
- **Severity:** P2 (Resolved in Prior Cycle)
- **Symptom:**
  Extraneous "Official Design Inspiration" text container next to the emblem.
- **Resolution:**
  Removed from `frontend/src/components/common/RoyalEmblem.tsx` while preserving the centered Rajasthan Royals emblem card.
