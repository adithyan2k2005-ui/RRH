"""Contract tests for SupeRR Intelligence Lab Overview endpoint.

Verifies:
1. /api/overview HTTP 200 response with correct top-level keys.
2. competitions_distribution is a List[CompetitionStat] with comp_id, comp_name, matches_count, deliveries_count.
3. pipeline_phases contains 6 phases with both phase_name/name and deliverable/key_output.
4. PlayerTopSummary contains hp_stat_display, pressure_stat, uplift, consistency, key_trait.
5. total_batters_evaluated and total_bowlers_evaluated are populated integers (888 and 647).
6. pressure_distribution matches Phase 3 categories: LOW_PRESSURE, MEDIUM_PRESSURE, HIGH_PRESSURE.
"""

from __future__ import annotations

import pytest
from backend.api.routes.overview import get_overview
from backend.api.services.data_loader import AnalyticsDataStore
from backend.api.schemas.models import OverviewResponse, CompetitionStat


@pytest.fixture(scope="module")
def datastore():
    return AnalyticsDataStore.get_instance()


def test_overview_contract_structure(datastore):
    """Verifies get_overview returns a valid OverviewResponse matching frontend contract."""
    response = get_overview(store=datastore)
    assert isinstance(response, OverviewResponse)
    
    # 1. Competitions distribution must be a list of CompetitionStat objects
    assert isinstance(response.competitions_distribution, list)
    assert len(response.competitions_distribution) > 0
    first_comp = response.competitions_distribution[0]
    assert isinstance(first_comp, CompetitionStat)
    assert hasattr(first_comp, "comp_id")
    assert hasattr(first_comp, "comp_name")
    assert hasattr(first_comp, "matches_count")
    assert hasattr(first_comp, "deliveries_count")
    assert isinstance(first_comp.comp_name, str)
    assert isinstance(first_comp.matches_count, int)
    assert first_comp.matches_count > 0


def test_overview_evaluated_counts(datastore):
    """Verifies total evaluated players match actual dataset sizes."""
    response = get_overview(store=datastore)
    
    assert response.total_batters_evaluated == 888
    assert response.total_bowlers_evaluated == 647
    assert response.eligible_batters == 155
    assert response.eligible_bowlers == 270
    assert response.total_matches == 883
    assert response.total_deliveries == 200999


def test_overview_pipeline_phases_fields(datastore):
    """Verifies pipeline phases contain all required fields for frontend cards."""
    response = get_overview(store=datastore)
    assert len(response.pipeline_phases) == 6
    
    for phase in response.pipeline_phases:
        # Check both naming conventions for resilient contract
        assert phase.phase_id is not None
        assert phase.phase_name is not None
        assert phase.name is not None
        assert phase.status in ("PASS", "PASSED", "PASS_WITH_WARNINGS", "VERIFIED", "UNVERIFIED")
        assert phase.deliverable is not None
        assert phase.key_output is not None


def test_overview_player_summaries(datastore):
    """Verifies top batter and bowler summaries have all required metrics."""
    response = get_overview(store=datastore)
    
    batter = response.top_batter_summary
    bowler = response.top_bowler_summary
    
    assert batter.player_name == "Vipraj Nigam"
    assert batter.rank == 1
    assert batter.hp_stat_display is not None
    assert batter.pressure_stat is not None
    assert batter.key_trait is not None
    assert "Uplift" in batter.key_trait
    assert batter.uplift is not None
    assert batter.consistency is not None
    
    assert bowler.player_name == "Manimaran Siddharth"
    assert bowler.rank == 1
    assert bowler.hp_stat_display is not None
    assert bowler.pressure_stat is not None
    assert bowler.key_trait is not None
    assert bowler.uplift is not None
    assert bowler.consistency is not None


def test_overview_pressure_distribution(datastore):
    """Verifies Phase 3 pressure categories and total count."""
    response = get_overview(store=datastore)
    dist = response.pressure_distribution
    
    # Must contain Phase 3 categories for both batting and bowling
    for discipline_dict in (dist.batting, dist.bowling):
        assert "LOW_PRESSURE" in discipline_dict
        assert "MEDIUM_PRESSURE" in discipline_dict
        assert "HIGH_PRESSURE" in discipline_dict
        
        # Each discipline must sum to total deliveries
        assert sum(discipline_dict.values()) == response.total_deliveries
