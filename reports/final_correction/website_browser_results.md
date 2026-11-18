# Headless Browser Automation Test Results

**Project:** Rajasthan Royals SupeRR Selector Season 2 — Round 1  
**Audit Timestamp:** 2026-11-18T10:22:24Z  
**Engine:** Playwright with Microsoft Edge (Chromium Engine `157.0.4341.60`)  
**Backend:** FastAPI (Python 3.13) on `http://127.0.0.1:8000`  
**Frontend:** React 18 / Vite on `http://127.0.0.1:5173` and bundled SPA  

---

## 1. Route-by-Route Verification Matrix

| Stage | Route URL | Viewport | Verified Controls & Visuals | Console Errors | Network Failures | Result | Screenshot File |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | `/` (Overview) | 1920x1080 | Centered RR emblem card, headline KPIs, tournament distribution bar chart, dynamic pipeline phases | 0 | 0 | **PASS** | [`01_overview_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/01_overview_desktop.png) |
| **2** | `/explorer` | 1920x1080 | Parquet dataset dropdown, column schema badges, 50-row pagination preview table | 0 | 0 | **PASS** | [`02_data_explorer_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/02_data_explorer_desktop.png) |
| **3** | `/replay` | 1920x1080 | Match selector (867 active fixtures), chronological delivery timeline, dual pressure curve overlay | 0 | 0 | **PASS** | [`03_match_replay_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/03_match_replay_desktop.png) |
| **4** | `/pressure` | 1920x1080 | Interactive RRR and wicket deficit sliders, 2D/3D pressure response surface canvas | 0 | 0 | **PASS** | [`04_pressure_lab_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/04_pressure_lab_desktop.png) |
| **5** | `/players` | 1920x1080 | Candidate search input, candidate card grid, high-pressure vs ordinary splits | 0 | 0 | **PASS** | [`05_player_intelligence_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/05_player_intelligence_desktop.png) |
| **6** | `/rankings` | 1920x1080 | Batters/Bowlers tabs, Top 10 tables (**Vipraj Nigam #1, M. Siddharth #1**), radar comparison, CSV download | 0 | 0 | **PASS** | [`06_reliability_rankings_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/06_reliability_rankings_desktop.png) |
| **7** | `/reports` | 1920x1080 | 4-pillar formula documentation, PDF previewer, dynamic download buttons | 0 | 0 | **PASS** | [`07_methodology_reports_desktop.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/07_methodology_reports_desktop.png) |
| **8** | `/rankings` (Mobile) | 390x844 | Mobile responsive hamburger menu, responsive table cards, touch scroll | 0 | 0 | **PASS** | [`08_mobile_rankings_viewport.png`](file:///c:/Users/Adithyan%20R/Documents/RR/superr-selector-analytics/reports/master_verification/screenshots/08_mobile_rankings_viewport.png) |

---

## 2. Visual & Architectural Integrity

1. **Emblem Card Polish:** The Rajasthan Royals emblem is centered, framed with ambient burgundy glow, and free of any text labels or redundant "Official Design Inspiration" containers.
2. **Zero Errors:** 0 console errors, 0 unhandled exceptions, and 0 failed network requests recorded during automated execution.
