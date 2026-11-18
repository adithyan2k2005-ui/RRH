"""Submission Formatter and CSV Export Module for SupeRR Selector Analytics.

Formats official submission files according to hackathon specifications:
- outputs/top_10_batters.csv
- outputs/top_10_bowlers.csv
- outputs/full_batting_rankings.csv
- outputs/full_bowling_rankings.csv
- outputs/submission_selections.md
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


def format_batter_output(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes batter ranking columns into official submission schema."""
    out = pd.DataFrame({
        "rank": df["rank"].values,
        "player_id": df["striker_id"].values,
        "player_name": df["player_name"].values,
        "reliability_score": df["reliability_score"].values,
        "pressure_matches": df["hp_matches"].values,
        "pressure_balls_faced": df["hp_balls"].values,
        "pressure_runs": df["hp_batter_runs"].values,
        "high_pressure_impact": df["hp_combined_impact_per_ball"].values,
        "ordinary_performance_baseline": df["ord_combined_impact_per_ball"].values,
        "pressure_uplift": df["batting_pressure_uplift"].values,
        "consistency_metric": df["positive_match_ratio"].values,
        "uncertainty_measure": df["cluster_se"].values,
        "eligibility_status": df["eligibility_status"].values,
    })
    return out


def format_bowler_output(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes bowler ranking columns into official submission schema."""
    out = pd.DataFrame({
        "rank": df["rank"].values,
        "player_id": df["bowler_id"].values,
        "player_name": df["player_name"].values,
        "reliability_score": df["reliability_score"].values,
        "pressure_matches": df["hp_matches"].values,
        "pressure_legal_balls": df["hp_balls"].values,
        "pressure_runs_conceded": df["hp_runs_conceded"].values,
        "pressure_wickets": df["hp_bowler_wickets"].values,
        "high_pressure_impact": df["hp_combined_impact_per_ball"].values,
        "ordinary_performance_baseline": df["ord_combined_impact_per_ball"].values,
        "pressure_uplift": df["bowling_pressure_uplift"].values,
        "consistency_metric": df["positive_match_ratio"].values,
        "uncertainty_measure": df["cluster_se"].values,
        "eligibility_status": df["eligibility_status"].values,
    })
    return out


def save_ranking_csvs(
    rankings_dict: Dict[str, pd.DataFrame],
    output_dir: Path,
) -> None:
    """Exports standardized CSV ranking outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Exporting ranking CSVs to %s.", output_dir)

    top_10_b = format_batter_output(rankings_dict["top_10_batters"])
    full_b = format_batter_output(rankings_dict["full_batting_rankings"])

    top_10_bw = format_bowler_output(rankings_dict["top_10_bowlers"])
    full_bw = format_bowler_output(rankings_dict["full_bowling_rankings"])

    top_10_b.to_csv(output_dir / "top_10_batters.csv", index=False)
    full_b.to_csv(output_dir / "full_batting_rankings.csv", index=False)

    top_10_bw.to_csv(output_dir / "top_10_bowlers.csv", index=False)
    full_bw.to_csv(output_dir / "full_bowling_rankings.csv", index=False)

    logger.info("Saved top_10_batters.csv, top_10_bowlers.csv, and full ranking CSVs.")


def format_submission_selections(
    top_10_batters: pd.DataFrame,
    top_10_bowlers: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generates the official outputs/submission_selections.md reference document."""
    logger.info("Writing submission selections reference to %s.", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# SupeRR Selector Season 2 — Round 1 Official Submission Selections",
        "",
        "This document lists the official evidence-backed top-10 player selections for submission.",
        "",
        "> [!IMPORTANT]",
        "> **Unstop Submission Verification Note**:",
        "> Check and confirm the exact dropdown player labels in the Unstop portal against the player names",
        "> and IDs below before final submission. If any selected player is missing from the official Unstop dropdown,",
        "> flag the issue for manual review. Do NOT automatically replace that player with another candidate.",
        "> Do NOT attempt to submit anything via automated scripts.",
        "",
        "---",
        "",
        "## SECTION A — TOP 10 BATTERS",
        "",
    ]

    for idx, row in top_10_batters.iterrows():
        r = int(row["rank"])
        p_id = int(row["striker_id"] if "striker_id" in row else row["player_id"])
        name = str(row["player_name"])
        score = float(row["reliability_score"])
        lines.append(f"Rank {r}: {name} — {p_id} (Reliability Score: {score:.2f})")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION B — TOP 10 BOWLERS",
        "",
    ])

    for idx, row in top_10_bowlers.iterrows():
        r = int(row["rank"])
        p_id = int(row["bowler_id"] if "bowler_id" in row else row["player_id"])
        name = str(row["player_name"])
        score = float(row["reliability_score"])
        lines.append(f"Rank {r}: {name} — {p_id} (Reliability Score: {score:.2f})")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

