"""Competitions API Routes."""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends

from backend.api.schemas.models import CompetitionItem
from backend.api.services.data_loader import AnalyticsDataStore, get_datastore

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.get("", response_model=List[CompetitionItem])
def list_competitions(store: AnalyticsDataStore = Depends(get_datastore)) -> List[CompetitionItem]:
    """Returns all 6 competitions with aggregate match and team counts."""
    results = []
    comp_df = store.competitions_df
    matches_df = store.matches_df

    for _, row in comp_df.iterrows():
        c_id = int(row["comp_id"])
        c_name = str(row.get("comp_name", f"Competition {c_id}"))
        c_format = str(row.get("match_format", "T20"))

        m_sub = matches_df[matches_df["comp_id"] == c_id]
        m_cnt = len(m_sub)
        h_teams = set(m_sub["home_team_id"].dropna()) if "home_team_id" in m_sub.columns else set()
        a_teams = set(m_sub["away_team_id"].dropna()) if "away_team_id" in m_sub.columns else set()
        t_cnt = len(h_teams.union(a_teams)) if m_cnt > 0 else 0

        dates = m_sub["match_date"].dropna().astype(str).tolist() if m_cnt > 0 else []
        first_d = min(dates) if dates else None
        last_d = max(dates) if dates else None

        results.append(CompetitionItem(
            comp_id=c_id,
            comp_name=c_name,
            match_format=c_format,
            matches_count=m_cnt,
            teams_count=t_cnt,
            first_match_date=first_d,
            last_match_date=last_d,
        ))

    return results

