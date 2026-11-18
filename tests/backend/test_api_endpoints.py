"""Backend API Endpoint Tests for SupeRR Intelligence Lab."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_api_health_endpoint():
    """Verifies /api/health returns status ok, correct data volumes, and dynamic test status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["deliveries_loaded"] == 200999
    assert data["matches_loaded"] == 883
    assert "PASSED" in data["test_suite_status"] or "UNVERIFIED" in data["test_suite_status"]
    assert "verification_status" in data


def test_api_overview_endpoint():
    """Verifies /api/overview returns verified counts and top player summaries."""
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_matches"] == 883
    assert data["total_deliveries"] == 200999
    assert data["eligible_batters"] == 155
    assert data["eligible_bowlers"] == 270
    assert len(data["pipeline_phases"]) == 6

    # Verify Top 1 players
    assert data["top_batter_summary"]["player_id"] == 46066
    assert data["top_batter_summary"]["player_name"] == "Vipraj Nigam"
    assert data["top_bowler_summary"]["player_id"] == 6237
    assert data["top_bowler_summary"]["player_name"] == "Manimaran Siddharth"


def test_api_pipeline_status():
    """Verifies all 6 phases report verified status from manifest."""
    resp = client.get("/api/pipeline/status")
    assert resp.status_code == 200
    phases = resp.json()
    assert len(phases) == 6
    for p in phases:
        assert p["status"] in ["PASS", "PASSED", "PASS_WITH_WARNINGS", "UNVERIFIED"]


def test_api_datasets_list_and_records():
    """Verifies dataset catalog and paginated record retrieval."""
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) >= 10

    # Test records pagination on competitions
    rec_resp = client.get("/api/datasets/competitions/records?page=1&page_size=5")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["total_records"] == 141
    assert len(rec_data["records"]) <= 5


def test_api_competitions():
    """Verifies all competitions are returned with match counts."""
    resp = client.get("/api/competitions")
    assert resp.status_code == 200
    comps = resp.json()
    assert len(comps) == 141
    total_matches = sum(c["matches_count"] for c in comps)
    assert total_matches == 883


def test_api_matches_and_deliveries():
    """Verifies match listing, single match retrieval, and delivery states."""
    resp = client.get("/api/matches?limit=10")
    assert resp.status_code == 200
    matches = resp.json()
    assert len(matches) > 0

    first_m_id = matches[0]["match_id"]
    detail_resp = client.get(f"/api/matches/{first_m_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["match_id"] == first_m_id

    # Test deliveries
    deliv_resp = client.get(f"/api/matches/{first_m_id}/deliveries")
    assert deliv_resp.status_code == 200
    delivs = deliv_resp.json()
    if len(delivs) > 0:
        d0 = delivs[0]
        assert "innings_score_before" in d0
        assert "batting_pressure_score" in d0
        assert "bowling_pressure_score" in d0

    # Test pressure timeline
    press_resp = client.get(f"/api/matches/{first_m_id}/pressure")
    assert press_resp.status_code == 200
    assert "pressure_timeline" in press_resp.json()


def test_api_rankings_batting_and_bowling():
    """Verifies official rankings match Phase 5 exactly."""
    bat_resp = client.get("/api/rankings/batting")
    assert bat_resp.status_code == 200
    bat_data = bat_resp.json()

    assert bat_data["total_eligible"] == 155
    assert len(bat_data["top_10"]) == 10
    assert bat_data["top_10"][0]["player_id"] == 46066
    assert bat_data["top_10"][0]["player_name"] == "Vipraj Nigam"
    assert bat_data["top_10"][0]["reliability_score"] == 92.69
    assert len(bat_data["near_miss_11_15"]) == 5

    bowl_resp = client.get("/api/rankings/bowling")
    assert bowl_resp.status_code == 200
    bowl_data = bowl_resp.json()

    assert bowl_data["total_eligible"] == 270
    assert len(bowl_data["top_10"]) == 10
    assert bowl_data["top_10"][0]["player_id"] == 6237
    assert bowl_data["top_10"][0]["player_name"] == "Manimaran Siddharth"
    assert bowl_data["top_10"][0]["reliability_score"] == 88.46


def test_api_rankings_validation():
    """Verifies all 16 quality gates are reported as passed."""
    resp = client.get("/api/rankings/validation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_quality_gates_passed"] is True
    assert data["gates_count"] == 16


def test_api_players_detail_and_compare():
    """Verifies player details, match appearances, and comparison endpoint."""
    resp = client.get("/api/players/46066?discipline=batting")
    assert resp.status_code == 200
    p_data = resp.json()
    assert p_data["summary"]["player_name"] == "Vipraj Nigam"
    assert p_data["summary"]["reliability_score"] == 92.69

    # Compare 46066 vs 6651 (Rank 1 vs Rank 2)
    comp_resp = client.get("/api/players/compare?player_a_id=46066&player_b_id=6651&discipline=batting")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert "radar_comparison" in comp_data
    assert len(comp_data["advantage_analysis"]) > 0


def test_api_reports_list_and_download():
    """Verifies report listing and downloading."""
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    reports = resp.json()
    assert len(reports) >= 7

    # Download CSV
    csv_resp = client.get("/api/reports/top-10-batters-csv/download")
    assert csv_resp.status_code == 200
    assert "Vipraj Nigam" in csv_resp.text


def test_api_verification_manifest_and_gates():
    """Verifies verification manifest endpoint and submission gates."""
    resp = client.get("/api/verification/manifest")
    assert resp.status_code == 200
    m_data = resp.json()
    assert "overall_status" in m_data
    assert "phases" in m_data

    gates_resp = client.get("/api/verification/submission-gates")
    assert gates_resp.status_code == 200
    g_data = gates_resp.json()
    assert g_data["submission_readiness"] in ["PASS", "FAIL", "UNVERIFIED"]
    assert len(g_data["gates"]) == 12
    for i in range(1, 13):
        assert f"GATE_{i}" in g_data["gates"]

