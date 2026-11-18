"""Player Intelligence and Comparison Routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.schemas.models import (
    PlayerComparisonResponse,
    PlayerDetail,
    PlayerItem,
    PlayerPerformancePoint,
)
from backend.api.services.data_loader import AnalyticsDataStore, get_datastore

router = APIRouter(prefix="/players", tags=["Players"])


def _extract_player_item(row: pd.Series, discipline: str, rank: Optional[int] = None) -> PlayerItem:
    p_id = int(row["striker_id"] if discipline == "batting" else row["bowler_id"])
    name = str(row["player_name"])
    score = round(float(row.get("reliability_score", 0.0)), 2)
    elig = str(row.get("eligibility_status", "UNKNOWN"))

    hp_m = int(row.get("hp_matches", 0))
    hp_b = int(row.get("hp_balls", 0))
    hp_stat = int(row.get("hp_batter_runs", 0) if discipline == "batting" else row.get("hp_bowler_wickets", 0))

    hp_imp = round(float(row.get("hp_combined_impact_per_ball", 0.0)), 4)
    ord_imp = round(float(row.get("ord_combined_impact_per_ball", 0.0)), 4)
    uplift = round(float(row.get("batting_pressure_uplift" if discipline == "batting" else "bowling_pressure_uplift", 0.0)), 4)
    cons = round(float(row.get("positive_match_ratio", 0.0)), 4)
    unc = round(float(row.get("cluster_se", 0.0)), 4)
    shrink = round(float(row.get("shrinkage_weight", 0.0)), 4)

    return PlayerItem(
        player_id=p_id,
        player_name=name,
        discipline=discipline,
        rank=rank,
        reliability_score=score,
        eligibility_status=elig,
        hp_matches=hp_m,
        hp_balls=hp_b,
        hp_runs_or_wkts=hp_stat,
        hp_impact_per_ball=hp_imp,
        ord_baseline_impact=ord_imp,
        pressure_uplift=uplift,
        consistency_metric=cons,
        uncertainty_se=unc,
        shrinkage_weight=shrink,
    )


@router.get("", response_model=List[PlayerItem])
def list_players(
    discipline: str = Query("batting", pattern="^(batting|bowling)$"),
    eligibility: Optional[str] = Query("ELIGIBLE"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> List[PlayerItem]:
    """Lists players filtered by discipline, eligibility, or name/id search."""
    df = store.player_batting_df if discipline == "batting" else store.player_bowling_df

    if eligibility and eligibility != "all":
        df = df[df["eligibility_status"] == eligibility]

    id_col = "striker_id" if discipline == "batting" else "bowler_id"

    if search:
        s = search.strip().lower()
        df = df[
            df["player_name"].astype(str).str.lower().str.contains(s, na=False)
            | df[id_col].astype(str).str.contains(s, na=False)
        ]

    # Sort by reliability score descending
    df = df.sort_values(by="reliability_score", ascending=False).head(limit)

    # Rank map from full rankings if available
    rankings_df = store.full_batting_rankings_df if discipline == "batting" else store.full_bowling_rankings_df
    rank_map = dict(zip(rankings_df["player_id"], rankings_df["rank"]))

    results = []
    for _, row in df.iterrows():
        p_id = int(row[id_col])
        r = rank_map.get(p_id)
        results.append(_extract_player_item(row, discipline, rank=r))

    return results


@router.get("/compare", response_model=PlayerComparisonResponse)
def compare_players(
    player_a_id: int = Query(...),
    player_b_id: int = Query(...),
    discipline: str = Query("batting", pattern="^(batting|bowling)$"),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> PlayerComparisonResponse:
    """Provides side-by-side comparative analysis between two players."""
    detail_a = get_player_detail(player_a_id, discipline=discipline, store=store)
    detail_b = get_player_detail(player_b_id, discipline=discipline, store=store)

    sa = detail_a.summary
    sb = detail_b.summary

    # Normalized radar scores (0 to 100)
    radar = {
        "reliability": {sa.player_name: sa.reliability_score, sb.player_name: sb.reliability_score},
        "hp_impact": {
            sa.player_name: min(100.0, max(0.0, sa.hp_impact_per_ball * 40.0 + 30.0)),
            sb.player_name: min(100.0, max(0.0, sb.hp_impact_per_ball * 40.0 + 30.0)),
        },
        "uplift": {
            sa.player_name: min(100.0, max(0.0, sa.pressure_uplift * 30.0 + 40.0)),
            sb.player_name: min(100.0, max(0.0, sb.pressure_uplift * 30.0 + 40.0)),
        },
        "consistency": {sa.player_name: sa.consistency_metric * 100.0, sb.player_name: sb.consistency_metric * 100.0},
        "sample_weight": {sa.player_name: sa.shrinkage_weight * 100.0, sb.player_name: sb.shrinkage_weight * 100.0},
    }

    # Advantages
    advantages = []
    if sa.reliability_score > sb.reliability_score:
        diff = sa.reliability_score - sb.reliability_score
        advantages.append(f"{sa.player_name} holds higher composite reliability (+{diff:.2f} pts).")
    elif sb.reliability_score > sa.reliability_score:
        diff = sb.reliability_score - sa.reliability_score
        advantages.append(f"{sb.player_name} holds higher composite reliability (+{diff:.2f} pts).")

    if sa.pressure_uplift > sb.pressure_uplift:
        diff = sa.pressure_uplift - sb.pressure_uplift
        advantages.append(f"{sa.player_name} exhibits stronger pressure uplift (+{diff:.3f}).")
    elif sb.pressure_uplift > sa.pressure_uplift:
        diff = sb.pressure_uplift - sa.pressure_uplift
        advantages.append(f"{sb.player_name} exhibits stronger pressure uplift (+{diff:.3f}).")

    if sa.shrinkage_weight > sb.shrinkage_weight:
        diff = sa.shrinkage_weight - sb.shrinkage_weight
        advantages.append(f"{sa.player_name} has higher empirical sample certainty (+{diff:.2f}).")
    elif sb.shrinkage_weight > sa.shrinkage_weight:
        diff = sb.shrinkage_weight - sa.shrinkage_weight
        advantages.append(f"{sb.player_name} has higher empirical sample certainty (+{diff:.2f}).")

    return PlayerComparisonResponse(
        discipline=discipline,
        player_a=detail_a,
        player_b=detail_b,
        radar_comparison=radar,
        advantage_analysis=advantages,
    )


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player_detail(
    player_id: int,
    discipline: str = Query("batting", pattern="^(batting|bowling)$"),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> PlayerDetail:
    """Returns deep analytical dossier for a single player."""
    df = store.player_batting_df if discipline == "batting" else store.player_bowling_df
    id_col = "striker_id" if discipline == "batting" else "bowler_id"

    sub = df[df[id_col] == player_id]
    if sub.empty:
        # Check other discipline
        alt_disc = "bowling" if discipline == "batting" else "batting"
        alt_df = store.player_bowling_df if alt_disc == "bowling" else store.player_batting_df
        alt_id_col = "bowler_id" if alt_disc == "bowling" else "striker_id"
        if not alt_df[alt_df[alt_id_col] == player_id].empty:
            discipline = alt_disc
            df = alt_df
            id_col = alt_id_col
            sub = df[df[id_col] == player_id]
        else:
            raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found in {discipline}.")

    row = sub.iloc[0]

    # Rank
    rankings_df = store.full_batting_rankings_df if discipline == "batting" else store.full_bowling_rankings_df
    rank_map = dict(zip(rankings_df["player_id"], rankings_df["rank"]))
    p_rank = rank_map.get(player_id)

    item = _extract_player_item(row, discipline, rank=p_rank)

    # Match appearances from deliveries
    delivs = store.pressure_states_df[store.pressure_states_df[id_col] == player_id]
    p_class_col = "batting_pressure_class" if discipline == "batting" else "bowling_pressure_class"
    hp_delivs = delivs[delivs[p_class_col] == "HIGH_PRESSURE"]

    match_points = []
    if not hp_delivs.empty:
        # Group by match
        m_grouped = hp_delivs.groupby("match_id")
        for m_id, m_df in m_grouped:
            b_cnt = len(m_df)
            m_row = store.matches_df[store.matches_df["match_id"] == m_id]
            opp = "Opponent"
            v_name = "Venue"
            m_date = "Date"
            if not m_row.empty:
                mr = m_row.iloc[0]
                m_date = str(mr.get("match_date", "Date"))
                v_name = str(mr.get("venue", "Venue"))
                # Opponent
                bat_t = int(m_df["batting_team_id"].iloc[0])
                bowl_t = int(m_df["bowling_team_id"].iloc[0])
                opp_id = bowl_t if discipline == "batting" else bat_t
                opp = store.get_team_name(opp_id)

            if discipline == "batting":
                runs_or_w = int(m_df["runs_scored_on_ball"].sum())
            else:
                runs_or_w = int(m_df["is_bowler_wicket"].sum())

            # Impact estimate
            imp_rate = item.hp_impact_per_ball
            net_imp = round(b_cnt * imp_rate, 2)
            is_pos = net_imp > 0

            match_points.append(PlayerPerformancePoint(
                match_id=int(m_id),
                match_date=m_date,
                opponent_team=opp,
                opponent_name=opp,
                venue=v_name,
                balls=b_cnt,
                hp_balls=b_cnt,
                runs_or_wkts=runs_or_w,
                hp_runs_or_wkts=runs_or_w,
                net_impact=net_imp,
                hp_impact=net_imp,
                impact_per_ball=imp_rate,
                is_positive_contribution=is_pos,
            ))

    tot_m = int(row.get("total_matches", len(match_points)))
    tot_b = int(row.get("total_balls_faced" if discipline == "batting" else "total_legal_balls", item.hp_balls))
    tot_rw = int(row.get("total_batter_runs" if discipline == "batting" else "total_wickets", item.hp_runs_or_wkts))
    ord_b = int(row.get("ord_balls", 0))
    ord_rw = int(row.get("ord_batter_runs" if discipline == "batting" else "ord_wickets", 0))

    ci_l = round(float(row.get("ci_lower_90", item.reliability_score - 5.0)), 2)
    ci_u = round(float(row.get("ci_upper_90", item.reliability_score + 5.0)), 2)
    best_m = round(float(row.get("mean_match_impact", 1.0)) * 1.5, 2)
    worst_m = round(float(row.get("worst_quartile_match_impact", -0.5)), 2)

    return PlayerDetail(
        summary=item,
        competitions_count=int(row.get("competitions_represented", 1)),
        total_matches=tot_m,
        total_balls=tot_b,
        total_runs_or_wkts=tot_rw,
        ordinary_balls=ord_b,
        ordinary_runs_or_wkts=ord_rw,
        ordinary_impact_per_ball=item.ord_baseline_impact,
        ci_lower_90=ci_l,
        ci_upper_90=ci_u,
        best_match_impact=best_m,
        worst_match_impact=worst_m,
        match_appearances=match_points,
    )

