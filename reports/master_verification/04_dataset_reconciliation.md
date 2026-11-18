# Master Verification Deliverable 4: Dataset Coverage & Funnel Reconciliation

**Project:** Rajasthan Royals SupeRR Selector Season 2 — Round 1  
**Audit Date:** 2026-11-18T10:04:02Z  
**Auditor:** Senior Cricket Data Engineer & Quality Auditor

---

## 1. Authoritative Source Dataset Invariants

| Dataset Entity | Record Count | Processing Step | Integrity Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Total Matches** | **883** | Ingestion & Match State | 867 fixtures with delivery records + 16 weather-abandoned fixtures | **VERIFIED** |
| **Active Matches** | **867** | Match State Reconstruction | 867 fixtures with 200,999 valid ball-by-ball deliveries | **VERIFIED** |
| **Abandoned Matches** | **16** | Data Quality Classification | Documented abandoned fixtures with playing XIs but 0 deliveries | **VERIFIED** |
| **Competitions** | **141** | Metadata Ingestion | 141 competition records across IPL and international T20 leagues | **VERIFIED** |
| **Total Deliveries** | **200,999** | Ball-by-Ball Processing | 200,999 deliveries (zero dropped, zero synthetic) | **VERIFIED** |
| **Unique Teams** | **353** | Team Standardization | 353 distinct international and domestic franchises | **VERIFIED** |
| **Player Mappings** | **6,413** | Identity Resolution | 6,413 unique player identifier mappings | **VERIFIED** |
| **Playing XI Entries** | **28,381** | Match Roster Construction | 28,381 official playing XI roster records | **VERIFIED** |

---

## 2. Ingestion Funnel Audit

```
Source Deliveries: 200,999 deliveries
  ├── Legal deliveries: 193,421 (96.23%)
  └── Extras (wides/no-balls): 7,578 (3.77%)
  └── Zero dropped rows throughout entire pipeline

Matches: 883 matches
  ├── Matches with delivery records: 867 matches
  └── Weather-abandoned fixtures: 16 matches (playing XIs intact)
```

### Anomaly Investigation: Speed Gun Radar Outliers
During Phase 1 data validation, three deliveries exhibited radar speed gun readings exceeding 165 km/h:
1. Match 1304112, Over 14.3: 175.2 km/h
2. Match 1359514, Over 3.2: 168.4 km/h
3. Match 1384402, Over 18.5: 166.1 km/h

**Resolution & Audit Action:**
These records represent known optical radar tracking glitches in venue hardware. Rather than silently modifying or dropping the raw source data (which would violate hackathon reproducibility), the pipeline flags them with a warning, tags them in the data quality report, and isolates them from velocity-based models. All deliveries remain present in the 200,999 count.
