# SupeRR Intelligence Lab — Frontend & API Defects Register
## Critical Repair 3 Defect Audit, Root Cause Analysis, and Verification

**Date**: November 18, 2026  
**Auditor**: Senior Full-Stack Architect, React/TypeScript & FastAPI Specialist  
**Status**: **ALL DEFECTS RESOLVED & VERIFIED (0 OPEN DEFECTS)**  

---

### 1. Defect Summary Table

| Defect ID | Severity | Category | Component / Route | Root Cause Summary | Resolution Status |
|:---|:---:|:---:|:---|:---|:---:|
| **DEF-001** | **CRITICAL** | Frontend Crash | `Overview.tsx` (Recharts) | Minified React error #31: `competitions_distribution` treated as dictionary object instead of array of `CompetitionStat` objects | **RESOLVED & VERIFIED** |
| **DEF-002** | **CRITICAL** | Backend API 500 | `backend/api/routes/players.py` | `NameError: name 'pd' is not defined` during player dossier and dataset extraction | **RESOLVED & VERIFIED** |
| **DEF-003** | **HIGH** | Functional Failure | `backend/api/routes/datasets.py` | Pandas 2.x string column search failed due to strict `df[col].dtype == "object"` check omitting string dtype columns | **RESOLVED & VERIFIED** |
| **DEF-004** | **HIGH** | Contract Discrepancy | `backend/api/routes/methodology.py` | Outdated reliability weights `{0.35, 0.30, 0.20, 0.15}` returned instead of authoritative Repair 1 specification `{0.40, 0.25, 0.20, 0.15}` | **RESOLVED & VERIFIED** |
| **DEF-005** | **MEDIUM** | Documentation / UI Mismatch | `frontend/src/pages/MethodologyReports.tsx` | UI displayed preliminary shrinkage parameter $k_0 = 15.0$ instead of verified $k_0 = 20.0$ (batting) and $24.0$ (bowling) | **RESOLVED & VERIFIED** |
| **DEF-006** | **MEDIUM** | Contract Naming | `backend/api/routes/overview.py` & `models.py` | Dual naming aliases (`phase_name`/`name`, `deliverable`/`key_output`) not unified, risking undefined field rendering | **RESOLVED & VERIFIED** |
| **DEF-007** | **LOW** | Robustness / UX | `frontend/src/services/api.ts` | Missing defensive runtime validation prior to Recharts ingestion, allowing corrupted payloads to propagate to DOM | **RESOLVED & VERIFIED** |
| **DEF-008** | **LOW** | Resiliency | `frontend/src/components/common/ErrorBoundary.tsx` | ErrorBoundary needed enhanced fallback recovery with reload controls for granular page recovery | **RESOLVED & VERIFIED** |

---

### 2. Detailed Defect Reports & Root Cause Analyses

#### DEF-001: Minified React Error #31 in Overview (`competitions_distribution`)
- **Severity**: Critical (P0) — Application crash on initial load.
- **Location**: `frontend/src/pages/Overview.tsx`, lines 260–290; `frontend/src/services/api.ts`.
- **Symptom**:
  Opening the home page (`http://localhost:8000/`) produced an uncaught exception:
  `Minified React error #31: Objects are not valid as a React child (found: object with keys {comp_id, comp_name, matches_count, deliveries_count}).`
  The entire React tree unmounted, leaving a blank viewport.
- **Root Cause**:
  In earlier prototypes, `competitions_distribution` was typed as `Record<string, number>`. The backend Pydantic model evolved into a list of structured objects (`List[CompetitionStat]`), each containing `comp_id`, `comp_name`, `matches_count`, and `deliveries_count`. The frontend code iterated over the payload with `Object.entries()`, passing the raw object as a child node or chart value to Recharts `<Bar />` and `<XAxis />`.
- **Resolution**:
  1. Updated `OverviewResponse` interface in `frontend/src/services/api.ts`:
     ```typescript
     export interface CompetitionStat {
       comp_id: string;
       comp_name: string;
       matches_count: number;
       deliveries_count: number;
     }
     export interface OverviewResponse {
       ...
       competitions_distribution: CompetitionStat[];
     }
     ```
  2. In `Overview.tsx`, converted the Recharts data transformation into an explicit array mapping with numeric casting:
     ```typescript
     const competitionChartData = Array.isArray(data.competitions_distribution)
       ? data.competitions_distribution.map((c) => ({
           name: c.comp_name.replace("Indian Premier League", "IPL").replace("ICC Men's ", ""),
           matches: Number(c.matches_count) || 0,
           deliveries: Number(c.deliveries_count) || 0,
         }))
       : [];
     ```
  3. Added `validateOverviewResponse()` in `frontend/src/services/api.ts` to ensure runtime safety before state update.
- **Verification**: Verified via real MS Edge headless browser test suite (`01_overview_desktop.png`). Zero console errors, chart renders 141 competitions cleanly.

---

#### DEF-002: Backend NameError in Player Routes (`import pandas as pd`)
- **Severity**: Critical (P0) — API 500 Internal Server Error.
- **Location**: `backend/api/routes/players.py`, line 1.
- **Symptom**:
  Invoking `GET /api/players` or `GET /api/players/{player_id}` triggered a 500 response:
  `NameError: name 'pd' is not defined` when extracting candidate metrics and calculating percentile bands.
- **Root Cause**:
  `players.py` used `pd.isna()` and `pd.DataFrame` in helper normalization routines, but lacked the top-level import statement `import pandas as pd`.
- **Resolution**:
  Added `import pandas as pd` to the imports header of `backend/api/routes/players.py`.
- **Verification**: Executed `pytest tests/backend/test_api_endpoints.py::test_get_players_list`. Returned HTTP 200 with 114 evaluated players.

---

#### DEF-003: String Filtering Failure in Dataset Records (`datasets.py`)
- **Severity**: High (P1) — Search functionality broken for string columns.
- **Location**: `backend/api/routes/datasets.py`, lines 105–125.
- **Symptom**:
  Searching for player names (e.g. `"Vipraj"`, `"Klaasen"`) in the Data Explorer returned 0 records even though records were present in the dataset.
- **Root Cause**:
  The route filtered columns with:
  `str_cols = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype).startswith("string")]`
  Under Pandas 2.x on Python 3.13, string-inferred columns had `dtype == "str"`, which evaluated to `False` under both conditions, resulting in an empty list of search columns and an empty search mask.
- **Resolution**:
  Replaced strict dtype checks with universal string conversion mask:
  ```python
  if search:
      search_lower = search.strip().lower()
      masks = [
          df[col].astype(str).str.lower().str.contains(search_lower, na=False)
          for col in df.columns
      ]
      if masks:
          combined_mask = pd.concat(masks, axis=1).any(axis=1)
          df = df[combined_mask]
  ```
- **Verification**: Executed search test for `"Vipraj"` against `player_mappings`. Returned exactly 1 record (`Vipraj Nigam`). Verified in browser test suite (`02_data_explorer_desktop.png`).

---

#### DEF-004: Stale Reliability Weights in Methodology API Route
- **Severity**: High (P1) — Statistical contract discrepancy.
- **Location**: `backend/api/routes/methodology.py`, line 28.
- **Symptom**:
  `GET /api/methodology` returned outdated pilot weights:
  `{"hp_uplift": 0.35, "consistency": 0.30, "sample_adequacy": 0.20, "win_context": 0.15}`
  This contradicted the verified Repair 1 specification and hackathon report formula.
- **Root Cause**:
  A hardcoded default dictionary in `backend/api/routes/methodology.py` had not been synchronized with the authoritative weights defined in `src/models/scoring_spec.py`.
- **Resolution**:
  Updated the weights dictionary in `backend/api/routes/methodology.py`:
  ```python
  "reliability_weights": {
      "hp_uplift": 0.40,
      "consistency": 0.25,
      "sample_adequacy": 0.20,
      "win_context": 0.15,
  }
  ```
- **Verification**: Verified via `pytest tests/backend/test_api_endpoints.py::test_get_methodology`. Returned exactly `{0.40, 0.25, 0.20, 0.15}`, sum = 1.00.

---

#### DEF-005: Empirical Bayes Shrinkage Constant Inconsistency in Methodology Page
- **Severity**: Medium (P2) — UI text discrepancy with mathematical model.
- **Location**: `frontend/src/pages/MethodologyReports.tsx`, line 214.
- **Symptom**:
  Methodology tab rendered: `"Empirical Bayes shrinkage parameter k0 = 15.0"`.
- **Root Cause**:
  Preliminary prototype text in the React component was static and had not been updated after Repair 1 established role-specific empirical shrinkage parameters: $k_0 = 20.0$ balls for batting and $k_0 = 24.0$ balls for bowling.
- **Resolution**:
  Updated `frontend/src/pages/MethodologyReports.tsx` to read:
  `"Empirical Bayes shrinkage parameter k₀ = 20.0 balls (batting), 24.0 balls (bowling)"`.
- **Verification**: Verified via browser test screenshot `07_methodology_reports_desktop.png`.

---

#### DEF-006: Pipeline Phase Property Naming Mismatch
- **Severity**: Medium (P2) — Potential undefined field rendering in fallback states.
- **Location**: `backend/api/schemas/models.py`, `backend/api/routes/overview.py`.
- **Symptom**:
  Frontend components occasionally looked for `name` and `key_output` while backend schemas emitted `phase_name` and `deliverable`.
- **Root Cause**:
  Differences between early specification drafts and final Pydantic schemas.
- **Resolution**:
  Added dual alias properties in `PhaseStatus` Pydantic model and TypeScript interfaces so both property names resolve reliably.
- **Verification**: Verified across both Overview pipeline cards and direct API serialization.

---

#### DEF-007: Lack of Defensive Runtime Validation for API Responses
- **Severity**: Low (P3) — Fragility to network payload corruption.
- **Location**: `frontend/src/services/api.ts`.
- **Symptom**:
  If the network returned unexpected shapes or nulls, components would throw unhandled runtime TypeError exceptions.
- **Root Cause**:
  TypeScript interfaces provide build-time type checking but are erased at runtime in JavaScript.
- **Resolution**:
  Added explicit runtime sanitizers and validators (`validateOverviewResponse`, fallback empty arrays for all chart feeds).
- **Verification**: Verified by testing API responses with edge-case null parameters.

---

#### DEF-008: Generic ErrorBoundary Recovery Controls
- **Severity**: Low (P3) — Degraded UX in error recovery.
- **Location**: `frontend/src/components/common/ErrorBoundary.tsx`.
- **Symptom**:
  When a subcomponent threw, the user was left with a generic error message with no actionable reload or navigation option.
- **Root Cause**:
  Basic fallback component without session reset or retry dispatchers.
- **Resolution**:
  Enhanced `ErrorBoundary.tsx` with clear Rajasthan Royals branding, diagnostic error trace toggle, and a "Retry / Reload View" button that resets component state.
- **Verification**: Verified through simulated component throw test.

---

### 3. Defect Closure Sign-Off

All 8 identified defects have been completely repaired, regression-tested, and verified through both automated unit/integration tests (`pytest`) and live browser execution (`playwright`).

**Residual Open Defects**: 0  
**Critical/Blocker Defects**: 0  
**Status**: **CLEARED FOR CRITICAL REPAIR 3 COMPLETION**
