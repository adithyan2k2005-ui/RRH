import pandas as pd
from pathlib import Path

REPO_ROOT = Path("c:/Users/Adithyan R/Documents/RR/superr-selector-analytics")
DATA_DIR = REPO_ROOT / "data" / "processed"
map_df = pd.read_parquet(DATA_DIR / "competition_team_player_mapping.parquet")
bat_df = pd.read_parquet(DATA_DIR / "player_batting_metrics.parquet")
bowl_df = pd.read_parquet(DATA_DIR / "player_bowling_metrics.parquet")
top_bat = pd.read_csv(REPO_ROOT / "outputs" / "top_10_batters.csv")
top_bowl = pd.read_csv(REPO_ROOT / "outputs" / "top_10_bowlers.csv")

print("=== TOP 10 BATTERS FROM PHASE 5 & MAPPINGS ===")
for idx, r in top_bat.iterrows():
    p_id = int(r["player_id"])
    names = map_df[map_df["player_id"] == p_id]["player_name"].unique()
    match_b = bat_df[bat_df["striker_id"] == p_id]
    b_score = match_b.iloc[0]["reliability_score"] if len(match_b) > 0 else None
    b_name = match_b.iloc[0]["player_name"] if len(match_b) > 0 else None
    print(f"Rank {int(r['rank'])}: ID={p_id} | CSV='{r['player_name']}' | Mapped={list(names)} | MetricsScore={b_score:.4f} | MetricsName='{b_name}'")

print("\n=== TOP 10 BOWLERS FROM PHASE 5 & MAPPINGS ===")
for idx, r in top_bowl.iterrows():
    p_id = int(r["player_id"])
    names = map_df[map_df["player_id"] == p_id]["player_name"].unique()
    match_bw = bowl_df[bowl_df["bowler_id"] == p_id]
    bw_score = match_bw.iloc[0]["reliability_score"] if len(match_bw) > 0 else None
    bw_name = match_bw.iloc[0]["player_name"] if len(match_bw) > 0 else None
    print(f"Rank {int(r['rank'])}: ID={p_id} | CSV='{r['player_name']}' | Mapped={list(names)} | MetricsScore={bw_score:.4f} | MetricsName='{bw_name}'")

print("\n=== ACTUAL RANKS OF COMMONLY CONFUSED PLAYERS ===")
bat_all = pd.read_csv(REPO_ROOT / "outputs" / "full_batting_rankings.csv")
bowl_all = pd.read_csv(REPO_ROOT / "outputs" / "full_bowling_rankings.csv")

for name in ["Pooran", "Klaasen", "Stubbs", "Bumrah", "Narine", "Rashid"]:
    b_match = bat_all[bat_all["player_name"].str.contains(name, case=False, na=False)]
    for _, r in b_match.iterrows():
        print(f"Batter: {r['player_name']} (ID: {r['player_id']}) -> Rank: {r['rank']}, Score: {r['reliability_score']:.2f}")
    bw_match = bowl_all[bowl_all["player_name"].str.contains(name, case=False, na=False)]
    for _, r in bw_match.iterrows():
        print(f"Bowler: {r['player_name']} (ID: {r['player_id']}) -> Rank: {r['rank']}, Score: {r['reliability_score']:.2f}")
