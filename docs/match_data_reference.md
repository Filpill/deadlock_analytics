# Match Data Reference

## Overview

This document provides a comprehensive reference for all data points available in a single Deadlock match, sourced from the match metadata endpoint. Each section includes the available data fields and suggested visualizations/tables that can be produced.

**API Endpoint**: `/v1/matches/{match_id}/metadata`
**Data Source**: `sample/sample-match.json`

---

## 1. Match Metadata

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `match_info.duration_s` | int | Total match duration in seconds |
| `match_info.match_outcome` | int | Match outcome identifier |
| `match_info.winning_team` | int | Winning team (0 or 1) |
| `match_info.start_time` | int | Unix timestamp of match start |
| `match_info.match_id` | int | Unique match identifier |
| `match_info.game_mode` | int | Game mode identifier |
| `match_info.match_mode` | int | Match mode identifier |
| `match_info.game_mode_version` | int | Game mode version number |
| `match_info.is_high_skill_range_parties` | bool | High skill range indicator |
| `match_info.low_pri_pool` | bool | Low priority pool indicator |
| `match_info.new_player_pool` | bool | New player pool indicator |
| `match_info.average_badge_team0` | int | Average rank badge for team 0 |
| `match_info.average_badge_team1` | int | Average rank badge for team 1 |
| `match_info.rewards_eligible` | bool | Match rewards eligibility |
| `match_info.not_scored` | bool | Match scoring status |
| `match_info.bot_difficulty` | int | Bot difficulty level (if applicable) |
| `match_info.team_score` | array | Team scores |

### Potential Visualizations

1. **Match Summary Card**
   - Match ID, duration, start time
   - Game mode and version
   - Winning team indicator
   - Pool indicators (new player, low priority, high skill)

2. **Team Comparison Table**
   - Average badge (rank) per team
   - Team scores
   - Win/loss outcome

3. **Match Duration Distribution** (across multiple matches)
   - Histogram of match durations
   - Average duration by game mode

---

## 2. Player Summary Data

### Available Fields (per player)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].account_id` | int | Player's Steam account ID |
| `match_info.players[].player_slot` | int | Player slot (0-11) |
| `match_info.players[].team` | int | Player's team (0 or 1) |
| `match_info.players[].hero_id` | int | Hero played |
| `match_info.players[].party` | int | Party identifier |
| `match_info.players[].assigned_lane` | int | Assigned lane |
| `match_info.players[].level` | int | Final player level |
| `match_info.players[].kills` | int | Total kills |
| `match_info.players[].deaths` | int | Total deaths |
| `match_info.players[].assists` | int | Total assists |
| `match_info.players[].net_worth` | int | Final net worth (souls) |
| `match_info.players[].last_hits` | int | Total last hits |
| `match_info.players[].denies` | int | Total denies |
| `match_info.players[].ability_points` | int | Total ability points earned |
| `match_info.players[].rewards_eligible` | bool | Player rewards eligibility |
| `match_info.players[].abandon_match_time_s` | int/null | Time abandoned (if applicable) |
| `match_info.players[].hero_data.hero_xp` | int | Hero XP earned |
| `match_info.players[].mvp_rank` | int/null | MVP rank (if applicable) |
| `match_info.players[].earned_holiday_award_2025` | int/null | Holiday award status |

### Potential Visualizations

1. **Player Scoreboard Table**
   - All players with K/D/A, net worth, last hits, denies
   - Sortable by any column
   - Color-coded by team
   - Hero icons

2. **Team Performance Comparison**
   - Side-by-side bar charts: kills, assists, net worth per team
   - Box plots: distribution of stats within each team

3. **Individual Player Card**
   - Hero portrait with player name
   - KDA breakdown
   - Economy stats (net worth, last hits, denies)
   - Final level and lane assignment

4. **Party Analysis**
   - Group players by party
   - Compare party performance vs solo players

5. **Lane Assignment Heatmap**
   - Show which lanes had the most action
   - Performance by lane

---

## 3. Player Stats (Time-Series)

### Available Fields (per timestamp)

Each player has an array of stats recorded at intervals throughout the match.

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].stats[].time_stamp_s` | int | Timestamp in seconds |
| `match_info.players[].stats[].net_worth` | int | Net worth at this time |
| `match_info.players[].stats[].level` | int | Player level |
| `match_info.players[].stats[].kills` | int | Cumulative kills |
| `match_info.players[].stats[].deaths` | int | Cumulative deaths |
| `match_info.players[].stats[].assists` | int | Cumulative assists |
| `match_info.players[].stats[].creep_kills` | int | Creep kills |
| `match_info.players[].stats[].neutral_kills` | int | Neutral creep kills |
| `match_info.players[].stats[].denies` | int | Cumulative denies |
| `match_info.players[].stats[].player_damage` | int | Damage to players |
| `match_info.players[].stats[].creep_damage` | int | Damage to creeps |
| `match_info.players[].stats[].neutral_damage` | int | Damage to neutrals |
| `match_info.players[].stats[].boss_damage` | int | Damage to bosses |
| `match_info.players[].stats[].player_healing` | int | Healing provided to players |
| `match_info.players[].stats[].self_healing` | int | Self-healing |
| `match_info.players[].stats[].teammate_healing` | int | Healing to teammates |
| `match_info.players[].stats[].player_damage_taken` | int | Damage taken |
| `match_info.players[].stats[].damage_mitigated` | int | Damage mitigated |
| `match_info.players[].stats[].damage_absorbed` | int | Damage absorbed |
| `match_info.players[].stats[].absorption_provided` | int | Absorption provided to others |
| `match_info.players[].stats[].player_barriering` | int | Barrier applied to self |
| `match_info.players[].stats[].teammate_barriering` | int | Barrier applied to teammates |
| `match_info.players[].stats[].max_health` | int | Maximum health |
| `match_info.players[].stats[].weapon_power` | int | Weapon power stat |
| `match_info.players[].stats[].tech_power` | int | Tech power stat |
| `match_info.players[].stats[].shots_hit` | int | Shots hit |
| `match_info.players[].stats[].shots_missed` | int | Shots missed |
| `match_info.players[].stats[].hero_bullets_hit` | int | Bullets hit on heroes |
| `match_info.players[].stats[].hero_bullets_hit_crit` | int | Critical hits on heroes |
| `match_info.players[].stats[].heal_prevented` | int | Healing prevented |
| `match_info.players[].stats[].heal_lost` | int | Healing lost |
| `match_info.players[].stats[].self_damage` | int | Self-inflicted damage |
| `match_info.players[].stats[].bullet_kills` | int | Kills via bullets |
| `match_info.players[].stats[].melee_kills` | int | Kills via melee |
| `match_info.players[].stats[].ability_kills` | int | Kills via abilities |
| `match_info.players[].stats[].headshot_kills` | int | Headshot kills |

#### Gold Breakdown (per timestamp)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].stats[].gold_player` | int | Gold from player kills |
| `match_info.players[].stats[].gold_player_orbs` | int | Gold from player orbs |
| `match_info.players[].stats[].gold_lane_creep_orbs` | int | Gold from lane creep orbs |
| `match_info.players[].stats[].gold_neutral_creep_orbs` | int | Gold from neutral orbs |
| `match_info.players[].stats[].gold_boss` | int | Gold from boss kills |
| `match_info.players[].stats[].gold_boss_orb` | int | Gold from boss orbs |
| `match_info.players[].stats[].gold_treasure` | int | Gold from treasure |
| `match_info.players[].stats[].gold_denied` | int | Gold denied to enemy |
| `match_info.players[].stats[].gold_death_loss` | int | Gold lost from deaths |
| `match_info.players[].stats[].gold_lane_creep` | int | Gold from lane creeps |
| `match_info.players[].stats[].gold_neutral_creep` | int | Gold from neutral creeps |

### Potential Visualizations

1. **Net Worth Over Time (Line Chart)**
   - All 12 players on one chart
   - Color-coded by team
   - Identify gold lead swings

2. **KDA Progression (Multi-Line Chart)**
   - Kills, deaths, assists over time per player
   - Compare aggressive vs defensive playstyles

3. **Economy Breakdown (Stacked Area Chart)**
   - Show sources of gold over time
   - Lane creeps vs neutral vs player kills vs objectives

4. **Damage Output Over Time**
   - Player damage, creep damage, boss damage
   - Identify teamfight timings

5. **Accuracy and Shooting Stats**
   - Shots hit vs missed percentage over time
   - Critical hit rate progression
   - Headshot kill timeline

6. **Power Scaling (Line Chart)**
   - Weapon power and tech power over time
   - Max health progression
   - Compare scaling between heroes

7. **Healing and Support Metrics**
   - Self-healing vs teammate healing
   - Barrier application over time
   - Damage mitigated trends

8. **Kill Type Breakdown (Stacked Bar Chart)**
   - Bullet kills vs melee kills vs ability kills
   - Per player or team aggregate

9. **XP and Level Curve**
   - Level progression over time
   - Compare early game vs late game leveling speed

10. **Farming Efficiency**
    - Creep kills + neutral kills over time
    - Denies compared to last hits
    - Possible creeps vs actual creep kills (farm efficiency %)

---

## 4. Death Details

### Available Fields (per death)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].death_details[].game_time_s` | int | Time of death in seconds |
| `match_info.players[].death_details[].time_to_kill_s` | float | Time taken to kill player |
| `match_info.players[].death_details[].killer_player_slot` | int | Killer's player slot |
| `match_info.players[].death_details[].death_pos` | object | Death position coordinates |
| `match_info.players[].death_details[].killer_pos` | object | Killer position coordinates |
| `match_info.players[].death_details[].death_duration_s` | int | Death duration (respawn timer) |

### Potential Visualizations

1. **Death Timeline**
   - Scatter plot: time of death (x-axis) vs player (y-axis)
   - Color by team
   - Identify teamfight windows

2. **Death Heatmap on Minimap**
   - Overlay death positions on minimap
   - Size based on frequency
   - Color by team

3. **Kill Distance Analysis**
   - Calculate distance between killer_pos and death_pos
   - Histogram of kill ranges
   - Identify long-range vs close-range killers

4. **Time to Kill Distribution**
   - Histogram of time_to_kill_s
   - Compare by hero or player
   - Identify burst damage vs sustained damage

5. **Respawn Timer Analysis**
   - Death duration over game time
   - Shows how respawn timers scale

6. **Kill Matrix Table**
   - Rows: victims, Columns: killers
   - Heat map showing who killed whom most

7. **Death Clustering**
   - Group deaths within 10-second windows
   - Identify major teamfights
   - Show casualties per teamfight

---

## 5. Items and Builds

### Available Fields (per item transaction)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].items[].game_time_s` | int | Time item was purchased |
| `match_info.players[].items[].item_id` | int | Item identifier |
| `match_info.players[].items[].upgrade_id` | int | Upgrade tier |
| `match_info.players[].items[].sold_time_s` | int | Time item was sold (if applicable) |
| `match_info.players[].items[].flags` | int | Item flags |
| `match_info.players[].items[].imbued_ability_id` | int | Imbued ability (if applicable) |

### Potential Visualizations

1. **Item Build Timeline**
   - Horizontal bar chart showing when items were purchased
   - Compare build orders between players
   - Identify core items vs situational items

2. **Item Purchase Timing Table**
   - Player vs time for key items
   - Identify early game vs late game item preferences

3. **Item Popularity Heatmap**
   - Items (rows) vs players (columns)
   - Show which items were most purchased

4. **Item Selling Analysis**
   - Track items that were sold (sold_time_s not null)
   - Time held before selling
   - Common item replacement patterns

5. **Build Path Sankey Diagram**
   - Show progression from early items to late items
   - Common upgrade paths

6. **Item Win Rate Correlation** (across multiple matches)
   - Which items correlate with winning
   - Purchase timing impact on win rate

---

## 6. Ability Usage

### Available Fields (per ability)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].ability_stats[].ability_id` | int | Ability identifier |
| `match_info.players[].ability_stats[].ability_value` | int | Ability usage/value metric |

### Potential Visualizations

1. **Ability Usage Table**
   - Player vs ability
   - Usage counts or effectiveness metrics

2. **Ability Priority Analysis**
   - Which abilities are leveled first
   - Skill build orders

3. **Ability Effectiveness**
   - Damage/value per ability
   - Compare across players using same hero

---

## 7. Pings and Communication

### Available Fields (per ping)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].pings[].ping_type` | int | Type of ping |
| `match_info.players[].pings[].ping_data` | int | Ping data/context |
| `match_info.players[].pings[].game_time_s` | int | Time ping was sent |

### Potential Visualizations

1. **Ping Timeline**
   - Scatter plot of pings over time
   - Color by ping type
   - Identify communication patterns

2. **Ping Frequency by Player**
   - Bar chart: pings per player
   - Compare communication levels

3. **Ping Type Distribution**
   - Pie chart of ping types
   - Which pings are most used

4. **Ping Density Heatmap**
   - Time windows with high ping activity
   - Correlate with teamfights or objectives

---

## 8. Accolades and Awards

### Available Fields (per accolade)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].accolades[].accolade_id` | int | Accolade identifier |
| `match_info.players[].accolades[].accolade_stat_value` | int | Stat value for accolade |
| `match_info.players[].accolades[].accolade_threshold_achieved` | int | Threshold level achieved |

### Potential Visualizations

1. **Accolades Display Cards**
   - Show earned accolades per player
   - Icons and descriptions

2. **Accolade Distribution Table**
   - Players vs accolades earned
   - Highlight standout performances

3. **Threshold Achievement Progress**
   - Show how close players were to higher tiers

---

## 9. Power-Up Buffs

### Available Fields (per buff)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.players[].power_up_buffs[].type` | str | Buff type identifier |
| `match_info.players[].power_up_buffs[].value` | int | Buff value/magnitude |
| `match_info.players[].power_up_buffs[].is_permanent` | bool | Permanent buff indicator |

### Potential Visualizations

1. **Buff Summary Table**
   - Player vs buff types
   - Permanent vs temporary buffs

2. **Buff Value Comparison**
   - Bar chart of buff values per player
   - Total buff value per team

---

## 10. Objectives

### Available Fields (per objective)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.objectives[].team_objective_id` | int | Objective identifier |
| `match_info.objectives[].team` | int | Team that destroyed objective |
| `match_info.objectives[].destroyed_time_s` | int | Time objective was destroyed |
| `match_info.objectives[].first_damage_time_s` | int | First damage timestamp |
| `match_info.objectives[].creep_damage` | int | Damage from creeps |
| `match_info.objectives[].player_damage` | int | Damage from players |
| `match_info.objectives[].player_spirit_damage` | int | Spirit damage from players |
| `match_info.objectives[].creep_damage_mitigated` | int/null | Damage mitigated from creeps |
| `match_info.objectives[].player_damage_mitigated` | int/null | Damage mitigated from players |

### Potential Visualizations

1. **Objective Timeline**
   - Vertical timeline showing when objectives fell
   - Color by team
   - Show momentum swings

2. **Objective Damage Breakdown**
   - Stacked bar: player damage vs creep damage per objective
   - Spirit damage contribution

3. **Time to Destroy Analysis**
   - Calculate (destroyed_time_s - first_damage_time_s)
   - Show which objectives were contested vs easy takes

4. **Objective Map Visualization**
   - Minimap with objective locations
   - Color by which team destroyed them
   - Annotate with timestamps

5. **Team Objective Control Table**
   - Count objectives per team
   - Total damage dealt to objectives per team

---

## 11. Match Paths (Player Movement)

### Available Fields (per player)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.match_paths.version` | int | Path data version |
| `match_info.match_paths.interval_s` | float | Sampling interval in seconds |
| `match_info.match_paths.x_resolution` | int | X-axis resolution |
| `match_info.match_paths.y_resolution` | int | Y-axis resolution |
| `match_info.match_paths.paths[].player_slot` | int | Player identifier |
| `match_info.match_paths.paths[].x_min` | float | Minimum X coordinate |
| `match_info.match_paths.paths[].y_min` | float | Minimum Y coordinate |
| `match_info.match_paths.paths[].x_max` | float | Maximum X coordinate |
| `match_info.match_paths.paths[].y_max` | float | Maximum Y coordinate |
| `match_info.match_paths.paths[].x_pos` | array | X positions over time |
| `match_info.match_paths.paths[].y_pos` | array | Y positions over time |
| `match_info.match_paths.paths[].health` | array | Health at each position |
| `match_info.match_paths.paths[].combat_type` | array | Combat status at each position |
| `match_info.match_paths.paths[].move_type` | array | Movement type at each position |

### Potential Visualizations

1. **Player Movement Heatmap**
   - Overlay all positions on minimap
   - Color intensity by time spent
   - Show where players roam most

2. **Player Path Replay**
   - Animated map showing player movement over time
   - Include health bars
   - Highlight combat vs non-combat movement

3. **Territory Control Map**
   - Show which areas of map were controlled by each team
   - Time-based territory changes

4. **Movement Speed Analysis**
   - Calculate movement speed from position deltas
   - Histogram of speeds
   - Identify rotation timings

5. **Combat Location Heatmap**
   - Filter positions where combat_type indicates combat
   - Show teamfight locations

6. **Health Tracking**
   - Line chart of health over time
   - Correlate with position to show dangerous areas

7. **Player Proximity Analysis**
   - Calculate distance between players over time
   - Identify when teams group vs split

---

## 12. Damage Matrix

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `match_info.damage_matrix.damage_dealers[].dealer_player_slot` | int | Damage dealer identifier |
| `match_info.damage_matrix.damage_dealers[].damage_sources[]` | array | Array of damage source data |
| `match_info.damage_matrix.sample_time_s` | array | Timestamps for samples |
| `match_info.damage_matrix.source_details.stat_type` | array | Stat type identifiers |
| `match_info.damage_matrix.source_details.source_name` | array | Source names (abilities, items, etc.) |

### Potential Visualizations

1. **Damage Dealt Matrix**
   - Rows: damage dealers, Columns: damage targets
   - Heatmap showing who damaged whom most

2. **Damage Source Breakdown**
   - Stacked bar chart per player
   - Show damage from abilities, items, basic attacks

3. **Damage Over Time**
   - Line chart using sample_time_s
   - Track damage contribution per player

4. **Source Type Distribution**
   - Pie chart: percentage of damage per stat_type
   - Compare by player or hero

5. **Top Damage Sources Table**
   - Ranked list of abilities/items by damage dealt
   - Filter by player or team

---

## 13. Match Pauses

### Available Fields (per pause)

| Field | Type | Description |
|-------|------|-------------|
| `match_info.match_pauses[].game_time_s` | int | Time pause occurred |
| `match_info.match_pauses[].pause_duration_s` | int | Duration of pause |
| `match_info.match_pauses[].player_slot` | int | Player who paused |

### Potential Visualizations

1. **Pause Timeline**
   - Vertical bars showing when and how long pauses occurred
   - Annotate who paused

2. **Pause Summary Table**
   - Total pauses
   - Total pause time
   - Player pause frequency

---

## 14. Team Data

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `match_info.teams[].team` | int | Team identifier (0 or 1) |
| `match_info.teams[].team_tracked_stats` | array | Team-level tracked statistics |

### Potential Visualizations

1. **Team Stats Comparison Table**
   - Side-by-side comparison of team statistics
   - Aggregate metrics from team_tracked_stats

---

## 15. Custom Stats

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `match_info.custom_user_stats[].name` | str | Custom stat name |
| `match_info.custom_user_stats[].id` | int | Custom stat identifier |
| `match_info.players[].player_tracked_stats` | array | Player-specific tracked stats |
| `match_info.match_tracked_stats` | array | Match-level tracked stats |

### Potential Visualizations

1. **Custom Stats Table**
   - Display custom statistics per player or match
   - Flexible based on available stats

---

## 16. Mid Boss Events

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `match_info.mid_boss` | array | Mid boss event data |

### Potential Visualizations

1. **Mid Boss Timeline**
   - Show when mid boss was killed
   - Which team secured it
   - Impact on match momentum

---

## Summary: Comprehensive Dashboard Ideas

### 1. **Match Replay Dashboard**
- Timeline slider to scrub through match
- Synchronized visualizations updating as time progresses:
  - Player positions on minimap
  - Net worth chart
  - KDA chart
  - Health bars
  - Objective status

### 2. **Player Performance Report**
- Hero portrait and final K/D/A
- Economy chart (gold sources over time)
- Damage charts (dealt vs taken)
- Accuracy and shooting stats
- Item build timeline
- Movement heatmap
- Deaths and kill locations

### 3. **Team Comparison Dashboard**
- Head-to-head stats
- Objective control timeline
- Gold advantage chart
- Kill timeline
- Teamfight analysis (death clustering)

### 4. **Economic Analysis**
- Gold sources breakdown per player
- Net worth over time (all players)
- Farming efficiency (creep kills vs possible creeps)
- Gold lead timeline

### 5. **Combat Analysis**
- Damage matrix visualization
- Kill type breakdown
- Teamfight detection and analysis
- Death clustering heatmap
- Time to kill distributions

### 6. **Map Control Visualization**
- Player movement heatmaps
- Death locations
- Objective locations and timing
- Territory control over time
- Combat hotspots

### 7. **Hero Performance Deep Dive**
- Ability usage and effectiveness
- Item build path analysis
- Power scaling (weapon/tech power)
- Accuracy metrics
- Kill participation rate

---

## Data Processing Notes

- **Time-series data**: Most stats are sampled at intervals, allowing for precise temporal analysis
- **Coordinate system**: Position data uses a coordinate system that maps to the game minimap
- **Player slot**: Consistent identifier (0-11) used across all player-related arrays
- **Team identifiers**: Always 0 or 1
- **Timestamps**: Generally in seconds (game time, not real time)
- **Null values**: Some fields may be null (e.g., abandon_match_time_s, mvp_rank)

---

**Last Updated**: 2026-02-03
**API Endpoint**: `/v1/matches/{match_id}/metadata`
**Data Version**: Current match metadata schema
