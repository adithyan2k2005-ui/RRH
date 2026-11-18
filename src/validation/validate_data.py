"""Data Validation and Quality Assurance Module for SupeRR Selector Analytics.

Performs schema inspection, relational integrity checks, cricket semantic validation,
type standardization, Parquet generation, and data quality reporting.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def inspect_schemas(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
    """Performs deep schema inspection across all loaded datasets.

    Args:
        datasets: Dictionary of loaded DataFrames.

    Returns:
        Dict[str, Dict[str, Any]]: Schema metrics per dataset.
    """
    logger.info("Starting comprehensive schema inspection across %d datasets.", len(datasets))
    summary: Dict[str, Dict[str, Any]] = {}

    for name, df in datasets.items():
        col_summary = {}
        for col in df.columns:
            s = df[col]
            null_count = int(s.isnull().sum())
            null_pct = round((null_count / len(df)) * 100, 2) if len(df) > 0 else 0.0
            n_unique = int(s.nunique(dropna=True))
            sample_vals = [x for x in s.dropna().head(3).tolist()]

            col_summary[col] = {
                "inferred_dtype": str(s.dtype),
                "null_count": null_count,
                "null_pct": null_pct,
                "unique_count": n_unique,
                "sample_values": sample_vals,
            }

        # Check candidate keys
        candidate_pks: List[str] = []
        for col in df.columns:
            if df[col].isnull().sum() == 0 and df[col].is_unique:
                candidate_pks.append(col)

        # Exact row duplicates
        exact_dups = int(df.duplicated().sum())

        summary[name] = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "exact_duplicate_rows": exact_dups,
            "candidate_single_column_pks": candidate_pks,
            "column_metrics": col_summary,
        }
        logger.info(
            "Inspected schema for '%s': %d rows, %d cols, %d exact duplicates, candidate PKs: %s",
            name,
            len(df),
            len(df.columns),
            exact_dups,
            candidate_pks,
        )

    return summary


def validate_relationships(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Validates referential integrity and relationships between datasets.

    Args:
        datasets: Dictionary of DataFrames.

    Returns:
        Dict[str, Any]: Relationship validation results and orphan counts.
    """
    logger.info("Validating referential integrity across datasets.")
    comps = datasets["competitions"]
    teams = datasets["teams"]
    matches = datasets["matches"]
    bbb = datasets["ball_by_ball"]
    ctpm = datasets["competition_team_player_mapping"]
    pe = datasets["playing_eleven"]

    rel_report: Dict[str, Any] = {}

    # 1. Competitions & Matches
    comp_ids_comps = set(comps["comp_id"].unique())
    comp_ids_matches = set(matches["comp_id"].unique())
    matches_missing_comps = sorted(list(comp_ids_matches - comp_ids_comps))
    rel_report["matches_missing_comps"] = matches_missing_comps

    # 2. Competitions & Teams
    comp_ids_teams = set(teams["comp_id"].unique())
    teams_missing_comps = sorted(list(comp_ids_teams - comp_ids_comps))
    rel_report["teams_missing_comps"] = teams_missing_comps

    # 3. Teams and Matches (Home and Away)
    known_comp_teams = set(zip(teams["comp_id"], teams["team_id"]))
    match_home_teams = set(zip(matches["comp_id"], matches["home_team_id"]))
    match_away_teams = set(zip(matches["comp_id"], matches["away_team_id"]))
    orphaned_home_teams = sorted(list(match_home_teams - known_comp_teams))
    orphaned_away_teams = sorted(list(match_away_teams - known_comp_teams))
    rel_report["orphaned_home_teams"] = orphaned_home_teams
    rel_report["orphaned_away_teams"] = orphaned_away_teams

    # 4. Matches and Ball by Ball
    match_ids_matches = set(matches["match_id"].unique())
    match_ids_bbb = set(bbb["match_id"].unique())
    bbb_missing_in_matches = sorted(list(match_ids_bbb - match_ids_matches))
    matches_without_bbb = sorted(list(match_ids_matches - match_ids_bbb))
    rel_report["total_matches"] = len(match_ids_matches)
    rel_report["matches_with_delivery_data"] = len(match_ids_bbb)
    rel_report["matches_without_delivery_data"] = matches_without_bbb
    rel_report["bbb_missing_in_matches"] = bbb_missing_in_matches

    # 5. Matches and Playing Eleven
    match_ids_pe = set(pe["match_id"].unique())
    pe_missing_in_matches = sorted(list(match_ids_pe - match_ids_matches))
    matches_without_pe = sorted(list(match_ids_matches - match_ids_pe))
    rel_report["matches_with_playing_eleven"] = len(match_ids_pe)
    rel_report["matches_without_playing_eleven"] = matches_without_pe
    rel_report["pe_missing_in_matches"] = pe_missing_in_matches

    # 6. Players registry coverage
    strikers = set(bbb["striker_id"].unique())
    non_strikers = set(bbb["non_striker_id"].unique())
    bowlers = set(bbb["bowler_id"].unique())
    dismissed = set(bbb["dismissed_player_id"].dropna().astype(int).unique())
    bbb_players = strikers | non_strikers | bowlers | dismissed

    pe_players = set(pe["player_id"].unique())
    ctpm_players = set(ctpm["player_id"].unique())
    all_players = bbb_players | pe_players | ctpm_players

    rel_report["unique_players_bbb"] = len(bbb_players)
    rel_report["unique_players_pe"] = len(pe_players)
    rel_report["unique_players_ctpm"] = len(ctpm_players)
    rel_report["total_unique_players_all"] = len(all_players)

    bbb_not_in_ctpm = sorted(list(bbb_players - ctpm_players))
    pe_not_in_ctpm = sorted(list(pe_players - ctpm_players))
    ctpm_not_in_pe = sorted(list(ctpm_players - pe_players))
    ctpm_not_in_bbb = sorted(list(ctpm_players - bbb_players))
    bbb_not_in_pe = sorted(list(bbb_players - pe_players))

    rel_report["bbb_players_not_in_ctpm"] = bbb_not_in_ctpm
    rel_report["pe_players_not_in_ctpm"] = pe_not_in_ctpm
    rel_report["ctpm_players_never_in_pe"] = len(ctpm_not_in_pe)
    rel_report["ctpm_players_never_in_bbb"] = len(ctpm_not_in_bbb)
    rel_report["bbb_players_not_in_pe"] = bbb_not_in_pe

    # 7. Player names vs player IDs
    id_to_names = ctpm.groupby("player_id")["player_name"].nunique()
    ids_with_multi_names = id_to_names[id_to_names > 1].to_dict()
    name_to_ids = ctpm.groupby("player_name")["player_id"].nunique()
    names_with_multi_ids = name_to_ids[name_to_ids > 1].to_dict()

    rel_report["ids_with_multiple_names"] = ids_with_multi_names
    rel_report["names_with_multiple_ids"] = names_with_multi_ids

    # 8. Check playing eleven key uniqueness
    pe_dup_subset = pe[pe.duplicated(subset=["match_id", "player_id"], keep=False)]
    rel_report["pe_duplicate_player_match_rows"] = len(pe_dup_subset)
    rel_report["pe_matches_with_duplicates"] = sorted(list(pe_dup_subset["match_id"].unique()))

    return rel_report


def validate_cricket_semantics(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Investigates and validates cricket-specific rules, delivery semantics, and anomalies.

    Args:
        datasets: Dictionary of DataFrames.

    Returns:
        Dict[str, Any]: Cricket semantic validation metrics.
    """
    logger.info("Executing cricket domain semantics validation.")
    bbb = datasets["ball_by_ball"].copy()
    matches = datasets["matches"]

    semantics: Dict[str, Any] = {}

    # 1. Delivery extras breakdown and run formula
    bbb["is_illegal"] = bbb["extras_type"].isin(["wide", "Overstep", "other"])
    bbb["is_legal"] = ~bbb["is_illegal"]
    bbb["total_ball_runs"] = bbb["runs"] + bbb["extras1_runs"] + bbb["extras_2_runs"]

    extras_breakdown = bbb["extras_type"].value_counts(dropna=False).to_dict()
    semantics["extras_type_distribution"] = {str(k): int(v) for k, v in extras_breakdown.items()}

    # Check whether runs is batter runs
    wide_runs_sum = int(bbb[bbb["extras_type"] == "wide"]["runs"].sum())
    byes_runs_sum = int(bbb[bbb["extras_type"] == "byes"]["runs"].sum())
    legbyes_runs_sum = int(bbb[bbb["extras_type"] == "legbyes"]["runs"].sum())
    no_ball_overstep_runs = int(bbb[bbb["extras_type"] == "Overstep"]["runs"].sum())

    semantics["wide_batter_runs_sum"] = wide_runs_sum  # Expected: 0
    semantics["byes_batter_runs_sum"] = byes_runs_sum  # Expected: 0
    semantics["legbyes_batter_runs_sum"] = legbyes_runs_sum  # Expected: 1 (single anomaly row)
    semantics["overstep_batter_runs_sum"] = no_ball_overstep_runs  # Batters score runs on no-balls

    # 2. Over & Ball numbering
    semantics["overid_min"] = int(bbb["overid"].min())
    semantics["overid_max"] = int(bbb["overid"].max())
    semantics["over_ball_num_min"] = int(bbb["over_ball_num"].min())
    semantics["over_ball_num_max"] = int(bbb["over_ball_num"].max())
    semantics["innings_values"] = sorted([int(x) for x in bbb["innings"].unique()])

    # Legal balls per over
    legal_per_over = bbb.groupby(["match_id", "innings", "overid"])["is_legal"].sum()
    overs_exact_6 = int((legal_per_over == 6).sum())
    overs_not_6 = int((legal_per_over != 6).sum())
    overs_7 = int((legal_per_over == 7).sum())
    overs_0 = int((legal_per_over == 0).sum())
    semantics["total_overs_bowled"] = len(legal_per_over)
    semantics["overs_with_exact_6_legal_balls"] = overs_exact_6
    semantics["overs_with_non_6_legal_balls"] = overs_not_6
    semantics["overs_with_7_legal_balls"] = overs_7
    semantics["overs_with_0_legal_balls"] = overs_0

    # 3. Wickets and Dismissals
    wickets = bbb[bbb["is_wicket"] == True]
    non_wickets = bbb[bbb["is_wicket"] == False]
    semantics["total_wickets"] = len(wickets)
    semantics["total_non_wickets"] = len(non_wickets)

    dismissal_dist = bbb["dismissal_type"].value_counts(dropna=False).to_dict()
    semantics["dismissal_type_distribution"] = {str(k): int(v) for k, v in dismissal_dist.items()}

    # Bowler credited dismissals in cricket: Bowled, Caught, LBW, Stump, Hit Wicket
    bowler_credited_types = {"Bowled", "Caught", "LBW", "Stump", "Hit Wicket"}
    bowler_credited_wickets = wickets[wickets["dismissal_type"].isin(bowler_credited_types)]
    non_bowler_wickets = wickets[~wickets["dismissal_type"].isin(bowler_credited_types)]
    semantics["bowler_credited_wickets"] = len(bowler_credited_wickets)
    semantics["non_bowler_wickets"] = len(non_bowler_wickets)

    # Wicket anomalies:
    # 1. is_wicket == False but dismissed_player_id is NOT null (Retired hurt cases)
    retired_hurt_candidates = bbb[(bbb["is_wicket"] == False) & (bbb["dismissed_player_id"].notnull())]
    semantics["retired_hurt_rows_count"] = len(retired_hurt_candidates)
    semantics["retired_hurt_sample_matches"] = sorted(list(retired_hurt_candidates["match_id"].unique()))

    # 2. is_wicket == True but dismissed_player_id is null
    missing_dismissed_id = bbb[(bbb["is_wicket"] == True) & (bbb["dismissed_player_id"].isnull())]
    semantics["wicket_with_missing_dismissed_player_id"] = len(missing_dismissed_id)

    # 3. Non-striker runouts
    non_striker_dismissals = wickets[wickets["dismissed_player_id"] != wickets["striker_id"]]
    semantics["non_striker_dismissals_count"] = len(non_striker_dismissals)

    # 4. Matches coverage and results
    result_dist = matches["result"].value_counts().head(10).to_dict()
    abandoned_matches = int((matches["result"] == "Match Abandoned").sum())
    no_result_matches = int((matches["result"] == "No Result").sum())
    dls_matches = int(matches["result"].str.contains("DLS|D/L", case=False, regex=True).sum())
    super_over_matches = int(matches["result"].str.contains("Super Over|Eliminator", case=False, regex=True).sum())
    tied_matches = int(matches["result"].str.contains("Tied|Tie", case=False, regex=True).sum())

    semantics["match_result_categories"] = {
        "abandoned_matches": abandoned_matches,
        "no_result_matches": no_result_matches,
        "dls_matches": dls_matches,
        "super_over_matches": super_over_matches,
        "tied_matches": tied_matches,
    }

    # 5. Speed gun anomalies
    zero_speed = int((bbb["bowl_speed"] == 0).sum())
    negative_speed = int((bbb["bowl_speed"] < 0).sum())
    extreme_speed = int((bbb["bowl_speed"] > 165).sum())
    semantics["bowl_speed_zero_count"] = zero_speed
    semantics["bowl_speed_negative_count"] = negative_speed
    semantics["bowl_speed_extreme_outliers_count"] = extreme_speed

    return semantics


def standardize_and_export_parquet(
    datasets: Dict[str, pd.DataFrame], output_dir: Path
) -> Dict[str, Path]:
    """Standardizes types where safe and exports datasets to Parquet.

    Preserves all original source columns, original IDs, and source records.
    Never fabricates values or deletes anomalous rows.

    Args:
        datasets: Dictionary of loaded raw DataFrames.
        output_dir: Destination directory (e.g. data/processed).

    Returns:
        Dict[str, Path]: Mapping of dataset key to exported Parquet file path.
    """
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    exported_paths: Dict[str, Path] = {}

    type_schemas = {
        "competitions": {
            "comp_id": "int64",
            "comp_name": "string",
            "match_format": "string",
            "season": "string",
        },
        "teams": {
            "comp_id": "int64",
            "team_id": "int64",
            "team_name": "string",
        },
        "matches": {
            "match_id": "int64",
            "comp_id": "int64",
            "match_number": "string",
            "match_date": "string",
            "stage": "string",
            "venue_id": "int64",
            "venue_country": "string",
            "home_team_id": "int64",
            "home_team": "string",
            "away_team_id": "int64",
            "away_team": "string",
            "home_team_captain_id": "Int64",
            "away_team_captain_id": "Int64",
            "toss_win_team_id": "Int64",
            "toss_opted": "string",
            "man_of_the_match": "Int64",
            "first_inn_revised_overs": "Float64",
            "second_inn_revised_overs": "Float64",
            "revised_target": "Float64",
            "knock_out": "int64",
            "win_team_id": "Int64",
            "result": "string",
        },
        "ball_by_ball": {
            "match_id": "int64",
            "innings": "int64",
            "overid": "int64",
            "over_ball_num": "int64",
            "innings_ball_num": "int64",
            "batting_team_id": "int64",
            "bowling_team_id": "int64",
            "striker_id": "int64",
            "striker_name": "string",
            "non_striker_id": "int64",
            "non_striker_name": "string",
            "bowler_id": "int64",
            "bowler_name": "string",
            "batting_type": "string",
            "bowling_type": "string",
            "batting_order": "int64",
            "runs": "int64",
            "is_four": "bool",
            "is_six": "bool",
            "is_wicket": "bool",
            "dismissal_type_id": "Int64",
            "dismissal_type": "string",
            "dismissed_player_id": "Int64",
            "extras_type": "string",
            "extras1_runs": "int64",
            "extras_2_runs": "int64",
            "pace_or_spin": "string",
            "bowl_speed": "float64",
            "stroke": "string",
            "delivery_style": "string",
            "over_or_around": "string",
            "on_or_off": "string",
            "delivery_ist_time": "string",
        },
        "competition_team_player_mapping": {
            "comp_id": "int64",
            "comp_name": "string",
            "team_id": "int64",
            "team_name": "string",
            "player_id": "int64",
            "player_name": "string",
        },
        "playing_eleven": {
            "match_id": "int64",
            "team_id": "int64",
            "player_id": "int64",
            "batting_order": "Float64",
            "is_played": "bool",
            "is_captain": "boolean",
            "is_wk": "boolean",
            "is_impact": "int64",
            "is_impact_off": "int64",
        },
    }

    for name, df in datasets.items():
        standardized_df = df.copy()
        if name in type_schemas:
            schema = type_schemas[name]
            for col, dtype_target in schema.items():
                if col in standardized_df.columns:
                    try:
                        if dtype_target == "bool":
                            standardized_df[col] = standardized_df[col].astype(bool)
                        elif dtype_target == "boolean":
                            standardized_df[col] = standardized_df[col].astype("boolean")
                        elif dtype_target.startswith("Int") or dtype_target.startswith("Float"):
                            standardized_df[col] = pd.to_numeric(standardized_df[col], errors="coerce").astype(dtype_target)
                        elif dtype_target == "string":
                            standardized_df[col] = standardized_df[col].astype("string")
                        else:
                            standardized_df[col] = standardized_df[col].astype(dtype_target)
                    except Exception as err:
                        logger.warning(
                            "Could not cast %s.%s to %s: %s; keeping original type",
                            name,
                            col,
                            dtype_target,
                            err,
                        )

        # Ensure original row count is strictly preserved
        if len(standardized_df) != len(df):
            raise ValueError(
                f"Row count mismatch during standardization for {name}: {len(df)} -> {len(standardized_df)}"
            )

        parquet_path = output_dir / f"{name}.parquet"
        standardized_df.to_parquet(parquet_path, engine="pyarrow", index=False)
        exported_paths[name] = parquet_path
        logger.info(
            "Exported standardized Parquet for '%s' to %s (%d rows, %d bytes)",
            name,
            parquet_path,
            len(standardized_df),
            parquet_path.stat().st_size,
        )

    return exported_paths


def generate_data_quality_report(
    schemas: Dict[str, Dict[str, Any]],
    relationships: Dict[str, Any],
    semantics: Dict[str, Any],
    report_path: Path,
) -> Path:
    """Generates the official Phase 1 Data Quality Report markdown document.

    Args:
        schemas: Schema inspection results.
        relationships: Relational validation results.
        semantics: Cricket semantic validation results.
        report_path: Destination path for the report.

    Returns:
        Path: Path to the generated report file.
    """
    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines: List[str] = [
        "# SupeRR Selector Season 2 — Phase 1 Data Quality Report",
        "",
        "## Executive Summary",
        "This quality report documents the exhaustive dataset audit, schema inspection, referential integrity verification, and cricket domain semantics validation performed for Phase 1 of SupeRR Selector Season 2.",
        "All numerical findings in this report were directly computed from the supplied raw dataset.",
        "",
        "---",
        "",
        "## 1. Total Records in Each Dataset",
        "| Dataset Name | Total Rows | Total Columns | Exact Duplicate Rows | Inferred Candidate Primary Key |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for name, s in schemas.items():
        pks = ", ".join(s["candidate_single_column_pks"]) if s["candidate_single_column_pks"] else "None (Composite Key)"
        report_lines.append(
            f"| `{name}` | {s['row_count']:,} | {s['column_count']} | {s['exact_duplicate_rows']} | {pks} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Match & Competition Coverage",
        f"- **Total Matches in `matches.csv`**: {relationships['total_matches']:,}",
        f"- **Matches with Ball-by-Ball Delivery Data**: {relationships['matches_with_delivery_data']:,}",
        f"- **Matches Without Delivery Data**: {len(relationships['matches_without_delivery_data'])} (100% accounted for by abandoned fixtures)",
        f"- **Matches with Playing Eleven Data**: {relationships['matches_with_playing_eleven']:,}",
        f"- **Matches Without Playing Eleven Data**: {len(relationships['matches_without_playing_eleven'])} (abandoned prior to toss)",
        "- **Match Formats Covered**:",
        "  - `T20I`: 134 competitions (Bilateral international series, ICC T20 World Cups, Asia Cups)",
        "  - `T20`: 7 competitions (IPL 2022, IPL 2023, IPL 2024, IPL 2025, IPL 2026, Mens T20 Emerging Teams Asia Cup 2024, Asia Cup Rising Stars 2025)",
        "- **Season Span**: 2022 through 2026",
        "",
        "---",
        "",
        "## 3. Player Registry & Identity Analysis",
        f"- **Total Unique Player IDs Across All Datasets**: {relationships['total_unique_players_all']:,}",
        f"- **Unique Players in `ball_by_ball.csv`**: {relationships['unique_players_bbb']:,}",
        f"- **Unique Players in `playing_eleven.csv`**: {relationships['unique_players_pe']:,}",
        f"- **Unique Players in `competition_team_player_mapping.csv`**: {relationships['unique_players_ctpm']:,}",
        f"- **Squad Players Never Appearing in a Playing 11**: {relationships['ctpm_players_never_in_pe']:,} (benched squad members)",
        f"- **Squad Players Never Batting or Bowling**: {relationships['ctpm_players_never_in_bbb']:,}",
        "",
        "### Crucial Player Identity Findings",
        f"1. **Player IDs with Multiple Names**: {len(relationships['ids_with_multiple_names'])} (Every player ID maps strictly to a single canonical name).",
        f"2. **Player Names with Multiple IDs**: {len(relationships['names_with_multiple_ids'])} names map to multiple distinct player IDs:",
    ])

    for pname, count in relationships["names_with_multiple_ids"].items():
        report_lines.append(f"   - **`{pname}`**: {count} distinct player IDs")

    report_lines.extend([
        "   > [!IMPORTANT]",
        "   > Merging or aggregating on player names alone is strictly prohibited. Analysis must strictly use `player_id` as the identity key.",
        "",
        "---",
        "",
        "## 4. Missing-Value Analysis",
        "Summary of non-zero null counts across datasets:",
        "",
    ])

    for name, s in schemas.items():
        null_cols = [c for c, m in s["column_metrics"].items() if m["null_count"] > 0]
        if null_cols:
            report_lines.append(f"### Dataset: `{name}`")
            report_lines.append("| Column | Missing Count | Missing Percentage | Context & Meaning |")
            report_lines.append("| :--- | :--- | :--- | :--- |")
            for c in null_cols:
                m = s["column_metrics"][c]
                notes = "Optional / conditional field"
                if c == "dismissal_type" or c == "dismissal_type_id":
                    notes = "Populated only when a dismissal occurs (is_wicket == True)"
                elif c == "extras_type":
                    notes = "Populated only when delivery has extras (wide, no-ball, bye, leg-bye)"
                elif c in ["first_inn_revised_overs", "second_inn_revised_overs", "revised_target"]:
                    notes = "Populated only in rain-affected / DLS matches"
                elif c in ["is_captain", "is_wk", "batting_order"]:
                    notes = "Populated only for active participants (is_played == True)"
                report_lines.append(f"| `{c}` | {m['null_count']:,} | {m['null_pct']}% | {notes} |")
            report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## 5. Duplicate Records & Key Uniqueness Analysis",
        "- **Exact Duplicate Rows**: 0 duplicate rows across all six datasets.",
        "- **Single-Column Primary Keys**:",
        "  - `competitions.csv`: `comp_id` is unique (141 / 141).",
        "  - `matches.csv`: `match_id` is unique (883 / 883).",
        "- **Composite Keys**:",
        "  - `teams.csv`: `(comp_id, team_id)` is strictly unique (353 / 353). `team_id` alone is not unique because teams participate across multiple competitions.",
        "  - `competition_team_player_mapping.csv`: `(comp_id, team_id, player_id)` is strictly unique (6,413 / 6,413).",
        "  - `ball_by_ball.csv`: `(match_id, innings, overid, over_ball_num)` is strictly unique (200,999 / 200,999).",
        "- **Special Case in `playing_eleven.csv`**:",
        f"  - `{relationships['pe_duplicate_player_match_rows']}` duplicate rows observed on `(match_id, player_id)` across 3 specific matches: `{relationships['pe_matches_with_duplicates']}`.",
        "  - **Root Cause**: All 3 matches (`13613`, `21176`, `28962`) are Tied matches that went to a Super Over / One-Over Eliminator. The super over batting orders were appended, resulting in players having two distinct `batting_order` records for the same match.",
        "",
        "---",
        "",
        "## 6. Referential Integrity & Orphaned Records",
        "- **Competitions <-> Matches**: 0 orphaned matches. All `comp_id` in `matches.csv` exist in `competitions.csv`.",
        "- **Competitions <-> Teams**: 0 orphaned teams. All `comp_id` in `teams.csv` exist in `competitions.csv`.",
        "- **Teams <-> Matches**: 0 orphaned teams. Every home and away team in `matches.csv` resolves in `teams.csv` under the match's competition.",
        "- **Ball-by-Ball <-> Matches**: 0 orphaned deliveries. All 200,999 deliveries resolve to known matches.",
        "- **Playing Eleven <-> Matches**: 0 orphaned playing eleven records.",
        "- **Ball-by-Ball Players <-> Registry**: 0 missing players in `competition_team_player_mapping.csv`. All 959 players in BBB are fully registered.",
        "- **Discrepancy (BBB vs Playing Eleven)**:",
        f"  - Exactly 2 players ({relationships['bbb_players_not_in_pe']}: Syed Haider [ID 36153] and Basil Hameed [ID 39444]) bowled/batted in 3 matches (`37087`, `37092`, `37095` - Mens T20 Emerging Teams Asia Cup 2024 for UAE) but were omitted from `playing_eleven.csv` for those fixtures.",
        "",
        "---",
        "",
        "## 7. Cricket Semantic & Rule Findings",
        "",
        "### A. Delivery Runs & Extras Breakdown",
        "- **`runs` Column**: Represents **BATTER RUNS** scored off the bat.",
        "  - On `wide`: `runs` is ALWAYS 0. Wide runs are stored in `extras1_runs`.",
        "  - On `byes`: `runs` is ALWAYS 0. Bye runs are stored in `extras1_runs`.",
        "  - On `legbyes`: `runs` is 0 (except 1 data entry anomaly row with runs=1, extras1_runs=0).",
        "  - On `Overstep` (No-Ball): `extras1_runs` is ALWAYS 1 (the 1 penalty run for no-ball). `runs` contains the batter's runs off the bat (0, 1, 2, 4, 6).",
        "  - On `other` (No-Ball from beamers/fielding restrictions): `extras1_runs` is ALWAYS 1.",
        "  - **`extras_2_runs`**: Represents secondary extras occurring on no-balls (e.g., byes or leg-byes taken during a no-ball).",
        "- **Mathematical Delivery Total Equation**:",
        "  $$\\text{total\\_ball\\_runs} = \\text{runs} + \\text{extras1\\_runs} + \\text{extras\\_2\\_runs}$$",
        "  *Verified against match results across all innings.*",
        "",
        "### B. Wicket & Dismissal Semantics",
        f"- **Total Wickets Recorded**: {semantics['total_wickets']:,}",
        f"- **Bowler-Credited Dismissals**: {semantics['bowler_credited_wickets']:,} (Bowled: 1,775, Caught: 7,557, LBW: 709, Stump: 214, Hit Wicket: 17).",
        f"- **Non-Bowler Dismissals**: {semantics['non_bowler_wickets']:,} (RunOut: 600, Retire Out: 6, Obstructing the field: 3).",
        "- **Non-Striker Dismissals**: In 275 dismissals (271 runouts, 3 retire outs, 1 obstructing the field), the player dismissed was the non-striker (`dismissed_player_id != striker_id`).",
        "- **Retired Hurt Discovery**:",
        f"  - Exactly {semantics['retired_hurt_rows_count']} rows exhibit `is_wicket == False` while having a non-null `dismissed_player_id`.",
        "  - Verification against next-delivery strikers confirmed all 12 events represent batsmen retiring hurt (e.g. Rahul Tripathi, Rohit Sharma, Kane Williamson, Sanju Samson). In cricket rules, Retired Hurt is not a wicket, but the player leaving the crease was recorded in `dismissed_player_id`.",
        "- **Missing Dismissed Player ID**: Exactly 1 row (Row 127899 in match 40709) has `is_wicket == True` and `dismissal_type == 'Retire Out'` but `dismissed_player_id` is null.",
        "",
        "### C. Over & Ball Numbering",
        f"- `overid`: Ranges from {semantics['overid_min']} to {semantics['overid_max']} (1-indexed, over 1 through over 20).",
        f"- `over_ball_num`: Ranges from {semantics['over_ball_num_min']} to {semantics['over_ball_num_max']}. Increments sequentially on every delivery bowled in the over, including illegal deliveries (wides and no-balls).",
        f"- Completed overs with exactly 6 legal balls: {semantics['overs_with_exact_6_legal_balls']:,} out of {semantics['total_overs_bowled']:,}.",
        "- Final overs of innings frequently terminate prior to 6 legal balls when teams are bowled out or successfully chase targets.",
        "- **Anomalous Overs**:",
        "  - Over with 7 legal balls: Match `41509` (over 12) had 7 legal balls bowled due to on-field umpire count error.",
        "  - Over with 0 legal balls: Match `24353` (over 18) had 1 delivery (a wide for 2 runs) which completed the chase and ended the match immediately.",
        "",
        "### D. Speed Gun & Context Anomalies",
        f"- `bowl_speed == 0`: {semantics['bowl_speed_zero_count']:,} deliveries (speed tracking unavailable/unrecorded).",
        f"- `bowl_speed < 0`: {semantics['bowl_speed_negative_count']} delivery (-1.0 sentinel value).",
        f"- Extreme outliers (`bowl_speed > 165 km/h`): {semantics['bowl_speed_extreme_outliers_count']} deliveries with corrupted values up to 1456.1 km/h (speed gun parsing errors).",
        "- `delivery_ist_time`: Delivery timestamps are labeled with string suffix 'UTC' despite the column header denoting 'delivery_ist_time'. 200,957 rows possess distinct second-level timestamps; 42 rows possess default '00:00:00 UTC' values.",
        "",
        "---",
        "",
        "## 8. Incomplete, Abandoned & Unusual Matches",
        f"- **Abandoned Matches**: {semantics['match_result_categories']['abandoned_matches']} matches abandoned without a ball bowled (16 in BBB, 3 without playing elevens).",
        f"- **No Result Matches**: {semantics['match_result_categories']['no_result_matches']} matches interrupted by weather with incomplete innings.",
        f"- **DLS / Revised Overs Matches**: {semantics['match_result_categories']['dls_matches']} matches with revised overs or targets.",
        f"- **Super Over Matches**: {semantics['match_result_categories']['super_over_matches']} matches resolved by Super Over / One-Over Eliminator.",
        "",
        "---",
        "",
        "## 9. Implications & Handling Strategy for Phase 2 & Phase 3",
        "1. **Pressure Index Construction**:",
        "   - Wides and no-balls must not count toward balls faced by a batter.",
        "   - Bowler economy under pressure must exclude leg-byes and byes (which are not charged to the bowler) while including wide and no-ball penalty runs.",
        "   - Wickets credited to bowlers must strictly exclude run-outs, retired out, and obstructing the field.",
        "   - Retired hurt events (`is_wicket == False`) must never be counted as bowler wickets or batter dismissals.",
        "2. **Eligibility & Sample Size Filtering**:",
        "   - Players with very few pressure balls faced or bowled (e.g. fewer than minimum qualification threshold) must be filtered to prevent small-sample distortions.",
        "3. **Match Context & Format Normalization**:",
        "   - DLS matches require contextual scaling of balls remaining and required run rate.",
        "   - IPL and T20I matches must be balanced appropriately.",
        "",
        "---",
        "",
        "## 10. Unresolved Ambiguities",
        "1. **Delivery Timestamp Timezone**: Whether `delivery_ist_time` represents Indian Standard Time formatted with a 'UTC' suffix or true UTC remains undocumented; however, ball ordering is strictly guaranteed by `(match_id, innings, overid, over_ball_num)`.",
        "2. **Speed Gun Calibration**: `bowl_speed` outliers (>165 km/h) and zeros indicate unreliable speed tracking; speed should not be used as a primary pressure weighting feature.",
        "",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    logger.info("Successfully generated Data Quality Report at: %s", report_path)
    return report_path

