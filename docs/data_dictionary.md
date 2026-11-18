# SupeRR Selector Season 2 — Comprehensive Data Dictionary

This document provides the authoritative schema documentation and cricket semantic dictionary for all six datasets provided in the SupeRR Selector Season 2 data pack.

All definitions clearly distinguish **confirmed facts** (verified directly through empirical validation) from **inferred meanings** and **known limitations**.

---

## 1. `competitions.csv`
- **Description**: Master registry of competitions and tournaments spanning 2022 to 2026.
- **Total Records**: 141 rows, 4 columns.
- **Primary Key**: `comp_id` (Confirmed unique: 141 / 141).

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Unique integer identifier for the competition. | Integer range [1331, 3816] | Primary key referenced by `teams`, `matches`, `competition_team_player_mapping` | None. |
| `comp_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Full official title of the tournament or series. | Text (e.g., "IPL 2024", "ICC Men's T20 World Cup 2024") | Informational | None. |
| `match_format` | `string` | 0 (0.0%) | **Confirmed Fact**: Format classification of the tournament. | `'T20I'` (134 comps), `'T20'` (7 comps) | Used for format-based filtering and normalization | All 7 `'T20'` entries represent franchise or emerging T20 tournaments (IPL 2022-2026, Emerging Teams Asia Cup, Rising Stars). |
| `season` | `string` | 0 (0.0%) | **Confirmed Fact**: Cricket season year or split-year. | `'2022'`, `'2023'`, `'2024'`, `'2025'`, `'2026'`, `'2022/23'`, `'2023/24'`, `'2024/25'` | Temporal grouping | Stored as string to accommodate split seasons (e.g. 2022/23). |

---

## 2. `teams.csv`
- **Description**: Mapping of participating teams within each competition.
- **Total Records**: 353 rows, 3 columns.
- **Primary Key**: Composite `(comp_id, team_id)` (Confirmed unique: 353 / 353).

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Foreign key referencing competition. | Integer | FK -> `competitions.comp_id` | None. |
| `team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Unique identifier for the team. | 38 unique team IDs | FK referenced by `matches`, `playing_eleven`, `competition_team_player_mapping` | `team_id` is NOT unique alone because teams compete across multiple competitions. |
| `team_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Official name of the cricket team. | Text (e.g., "India", "Rajasthan Royals", "England") | Informational | Team name strings are consistent across competitions for each `team_id`. |

---

## 3. `matches.csv`
- **Description**: Match-level fixtures, conditions, venues, captains, and outcomes.
- **Total Records**: 883 rows, 22 columns.
- **Primary Key**: `match_id` (Confirmed unique: 883 / 883).

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Unique integer identifier for each match. | Integer | Primary key referenced by `ball_by_ball`, `playing_eleven` | None. |
| `comp_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Competition ID. | Integer | FK -> `competitions.comp_id` | 100% referential integrity verified. |
| `match_number` | `string` | 0 (0.0%) | **Confirmed Fact**: Match sequence within tournament. | Strings e.g. "1", "12", "Final", "3rd Match" | Informational | Mixed alphanumeric strings. |
| `match_date` | `string` | 0 (0.0%) | **Confirmed Fact**: Match date in ISO-8601 (`YYYY-MM-DD`). | 2022-01-22 to 2026-05-31 | Temporal ordering | Date of fixture commencement. |
| `stage` | `string` | 0 (0.0%) | **Confirmed Fact**: Tournament stage. | `'League'`, `'Super 8'`, `'Semi Final'`, `'Final'`, etc. | Match context indicator | Useful for high-stakes context filtering. |
| `venue_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Venue identifier. | Integer | Venue grouping | None. |
| `venue_country`| `string` | 0 (0.0%) | **Confirmed Fact**: Host country name. | Text (e.g., "India", "West Indies", "Australia") | Geographic context | None. |
| `home_team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team ID designated as home team. | Integer | FK -> `teams.team_id` | 100% integrity verified. |
| `home_team` | `string` | 0 (0.0%) | **Confirmed Fact**: Name of home team. | Text | Matches `teams.team_name` | None. |
| `away_team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team ID designated as away team. | Integer | FK -> `teams.team_id` | 100% integrity verified. |
| `away_team` | `string` | 0 (0.0%) | **Confirmed Fact**: Name of away team. | Text | Matches `teams.team_name` | None. |
| `home_team_captain_id` | `Int64` (nullable) | 44 (4.98%) | **Confirmed Fact**: Player ID of home captain. | Integer or null | FK -> `player_id` | Null in 44 abandoned/rain fixtures without toss. |
| `away_team_captain_id` | `Int64` (nullable) | 45 (5.10%) | **Confirmed Fact**: Player ID of away captain. | Integer or null | FK -> `player_id` | Null in 45 abandoned/rain fixtures without toss. |
| `toss_win_team_id` | `Int64` (nullable) | 15 (1.70%) | **Confirmed Fact**: Team ID winning toss. | Integer or null | FK -> `teams.team_id` | Null in 15 abandoned fixtures where toss did not take place. |
| `toss_opted` | `string` | 15 (1.70%) | **Confirmed Fact**: Decision made by toss winner. | `'Batting'`, `'Fielding'`, or null | Match context | Null when toss was abandoned. |
| `man_of_the_match` | `Int64` | 0 (0.0%) | **Confirmed Fact**: Player ID awarded Player of the Match. | Integer player ID, or `0` | FK -> `player_id` (when > 0) | `0` is used as a sentinel value when no award was made (119 matches). |
| `first_inn_revised_overs` | `Float64` (nullable) | 858 (97.17%)| **Confirmed Fact**: Revised overs allocated for 1st innings. | Float (e.g. 5.0, 10.0, 15.0) | Match context / DLS indicator | Null for all standard 20-over uninterrupted matches. |
| `second_inn_revised_overs` | `Float64` (nullable) | 858 (97.17%)| **Confirmed Fact**: Revised overs allocated for 2nd innings. | Float | Match context / DLS indicator | Null for standard uninterrupted matches. |
| `revised_target` | `Float64` (nullable) | 860 (97.40%)| **Confirmed Fact**: Target runs set under DLS method. | Float (e.g. 48.0, 142.0) | Chasing context indicator | Null for standard matches. Essential for calculating revised required run rates under pressure. |
| `knock_out` | `int64` | 0 (0.0%) | **Confirmed Fact**: Binary indicator for elimination fixtures. | `0` (852 matches), `1` (31 matches) | Context / stakes indicator | 1 indicates semi-finals, finals, qualifiers, and eliminators. |
| `win_team_id` | `Int64` (nullable) | 41 (4.64%) | **Confirmed Fact**: Team ID of the winner. | Integer or null | FK -> `teams.team_id` | Null in 41 matches (19 Abandoned, 21 No Result, 1 Match Tied without super over). |
| `result` | `string` | 0 (0.0%) | **Confirmed Fact**: Textual summary of the match result. | Strings detailing margin of victory, DLS, Super Overs, or Abandonment | Match outcome | Key values include "Match Abandoned" (19), "No Result" (21), "DLS method" (19), "Super Over" (10). |

---

## 4. `ball_by_ball.csv`
- **Description**: Detailed delivery-level match records.
- **Total Records**: 200,999 rows, 33 columns.
- **Primary Key**: Composite `(match_id, innings, overid, over_ball_num)` (Confirmed strictly unique: 200,999 / 200,999).

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Match identifier. | Integer | FK -> `matches.match_id` | 100% integrity verified. |
| `innings` | `int64` | 0 (0.0%) | **Confirmed Fact**: Innings number. | `1`, `2`, `3`, `4` | Innings sequence | Innings 3 and 4 represent Super Overs. |
| `overid` | `int64` | 0 (0.0%) | **Confirmed Fact**: Over number (1-indexed). | `1` through `20` | Delivery sequencing | Over 1 is the first over. Not 0-indexed. |
| `over_ball_num` | `int64` | 0 (0.0%) | **Confirmed Fact**: Delivery sequence within over. | `1` through `13` | Ball sequencing | Increments on EVERY delivery bowled, including wides and no-balls. |
| `innings_ball_num` | `int64` | 0 (0.0%) | **Confirmed Fact**: Delivery sequence within innings. | `1` through `142` | Total delivery timeline | Increments on all bowled balls including illegal deliveries. |
| `batting_team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team currently batting. | Integer | FK -> `teams.team_id` | None. |
| `bowling_team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team currently bowling. | Integer | FK -> `teams.team_id` | None. |
| `striker_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Player facing the delivery. | Integer | FK -> `player_id` | 100% integrity verified in player mapping. |
| `striker_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Striker's registered name. | Text | Informational | Do not join on name; multiple IDs share certain names. |
| `non_striker_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Player at the non-striker's end. | Integer | FK -> `player_id` | 100% integrity verified. |
| `non_striker_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Non-striker's registered name. | Text | Informational | None. |
| `bowler_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Player bowling the delivery. | Integer | FK -> `player_id` | 100% integrity verified. |
| `bowler_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Bowler's registered name. | Text | Informational | None. |
| `batting_type` | `string` | 0 (0.0%) | **Confirmed Fact**: Batting stance/handedness. | `'RHB'` (131,006), `'LHB'` (69,993) | Batter style | None. |
| `bowling_type` | `string` | 0 (0.0%) | **Confirmed Fact**: Bowling action style. | Text (e.g., 'Right-arm fast-medium') | Bowler style | None. |
| `batting_order` | `int64` | 0 (0.0%) | **Confirmed Fact**: Striker's position in batting line-up. | `1` through `11` | Batting role | None. |
| `runs` | `int64` | 0 (0.0%) | **Confirmed Fact**: Batter runs scored off the bat. | `0, 1, 2, 3, 4, 5, 6` | Batter performance metric | Strictly batter runs. Always 0 on wides, byes, and penalties. |
| `is_four` | `bool` | 0 (0.0%) | **Confirmed Fact**: Boundary 4 hit by batter. | `True`, `False` | Performance metric | Strictly boundaries off the bat. |
| `is_six` | `bool` | 0 (0.0%) | **Confirmed Fact**: Boundary 6 hit by batter. | `True`, `False` | Performance metric | Strictly sixes off the bat. |
| `is_wicket` | `bool` | 0 (0.0%) | **Confirmed Fact**: Whether a wicket fell on the delivery. | `True` (10,881), `False` (190,118) | Dismissal indicator | True for all dismissals (bowler and non-bowler). False for retired hurt. |
| `dismissal_type_id` | `Int64` (nullable) | 190,118 (94.59%) | **Confirmed Fact**: Numeric code for dismissal. | Integer | Dismissal category | Populated exactly when `is_wicket == True`. |
| `dismissal_type` | `string` (nullable) | 190,118 (94.59%) | **Confirmed Fact**: Mode of dismissal. | `'Caught'`, `'Bowled'`, `'LBW'`, `'RunOut'`, `'Stump'`, `'Hit Wicket'`, `'Retire Out'`, `'Obstructing the field'` | Dismissal category | Bowler credited: Caught, Bowled, LBW, Stump, Hit Wicket. |
| `dismissed_player_id` | `Int64` (nullable) | 190,107 (94.58%) | **Confirmed Fact**: ID of dismissed batter or retiring batter. | Integer or null | FK -> `player_id` | Contains non-striker ID on 275 occasions (mostly runouts). Populated in 12 retired hurt rows where is_wicket=False. |
| `extras_type` | `string` (nullable) | 189,167 (94.11%) | **Confirmed Fact**: Category of extras on the delivery. | `'wide'` (7,714), `'legbyes'` (2,748), `'Overstep'` (576), `'byes'` (529), `'other'` (264), `'Penalty'` (1) | Extra category | Null for normal legal deliveries. |
| `extras1_runs` | `int64` | 0 (0.0%) | **Confirmed Fact**: Primary extra runs awarded on ball. | Integer [0, 5] | Extras calculation | For wide: total wide runs (1..5). For Overstep/other: 1 penalty run. For byes/legbyes: bye runs. |
| `extras_2_runs` | `int64` | 0 (0.0%) | **Confirmed Fact**: Secondary extra runs on no-balls. | Integer (`0`: 200,963, `1`: 20, `4`: 16) | Extras calculation | Represents byes/legbyes scored during a no-ball. |
| `pace_or_spin` | `string` | 0 (0.0%) | **Confirmed Fact**: Classification of bowling speed type. | `'Pace'` (123,886), `'Spin'` (77,113) | Match context | None. |
| `bowl_speed` | `float64` | 0 (0.0%) | **Inferred**: Recorded bowling speed in km/h. | Float [-1.0, 1456.1] | Bowler speed tracking | **Severe Data Quality Anomaly**: 77,861 zeros, 1 value of -1.0, and 20 outliers > 165 km/h (up to 1456.1). Do not use without cleaning. |
| `stroke` | `string` (nullable) | 6,158 (3.06%) | **Confirmed Fact**: Batting stroke description. | Strings (e.g. 'Pull shot', 'Cover Drive', 'Worked') | Batting analysis | Missing in 6,158 balls (e.g. leaves, wides, missed swings). |
| `delivery_style`| `string` (nullable) | 391 (0.19%) | **Confirmed Fact**: Pitch variation or delivery style. | Strings (e.g. 'Seamed In', 'Orthodox', 'Googly') | Bowling analysis | Minor missing values. |
| `over_or_around`| `string` (nullable) | 407 (0.20%) | **Confirmed Fact**: Bowler approach angle to the wicket. | `'Over'` (154,670), `'Around'` (45,922), null (407) | Bowling context | None. |
| `on_or_off` | `string` | 0 (0.0%) | **Confirmed Fact**: Ball pitch line direction. | `'Off-side'` (104,875), `'On-side'` (96,124) | Pitch location | None. |
| `delivery_ist_time` | `string` | 0 (0.0%) | **Confirmed Fact**: Timestamp string for delivery. | Format `YYYY-MM-DD HH:MM:SS UTC` | Timestamp | Suffix states 'UTC' despite column name stating 'IST'. 42 rows have default '00:00:00 UTC'. |

---

## 5. `competition_team_player_mapping.csv`
- **Description**: Canonical registry linking players to teams and competitions.
- **Total Records**: 6,413 rows, 6 columns.
- **Primary Key**: Composite `(comp_id, team_id, player_id)` (Confirmed unique: 6,413 / 6,413).

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Competition ID. | Integer | FK -> `competitions.comp_id` | None. |
| `comp_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Competition name. | Text | Matches `competitions.comp_name` | None. |
| `team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team ID. | Integer | FK -> `teams.team_id` | None. |
| `team_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Team name. | Text | Matches `teams.team_name` | None. |
| `player_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Unique canonical player identifier. | 1,217 unique IDs | Authoritative player identifier | Every player ID maps strictly to exactly one player name. |
| `player_name` | `string` | 0 (0.0%) | **Confirmed Fact**: Registered player name. | Text | Informational | Exactly 7 player names are shared by multiple distinct player IDs. |

---

## 6. `playing_eleven.csv`
- **Description**: Match-level playing XIs, designations, and substitute/impact statuses.
- **Total Records**: 28,381 rows, 9 columns.
- **Primary Key**: Composite `(match_id, team_id, player_id)` with duplicate exceptions for Super Overs.

| Column Name | Inferred / Standard Dtype | Missing Values | Confirmed / Inferred Meaning | Important Allowed Values | Relationships | Limitations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Match identifier. | Integer | FK -> `matches.match_id` | 100% integrity verified. |
| `team_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Team identifier. | Integer | FK -> `teams.team_id` | None. |
| `player_id` | `int64` | 0 (0.0%) | **Confirmed Fact**: Player identifier. | Integer | FK -> `competition_team_player_mapping.player_id` | None. |
| `batting_order` | `Float64` (nullable) | 8,678 (30.58%) | **Confirmed Fact**: Designated batting position. | `1.0` through `11.0`, or null | Match lineup | Null for squad members who did not take the field (`is_played == False`). |
| `is_played` | `bool` | 0 (0.0%) | **Confirmed Fact**: Whether the player participated in the match. | `True` (19,714), `False` (8,667) | Participation flag | False indicates bench squad members listed in the match card. |
| `is_captain` | `boolean` (nullable) | 8,667 (30.54%) | **Confirmed Fact**: Team captain designation. | `True` (1,683), `False` (18,031), null | Role | Null when `is_played == False`. |
| `is_wk` | `boolean` (nullable) | 8,667 (30.54%) | **Confirmed Fact**: Designated wicketkeeper. | `True` (1,675), `False` (18,039), null | Role | Null when `is_played == False`. |
| `is_impact` | `int64` | 0 (0.0%) | **Confirmed Fact**: IPL Impact Player brought onto the field. | `0` (27,823), `1` (558) | IPL rule indicator | 1 indicates player entered match as tactical substitute. |
| `is_impact_off` | `int64` | 0 (0.0%) | **Confirmed Fact**: IPL Impact Player subbed off the field. | `0` (27,823), `1` (558) | IPL rule indicator | 1 indicates player was substituted out under impact rule. |

