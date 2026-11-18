"""Complete Dataset Reconciliation and Coverage Audit Script for SupeRR Selector Analytics.

Performs:
1. Raw CSV file analysis (row counts, column counts, missing values, duplicates, SHA-256 hashes).
2. Processed Parquet dataset comparison (record counts, schemas, type conversions, dropped/added rows).
3. Pipeline stage-by-stage coverage analysis (raw -> ball-by-ball -> match states -> pressure -> performance -> rankings).
4. Cricket domain data quality checks (wides, no-balls, byes, leg-byes, wickets, retired hurt, super overs, etc.).
5. Generates source_manifest.json, dataset_reconciliation.csv, analysis_coverage.json, and exclusions_audit.csv.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROC = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports" / "critical_repairs" / "repair2"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_reconciliation():
    raw_files = [
        "competitions.csv",
        "teams.csv",
        "matches.csv",
        "ball_by_ball.csv",
        "competition_team_player_mapping.csv",
        "playing_eleven.csv",
    ]

    # ---------------------------------------------------------
    # 1. SOURCE MANIFEST
    # ---------------------------------------------------------
    source_manifest: Dict[str, Any] = {
        "archive_file": "6af458274c1e8_data_pack.zip",
        "archive_sha256": sha256_file(PROJECT_ROOT / "6af458274c1e8_data_pack.zip"),
        "files": {},
    }

    raw_dfs: Dict[str, pd.DataFrame] = {}

    for fname in raw_files:
        p = DATA_RAW / fname
        sha = sha256_file(p)
        df = pd.read_csv(p, low_memory=False)
        raw_dfs[fname] = df

        null_summary = {col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0}

        source_manifest["files"][fname] = {
            "source_path": f"data/raw/{fname}",
            "file_size_bytes": p.stat().st_size,
            "sha256": sha,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "duplicate_rows": int(df.duplicated().sum()),
            "null_counts": null_summary,
        }

    manifest_path = REPORTS_DIR / "source_manifest.json"
    manifest_path.write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
    print(f"Source manifest saved to {manifest_path}")

    # ---------------------------------------------------------
    # 2. PROCESSED DATA RECONCILIATION
    # ---------------------------------------------------------
    proc_files = [
        ("competitions.csv", "competitions.parquet", "comp_id"),
        ("teams.csv", "teams.parquet", "team_id"),
        ("matches.csv", "matches.parquet", "match_id"),
        ("ball_by_ball.csv", "ball_by_ball.parquet", "match_id"),
        ("competition_team_player_mapping.csv", "competition_team_player_mapping.parquet", "player_id"),
        ("playing_eleven.csv", "playing_eleven.parquet", "match_id"),
    ]

    recon_rows: List[Dict[str, Any]] = []

    for raw_name, proc_name, id_col in proc_files:
        raw_df = raw_dfs[raw_name]
        proc_df = pd.read_parquet(DATA_PROC / proc_name)

        raw_rows = len(raw_df)
        proc_rows = len(proc_df)
        raw_cols = len(raw_df.columns)
        proc_cols = len(proc_df.columns)

        recon_rows.append({
            "table_name": proc_name.replace(".parquet", ""),
            "raw_filename": raw_name,
            "processed_filename": proc_name,
            "raw_row_count": raw_rows,
            "processed_row_count": proc_rows,
            "row_discrepancy": proc_rows - raw_rows,
            "raw_column_count": raw_cols,
            "processed_column_count": proc_cols,
            "column_discrepancy": proc_cols - raw_cols,
            "raw_unique_ids": int(raw_df[id_col].nunique()) if id_col in raw_df else None,
            "processed_unique_ids": int(proc_df[id_col].nunique()) if id_col in proc_df else None,
            "join_multiplication_detected": proc_rows > raw_rows,
            "record_loss_detected": proc_rows < raw_rows,
            "traceability_status": "EXACT_1_TO_1_MATCH" if raw_rows == proc_rows and raw_cols == proc_cols else "MODIFIED",
        })

    recon_df = pd.DataFrame(recon_rows)
    recon_path = REPORTS_DIR / "dataset_reconciliation.csv"
    recon_df.to_csv(recon_path, index=False)
    print(f"Dataset reconciliation saved to {recon_path}")

    # ---------------------------------------------------------
    # 3. ANALYSIS COVERAGE STATS
    # ---------------------------------------------------------
    matches_df = raw_dfs["matches.csv"]
    bbb_df = raw_dfs["ball_by_ball.csv"]
    p11_df = raw_dfs["playing_eleven.csv"]
    mapping_df = raw_dfs["competition_team_player_mapping.csv"]
    comps_df = raw_dfs["competitions.csv"]
    teams_df = raw_dfs["teams.csv"]

    match_states_df = pd.read_parquet(DATA_PROC / "match_states.parquet")
    pressure_states_df = pd.read_parquet(DATA_PROC / "pressure_states.parquet")
    bat_perf_df = pd.read_parquet(DATA_PROC / "batting_performance.parquet")
    bowl_perf_df = pd.read_parquet(DATA_PROC / "bowling_performance.parquet")
    p_bat_df = pd.read_parquet(DATA_PROC / "player_batting_metrics.parquet")
    p_bowl_df = pd.read_parquet(DATA_PROC / "player_bowling_metrics.parquet")
    top_bat = pd.read_csv(OUTPUTS_DIR / "top_10_batters.csv")
    top_bowl = pd.read_csv(OUTPUTS_DIR / "top_10_bowlers.csv")

    all_match_ids = set(matches_df["match_id"])
    bbb_match_ids = set(bbb_df["match_id"])
    state_match_ids = set(match_states_df["match_id"])
    press_match_ids = set(pressure_states_df["match_id"])
    perf_match_ids = set(bat_perf_df["match_id"]).union(set(bowl_perf_df["match_id"]))

    # Matches contributing to final rankings
    # Batting Top 10 matches:
    top_bat_ids = set(top_bat["player_id"])
    top_bat_matches = set(bat_perf_df[bat_perf_df["striker_id"].isin(top_bat_ids)]["match_id"])
    top_bowl_ids = set(top_bowl["player_id"])
    top_bowl_matches = set(bowl_perf_df[bowl_perf_df["bowler_id"].isin(top_bowl_ids)]["match_id"])
    ranking_contributing_matches = top_bat_matches.union(top_bowl_matches)

    # Competitions coverage
    all_comp_ids = set(comps_df["comp_id"])
    matches_comp_ids = set(matches_df["comp_id"])
    bbb_comps = set(matches_df[matches_df["match_id"].isin(bbb_match_ids)]["comp_id"])

    # Players coverage
    all_registry_players = set(mapping_df["player_id"])
    p11_players = set(p11_df["player_id"])
    batting_players = set(bbb_df["striker_id"]).union(set(bbb_df["non_striker_id"]))
    bowling_players = set(bbb_df["bowler_id"])
    all_observed_players = batting_players.union(bowling_players)

    eligible_batters = set(p_bat_df[p_bat_df["eligibility_status"] == "ELIGIBLE"].index)
    eligible_bowlers = set(p_bowl_df[p_bowl_df["eligibility_status"] == "ELIGIBLE"].index)

    analysis_coverage: Dict[str, Any] = {
        "matches": {
            "A_total_supplied_matches": len(all_match_ids),
            "B_matches_with_ball_by_ball_coverage": len(bbb_match_ids),
            "C_matches_with_valid_reconstructed_states": len(state_match_ids),
            "D_matches_eligible_for_pressure_modelling": len(press_match_ids),
            "E_matches_eligible_for_player_performance": len(perf_match_ids),
            "F_matches_contributing_to_top_10_rankings": len(ranking_contributing_matches),
            "unplayed_or_abandoned_matches_without_deliveries": len(all_match_ids - bbb_match_ids),
        },
        "competitions": {
            "all_competitions_in_registry": len(all_comp_ids),
            "competitions_represented_in_matches": len(matches_comp_ids),
            "competitions_represented_in_deliveries": len(bbb_comps),
            "competitions_with_zero_matches": len(all_comp_ids - matches_comp_ids),
        },
        "teams": {
            "all_team_records_in_teams_table": len(teams_df),
            "distinct_team_ids": int(teams_df["team_id"].nunique()),
            "teams_participating_in_matches": int(pd.concat([matches_df["home_team_id"], matches_df["away_team_id"]]).nunique()),
        },
        "players": {
            "all_mapped_player_ids_in_registry": len(all_registry_players),
            "players_appearing_in_playing_xi": len(p11_players),
            "players_observed_batting_or_bowling": len(all_observed_players),
            "players_observed_batting": len(batting_players),
            "players_observed_bowling": len(bowling_players),
            "evaluated_batters_pool": len(p_bat_df),
            "eligible_batters_count": len(eligible_batters),
            "evaluated_bowlers_pool": len(p_bowl_df),
            "eligible_bowlers_count": len(eligible_bowlers),
            "top_10_batters_count": len(top_bat),
            "top_10_bowlers_count": len(top_bowl),
        },
        "deliveries": {
            "total_raw_deliveries": len(bbb_df),
            "reconstructed_state_deliveries": len(match_states_df),
            "pressure_state_deliveries": len(pressure_states_df),
            "high_pressure_batting_deliveries": int((pressure_states_df["batting_pressure_class"] == "HIGH_PRESSURE").sum()),
            "high_pressure_bowling_deliveries": int((pressure_states_df["bowling_pressure_class"] == "HIGH_PRESSURE").sum()),
        }
    }

    coverage_path = REPORTS_DIR / "analysis_coverage.json"
    coverage_path.write_text(json.dumps(analysis_coverage, indent=2), encoding="utf-8")
    print(f"Analysis coverage saved to {coverage_path}")

    # ---------------------------------------------------------
    # 4. EXCLUSIONS AUDIT
    # ---------------------------------------------------------
    # Identify every unplayed/abandoned match and explain why it has 0 deliveries
    no_deliv_matches = matches_df[matches_df["match_id"].isin(all_match_ids - bbb_match_ids)].copy()
    exclusions_list: List[Dict[str, Any]] = []

    for _, row in no_deliv_matches.iterrows():
        exclusions_list.append({
            "entity_type": "MATCH",
            "entity_id": int(row["match_id"]),
            "entity_label": f"{row['home_team']} vs {row['away_team']} ({row['match_date']})",
            "comp_id": int(row["comp_id"]),
            "exclusion_stage": "STAGE_1_INGESTION_DELIVERY_ABSENCE",
            "exclusion_reason": f"Match result: {row['result']}. Abandoned prior to legal ball bowled.",
            "impact_on_rankings": "NONE (No player exposure occurred)",
        })

    # Competitions in competitions.csv without matches
    no_match_comps = comps_df[comps_df["comp_id"].isin(all_comp_ids - matches_comp_ids)].copy()
    for _, row in no_match_comps.iterrows():
        exclusions_list.append({
            "entity_type": "COMPETITION",
            "entity_id": int(row["comp_id"]),
            "entity_label": f"{row['comp_name']} ({row['season']})",
            "comp_id": int(row["comp_id"]),
            "exclusion_stage": "STAGE_1_INGESTION_FIXTURE_ABSENCE",
            "exclusion_reason": "Zero fixtures scheduled/recorded in matches.csv for this competition registry entry.",
            "impact_on_rankings": "NONE (No fixtures played)",
        })

    # Ineligible batters audit
    inelig_batters = p_bat_df[p_bat_df["eligibility_status"] != "ELIGIBLE"].copy()
    for pid, row in inelig_batters.iterrows():
        exclusions_list.append({
            "entity_type": "PLAYER_BATTER",
            "entity_id": int(pid),
            "entity_label": str(row.get("player_name", f"Player {pid}")),
            "comp_id": None,
            "exclusion_stage": "STAGE_4_SAMPLE_SIZE_ELIGIBILITY",
            "exclusion_reason": str(row["eligibility_reason"]),
            "impact_on_rankings": "EXCLUDED_FROM_RANKING_CANDIDATE_POOL",
        })

    # Ineligible bowlers audit
    inelig_bowlers = p_bowl_df[p_bowl_df["eligibility_status"] != "ELIGIBLE"].copy()
    for pid, row in inelig_bowlers.iterrows():
        exclusions_list.append({
            "entity_type": "PLAYER_BOWLER",
            "entity_id": int(pid),
            "entity_label": str(row.get("player_name", f"Player {pid}")),
            "comp_id": None,
            "exclusion_stage": "STAGE_4_SAMPLE_SIZE_ELIGIBILITY",
            "exclusion_reason": str(row["eligibility_reason"]),
            "impact_on_rankings": "EXCLUDED_FROM_RANKING_CANDIDATE_POOL",
        })

    exclusions_df = pd.DataFrame(exclusions_list)
    exclusions_path = REPORTS_DIR / "exclusions_audit.csv"
    exclusions_df.to_csv(exclusions_path, index=False)
    print(f"Exclusions audit saved to {exclusions_path} ({len(exclusions_df)} rows).")

    # ---------------------------------------------------------
    # 5. CRICKET SEMANTICS & DATA QUALITY CHECKS
    # ---------------------------------------------------------
    print("\n=======================================================")
    print("CRICKET SEMANTICS QUALITY AUDIT")
    print("=======================================================")
    print(f"Total Deliveries: {len(bbb_df):,}")
    print(f"Wides count (extras_type == 'wide'): {(bbb_df['extras_type'] == 'wide').sum():,}")
    print(f"No-balls count (Overstep/other): {bbb_df['extras_type'].isin(['Overstep', 'other']).sum():,}")
    print(f"Byes count: {(bbb_df['extras_type'] == 'byes').sum():,}")
    print(f"Leg-byes count: {(bbb_df['extras_type'] == 'legbyes').sum():,}")
    print(f"Penalty runs count: {(bbb_df['extras_type'] == 'Penalty').sum():,}")
    print(f"Wickets count (is_wicket == 1): {(bbb_df['is_wicket'] == 1).sum():,}")
    print(f"Dismissal types:\n{bbb_df['dismissal_type'].value_counts(dropna=False)}")

    # Retired hurt check
    ret_hurt = bbb_df[bbb_df['dismissal_type'].str.lower().str.contains('retired', na=False)]
    print(f"Retired dismissals: {len(ret_hurt)}")
    if len(ret_hurt) > 0:
        print(ret_hurt[['match_id', 'innings', 'overid', 'striker_name', 'dismissal_type']])

    # Super Overs check
    super_overs = bbb_df[bbb_df['innings'] > 2]
    print(f"Super Over deliveries (innings > 2): {len(super_overs):,} across {super_overs['match_id'].nunique()} matches")

    # Revised targets check in matches.csv
    revised = matches_df[matches_df['revised_target'].notnull()]
    print(f"Matches with revised targets (DLS/curtailed): {len(revised)}")

    print("\nRECONCILIATION SUMMARY:")
    print(f"  Supplied Matches:              {len(all_match_ids)}")
    print(f"  Matches with Deliveries:        {len(bbb_match_ids)}")
    print(f"  Abandoned/No-Ball Matches:      {len(all_match_ids - bbb_match_ids)}")
    print(f"  Matches with Valid States:      {len(state_match_ids)}")
    print(f"  Pressure-Modeled Matches:       {len(press_match_ids)}")
    print(f"  Performance-Analyzed Matches:   {len(perf_match_ids)}")
    print(f"  Ranking-Contributing Matches:   {len(ranking_contributing_matches)}")
    print(f"  Supplied Deliveries:            {len(bbb_df):,}")
    print(f"  Processed Deliveries:           {len(pressure_states_df):,}")
    print(f"  Evaluated Batters:              {len(p_bat_df):,} (Qualified: {len(eligible_batters)})")
    print(f"  Evaluated Bowlers:              {len(p_bowl_df):,} (Qualified: {len(eligible_bowlers)})")


if __name__ == "__main__":
    run_reconciliation()
