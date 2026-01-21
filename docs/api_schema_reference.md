# Deadlock API Schema Reference

This document provides detailed schema information for all Deadlock API endpoints used in the analytics application.

**Generated**: 2026-01-20
**Sample Player ID**: 199540209

---

## Table of Contents

1. [Heroes Endpoint](#1-heroes-endpoint)
2. [Match History Endpoint](#2-match-history-endpoint)
3. [Player Stats Endpoint](#3-player-stats-endpoint)
4. [Player Performance Curve Endpoint](#4-player-performance-curve-endpoint)
5. [Kill/Death Stats Endpoint](#5-killdeath-stats-endpoint)
6. [Hero Stats Endpoint](#6-hero-stats-endpoint)
7. [Item Stats Endpoint](#7-item-stats-endpoint)

---

## 1. Heroes Endpoint

**URL**: `/v2/heroes`
**API**: assets-api
**Type**: List
**Records**: 53 heroes

### Key Columns (261 total)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | int64 | Unique hero identifier | 1 |
| `class_name` | object | Internal hero class name | "hero_inferno" |
| `name` | object | Display name | "Infernus" |
| `player_selectable` | bool | Can be selected by players | true |
| `complexity` | int64 | Hero difficulty (1-3) | 1 |
| `hero_type` | object | Role type | "marksman" |
| `description.lore` | object | Hero backstory | "Like most teenagers..." |
| `description.role` | object | Gameplay role | "Lights up enemies..." |
| `description.playstyle` | object | How to play | "Infernus has many ways..." |
| `images.icon_hero_card` | object | Hero card image URL | "https://..." |
| `starting_stats.max_health.value` | int64 | Base health | 800 |
| `starting_stats.max_move_speed.value` | float64 | Base movement speed | 6.7 |

### Usage Notes
- Use `id` to join with match history's `hero_id`
- Images are available in both PNG and WebP formats
- Starting stats nested under `starting_stats.*`

---

## 2. Match History Endpoint

**URL**: `/v1/players/{player_id}/match-history?only_stored_history=false`
**API**: data-api
**Type**: List
**Records**: Varies per player (157 in sample)

### Columns (21 total)

| Column | Type | Non-Null | Description | Example |
|--------|------|----------|-------------|---------|
| `account_id` | int64 | 100% | Player's account ID | 199540209 |
| `match_id` | int64 | 100% | Unique match identifier | 51236066 |
| `hero_id` | int64 | 100% | Hero played (join with heroes.id) | 63 |
| `hero_level` | int64 | 100% | Hero level reached in match | 30 |
| `start_time` | int64 | 100% | Match start timestamp (Unix) | 1768929026 |
| `game_mode` | int64 | 100% | Game mode identifier | 1 |
| `match_mode` | int64 | 100% | Match type | 1 |
| `player_team` | int64 | 100% | Player's team (0 or 1) | 1 |
| `player_kills` | int64 | 100% | Kills | 15 |
| `player_deaths` | int64 | 100% | Deaths | 9 |
| `player_assists` | int64 | 100% | Assists | 7 |
| `denies` | int64 | 100% | Creep denies | 25 |
| `net_worth` | int64 | 100% | Total gold earned | 39454 |
| `last_hits` | int64 | 100% | Creep last hits | 160 |
| `team_abandoned` | object | 61% | Which team abandoned | null |
| `abandoned_time_s` | object | 0% | When abandon occurred | null |
| `match_duration_s` | int64 | 100% | Match length in seconds | 1817 |
| `match_result` | int64 | 100% | Win (1) or Loss (0) | 0 |
| `objectives_mask_team0` | int64 | 100% | Team 0 objectives bitmask | 65221 |
| `objectives_mask_team1` | int64 | 100% | Team 1 objectives bitmask | 8260 |
| `username` | object | 100% | Player username | "api" |

### Usage Notes
- **Win/Loss determination**: Compare `player_team` with `match_result`
  - Win: `player_team == match_result`
  - Loss: `player_team != match_result`
- Convert `start_time` to datetime: `pd.to_datetime(start_time, unit='s')`
- Join with heroes table on `hero_id = heroes.id` for hero names

### Statistics
- Average match duration: ~25-30 minutes
- Typical kills: 0-30 per match
- Typical deaths: 0-20 per match

---

## 3. Player Stats Endpoint

**URL**: `/v1/analytics/player-stats/metrics?account_ids={player_id}`
**API**: data-api
**Type**: Dictionary (flattens to DataFrame with 286 columns)

### Structure
Each stat contains 11 fields:
- `avg` - Average value
- `std` - Standard deviation
- `percentile1`, `percentile5`, `percentile10`, `percentile25`, `percentile50`, `percentile75`, `percentile90`, `percentile95`, `percentile99`

### Key Stats Available

| Stat Name | Description |
|-----------|-------------|
| `kills` | Kill statistics |
| `deaths` | Death statistics |
| `assists` | Assist statistics |
| `kd` | Kill/death ratio |
| `kda` | KDA ratio |
| `net_worth` | Gold earned |
| `net_worth_per_min` | Gold per minute |
| `last_hits` | Creep last hits |
| `denies` | Creep denies |
| `player_damage` | Damage to players |
| `player_damage_per_min` | Player damage per minute |
| `player_damage_taken_per_min` | Damage taken per minute |
| `player_healing` | Healing done to players |
| `healing` | Total healing |
| `boss_damage` | Damage to bosses |
| `neutral_damage` | Damage to neutral creeps |
| `accuracy` | Shot accuracy percentage |
| `crit_shot_rate` | Critical hit rate |

### Usage Notes
- Access specific stats: `df['kills.avg']`, `df['kd.percentile50']`
- Use `.avg` for typical performance metrics
- Use percentiles for player ranking/comparison

---

## 4. Player Performance Curve Endpoint

**URL**: `/v1/analytics/player-performance-curve?account_ids={player_id}&resolution=0`
**API**: data-api
**Type**: List
**Records**: 12 time intervals

### Columns (9 total)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `game_time` | int64 | Time point in seconds | 180 |
| `net_worth_avg` | float64 | Average net worth at this time | 2045.67 |
| `net_worth_std` | float64 | Net worth std deviation | 302.67 |
| `kills_avg` | float64 | Average kills at this time | 0.2 |
| `kills_std` | float64 | Kills std deviation | 0.4 |
| `deaths_avg` | float64 | Average deaths at this time | 0.13 |
| `deaths_std` | float64 | Deaths std deviation | 0.34 |
| `assists_avg` | float64 | Average assists at this time | 0.33 |
| `assists_std` | float64 | Assists std deviation | 0.70 |

### Usage Notes
- Time intervals: 180s, 360s, ..., up to 3000s (50 minutes)
- Perfect for line charts showing progression over game time
- Standard deviations show consistency of performance

---

## 5. Kill/Death Stats Endpoint

**URL**: `/v1/analytics/kill-death-stats?account_ids={player_id}`
**API**: data-api
**Type**: List
**Records**: Varies (439 in sample)

### Columns (5 total)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `position_x` | int64 | X coordinate on map | 7500 |
| `position_y` | int64 | Y coordinate on map | 1400 |
| `killer_team` | int64 | Team that got the kill (0 or 1) | 0 |
| `deaths` | int64 | Number of deaths at this location | 1 |
| `kills` | int64 | Number of kills at this location | 0 |

### Usage Notes
- **Heatmap data** - shows where kills/deaths occurred on the map
- Coordinates range: approximately -9000 to 9000
- Can create separate heatmaps for kills vs deaths
- Filter by `killer_team` for team-specific analysis

---

## 6. Hero Stats Endpoint

**URL**: `/v1/analytics/hero-stats?account_ids={player_id}&bucket=no_bucket`
**API**: data-api
**Type**: List
**Records**: One per hero played

### Columns (21 total)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `hero_id` | int64 | Hero identifier (join with heroes) | 3 |
| `bucket` | int64 | Bucket type (0 for no_bucket) | 0 |
| `wins` | int64 | Wins with this hero | 0 |
| `losses` | int64 | Losses with this hero | 2 |
| `matches` | int64 | Total matches with hero | 2 |
| `matches_per_bucket` | int64 | Matches in this bucket | 2 |
| `players` | int64 | Number of players (1 for single player query) | 1 |
| `total_kills` | int64 | Total kills across all matches | 7 |
| `total_deaths` | int64 | Total deaths across all matches | 15 |
| `total_assists` | int64 | Total assists across all matches | 12 |
| `total_net_worth` | int64 | Total gold earned | 75848 |
| `total_last_hits` | int64 | Total last hits | 316 |
| `total_denies` | int64 | Total denies | 16 |
| `total_player_damage` | int64 | Total damage to players | 53625 |
| `total_player_damage_taken` | int64 | Total damage taken | 55903 |
| `total_boss_damage` | int64 | Total damage to bosses | 18521 |
| `total_creep_damage` | int64 | Total damage to creeps | 85314 |
| `total_neutral_damage` | int64 | Total damage to neutrals | 8728 |
| `total_max_health` | int64 | Sum of max health across matches | 5832 |
| `total_shots_hit` | int64 | Total shots that hit | 2901 |
| `total_shots_missed` | int64 | Total shots missed | 3493 |

### Usage Notes
- Join with heroes table on `hero_id = heroes.id` for hero names
- Calculate derived metrics:
  - Win rate: `wins / matches`
  - KDA: `(total_kills + total_assists) / total_deaths`
  - Accuracy: `total_shots_hit / (total_shots_hit + total_shots_missed)`
  - Average per match: `total_* / matches`

---

## 7. Item Stats Endpoint

**URL**: `/v1/analytics/item-stats?account_ids={player_id}&bucket=no_bucket`
**API**: data-api
**Type**: List
**Records**: One per item purchased

### Columns (10 total)

| Column | Type | Non-Null | Description | Example |
|--------|------|----------|-------------|---------|
| `item_id` | int64 | 100% | Unique item identifier | 84321454 |
| `bucket` | int64 | 100% | Bucket type | 0 |
| `wins` | int64 | 100% | Wins when item purchased | 12 |
| `losses` | int64 | 100% | Losses when item purchased | 16 |
| `matches` | int64 | 100% | Matches where item purchased | 28 |
| `players` | int64 | 100% | Number of players | 1 |
| `avg_buy_time_s` | float64 | 100% | Average time purchased (seconds) | 516.79 |
| `avg_sell_time_s` | float64 | 50% | Average time sold (seconds, if sold) | 2138.44 |
| `avg_buy_time_relative` | float64 | 100% | Buy time as % of match duration | 23.31 |
| `avg_sell_time_relative` | float64 | 50% | Sell time as % of match duration | 80.50 |

### Usage Notes
- Join with items table (from assets-api) on `item_id` for item names
- `avg_sell_time_s` is null if item was never sold
- Relative times help normalize across different match lengths
- Use to analyze:
  - Most purchased items
  - Win rates with specific items
  - Build timing optimization

---

## Common Patterns & Tips

### Joining DataFrames

```python
# Add hero names to match history
df_match = pd.merge(
    df_match_history,
    df_heroes[['id', 'name']],
    left_on='hero_id',
    right_on='id',
    how='left'
)

# Add hero names to hero stats
df_hero_stats = pd.merge(
    df_hero_stats,
    df_heroes[['id', 'name']],
    left_on='hero_id',
    right_on='id',
    how='left'
).rename(columns={'name': 'hero_name'})
```

### Calculating Win/Loss

```python
# From match_history
df['result'] = df.apply(
    lambda row: 'Win' if row['player_team'] == row['match_result'] else 'Loss',
    axis=1
)

# From hero_stats or item_stats
df['win_rate'] = df['wins'] / df['matches'] * 100
```

### Time Conversions

```python
# Convert Unix timestamp to datetime
df['datetime'] = pd.to_datetime(df['start_time'], unit='s')

# Convert seconds to minutes
df['duration_minutes'] = df['match_duration_s'] / 60
```

### Calculating Averages from Totals

```python
# For hero_stats
df['avg_kills_per_match'] = df['total_kills'] / df['matches']
df['avg_damage_per_match'] = df['total_player_damage'] / df['matches']
df['kda'] = (df['total_kills'] + df['total_assists']) / df['total_deaths'].replace(0, 1)
```

---

## Chart Recommendations

Based on the schemas, here are effective visualizations:

### Match History
- **Timeline**: Wins/losses over time (histogram with colors)
- **Performance trends**: Kills/deaths/assists per match over time
- **Hero distribution**: Pie chart of most played heroes

### Player Stats
- **Comparison**: Radar chart of key metrics (KDA, damage, healing)
- **Distribution**: Box plots showing percentiles

### Performance Curve
- **Line charts**: Net worth, kills, deaths progression over game time
- **Stacked area**: Show all metrics together with filled areas

### Kill/Death Stats
- **Heatmap**: 2D heatmap of map positions
- **Scatter plot**: Kill/death locations with size indicating frequency

### Hero Stats
- **Bar charts**: Wins/losses by hero (stacked)
- **Scatter plot**: Win rate vs matches played
- **Table**: Top heroes by various metrics

### Item Stats
- **Timeline**: When items are typically bought (bar chart)
- **Win correlation**: Items with highest win rates
- **Frequency**: Most purchased items

---

## API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid player_id format) |
| 404 | Player not found |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## Notes

- All numeric IDs are int64
- Timestamps are Unix epoch (seconds)
- Percentages are typically decimals (0.45 = 45%)
- Some fields may be null/NaN for incomplete data
- Data is updated periodically (not real-time)
