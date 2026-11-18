# Test Execution & Quality Assurance Results

**Project:** Rajasthan Royals SupeRR Selector Season 2 — Round 1  
**Audit Timestamp:** 2026-11-18T10:22:24Z  

---

## 1. Pytest Test Suite Results (150 Items)

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Adithyan R\Documents\RR\superr-selector-analytics
configfile: pytest.ini
collected 150 items

tests\backend\test_api_endpoints.py ...........                          [  7%]
tests\backend\test_overview_contract.py .....                            [ 10%]
tests\test_batting_metrics.py .....                                      [ 14%]
tests\test_bowling_metrics.py ....                                       [ 16%]
tests\test_consistency.py ..                                             [ 18%]
tests\test_cricket_rules.py ....                                         [ 20%]
tests\test_cross_document_player_consistency.py ........                 [ 26%]
tests\test_dataset_integrity.py ..........                               [ 32%]
tests\test_delivery_order.py .....                                       [ 36%]
tests\test_expected_performance.py ..                                    [ 37%]
tests\test_ingestion.py ......                                           [ 41%]
tests\test_match_state.py ...                                            [ 43%]
tests\test_match_state_integration.py ....                               [ 46%]
tests\test_phase4_integration.py ....                                    [ 48%]
tests\test_phase5_integration.py .....                                   [ 52%]
tests\test_player_baselines.py ..                                        [ 53%]
tests\test_pressure_features.py .....                                    [ 56%]
tests\test_pressure_integration.py .....                                 [ 60%]
tests\test_pressure_leakage.py ...                                       [ 62%]
tests\test_pressure_model.py ........                                    [ 67%]
tests\test_ranking_eligibility.py ..                                     [ 68%]
tests\test_ranking_engine.py ...                                         [ 70%]
tests\test_ranking_integrity.py ..                                       [ 72%]
tests\test_ranking_stability.py ..                                       [ 73%]
tests\test_reliability.py ...                                            [ 75%]
tests\test_reliability_audit.py .........                                [ 81%]
tests\test_submission_integrity.py .....                                 [ 84%]
tests\test_validation.py ...........                                     [ 92%]
tests\test_verification_manifest.py ............                         [100%]

======================= 150 passed, 1 warning in 20.71s =======================
```

---

## 2. Project Verification Runner Results (`scripts/verify_project.py`)

- **Total Verification Checks Executed:** 138
- **Passed Checks:** 138 (100.0%)
- **Failed Checks:** 0
- **Official Submission Gates:** 12 / 12 PASSED (100.0%)
- **Manifest Location:** `reports/verification_manifest.json` (SHA-256: `535c475d59070a9ea2f4ddd25b04237af664182f721ef90cf0f05b3734744233`)

---

## 3. Dedicated Player-Identity Consistency Suite (`tests/test_cross_document_player_consistency.py`)

| Test Function | Description | Result |
| :--- | :--- | :---: |
| `test_top_batters_csv_ground_truth` | All 10 batters match expected ID, Name, Score | **PASSED** |
| `test_top_bowlers_csv_ground_truth` | All 10 bowlers match expected ID, Name, Score | **PASSED** |
| `test_player_mapping_integrity` | All 20 IDs match relational mapping names | **PASSED** |
| `test_methodology_markdown_player_consistency` | Markdown text matches all 20 players without substitutions | **PASSED** |
| `test_submission_selections_markdown_consistency` | Unstop selection guide matches all 20 players in order | **PASSED** |
| `test_methodology_pdf_player_consistency` | PDF text extract confirms all 20 players without substitutions | **PASSED** |
| `test_cricket_rules_explanation_accuracy` | Confirms accurate legal ball and no-ball explanation | **PASSED** |
| `test_reject_wrong_player_score_assignment` | Explicitly verifies test fails if wrong player assigned | **PASSED** |
