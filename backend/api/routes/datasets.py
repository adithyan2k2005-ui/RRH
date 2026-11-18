"""Data Explorer Routes for Dataset Inspection and Paginated Queries."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.api.schemas.models import DatasetMeta, DatasetRecordsResponse
from backend.api.services.data_loader import DATA_DIR, OUTPUTS_DIR, AnalyticsDataStore, get_datastore

router = APIRouter(prefix="/datasets", tags=["Datasets"])

DATASET_CATALOG = {
    "competitions": {
        "name": "Competitions Metadata",
        "file": DATA_DIR / "competitions.parquet",
        "description": "Multi-competition T20 tournament metadata (comp_id, format, season).",
    },
    "teams": {
        "name": "Teams Registry",
        "file": DATA_DIR / "teams.parquet",
        "description": "Participating franchise and international cricket teams.",
    },
    "matches": {
        "name": "Matches Registry",
        "file": DATA_DIR / "matches.parquet",
        "description": "Match fixtures, dates, venues, targets, results, and knockout stages.",
    },
    "playing_eleven": {
        "name": "Playing XI Confirmations",
        "file": DATA_DIR / "playing_eleven.parquet",
        "description": "Player match selection lineup confirmations.",
    },
    "match_states": {
        "name": "Reconstructed Match States (Phase 2)",
        "file": DATA_DIR / "match_states.parquet",
        "description": "Delivery-by-delivery chronological state with zero future leakage.",
    },
    "pressure_states": {
        "name": "Pressure States (Phase 3)",
        "file": DATA_DIR / "pressure_states.parquet",
        "description": "Ball-by-ball batting and bowling pressure scores (0-100) and factors.",
    },
    "player_batting_metrics": {
        "name": "Player Batting Metrics (Phase 4)",
        "file": DATA_DIR / "player_batting_metrics.parquet",
        "description": "Context-adjusted batting impact, uplift, consistency, and reliability.",
    },
    "player_bowling_metrics": {
        "name": "Player Bowling Metrics (Phase 4)",
        "file": DATA_DIR / "player_bowling_metrics.parquet",
        "description": "Context-adjusted bowling impact, uplift, consistency, and reliability.",
    },
    "top_10_batters": {
        "name": "Official Top 10 Batters (Phase 5)",
        "file": OUTPUTS_DIR / "top_10_batters.csv",
        "description": "Official verified Top 10 Batters ranked under pressure.",
    },
    "top_10_bowlers": {
        "name": "Official Top 10 Bowlers (Phase 5)",
        "file": OUTPUTS_DIR / "top_10_bowlers.csv",
        "description": "Official verified Top 10 Bowlers ranked under pressure.",
    },
    "full_batting_rankings": {
        "name": "Full Batting Rankings (Phase 5)",
        "file": OUTPUTS_DIR / "full_batting_rankings.csv",
        "description": "All 155 qualified batters ordered by reliability.",
    },
    "full_bowling_rankings": {
        "name": "Full Bowling Rankings (Phase 5)",
        "file": OUTPUTS_DIR / "full_bowling_rankings.csv",
        "description": "All 270 qualified bowlers ordered by reliability.",
    },
}


def _load_dataset_df(dataset_id: str, store: AnalyticsDataStore) -> pd.DataFrame:
    if dataset_id not in DATASET_CATALOG:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    meta = DATASET_CATALOG[dataset_id]
    file_path: Path = meta["file"]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File for dataset '{dataset_id}' is missing.")

    if dataset_id == "matches":
        return store.matches_df
    elif dataset_id == "pressure_states":
        return store.pressure_states_df
    elif dataset_id == "competitions":
        return store.competitions_df
    elif dataset_id == "teams":
        return store.teams_df
    elif dataset_id == "player_batting_metrics":
        return store.player_batting_df
    elif dataset_id == "player_bowling_metrics":
        return store.player_bowling_df
    elif dataset_id == "top_10_batters":
        return store.top_10_batters_df
    elif dataset_id == "top_10_bowlers":
        return store.top_10_bowlers_df
    elif dataset_id == "full_batting_rankings":
        return store.full_batting_rankings_df
    elif dataset_id == "full_bowling_rankings":
        return store.full_bowling_rankings_df

    if str(file_path).endswith(".parquet"):
        return pd.read_parquet(file_path)
    else:
        return pd.read_csv(file_path)


@router.get("", response_model=List[DatasetMeta])
def list_datasets(store: AnalyticsDataStore = Depends(get_datastore)) -> List[DatasetMeta]:
    """Lists all available raw and processed datasets with metadata."""
    results = []
    for d_id, info in DATASET_CATALOG.items():
        p: Path = info["file"]
        if p.exists():
            df = _load_dataset_df(d_id, store)
            col_list = [{"name": str(col), "type": str(dtype)} for col, dtype in df.dtypes.items()]
            results.append(DatasetMeta(
                dataset_id=d_id,
                name=info["name"],
                row_count=len(df),
                rows_count=len(df),
                column_count=len(df.columns),
                columns_count=len(df.columns),
                size_bytes=p.stat().st_size,
                file_size_bytes=p.stat().st_size,
                description=info["description"],
                columns=col_list,
            ))
    return results


@router.get("/{dataset_id}/schema", response_model=DatasetMeta)
def get_dataset_schema(dataset_id: str, store: AnalyticsDataStore = Depends(get_datastore)) -> DatasetMeta:
    """Returns detailed schema, row count, and column data types for a dataset."""
    df = _load_dataset_df(dataset_id, store)
    info = DATASET_CATALOG[dataset_id]
    col_list = [{"name": str(col), "type": str(dtype)} for col, dtype in df.dtypes.items()]
    return DatasetMeta(
        dataset_id=dataset_id,
        name=info["name"],
        row_count=len(df),
        rows_count=len(df),
        column_count=len(df.columns),
        columns_count=len(df.columns),
        size_bytes=info["file"].stat().st_size,
        file_size_bytes=info["file"].stat().st_size,
        description=info["description"],
        columns=col_list,
    )


@router.get("/{dataset_id}/records", response_model=DatasetRecordsResponse)
def get_dataset_records(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    format_csv: bool = Query(False),
    store: AnalyticsDataStore = Depends(get_datastore),
) -> Any:
    """Returns paginated and searchable records from the dataset, or exports as CSV."""
    df = _load_dataset_df(dataset_id, store)

    # Search filter across columns
    if search:
        search_lower = search.strip().lower()
        masks = [df[col].astype(str).str.lower().str.contains(search_lower, na=False) for col in df.columns]
        if masks:
            combined_mask = masks[0]
            for m in masks[1:]:
                combined_mask |= m
            df = df[combined_mask]

    # Sorting
    if sort_by and sort_by in df.columns:
        ascending = sort_order == "asc"
        df = df.sort_values(by=sort_by, ascending=ascending)

    total_records = len(df)
    total_pages = max(1, (total_records + page_size - 1) // page_size)

    # CSV Export format
    if format_csv:
        output = io.StringIO()
        export_df = df.head(5000)  # Max export limit
        export_df.to_csv(output, index=False)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={dataset_id}_export.csv"},
        )

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    sliced = df.iloc[start:end].copy()

    # Convert NaNs to None for clean JSON serialization
    records = sliced.where(pd.notnull(sliced), None).to_dict(orient="records")

    return DatasetRecordsResponse(
        dataset_id=dataset_id,
        total_records=total_records,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        columns=list(df.columns),
        records=records,
    )

