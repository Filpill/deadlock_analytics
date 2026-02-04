# Minimap Replay

Animated player-position replay chart on the `/match-analysis` page. Shows all 12 players moving across the minimap over match time, with objective markers that fade when destroyed.

**Last Updated**: 2026-02-04

---

## Data Sources

| Source | Endpoint | What it provides |
|--------|----------|-----------------|
| Player positions | `match_info.match_paths` (match metadata) | Per-second encoded X/Y positions + health for all 12 players |
| Objective positions | `objective_positions` (`/v1/map`) | Relative (0–1) positions of each objective on the minimap |
| Objective events | `match_info.objectives` (match metadata) | Destruction times per objective |
| Hero metadata | `/v2/heroes` | Hero names and icon image URLs |

---

## Player Position Decoding

Positions are encoded as integers within a per-player bounding box.

```
game_x = x_min + (x_pos / x_resolution) * (x_max - x_min)
game_y = y_min + (y_pos / y_resolution) * (y_max - y_min)
```

- `x_resolution` / `y_resolution`: 16383 (shared across all players)
- `x_min`, `x_max`, `y_min`, `y_max`: per-player bounding box
- Decoded coordinates map directly to chart axes ([-10000, 10000])
- Players may have slightly different path lengths — index is clamped to `min(t, len-1)`
- Downsampled to every 3 seconds (~700 frames for a 35-min match)

---

## Objective Coordinate Calibration

The map API's `left_relative` / `top_relative` values are NOT 1:1 with minimap pixels. They require asymmetric scaling to align with the player coordinate system, calibrated against actual match_paths positions on the lanes.

```
game_x = (left_relative - 0.45) * 29500
game_y = (0.46      - top_relative) * 21600
         ^cx                          ^cy
```

| Parameter | Value | Derivation |
|-----------|-------|------------|
| `cx` | 0.45 | Average `left_relative` of all symmetric objective pairs |
| `cy` | 0.46 | Average `top_relative` of all symmetric objective pairs |
| `scale_x` | 29500 | Calibrated: player on right lane at game_x ≈ 6950 corresponds to `lr=0.69` |
| `scale_y` | 21600 | Calibrated: player spawn (base) at game_y ≈ -10174 corresponds to `tr=0.93` |

### Objective ID → Position Key Mapping

| `team_objective_id` | Position key suffix | Shape |
|----------------------|---------------------|-------|
| 1 | `tier1_1` | Circle |
| 3 | `tier1_3` | Circle |
| 4 | `tier1_4` | Circle |
| 5 | `tier2_1` | Diamond |
| 7 | `tier2_3` | Diamond |
| 8 | `tier2_4` | Diamond |
| 10 | `titan` | Circle |
| 11 | `core` | Circle |

Position key is constructed as `team{0|1}_{suffix}`.

---

## Visual Design

### Team Colors

| Team | Color | Hex | Name |
|------|-------|-----|------|
| 0 | Blue | `#3b82f6` | Archmother |
| 1 | Orange | `#f97316` | Hidden King |

### Player Markers

Each player is rendered as three stacked `layout.images` entries (all `layer='above'`):

1. **Hero icon** — resolved from `df_heroes` using priority chain: `icon_image_small` → `icon_hero_card` → `minimap_image`. Size: 800 game units.
2. **Team hue overlay** — semi-transparent SVG circle (`rgba` 0.3 alpha) rendered as a base64 data URI, same size/position as the icon.
3. **Trace dot** — a 12px `go.Scatter` marker underneath the icons (used for hover tooltip).

Image anchor is top-left, so centering requires: `img_x = player_x - size/2`, `img_y = player_y + size/2`.

### Objective Markers

| Type | Shape | SVG element | Size | Stroke |
|------|-------|-------------|------|--------|
| Tier1 / Titan / Core | Circle | `<circle r="46">` | 600 | `#5a6a7a`, width 7 |
| Tier2 | Diamond | `<polygon>` (rotated square) | 1050 | `#5a6a7a`, width 7 |

Both are white-filled with the stroke providing contrast against the minimap.

### Opacity States

| Element | Alive / Visible | Dead / Destroyed |
|---------|-----------------|------------------|
| Player icons + overlays | 1.0 | 0.15 |
| Objective markers | 0.85 | 0.15 |

Player opacity is driven by `health[]`: 0 = dead (0.15), >0 = alive (1.0). Objective opacity flips at `destroyed_time_s`.

### Legend

Plotly's built-in legend cannot render images, so a custom HTML legend is built client-side:

- Populated from `charts.match_replay_legend` — a JSON list of `{hero_name, hero_icon_url, team}` per player.
- Two columns (one per team), each entry: circular hero icon with an absolute-positioned semi-transparent team-color overlay, plus the hero name.
- Positioned as a flex sibling to the right of the chart container.

---

## Animation Architecture

### layout.images Order (fixed across all frames)

| Index | Content |
|-------|---------|
| 0 | Minimap background (`layer='below'`) |
| 1–12 | Hero icons (`layer='above'`) |
| 13–24 | Team hue overlays (`layer='above'`) |
| 25+ | Objective markers (`layer='above'`) |

### Per-Frame Updates

Each `go.Frame` contains:

- **`data`** — 12 `go.Scatter` updates: new `x`, `y`, and `marker.opacity` per player.
- **`layout.images`** — element-wise merge array:
  - `[0]` = `{}` (minimap, no change)
  - `[1–12]` = icon `x`, `y`, `opacity`
  - `[13–24]` = overlay `x`, `y`, `opacity` (mirrors icons)
  - `[25+]` = objective `opacity` only (positions are static)

Frame names are formatted as `M:SS` for the slider labels.

### Play / Pause

Plotly's `updatemenus` buttons are not used. A single custom HTML toggle button sits over the slider:

```javascript
// Play
Plotly.animate('matchReplayChart', null, {
    frame: {duration: 100, redraw: true}, fromcurrent: true, transition: {duration: 0}
});

// Pause
Plotly.animate('matchReplayChart', [null], {
    frame: {duration: 0, redraw: false}, mode: 'immediate', transition: {duration: 0}
});
```

The `plotly_sliderchange` event is intentionally not listened to — it fires on every animation frame tick, not only on manual scrub, which would immediately reset the playing state.

---

## Files

| File | What changed |
|------|--------------|
| `app.py` | `create_match_visualizations()`: match_paths decoding, objective parsing + calibration, figure construction, frame generation. Also added `"map": "/v1/map"` to `get_match_api_connection()`. |
| `templates/match.html` | Chart container (flex wrapper + play/pause button + legend div), Plotly render + `addFrames`, legend population IIFE, play/pause toggle IIFE. |

---

**Generated from**: branch `dev/matches`
