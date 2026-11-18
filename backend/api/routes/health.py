"""Health Check Route."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends

from backend.api.schemas.models import HealthResponse
from backend.api.services.data_loader import AnalyticsDataStore, REPORTS_DIR, get_datastore

router = APIRouter(tags=["Health"])

MANIFEST_PATH = REPORTS_DIR / "verification_manifest.json"


def load_manifest() -> Optional[Dict[str, Any]]:
    """Loads verification manifest safely with error suppression."""
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "phases" in data and "summary" in data:
            return data
    except Exception:
        pass
    return None


@router.get("/health", response_model=HealthResponse)
def get_health(store: AnalyticsDataStore = Depends(get_datastore)) -> HealthResponse:
    """Returns system status, package versions, dataset load stats, and real test status."""
    manifest = load_manifest()
    if manifest and "summary" in manifest:
        passed = manifest["summary"].get("passed_tests", 0)
        total = manifest["summary"].get("total_tests", 0)
        overall = manifest.get("overall_status", "PASS")
        test_status = f"{passed} / {total} PASSED ({overall})"
        verification_status = overall
        last_verified = manifest.get("generated_at")
    else:
        test_status = "UNVERIFIED (Verification runner not executed)"
        verification_status = "UNVERIFIED"
        last_verified = None

    return HealthResponse(
        status="ok",
        version="2.0.0",
        app_name="SupeRR Intelligence Lab",
        deliveries_loaded=len(store.pressure_states_df),
        matches_loaded=len(store.matches_df),
        players_loaded=len(store.player_batting_df) + len(store.player_bowling_df),
        test_suite_status=test_status,
        verification_status=verification_status,
        last_verified_at=last_verified,
    )
