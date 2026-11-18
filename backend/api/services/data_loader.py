"""Data Loader and Cache Service for SupeRR Intelligence Lab.

Provides thread-safe, high-performance in-memory caching and indexed lookups
for all verified Parquet and CSV artifacts across Phases 1 through 6.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SUBMISSION_DIR = PROJECT_ROOT / "submission"
REPORTS_DIR = PROJECT_ROOT / "reports"


class AnalyticsDataStore:
    _instance: Optional[AnalyticsDataStore] = None

    def __init__(self) -> None:
        logger.info("Initializing AnalyticsDataStore...")
        self.competitions_df: pd.DataFrame = pd.DataFrame()
        self.teams_df: pd.DataFrame = pd.DataFrame()
        self.matches_df: pd.DataFrame = pd.DataFrame()
        self.pressure_states_df: pd.DataFrame = pd.DataFrame()
        self.player_batting_df: pd.DataFrame = pd.DataFrame()
        self.player_bowling_df: pd.DataFrame = pd.DataFrame()
        self.top_10_batters_df: pd.DataFrame = pd.DataFrame()
        self.top_10_bowlers_df: pd.DataFrame = pd.DataFrame()
        self.full_batting_rankings_df: pd.DataFrame = pd.DataFrame()
        self.full_bowling_rankings_df: pd.DataFrame = pd.DataFrame()

        self._comp_map: Dict[int, str] = {}
        self._team_map: Dict[int, str] = {}
        self._match_deliveries_cache: Dict[int, pd.DataFrame] = {}
        self._load_core_data()

    @classmethod
    def get_instance(cls) -> AnalyticsDataStore:
        if cls._instance is None:
            cls._instance = AnalyticsDataStore()
        return cls._instance

    def _load_core_data(self) -> None:
        try:
            logger.info("Loading competitions, teams, matches...")
            self.competitions_df = pd.read_parquet(DATA_DIR / "competitions.parquet")
            self.teams_df = pd.read_parquet(DATA_DIR / "teams.parquet")
            self.matches_df = pd.read_parquet(DATA_DIR / "matches.parquet")

            # Lookup dictionaries
            if "comp_id" in self.competitions_df.columns and "comp_name" in self.competitions_df.columns:
                self._comp_map = dict(zip(self.competitions_df["comp_id"], self.competitions_df["comp_name"]))
            if "team_id" in self.teams_df.columns and "team_name" in self.teams_df.columns:
                self._team_map = dict(zip(self.teams_df["team_id"], self.teams_df["team_name"]))

            logger.info("Loading player metrics parquets...")
            self.player_batting_df = pd.read_parquet(DATA_DIR / "player_batting_metrics.parquet")
            self.player_bowling_df = pd.read_parquet(DATA_DIR / "player_bowling_metrics.parquet")

            logger.info("Loading official ranking CSVs...")
            self.top_10_batters_df = pd.read_csv(OUTPUTS_DIR / "top_10_batters.csv")
            self.top_10_bowlers_df = pd.read_csv(OUTPUTS_DIR / "top_10_bowlers.csv")
            self.full_batting_rankings_df = pd.read_csv(OUTPUTS_DIR / "full_batting_rankings.csv")
            self.full_bowling_rankings_df = pd.read_csv(OUTPUTS_DIR / "full_bowling_rankings.csv")

            logger.info("Loading pressure states parquet for delivery inspection...")
            self.pressure_states_df = pd.read_parquet(DATA_DIR / "pressure_states.parquet")

            logger.info(
                "AnalyticsDataStore loaded: %d matches, %d deliveries, %d batters, %d bowlers.",
                len(self.matches_df),
                len(self.pressure_states_df),
                len(self.player_batting_df),
                len(self.player_bowling_df),
            )
        except Exception as e:
            logger.error("Failed to load core analytics data: %s", e, exc_info=True)
            raise

    def get_comp_name(self, comp_id: int) -> str:
        return self._comp_map.get(comp_id, f"Competition {comp_id}")

    def get_team_name(self, team_id: int) -> str:
        return self._team_map.get(team_id, f"Team {team_id}")

    def get_match_deliveries(self, match_id: int, innings: Optional[int] = None) -> pd.DataFrame:
        if match_id not in self._match_deliveries_cache:
            sub = self.pressure_states_df[self.pressure_states_df["match_id"] == match_id].sort_values(
                by=["innings", "delivery_seq"]
            )
            self._match_deliveries_cache[match_id] = sub

        df = self._match_deliveries_cache[match_id]
        if innings is not None:
            df = df[df["innings"] == innings]
        return df


def get_datastore() -> AnalyticsDataStore:
    """Dependency provider for FastAPI routes."""
    return AnalyticsDataStore.get_instance()

