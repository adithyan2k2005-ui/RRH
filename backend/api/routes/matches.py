"""Matches and Ball-by-Ball Replay API Routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.schemas.models import DeliveryState, MatchSummary
from backend.api.services.data_loader import AnalyticsDataStore, get_datastore

router = APIRouter(prefix="/matches", tags=["Matches"])


def safe_float(val: Any, default: Optional[float] = 0.0) -> Optional[float]:
    if pd.isna(val) or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@router.get("", response_model=List[MatchSummary])
def list_matches(
    comp_id: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    knock_out: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=750),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> List[MatchSummary]:
    """Returns matches filtered by competition, stage, knockout, or team/venue search."""
    df = store.matches_df.copy()

    if comp_id is not None:
        df = df[df["comp_id"] == comp_id]
    if stage is not None:
        df = df[df["stage"].str.lower() == stage.lower()]
    if knock_out is not None:
        df = df[df["knock_out"] == knock_out]

    if search:
        s = search.strip().lower()
        df = df[
            df["venue_country"].astype(str).str.lower().str.contains(s, na=False)
            | df["home_team"].astype(str).str.lower().str.contains(s, na=False)
            | df["away_team"].astype(str).str.lower().str.contains(s, na=False)
        ]

    df = df.head(limit)
    results = []

    for _, row in df.iterrows():
        m_id = int(row["match_id"])
        c_id = int(row["comp_id"])
        t1_id = int(row.get("home_team_id", 0)) if pd.notnull(row.get("home_team_id")) else 0
        t2_id = int(row.get("away_team_id", 0)) if pd.notnull(row.get("away_team_id")) else 0

        # Check innings available
        delivs = store.get_match_deliveries(m_id)
        inns = sorted(list(delivs["innings"].unique())) if not delivs.empty else []

        results.append(MatchSummary(
            match_id=m_id,
            comp_id=c_id,
            comp_name=store.get_comp_name(c_id),
            team1_id=t1_id,
            team1_name=str(row.get("home_team", store.get_team_name(t1_id))),
            team2_id=t2_id,
            team2_name=str(row.get("away_team", store.get_team_name(t2_id))),
            match_date=str(row.get("match_date", "Unknown")),
            venue=str(row.get("venue_country", "Unknown")),
            match_format=str(row.get("match_format", "T20")),
            stage=str(row.get("stage", "league")),
            knock_out=int(row.get("knock_out", 0)),
            scheduled_overs=float(row.get("scheduled_overs", 20.0)),
            target=float(row["revised_target"]) if pd.notnull(row.get("revised_target")) else None,
            is_target_revised=1 if pd.notnull(row.get("revised_target")) else 0,
            winner_team_id=int(row["win_team_id"]) if pd.notnull(row.get("win_team_id")) else None,
            result_margin=str(row["result"]) if pd.notnull(row.get("result")) else None,
            total_deliveries=len(delivs),
            innings_available=[int(i) for i in inns],
        ))

    return results


@router.get("/{match_id}", response_model=MatchSummary)
def get_match_detail(
    match_id: int,
    store: AnalyticsDataStore = Depends(get_datastore),
) -> MatchSummary:
    """Returns detailed match summary metadata."""
    sub = store.matches_df[store.matches_df["match_id"] == match_id]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"Match ID {match_id} not found.")

    row = sub.iloc[0]
    c_id = int(row["comp_id"])
    t1_id = int(row.get("home_team_id", 0)) if pd.notnull(row.get("home_team_id")) else 0
    t2_id = int(row.get("away_team_id", 0)) if pd.notnull(row.get("away_team_id")) else 0

    delivs = store.get_match_deliveries(match_id)
    inns = sorted(list(delivs["innings"].unique())) if not delivs.empty else []

    return MatchSummary(
        match_id=match_id,
        comp_id=c_id,
        comp_name=store.get_comp_name(c_id),
        team1_id=t1_id,
        team1_name=str(row.get("home_team", store.get_team_name(t1_id))),
        team2_id=t2_id,
        team2_name=str(row.get("away_team", store.get_team_name(t2_id))),
        match_date=str(row.get("match_date", "Unknown")),
        venue=str(row.get("venue_country", "Unknown")),
        match_format=str(row.get("match_format", "T20")),
        stage=str(row.get("stage", "league")),
        knock_out=int(row.get("knock_out", 0)),
        scheduled_overs=float(row.get("scheduled_overs", 20.0)),
        target=float(row["revised_target"]) if pd.notnull(row.get("revised_target")) else None,
        is_target_revised=1 if pd.notnull(row.get("revised_target")) else 0,
        winner_team_id=int(row["win_team_id"]) if pd.notnull(row.get("win_team_id")) else None,
        result_margin=str(row["result"]) if pd.notnull(row.get("result")) else None,
        total_deliveries=len(delivs),
        innings_available=[int(i) for i in inns],
    )


@router.get("/{match_id}/deliveries", response_model=List[DeliveryState])
def get_match_deliveries(
    match_id: int,
    innings: Optional[int] = Query(None),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> List[DeliveryState]:
    """Returns chronological delivery records with pre-ball match state and pressure scores."""
    delivs = store.get_match_deliveries(match_id, innings=innings)
    if delivs.empty:
        # Check if match exists
        if store.matches_df[store.matches_df["match_id"] == match_id].empty:
            raise HTTPException(status_code=404, detail=f"Match ID {match_id} not found.")
        return []

    results = []
    for _, row in delivs.iterrows():
        results.append(DeliveryState(
            match_id=int(row["match_id"]),
            innings=int(row["innings"]),
            delivery_seq=int(row["delivery_seq"]),
            overid=int(row["overid"]),
            over_ball_num=int(row["over_ball_num"]),
            innings_ball_num=int(row["innings_ball_num"]),
            striker_id=int(row["striker_id"]),
            striker_name=str(row.get("striker_name", "Unknown")),
            non_striker_id=int(row.get("non_striker_id", 0)),
            non_striker_name=str(row.get("non_striker_name", "")),
            bowler_id=int(row["bowler_id"]),
            bowler_name=str(row.get("bowler_name", "Unknown")),
            is_legal_ball=bool(row.get("is_legal_ball", True)),
            runs_scored_on_ball=int(row.get("runs_scored_on_ball", 0)),
            extras_on_ball=int(row.get("extras_on_ball", 0)),
            runs_charged_to_bowler=int(row.get("runs_charged_to_bowler_on_ball", 0)),
            is_team_wicket=bool(row.get("is_team_wicket", False)),
            is_bowler_wicket=bool(row.get("is_bowler_wicket", False)),
            dismissal_type=str(row["dismissal_type"]) if pd.notnull(row.get("dismissal_type")) else None,
            innings_score_before=int(row.get("innings_score_before", 0)),
            wickets_lost_before=int(row.get("wickets_lost_before", 0)),
            legal_balls_bowled_before=int(row.get("legal_balls_bowled_before", 0)),
            scheduled_balls_remaining_before=int(row.get("scheduled_balls_remaining_before", 120)),
            current_run_rate=round(safe_float(row.get("current_run_rate"), 0.0), 2),
            runs_required_before=safe_float(row.get("runs_required_before"), None),
            required_run_rate=round(safe_float(row.get("required_run_rate")), 2) if safe_float(row.get("required_run_rate"), None) is not None else None,
            batting_pressure_score=round(safe_float(row.get("batting_pressure_score"), 0.0), 2),
            bowling_pressure_score=round(safe_float(row.get("bowling_pressure_score"), 0.0), 2),
            match_tension_score=round(safe_float(row.get("match_tension_score"), 0.0), 2),
            batting_pressure_class=str(row.get("batting_pressure_class", "LOW_PRESSURE")),
            bowling_pressure_class=str(row.get("bowling_pressure_class", "LOW_PRESSURE")),
            wicket_vulnerability=round(safe_float(row.get("wicket_vulnerability"), 0.0), 4),
            time_pressure=round(safe_float(row.get("time_pressure"), 0.0), 4),
            chase_urgency=round(safe_float(row.get("chase_urgency"), 0.0), 4),
            match_closeness=round(safe_float(row.get("match_closeness"), 0.0), 4),
            first_inn_par_deficit=round(safe_float(row.get("first_inn_par_deficit"), 0.0), 4),
            match_stakes_multiplier=round(safe_float(row.get("match_stakes_multiplier"), 1.0), 2),
        ))

    return results


@router.get("/{match_id}/pressure")
def get_match_pressure_curve(
    match_id: int,
    innings: Optional[int] = Query(None),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> Dict[str, Any]:
    """Returns timeline arrays optimized for rendering pressure charts in the frontend."""
    delivs = store.get_match_deliveries(match_id, innings=innings)
    if delivs.empty:
        raise HTTPException(status_code=404, detail=f"No delivery pressure data for match {match_id}.")

    curve = []
    for _, r in delivs.iterrows():
        curve.append({
            "delivery_seq": int(r["delivery_seq"]),
            "innings": int(r["innings"]),
            "over_label": f"{int(r['overid'])}.{int(r['over_ball_num'])}",
            "batting_pressure": round(float(r.get("batting_pressure_score", 0.0)), 2),
            "bowling_pressure": round(float(r.get("bowling_pressure_score", 0.0)), 2),
            "match_tension": round(float(r.get("match_tension_score", 0.0)), 2),
            "striker": str(r.get("striker_name", "")),
            "bowler": str(r.get("bowler_name", "")),
            "runs": int(r.get("runs_scored_on_ball", 0)),
            "is_wicket": bool(r.get("is_team_wicket", False)),
            "score_before": f"{int(r.get('innings_score_before', 0))}/{int(r.get('wickets_lost_before', 0))}",
        })

    return {
        "match_id": match_id,
        "innings": innings,
        "total_deliveries": len(curve),
        "pressure_timeline": curve,
    }

