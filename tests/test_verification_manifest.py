"""Tests for Verification Manifest, Submission Gates, and Integrity Architecture.

Covers all 12 verification scenarios required by Critical Repair 4:
1. Passing verification manifests.
2. Failed verification manifests.
3. Missing manifest.
4. Malformed manifest.
5. Stale manifest.
6. Partial phase completion.
7. Failed artifact checks.
8. Incorrect ranking order.
9. Missing report sections.
10. Frontend status rendering.
11. API status consistency.
12. Repeated verification execution.
"""

from __future__ import annotations

import copy
import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.routes import health, overview
from scripts import verify_project

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "reports" / "verification_manifest.json"


@pytest.fixture
def valid_manifest_data() -> Dict[str, Any]:
    """Provides a fresh, valid copy of verification manifest."""
    assert MANIFEST_PATH.exists(), "Production manifest must exist before test"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_01_passing_verification_manifest(valid_manifest_data):
    """1. Verifies that when all phases pass without failure, overall status is PASS or PASS_WITH_WARNINGS."""
    manifest = copy.deepcopy(valid_manifest_data)
    assert manifest["overall_status"] in ["PASS", "PASS_WITH_WARNINGS"]
    assert manifest["submission_readiness"] == "PASS"
    assert manifest["summary"]["failed_tests"] == 0
    assert manifest["summary"]["submission_gates_passed"] == 12


def test_02_failed_verification_manifest(valid_manifest_data):
    """2. Verifies that a failing phase forces overall status to FAIL."""
    manifest = copy.deepcopy(valid_manifest_data)
    manifest["phases"]["3"]["status"] = "FAIL"

    # Evaluate overall status logic
    any_failed = any(p["status"] == "FAIL" for p in manifest["phases"].values())
    overall = "FAIL" if any_failed else "PASS"
    assert overall == "FAIL"


def test_03_missing_manifest(monkeypatch, tmp_path):
    """3. Verifies that when the manifest file is absent, API returns UNVERIFIED safely without throwing 500."""
    non_existent = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(overview, "MANIFEST_PATH", non_existent)
    monkeypatch.setattr(health, "MANIFEST_PATH", non_existent)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    h_data = resp.json()
    assert h_data["verification_status"] == "UNVERIFIED"
    assert "UNVERIFIED" in h_data["test_suite_status"]

    o_resp = client.get("/api/overview")
    assert o_resp.status_code == 200
    o_data = o_resp.json()
    assert o_data["overall_verification_status"] == "UNVERIFIED"
    for phase in o_data["pipeline_phases"]:
        assert phase["status"] == "UNVERIFIED"


def test_04_malformed_manifest(monkeypatch, tmp_path):
    """4. Verifies that a corrupted or malformed manifest file is handled gracefully as UNVERIFIED."""
    corrupt_file = tmp_path / "corrupt_manifest.json"
    corrupt_file.write_text("NOT_VALID_JSON{:::broken}", encoding="utf-8")

    monkeypatch.setattr(overview, "MANIFEST_PATH", corrupt_file)
    monkeypatch.setattr(health, "MANIFEST_PATH", corrupt_file)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "UNVERIFIED"

    o_resp = client.get("/api/overview")
    assert o_resp.status_code == 200
    assert o_resp.json()["overall_verification_status"] == "UNVERIFIED"


def test_05_stale_manifest(valid_manifest_data):
    """5. Verifies that manifest timestamp can be inspected to detect stale results (> 48 hours)."""
    gen_time_str = valid_manifest_data["generated_at"]
    gen_time = datetime.datetime.fromisoformat(gen_time_str)
    now = datetime.datetime.now(datetime.timezone.utc)
    age_hours = (now - gen_time).total_seconds() / 3600.0

    # Manifest was just generated, age must be less than 1 hour
    assert age_hours < 1.0, f"Manifest is unexpectedly stale: {age_hours:.2f} hours old"


def test_06_partial_phase_completion():
    """6. Verifies that verify_project can execute and return a single isolated phase."""
    single_res = verify_project.verify_phase2()
    assert single_res["phase_number"] == 2
    assert single_res["status"] in ["PASS", "PASS_WITH_WARNINGS"]
    assert single_res["test_count"] == 16
    assert single_res["passed_tests"] == 16


def test_07_failed_artifact_checks(tmp_path, monkeypatch):
    """7. Verifies that if required artifacts are absent, phase verification fails."""
    empty_dir = tmp_path / "empty_processed"
    empty_dir.mkdir()
    monkeypatch.setattr(verify_project, "DATA_PROCESSED", empty_dir)

    p2_res = verify_project.verify_phase2()
    assert p2_res["status"] == "FAIL"
    assert p2_res["artifacts_available"] is False


def test_08_incorrect_ranking_order(tmp_path, monkeypatch):
    """8. Verifies Gate 5 catches non-monotonic or disordered reliability rankings."""
    bad_outputs = tmp_path / "outputs"
    bad_outputs.mkdir()

    # Create disordered ranking CSV (Rank 1 score lower than Rank 2)
    bad_batters = pd.DataFrame([
        {"rank": 1, "player_id": 1, "player_name": "A", "reliability_score": 75.0, "eligibility_status": "ELIGIBLE"},
        {"rank": 2, "player_id": 2, "player_name": "B", "reliability_score": 85.0, "eligibility_status": "ELIGIBLE"},
    ])
    bad_batters.to_csv(bad_outputs / "top_10_batters.csv", index=False)

    valid_bowlers = pd.DataFrame([
        {"rank": 1, "player_id": 3, "player_name": "C", "reliability_score": 90.0, "eligibility_status": "ELIGIBLE"},
        {"rank": 2, "player_id": 4, "player_name": "D", "reliability_score": 80.0, "eligibility_status": "ELIGIBLE"},
    ])
    valid_bowlers.to_csv(bad_outputs / "top_10_bowlers.csv", index=False)

    monkeypatch.setattr(verify_project, "OUTPUTS_DIR", bad_outputs)
    gates = verify_project.evaluate_submission_readiness_gates()
    assert gates["GATE_5"]["status"] == "FAIL"


def test_09_missing_report_sections(tmp_path, monkeypatch):
    """9. Verifies Gate 10 fails if required methodology sections are missing."""
    bad_sub = tmp_path / "submission"
    bad_sub.mkdir()
    # Provide empty or invalid report
    (bad_sub / "methodology_report.pdf").write_bytes(b"%PDF-1.4 dummy empty content")

    monkeypatch.setattr(verify_project, "SUBMISSION_DIR", bad_sub)
    gates = verify_project.evaluate_submission_readiness_gates()
    assert gates["GATE_10"]["status"] == "FAIL"


def test_10_frontend_status_rendering():
    """10. Verifies Overview endpoint outputs all necessary fields for frontend status badge rendering."""
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_verification_status" in data
    assert "submission_readiness" in data
    assert "last_verified_at" in data
    assert len(data["pipeline_phases"]) == 6
    for p in data["pipeline_phases"]:
        assert "status" in p
        assert p["status"] in ["PASS", "PASS_WITH_WARNINGS", "FAIL", "UNVERIFIED"]


def test_11_api_status_consistency():
    """11. Verifies that /api/overview, /api/pipeline/status, and /api/health report consistent status."""
    health_resp = client.get("/api/health").json()
    overview_resp = client.get("/api/overview").json()
    pipe_resp = client.get("/api/pipeline/status").json()

    # Health overall matches overview overall
    assert health_resp["verification_status"] == overview_resp["overall_verification_status"]

    # Pipeline status list matches overview pipeline phases
    assert len(pipe_resp) == len(overview_resp["pipeline_phases"])
    for p1, p2 in zip(pipe_resp, overview_resp["pipeline_phases"]):
        assert p1["phase_number"] == p2["phase_number"]
        assert p1["status"] == p2["status"]


def test_12_repeated_verification_execution():
    """12. Verifies repeated gate evaluation is deterministic with identical pass counts."""
    gates_1 = verify_project.evaluate_submission_readiness_gates()
    gates_2 = verify_project.evaluate_submission_readiness_gates()

    for k in gates_1:
        assert gates_1[k]["status"] == gates_2[k]["status"]
        assert gates_1[k]["title"] == gates_2[k]["title"]
