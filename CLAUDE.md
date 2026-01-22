# Deadlock Analytics - Project Documentation

## Project Overview

Deadlock Analytics is a comprehensive Python-based analytics platform for Deadlock game data. The project features:

- **Flask Web Application**: Interactive player analytics dashboard with real-time visualizations
- **Marimo Notebooks**: Exploratory data analysis environment
- **API Integration**: Direct integration with official Deadlock API
- **Data Visualization**: Interactive charts using Plotly for performance analysis

## Technology Stack

- **Python Version**: 3.12+
- **Package Manager**: uv (fast Python package installer and resolver)
- **Web Framework**: Flask 3.1+
- **Data Visualization**: Plotly 6.5+
- **Data Analysis**: pandas 2.3+
- **Statistical Computing**: scipy 1.14+ (distribution curves), numpy 2.0+ (numerical operations)
- **Notebooks**: marimo 0.19+
- **API Client**: deadlock-api-client (from GitHub repository)

## Project Structure

```
deadlock-analytics/
├── app.py                      # Flask web application (main entry point)
├── Dockerfile                  # Cloud Run optimized Docker image
├── .dockerignore               # Docker build exclusions
├── .gcloudignore               # Cloud Build exclusions
├── templates/                  # HTML templates for Flask
│   ├── index.html             # Landing page with player ID input (with audio)
│   └── results.html           # Analytics dashboard with charts (with audio + hero filtering)
├── static/                     # Static assets
│   ├── fonts/                 # Custom fonts
│   │   └── ForevsDemo-*.otf  # ForevsDemo font family (14 variants)
│   └── img/
│       ├── minimap.png        # Deadlock minimap image (512x512px)
│       ├── graphic_cityscape.png  # Banner image for README
│       ├── deadlock-logo-no-title-flat.png  # Deadlock logo (flat version)
│       ├── catalog_tooltip_bg_modifies_vitality.webp  # Background image
│       └── Deadlock-icon-no-title.webp      # Deadlock icon
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                # Cloud Run service configuration
│   ├── variables.tf           # Terraform variables (pre-configured)
│   ├── outputs.tf             # Service outputs (URL, name, etc.)
│   ├── .gitignore             # Terraform state exclusions
│   ├── terraform.tfvars.example  # Example variable file
│   └── README.md              # Terraform deployment guide
├── scripts/                    # Analysis scripts and notebooks
│   ├── deadlock_notebook.py  # Original marimo notebook
│   └── analyze_schema.py     # API schema analysis tool
├── docs/                       # Documentation
│   └── api_schema_reference.md # Comprehensive API schema documentation
├── __marimo__/                 # Marimo notebook cache and sessions
│   └── session/               # Session data
├── .venv/                     # Virtual environment (managed by uv)
├── .claude/                   # Claude Code configuration
├── .gitignore                 # Git ignore patterns (includes Python cache)
├── .python-version            # Python version specification (3.12)
├── pyproject.toml             # Project dependencies and metadata
├── uv.lock                    # Locked dependency versions
├── CLAUDE.md                  # This file
└── README.md                  # Project readme with live deployment link
```

## Quick Start

### 1. Setup Environment

```bash
# Ensure Python 3.12+ is installed
python --version

# Install uv (if not already installed)
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv sync
```

### 2. Run Flask Web Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Flask app
python app.py

# Open browser to http://localhost:5000
```

### 3. Use the Dashboard

1. Enter a player ID in SteamID3 format (e.g., `199540209`)
2. Click "Analyze Player Stats"
3. View interactive analytics dashboard with Steam profile, rank badge, 5 KPI tiles, top 5 heroes, and 7 visualizations

## Docker Deployment (Google Cloud Run)

**Live Application**: https://deadlock-analytics-164941517977.europe-west2.run.app

The application is deployed to Google Cloud Run in the `europe-west2` region (London).

### Production Configuration

- **Project**: deadlock-485121
- **Service**: deadlock-analytics
- **Region**: europe-west2
- **Service Account**: sa-deadlock-cloud-run@deadlock-485121.iam.gserviceaccount.com
- **Container Registry**: europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app

### Deployment Methods

#### Option 1: Terraform (Recommended for Infrastructure as Code)

```bash
# 1. Build and push Docker image
docker build -t flask_deadlock_analytics_app:latest .
docker tag flask_deadlock_analytics_app:latest \
  europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest

# Configure Docker authentication
gcloud auth configure-docker europe-west2-docker.pkg.dev

# Push image
docker push europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest

# 2. Deploy with Terraform
cd terraform
terraform init
terraform plan
terraform apply

# 3. Get service URL
terraform output service_url
```

**Terraform Configuration** (`terraform/variables.tf`):
- Pre-configured with production values
- Memory: 2Gi, CPU: 2 cores
- Timeout: 120 seconds
- Scaling: 0-10 instances
- Public access enabled

See `terraform/README.md` for:
- Complete deployment guide
- Configuration options
- State management
- CI/CD integration
- Cost estimation

#### Option 2: gcloud CLI (Manual Deployment)

```bash
# Deploy directly from source
gcloud run deploy deadlock-analytics \
  --source . \
  --region europe-west2 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120

# Or build and deploy manually
docker build -t deadlock-analytics:latest .
docker tag deadlock-analytics:latest gcr.io/deadlock-485121/deadlock-analytics:latest
gcloud auth configure-docker
docker push gcr.io/deadlock-485121/deadlock-analytics:latest
gcloud run deploy deadlock-analytics \
  --image gcr.io/deadlock-485121/deadlock-analytics:latest \
  --region europe-west2
```

### Docker Configuration (Cloud Run Optimized)

**Dockerfile** (located in project root):
- **Base Image**: `python:3.12-slim` for minimal footprint (~300-400MB)
- **WSGI Server**: Gunicorn with inline configuration
- **Workers**: 2 workers (Cloud Run scales via container instances, not workers)
- **Threads**: 4 threads per worker for concurrent request handling
- **Timeout**: 120 seconds for long-running API requests
- **Package Manager**: uv for fast dependency installation
- **Port**: Uses `$PORT` environment variable (Cloud Run default: 8080)
- **Scaling**: Auto-scales from 0 to max instances based on load
- **Logging**: stdout/stderr integrated with Google Cloud Logging

**Key Settings**:
```dockerfile
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --graceful-timeout 30 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
```

**No separate gunicorn.conf.py needed** - all settings are inline in the Dockerfile CMD.

### Build Context

The Dockerfile is in the project root and expects to be built from the root directory:

```bash
# Correct (from project root)
docker build -t deadlock-analytics .

# Incorrect (don't use -f flag pointing elsewhere)
docker build -f some/path/Dockerfile -t deadlock-analytics .
```

### Service Configuration

Cloud Run service is configured with:
- **Memory**: 2Gi (sufficient for API responses and data processing)
- **CPU**: 2 cores (handles concurrent requests efficiently)
  - *Can increase to 4 cores for higher concurrency if needed*
- **Timeout**: 120 seconds (allows time for Deadlock API calls and chart generation)
- **Concurrency**: 80 requests per container instance (default)
- **Min Instances**: 0 (scales to zero when idle for cost savings)
- **Max Instances**: 10 (prevents runaway costs)
- **Authentication**: Public access (allUsers can invoke)

### Monitoring and Logs

```bash
# View service details
gcloud run services describe deadlock-analytics --region europe-west2

# Stream logs
gcloud run services logs tail deadlock-analytics --region europe-west2 --follow

# View recent logs
gcloud run services logs read deadlock-analytics --region europe-west2 --limit 50

# View metrics
# https://console.cloud.google.com/run/detail/europe-west2/deadlock-analytics/metrics?project=deadlock-485121
```

## Flask Web Application

### Features

The Flask application provides a comprehensive player analytics dashboard with Steam-themed UI:

#### Header Section
- **Player Profile** (left side):
  - Steam avatar (120x120px) with blue border and glow effect
  - Username (displayed in large font, left-justified) with rank badge next to it
  - Rank badge (48x48px) with hover tooltip showing rank name and tier
  - Steam ID (below username, left-justified)
- **Deadlock Logo** (center): Flat version, 125px width, 120px height, positioned at 45% vertical alignment with opacity transition effect
- **Navigation Button** (right side): "Analyze Another Player"
- **Container**: Max-width 1200px, 50px padding, dark gradient background

#### KPI Tiles (5-card grid)
1. **Total Matches**: Count of all matches analyzed
2. **Wins**: Count of victories (green text)
3. **Losses**: Count of defeats (red text)
4. **Win Rate**: Percentage with color-coded display
5. **Avg K / D / A**: Combined kills/deaths/assists with color coding and slash separators

#### Chart 1: Number of Matches Played
- **Type**: Histogram with win/loss color coding
- **Description**: Shows match frequency over time with green (wins) and red (losses) bars
- **Purpose**: Visualize match activity and winning/losing patterns
- **Title**: "Number of Matches Played"

#### Chart 2: Performance Curve (Interactive Dropdown)
- **Type**: Line chart with dynamic dropdown selector
- **Metrics Available**:
  - Net Worth (Souls) - Average Souls earned over game time
  - Kills - Average kills per time interval
  - Deaths - Average deaths per time interval
  - Assists - Average assists per time interval
- **Description**: Shows how metrics evolve during match progression (0-50 minutes)
- **Dynamic Title**: "Average {Metric} Over Game Time" (e.g., "Average Net Worth Over Game Time")
- **Purpose**: Understand early game vs late game performance patterns

#### Chart 3: Kill and Death Locations
- **Type**: Scatter plot overlaid on minimap (600x600px)
- **Description**:
  - Green markers: Kill locations with count
  - Red markers: Death locations with count
  - Overlaid on Deadlock minimap
  - Legend positioned in top right corner (inside chart)
- **Purpose**: Identify hot zones, safe areas, and positioning patterns
- **Title**: "Kill and Death Locations"

#### Chart 4: Community Distribution Comparison (Interactive Dropdown)
- **Type**: Normal distribution curve with dropdown selector (600px height)
- **Metrics Available**: Kills, Deaths, Assists, K/D, KDA, Net Worth, Souls Per Minute, Last Hits, Denies, Player Damage, Player Damage Per Minute
- **Description**:
  - Blue filled curve: Community distribution (estimated from percentiles)
  - Colored dotted lines: Community percentiles (P10, P25, P50, P75, P90)
  - Green bold line: Player's average
- **Percentiles Displayed**: P10, P25, P50 (median), P75, P90 (P1, P5, P95, P99 removed for clarity)
- **Dynamic Title**: "{Metric} Compared To Community Distribution" (e.g., "Kills Compared To Community Distribution")
- **Purpose**: Compare player performance against community benchmarks
- **Layout**: Stacked vertically above Kill/Death Locations chart

#### Top 5 Heroes Section
- **Type**: Clickable card grid displaying most-played heroes
- **Description**:
  - Hero icon (from heroes endpoint via `images.icon_hero_card` or similar)
  - Hero name
  - Total matches played
  - Win rate percentage
- **Layout**: 5-card horizontal grid with Steam-themed styling
- **Data Source**: Grouped by `hero_name` from match history
- **Purpose**: Show player's hero preferences and performance
- **Interactive Features**:
  - **Hero Filtering**: Click any hero card to filter all dashboard data by that hero
  - **URL Updates**: Clicking a hero updates URL to `/analyze?player_id=X&hero_id=Y`
  - **Visual Feedback**:
    - Selected hero card highlighted with blue border and glow effect
    - Unselected cards dimmed to 50% opacity
    - "Viewing: {Hero Name}" badge appears in section header
    - "Clear Filter" button appears to return to unfiltered view
  - **Audio**: Plays random hero voiceline on click (from assets API `vo.{hero_class_name}` sounds containing "_select_")
  - **Data Filtering**: When filtered, all charts and stats show only matches for that hero
  - **Top Heroes Preserved**: All 5 hero cards remain visible when filtering (uses unfiltered data)

#### Chart 5: Kill and Death Locations
- **Type**: Scatter plot overlaid on minimap (600x600px)
- **Description**:
  - Green markers: Kill locations with count
  - Red markers: Death locations with count
  - Overlaid on Deadlock minimap
  - Legend positioned in top right corner (inside chart)
- **Purpose**: Identify hot zones, safe areas, and positioning patterns
- **Title**: "Kill and Death Locations"
- **Layout**: Bottom of page, centered in container (max-width 600px)

#### Chart 6: MMR History
- **Type**: Line chart with 7-day rolling average
- **Description**:
  - Primary Y-axis (left): MMR score in orange
  - Secondary Y-axis (right): Rank tier (0-11)
  - Bold line: 7-day rolling average for smoothing
  - X-axis: Match timestamps
- **Purpose**: Track rank progression and MMR changes over time
- **Title**: "MMR History (7-Day Rolling Average)"

#### Chart 7: KDA Trend Over Time
- **Type**: Line chart with 7-day rolling average
- **Description**:
  - Bold lines: 7-day rolling average (Kills, Deaths, Assists)
  - Faint scatter points: Individual match performance (hover disabled)
  - Color coded: Kills (green), Deaths (red), Assists (blue)
- **Purpose**: Track skill progression and performance improvement over time
- **Title**: "KDA Trend Over Time (7-Day Rolling Average)"

### Interactive Audio Features

The application includes immersive audio feedback for various user interactions:

#### Audio System
- **Volume**: Fixed at 50% (0.5) for all sounds
- **Assets Source**: Deadlock Assets API (`assets.deadlock-api.com`)
- **Audio Data Loading**: Fetches full sound catalog from `/v1/images` endpoint on results page load

#### Clickable Elements with Sounds

1. **Hero Cards** (Top 5 Heroes section)
   - **Sound**: Random hero voiceline from `vo.{hero_class_name}` containing "_select_"
   - **Behavior**: Plays voiceline, waits for completion, then navigates to filtered view
   - **Purpose**: Character selection feedback

2. **KPI Tiles** (Summary Cards)
   - **Sound**: Sequential dirt footstep sounds from `player.footsteps.shared.surface_sweeteners.soft_impact.dirt_{01-14}`
   - **Behavior**: Plays sounds in sequence (dirt_01, dirt_02, ..., dirt_14, then loops back to dirt_01)
   - **Counter**: Shared across all 5 tiles, increments with each click
   - **Purpose**: Satisfying tactile feedback for stat exploration

3. **Player Avatar** (Header left)
   - **Sound**: `ui_friends_list_send_invite_02.mp3`
   - **Behavior**: Plays immediately on click (non-blocking)
   - **Purpose**: UI interaction feedback

4. **Deadlock Logo** (Header center)
   - **Sound**: `ui_friends_list_send_invite_02.mp3` (same as avatar)
   - **Behavior**: Plays immediately on click (non-blocking)
   - **Purpose**: UI interaction feedback

5. **Initial Analysis Form** (index.html)
   - **Sound**: `ui_hud_acquire_ap_02.mp3`
   - **Behavior**: Plays and waits for completion before submitting form
   - **Purpose**: Data fetch confirmation

6. **Clear Filter Button** (results.html)
   - **Sound**: `ui_hud_acquire_ap_02.mp3`
   - **Behavior**: Plays and waits for completion before navigating
   - **Purpose**: Action confirmation

7. **Analyze Another Player Button** (results.html)
   - **Sound**: `ui_hud_acquire_ap_02.mp3`
   - **Behavior**: Plays asynchronously while navigating (non-blocking)
   - **Purpose**: Smooth transition without delay

#### Audio Implementation Details

**Hero Voiceline System**:
- Fetches hero class name from heroes API
- Strips "hero_" prefix from class name for sounds API compatibility
- Filters for voicelines containing "_select_" in the key
- Picks random sound from available select voicelines
- Uses Promise-based async/await to ensure voiceline plays fully before navigation

**KPI Sequential Sounds**:
- Global counter starts at 1
- Counter increments after successful sound playback
- Resets to 1 after reaching 14
- All tiles share the same counter for consistent progression

**Loading States**:
- "Applying filter..." overlay shown during hero filtering
- No overlay for "Analyze Another Player" (instant navigation with async sound)
- Loading overlay hidden on page back navigation (pageshow event)

### Steam Theme Design

The entire application uses Steam's signature aesthetic:

**Colors**:
- Dark blue gradients: `#1b2838`, `#16202d`, `#2a475e`
- Steam blue highlights: `#66c0f4` (used for borders, titles, accents)
- Success green: `#5cc85c` (wins, kills)
- Error red: `#d94040` (losses, deaths)
- Neutral gray: `#8f98a0` (secondary text)
- Light text: `#c7d5e0` (primary text)

**Typography**:
- Font family: Motiva Sans (Steam's official font), fallback to Arial
- Chart titles: 22px, Steam blue (#66c0f4)
- Body text: 12px, light gray (#c7d5e0)
- Headers: Varied sizes with letter-spacing for readability

**Effects**:
- Glow effects on interactive elements
- Smooth transitions (0.2s ease)
- Hover effects with increased opacity
- Box shadows with Steam blue tint

**Layout**:
- Responsive grid system
- Max-width container (1200px)
- Generous padding and spacing
- Card-based design with subtle borders

### API Endpoints

#### `/` (GET)
- Home page with player ID input form
- Clean, modern UI with gradient background
- Plays UI sound on form submission before navigating

#### `/analyze` (GET, POST)
- **POST**: Accepts `player_id` form parameter from index page
- **GET**: Accepts `player_id` and optional `hero_id` query parameters for filtered views
- **Hero Filtering**: When `hero_id` is provided:
  - Filters match history to only show matches for that hero
  - Updates all charts and statistics to reflect filtered data
  - Preserves top 5 heroes display using unfiltered data
  - Passes `filtered_hero_name` to template for UI feedback
- Fetches data from multiple API endpoints
- Processes data with pandas
- Generates Plotly visualizations
- Renders analytics dashboard
- **URL Examples**:
  - `/analyze?player_id=199540209` (unfiltered view)
  - `/analyze?player_id=199540209&hero_id=5` (filtered to hero_id 5)

### Data Processing Pipeline

1. **Input Validation**: Validate player ID format (SteamID3) and optional hero_id parameter
2. **API Calls**: Fetch data from 9 endpoints:
   - `/v2/heroes` - Hero names and metadata (includes images via flattened columns)
   - `/v1/players/{id}/match-history` - Match details (always unfiltered)
   - `/v1/players/steam-search?search_query={id}` - Steam profile data
   - `/v1/analytics/player-stats/metrics?account_ids={id}&hero_ids={hero_id}` - Player statistics with community percentiles (filtered if hero_id provided)
   - `/v1/analytics/player-performance-curve?account_ids={id}&hero_ids={hero_id}` - Performance metrics over game time (filtered if hero_id provided)
   - `/v1/analytics/kill-death-stats?account_ids={id}&hero_ids={hero_id}` - Spatial kill/death coordinates (filtered if hero_id provided)
   - `/v1/players/{id}/mmr-history` - MMR progression over time (never filtered)
   - `/v2/ranks` - Rank metadata including badge images
   - `/v1/images` - Asset images (heroes, items, abilities, sounds)
3. **Data Transformation**:
   - Convert to pandas DataFrames with `json_normalize()`
   - Filter steam-search results by matching account_id
   - Extract Steam username and full-size avatar
   - Join hero names with match data, **preserve hero_id column** for filtering
   - Calculate win/loss from match_result
   - **Hero Filtering Logic** (if hero_id provided):
     - Save unfiltered copy of match history (`df_match_history_unfiltered`) for top heroes calculation
     - Filter match history to only matches where `hero_id == filter_value`
     - Extract `filtered_hero_name` from filtered data
     - Use filtered data for all charts/stats except top heroes
     - Top heroes always uses unfiltered data to show all 5 cards
   - Apply 7-day rolling window for KDA trend
   - Sort by timestamp for chronological display
   - Generate normal distribution curves using scipy.stats
   - Filter metrics with std_dev < 0.01 to avoid flat curves
   - Handle degenerate distributions with "Insufficient match data" placeholders
4. **Visualization**: Generate Plotly charts with PlotlyJSONEncoder
   - Apply Steam theme using JavaScript `applySteamTheme()` function
   - Dynamic chart titles based on dropdown selections
   - Preserve chart properties while applying colors
   - Show filter subtitle when hero filtering is active
5. **Rendering**: Pass charts, summary stats, Steam profile, top heroes, hero_id, and filtered_hero_name to HTML template

## Game Terminology

Understanding Deadlock-specific terms:

- **Souls**: In-game currency (NOT "Gold"). Use "Souls" in all references.
- **Net Worth**: Total Souls earned by a player during a match
- **KDA**: Kills, Deaths, Assists - primary performance metrics
- **Hero**: Playable character (similar to champions in other MOBAs)
- **Match Result**: Integer (0 or 1) indicating which team won
- **Player Team**: Integer (0 or 1) indicating player's team
- **Win Determination**: `player_team == match_result`
- **SteamID3**: Player identifier format (e.g., 199540209)

## Deadlock API Documentation

### API Hosts
- **Data API**: `api.deadlock-api.com`
- **Assets API**: `assets.deadlock-api.com`

### Documentation Resources
- **Scalar API Docs**: https://assets.deadlock-api.com/scalar
  - Interactive documentation with request/response examples
  - Try API calls directly in browser
- **OpenAPI Docs**: https://api.deadlock-api.com/docs
  - Standard OpenAPI specification interface
  - Machine-readable API schema

### Schema Reference
See `/docs/api_schema_reference.md` for comprehensive documentation including:
- Detailed column descriptions for each endpoint
- Data types and value ranges
- Example responses
- Common patterns and usage tips
- Chart recommendations

### Key Endpoints Used

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `/v2/heroes` | Hero metadata | List of 53 heroes with names, images (flattened), stats, class_name |
| `/v1/players/{id}/match-history` | Match details | List of matches (21 columns per match) with hero_id |
| `/v1/players/steam-search` | Steam profile lookup | List of matching profiles with username, avatars |
| `/v1/analytics/player-stats/metrics?account_ids={id}&hero_ids={hero_id}` | Player statistics | Averages, std dev, and community percentiles (P1-P99). Supports filtering by hero_ids |
| `/v1/analytics/player-performance-curve?account_ids={id}&hero_ids={hero_id}` | Performance over game time | 12 time intervals with avg stats. Supports filtering by hero_ids |
| `/v1/analytics/kill-death-stats?account_ids={id}&hero_ids={hero_id}` | Kill/death locations | List of map coordinates with counts. Supports filtering by hero_ids |
| `/v1/players/{id}/mmr-history` | MMR progression | List of games with MMR score, division, tier (never filtered) |
| `/v2/ranks` | Rank metadata | List of ranks with badge images and tier info |
| `/v1/images` | Asset images | Dictionary of image URLs and sound URLs (heroes, items, abilities, vo, physics, player, ui) |

**Important**: Analytics endpoints use plural parameter names:
- `account_ids` (not `account_id`)
- `hero_ids` (not `hero_id`)
- Multiple IDs can be comma-separated

### Rate Limits
- No authentication required for public endpoints
- Rate limits may apply (check API documentation)
- Use responsibly to avoid throttling

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Keep functions focused and single-purpose
- Use meaningful variable names (e.g., `df_match_history` not `df1`)
- Document complex logic with comments
- No emojis unless explicitly requested

### Flask Development

#### Adding a New Chart

1. **Fetch Data**: Add API call in `create_visualizations()` function
   ```python
   new_data = get_request_data(connection, "data-api", "new_endpoint")
   df_new = pd.json_normalize(new_data)
   ```

2. **Process Data**: Transform and clean the data
   ```python
   df_new = df_new.sort_values('timestamp')
   df_new['calculated_field'] = df_new['field1'] / df_new['field2']
   ```

3. **Create Chart**: Generate Plotly figure
   ```python
   fig = go.Figure()
   fig.add_trace(go.Scatter(x=df_new['x'], y=df_new['y']))
   fig.update_layout(title='Chart Title')
   charts['new_chart'] = json.dumps(fig, cls=PlotlyJSONEncoder)
   ```

4. **Add HTML Container**: In `templates/results.html`
   ```html
   {% if charts.new_chart %}
   <div class="chart-container">
       <div id="chartN"></div>
   </div>
   {% endif %}
   ```

5. **Add Rendering Code**: In JavaScript section
   ```javascript
   {% if charts.new_chart %}
   var chartN = {{ charts.new_chart | safe }};
   Plotly.newPlot('chartN', chartN.data, chartN.layout);
   {% endif %}
   ```

#### Important Implementation Details

**Win/Loss Calculation**
```python
# CORRECT: Compare player_team with match_result
df['result'] = df.apply(
    lambda row: 'Win' if row['player_team'] == row['match_result'] else 'Loss',
    axis=1
)
```

**Rolling Window Average**
```python
# Time-based rolling window (7 days)
df = df.set_index('start_ts')  # Set timestamp as index
df['kills_avg'] = df['player_kills'].rolling(window='7D', min_periods=1).mean()
df = df.reset_index()  # Reset to get timestamp back as column
```

**Hero Name Joins**
```python
# Join match history with hero names
df_match = pd.merge(
    df_match_history,
    df_heroes[['id', 'name']],
    left_on='hero_id',
    right_on='id',
    how='left'
).rename(columns={'name': 'hero_name'})
```

**Minimap Overlay**
```python
# Add minimap as background image
fig.update_layout(
    images=[dict(
        source='/static/img/minimap.png',
        xref='x', yref='y',
        x=-10000, y=10000,  # Position at coordinate system origin
        sizex=20000, sizey=20000,  # Cover full coordinate range
        sizing='stretch',
        layer='below'  # Place below scatter markers
    )],
    # Position legend inside top right
    legend=dict(
        x=0.98, y=0.98,
        xanchor='right', yanchor='top',
        bgcolor='rgba(27, 40, 56, 0.9)',
        bordercolor='#3d4e5c'
    )
)
```

**Steam Profile Filtering**
```python
# Steam-search returns multiple results, filter by account_id
steam_profile = get_request_data(connection, "data-api", "steam_search")
for profile in steam_profile:
    if str(profile.get('account_id', '')) == str(player_id):
        steam_data = {
            'username': profile.get('personaname', 'Unknown Player'),
            'avatar_full': profile.get('avatarfull', ''),  # Full-size avatar
        }
        break
```

**Dynamic Chart Titles**
```python
# Performance curve dropdown updates title
dropdown_buttons.append({
    'label': metric['name'],
    'method': 'update',
    'args': [
        {'visible': visible},
        {
            'yaxis.title.text': metric['yaxis_title'],
            'title.text': f"Average {metric['name']} Over Game Time"
        }
    ]
})

# Distribution chart dropdown updates title
'title.text': f"{metric['name']} Probability Distribution Function"
```

**Distribution Chart Generation**
```python
# Generate normal distribution using player's personal stats
avg = float(df_player_stats[f'{metric_key}.avg'].iloc[0])
std_dev = float(df_player_stats[f'{metric_key}.std'].iloc[0])

# Create curve centered on player's average
x_range = np.linspace(avg - 4*std_dev, avg + 4*std_dev, 200)
y_range = stats.norm.pdf(x_range, avg, std_dev)

# Add distribution curve
fig.add_trace(go.Scatter(
    x=x_range.tolist(),
    y=y_range.tolist(),
    fill='tozeroy',
    fillcolor='rgba(102, 192, 244, 0.4)'
))

# Add player average line (green dashed)
fig.add_trace(go.Scatter(
    x=[avg, avg],
    y=[0, y_max * 1.1],
    line=dict(color='#5cc85c', width=4, dash='dash')
))

# Add ±1 standard deviation lines (gray dotted)
fig.add_trace(go.Scatter(
    x=[avg - std_dev, avg - std_dev],
    y=[0, y_max * 1.05],
    line=dict(color='#8f98a0', width=2, dash='dot')
))
```

**IMPORTANT: Distribution Chart Interpretation**

The distribution chart shows the player's **personal performance variance**, not community distribution:
- The curve represents how the player's performance varies across their own matches
- The green dashed line (player average) is always centered because it's the mean of their own data
- The ±1 SD lines show consistency: narrow spread = consistent, wide spread = variable
- This is NOT a community ranking visualization

The API provides percentile data (percentile1, percentile5, etc.) which represents community benchmarks, but these are not currently used to generate the curve. Future enhancement could plot percentile values as vertical reference lines to show community ranking.

**Data Type Conversions**
```python
# Always convert to lists when passing to Plotly
x=df['column'].tolist()  # Not just df['column']

# Convert Unix timestamp to datetime
df['datetime'] = pd.to_datetime(df['start_time'], unit='s')
```

**Disable Hover on Scatter Points**
```python
# For background scatter points in KDA trend
fig.add_trace(go.Scatter(
    mode='markers',
    hoverinfo='skip'  # Disable hover for these points
))
```

**Hero Filtering Implementation**
```python
# app.py - Route accepts both GET and POST
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        player_id = request.form.get('player_id', '').strip()
    else:  # GET request
        player_id = request.args.get('player_id', '').strip()

    hero_id = request.args.get('hero_id', type=int)  # Optional filter

    charts, summary, steam_data, top_heroes, filtered_hero_name = create_visualizations(player_id, hero_id)

    return render_template('results.html',
                          player_id=player_id,
                          hero_id=hero_id,
                          filtered_hero_name=filtered_hero_name,
                          charts=charts,
                          summary=summary,
                          steam_data=steam_data,
                          top_heroes=top_heroes)

# app.py - Preserve hero_id in data pipeline
df = df.drop(columns=["id"]).rename(columns={"name": "hero_name"})  # Keep hero_id

# app.py - Filter match history after enrichment
def create_visualizations(player_id, hero_id=None):
    # ... fetch and enrich match history ...

    # Save unfiltered copy for top heroes calculation
    df_match_history_unfiltered = df_match_history.copy()

    # Apply hero filter if specified
    filtered_hero_name = None
    if hero_id is not None and not df_match_history.empty:
        if 'hero_name' in df_match_history.columns:
            hero_match = df_match_history[df_match_history['hero_id'] == hero_id]
            if not hero_match.empty:
                filtered_hero_name = hero_match.iloc[0]['hero_name']

        # Filter match history to selected hero
        df_match_history = df_match_history[df_match_history['hero_id'] == hero_id].copy()

    # Use df_match_history_unfiltered for top heroes calculation
    # Use df_match_history (filtered) for all charts and stats

    return charts, summary, steam_data, top_heroes, filtered_hero_name

# app.py - API connection with hero_ids parameter
def get_api_connection(player_id, hero_id=None):
    hero_param = f"&hero_ids={hero_id}" if hero_id is not None else ""
    return {
        "data-api": {
            # match_history: Don't filter (needed for top heroes)
            "match_history": f"/v1/players/{player_id}/match-history?only_stored_history=false",
            # Analytics endpoints: Filter by hero_ids if provided
            "player_stats": f"/v1/analytics/player-stats/metrics?account_ids={player_id}{hero_param}",
            "player_performance_curve": f"/v1/analytics/player-performance-curve?account_ids={player_id}&resolution=0{hero_param}",
            "kill_death_stats": f"/v1/analytics/kill-death-stats?account_ids={player_id}{hero_param}",
            # mmr_history: Never filtered
            "mmr_history": f"/v1/players/{player_id}/mmr-history",
        }
    }
```

**Hero Card Audio Integration**
```javascript
// results.html - Hero voiceline playback
async function playHeroSelectSound(heroId) {
    return new Promise((resolve, reject) => {
        const hero = heroesData.find(h => h.id === heroId);
        let heroClassName = hero.class_name;

        // Remove "hero_" prefix (sounds API doesn't use it)
        if (heroClassName.startsWith('hero_')) {
            heroClassName = heroClassName.substring(5);
        }

        const heroSounds = soundsData.vo[heroClassName];
        const selectSounds = Object.entries(heroSounds).filter(([key, url]) =>
            key.toLowerCase().includes('_select_')
        );

        const randomSound = selectSounds[Math.floor(Math.random() * selectSounds.length)];
        const [soundKey, soundUrl] = randomSound;

        const audio = new Audio(soundUrl);
        audio.volume = 0.5;

        audio.addEventListener('ended', () => resolve());
        audio.play().catch(err => resolve());
    });
}

// Hero card click handler
card.addEventListener('click', async function(e) {
    e.preventDefault();
    loadingOverlay.classList.add('active');

    if (heroId) {
        await playHeroSelectSound(heroId);
    }

    window.location.href = href;
}, true);
```

**KPI Tile Sequential Sounds**
```javascript
// results.html - Sequential dirt footstep sounds
let kpiSoundCounter = 1;

kpiTiles.forEach(function(tile) {
    tile.addEventListener('click', function() {
        const softImpactSounds = soundsData.player.footsteps.shared.surface_sweeteners.soft_impact;
        const soundKey = `dirt_${String(kpiSoundCounter).padStart(2, '0')}`;
        const soundUrl = softImpactSounds[soundKey];

        const audio = new Audio(soundUrl);
        audio.volume = 0.5;
        audio.play().then(() => {
            kpiSoundCounter++;
            if (kpiSoundCounter > 14) {
                kpiSoundCounter = 1;
            }
        });
    });
});
```

### Data Analysis Workflow
1. Fetch data using API endpoints
2. Convert to pandas DataFrames with `json_normalize()`
3. Clean and transform data (joins, calculations, filtering)
4. Sort by timestamp for chronological analysis
5. Apply aggregations (rolling windows, groupby)
6. Visualize with Plotly or export for further analysis

### Version Control
- Commit working code frequently with descriptive messages
- Keep notebooks in `scripts/` directory
- Don't commit `.venv`, `__pycache__`, or `__marimo__/session/`
- Test charts before committing
- Update documentation when adding features

## Marimo Notebooks

### Running Notebooks

**Edit Mode** (interactive development):
```bash
marimo edit scripts/deadlock_notebook.py
```

**Run Mode** (web app):
```bash
marimo run scripts/deadlock_notebook.py
```

### Marimo Features

Marimo is a reactive notebook environment where:
- **Reactive Execution**: Cells automatically re-run when dependencies change
- **State Management**: State is managed reactively across cells
- **Pure Python**: Notebooks are stored as pure Python files (not JSON)
- **UI Elements**: Interactive widgets with `mo.ui.*`
- **Markdown**: Use `mo.md()` for formatted text

**Key Benefits**:
- No out-of-order execution issues
- Reproducible results
- Version control friendly (pure Python)
- Can be run as standalone scripts or web apps

## Dependencies

### Core Dependencies
```toml
[project]
dependencies = [
    "deadlock-api-client",  # From GitHub
    "marimo>=0.19.4",
    "pandas>=2.3.3",
    "flask>=3.1.2",
    "plotly>=6.5.2",
    "scipy>=1.17.0",
    "numpy>=2.4.1",
    "gunicorn>=23.0.0",  # Production WSGI server
]
```

### Adding New Dependencies

```bash
# Add production dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Update all dependencies
uv lock --upgrade
uv sync
```

### Dependency Sources
- **deadlock-api-client**: Installed from Git
  ```toml
  [tool.uv.sources]
  deadlock-api-client = {
      git = "https://github.com/deadlock-api/openapi-clients",
      subdirectory = "python/api"
  }
  ```

## Terraform Infrastructure

The application uses Terraform for infrastructure as code deployment to Google Cloud Run.

### Terraform Structure

```
terraform/
├── main.tf                    # Cloud Run service resource
├── variables.tf               # Configuration variables (pre-configured)
├── outputs.tf                 # Service outputs (URL, name, location)
├── terraform.tfvars.example   # Example configuration
├── .gitignore                 # Excludes state files
└── README.md                  # Deployment guide
```

### Pre-configured Values

The Terraform configuration comes pre-configured for production:

```hcl
# variables.tf defaults
project_id      = "deadlock-485121"
region          = "europe-west2"
service_name    = "deadlock-analytics"
service_account = "sa-deadlock-cloud-run@deadlock-485121.iam.gserviceaccount.com"
container_image = "europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest"

# Resource allocation
memory        = "2Gi"
cpu           = "2"
timeout       = 120

# Scaling
min_instances = 0
max_instances = 10
```

### Terraform Workflow

**Initial Deployment**:
```bash
cd terraform
terraform init          # Initialize providers and modules
terraform plan          # Preview changes
terraform apply         # Apply changes (creates Cloud Run service)
terraform output        # View service URL and details
```

**Update Deployment**:
```bash
# Modify variables.tf or create terraform.tfvars
terraform plan          # Review changes
terraform apply         # Apply updates
```

**Destroy Service**:
```bash
terraform destroy       # Remove all Terraform-managed resources
```

### Key Terraform Resources

**main.tf** defines:
1. **google_cloud_run_v2_service**: The Cloud Run service
   - Container image from Artifact Registry
   - Service account attachment
   - Resource limits (CPU, memory)
   - Scaling configuration
   - Timeout settings
   - Port configuration (8080)

2. **google_cloud_run_v2_service_iam_member**: Public access policy
   - Role: `roles/run.invoker`
   - Member: `allUsers` (public access)

### Outputs

After deployment, Terraform provides:
- `service_url`: Full HTTPS URL of the deployed service
- `service_name`: Name of the Cloud Run service
- `service_location`: GCP region where service is deployed
- `service_id`: Full resource ID for the service

### State Management

**Local State** (default):
- State stored in `terraform.tfstate`
- Good for single-user development
- Included in `.gitignore`

**Remote State** (recommended for teams):
```hcl
# Create backend.tf
terraform {
  backend "gcs" {
    bucket = "deadlock-485121-terraform-state"
    prefix = "cloud-run/deadlock-analytics"
  }
}
```

Then migrate state:
```bash
gsutil mb gs://deadlock-485121-terraform-state
gsutil versioning set on gs://deadlock-485121-terraform-state
terraform init -migrate-state
```

### Terraform Best Practices

1. **Version Control**: Commit Terraform files (.tf) to git
2. **State Security**: Never commit .tfstate files
3. **Variable Files**: Use terraform.tfvars for environment-specific values
4. **Plan Before Apply**: Always run `terraform plan` first
5. **Remote State**: Use GCS backend for team collaboration
6. **Resource Tagging**: Consider adding labels for cost tracking

### CI/CD Integration

Example GitHub Actions workflow:
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - name: Terraform Init
        run: terraform init
        working-directory: terraform
      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform
```

## Troubleshooting

### Flask Application Issues

**Charts Not Displaying**
1. Check terminal for debug output (print statements show data shapes)
2. Verify DataFrame columns exist: `print(df.columns.tolist())`
3. Check browser console (F12) for JavaScript errors
4. Ensure `.tolist()` is called when passing data to Plotly
5. Verify data is not empty: `print(df.shape)`

**API Errors**
- Verify player ID format (SteamID3, e.g., 199540209)
- Check API status at deadlock-api.com
- Review terminal output for HTTP status codes
- Verify network connectivity
- Check for rate limiting (429 status code)

**Minimap Not Loading**
- Verify file exists: `ls -la static/img/minimap.png`
- Check file permissions (should be readable)
- Test direct URL: http://localhost:5000/static/img/minimap.png
- Verify Flask static folder configuration

**Data Issues**
- Print DataFrame shapes to verify data was fetched
- Check for None values from API calls
- Verify column names match API schema
- Test with known working player ID (199540209)

**Audio Issues**
- Check browser console (F12) for audio playback errors
- Verify audio data loaded: Check console for "Audio data loaded" message
- Test hero class names: Hero class_name from API should not include "hero_" prefix for sounds API
- Verify sound paths:
  - Hero voicelines: `vo.{hero_class_name}.{sound_key}` (must contain "_select_")
  - KPI sounds: `player.footsteps.shared.surface_sweeteners.soft_impact.dirt_{01-14}`
  - UI sounds: `ui_hud_acquire_ap_02.mp3`, `ui_friends_list_send_invite_02.mp3`
- Browser autoplay policies may block some sounds (user interaction required)
- Audio volume fixed at 0.5 (50%) in code

**Hero Filtering Issues**
- Verify hero_id is valid integer from heroes API
- Check that match history includes hero_id column
- Filtered data should preserve hero_id for filtering logic
- Top 5 heroes should always show (uses unfiltered data copy)
- Clear filter button navigates to `/analyze?player_id={id}` (no hero_id)
- If charts show "Insufficient match data", hero may have too few matches

### Docker Issues

**Build Failures**
```bash
# Check Dockerfile syntax
docker build -t test .

# View build logs
docker build --progress=plain -t test .

# Check if files are being copied correctly
docker build -t test . && docker run --rm test ls -la /app
```

**Container Won't Start**
```bash
# Check container logs
docker logs CONTAINER_ID

# Run interactively to debug
docker run -it --entrypoint /bin/bash IMAGE_NAME

# Test gunicorn command manually
docker run -it --entrypoint /bin/bash IMAGE_NAME
# Then inside container:
gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 120 app:app
```

**Image Size Issues**
- Image should be ~300-400MB compressed
- Check layers: `docker history IMAGE_NAME`
- Use `.dockerignore` to exclude unnecessary files
- Verify uv is caching correctly

### Cloud Run Issues

**Deployment Failures**
```bash
# Check service status
gcloud run services describe deadlock-analytics --region europe-west2

# View recent logs
gcloud run services logs read deadlock-analytics --region europe-west2 --limit 100

# Check deployment history
gcloud run revisions list --service deadlock-analytics --region europe-west2
```

**502 Bad Gateway**
- Usually indicates container startup timeout or crash
- Check if container is listening on `$PORT` (8080)
- Verify gunicorn binds to `0.0.0.0:$PORT`, not `127.0.0.1`
- Check memory limits aren't being exceeded
- Review startup logs for errors

**Cold Start Issues**
- First request after idle period may timeout
- Consider setting `min_instances = 1` to keep warm (costs more)
- Optimize container startup time
- Check timeout is sufficient (120s default)

**High Memory Usage**
- Monitor in Cloud Console metrics
- Increase memory allocation: `terraform apply -var="memory=4Gi"`
- Check for memory leaks in application
- Review pandas DataFrame sizes

**Performance Issues**
- Check Cloud Run metrics for CPU/memory utilization
- Consider increasing CPU: `terraform apply -var="cpu=4"`
- Review API call latency to Deadlock API
- Check number of concurrent requests
- Verify gunicorn worker/thread configuration

### Terraform Issues

**State Errors**
```bash
# Refresh state
terraform refresh

# View current state
terraform show

# Unlock state (if locked)
terraform force-unlock LOCK_ID
```

**Plan Shows Unexpected Changes**
- Check if resources were modified outside Terraform
- Review drift: `terraform plan -refresh-only`
- Import existing resources: `terraform import`

**Permission Errors**
- Verify service account has correct IAM roles
- Check project ID is correct
- Ensure APIs are enabled (Cloud Run, Artifact Registry)

**Image Not Found**
```bash
# Verify image exists in registry
gcloud artifacts docker images list \
  europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo

# Re-tag and push image
docker tag IMAGE_NAME europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest
docker push europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest
```

### Dependency Issues

```bash
# Update lock file and resync
uv lock --upgrade
uv sync

# Clean reinstall
rm -rf .venv
uv venv
uv sync
```

### API Connection Issues
- Verify API endpoints are accessible
- Check network connectivity
- Review rate limits at API documentation
- Try browser access: https://api.deadlock-api.com/docs
- Check firewall/proxy settings

### Notebook Issues

```bash
# Clear marimo cache
rm -rf __marimo__/session/

# Restart marimo server
# (Ctrl+C to stop, then restart)

# Check for syntax errors
python scripts/deadlock_notebook.py --check
```

## Testing

### Manual Testing

**Test Flask App**:
```bash
# Start app
python app.py

# Test with sample player ID
# Visit http://localhost:5000
# Enter: 199540209
# Verify all 4 charts display correctly
```

**Test API Connection**:
```bash
# Run schema analysis tool
python scripts/analyze_schema.py

# Should show:
# - 200 status codes
# - DataFrame shapes
# - Sample data
```

### What to Test
- [ ] Player ID input validation
- [ ] All API endpoints return 200 status
- [ ] All 4 charts display with data
- [ ] Rolling average calculation is correct
- [ ] Win/loss colors are correct (green/red)
- [ ] Minimap overlay shows markers
- [ ] Dropdown selector works on performance curve
- [ ] Summary stats calculate correctly
- [ ] Charts are interactive (hover, zoom, pan)

## Performance Optimization

### Tips for Large Datasets

1. **Use ScatterGL**: For scatter plots with >1000 points
   ```python
   go.Scattergl(...)  # Instead of go.Scatter()
   ```

2. **Limit Data Points**: Filter or sample large datasets
   ```python
   df_recent = df.tail(200)  # Last 200 matches
   ```

3. **Optimize Rolling Windows**: Use smaller windows for faster computation
   ```python
   df['avg'] = df['value'].rolling(window='3D').mean()  # 3 days instead of 7
   ```

4. **Cache API Responses**: Store responses to avoid repeated API calls
   ```python
   # TODO: Implement caching mechanism
   ```

## Contributing

When making changes:

1. **Branch**: Create a feature branch
   ```bash
   git checkout -b feature/new-chart
   ```

2. **Develop**: Make changes and test thoroughly
   ```bash
   python app.py
   # Test in browser
   ```

3. **Document**: Update documentation
   - Update this file (CLAUDE.md)
   - Update API schema docs if endpoints change
   - Add comments for complex logic

4. **Commit**: Use clear, descriptive messages
   ```bash
   git add .
   git commit -m "Add new performance metrics chart"
   ```

5. **Test**: Verify everything works
   - All charts display
   - No console errors
   - API calls succeed

## Documentation

### README.md
The project includes a comprehensive README with:
- **Banner Image**: Cityscape graphic (`static/img/graphic_cityscape.png`) displayed at full width
- **Quick Start Guide**: Installation and setup instructions using `uv`
- **Features List**: Overview of all dashboard capabilities
- **Technology Stack**: Key libraries and frameworks
- **Project Structure**: Directory layout
- **API Documentation Links**: References to Deadlock API resources

The README is designed for GitHub display and uses proper markdown formatting with HTML for the banner image.

### Custom Fonts
The project includes the **ForevsDemo** font family (14 variants) located in `static/fonts/`:
- Regular, Bold, Black, Medium, Light, Thin, Super (with Italic variants)
- Can be installed system-wide or per-user with `fc-cache -fv`
- Font family name: "Forevs Demo"
- Useful for creating custom graphics and SVG banners

## Resources

### Deadlock API
- [Scalar API Docs](https://assets.deadlock-api.com/scalar) - Interactive API documentation
- [OpenAPI Docs](https://api.deadlock-api.com/docs) - OpenAPI specification
- [GitHub Repository](https://github.com/deadlock-api/openapi-clients) - Source code

### Python Libraries
- [Flask Documentation](https://flask.palletsprojects.com/) - Web framework
- [Plotly Python](https://plotly.com/python/) - Interactive visualizations
- [pandas Documentation](https://pandas.pydata.org/docs/) - Data analysis
- [Marimo Documentation](https://docs.marimo.io/) - Reactive notebooks

### Development Tools
- [uv Documentation](https://github.com/astral-sh/uv) - Python package manager
- [Python Type Hints](https://docs.python.org/3/library/typing.html) - Type annotations

### Game Information
- [Deadlock Wiki](https://deadlock.fandom.com/) - Game mechanics and lore
- Community forums and Discord for player insights

## Recent Features (v0.2.0)

**Production Deployment** (2026-01-22)
- ✅ Deployed to Google Cloud Run (europe-west2)
- ✅ Live at: https://deadlock-analytics-164941517977.europe-west2.run.app
- ✅ Terraform infrastructure as code configuration
- ✅ Docker containerization with Gunicorn WSGI server
- ✅ Auto-scaling from 0-10 instances
- ✅ 2Gi memory, 2 CPU cores per instance
- ✅ Artifact Registry integration

**Hero Filtering System** (2026-01-22)
- ✅ Clickable hero cards to filter all dashboard data by hero_id
- ✅ URL parameter support for bookmarkable filtered views (`?hero_id=X`)
- ✅ Visual feedback with highlighted/dimmed cards and filter badges
- ✅ Preserves top 5 heroes display when filtering
- ✅ Backend filtering with GET request support
- ✅ "Clear Filter" button to return to unfiltered view

**Interactive Audio System** (2026-01-22)
- ✅ Hero voicelines play on hero card selection (random select sounds)
- ✅ Sequential dirt footstep sounds on KPI tile clicks (cycles dirt_01 to dirt_14)
- ✅ UI confirmation sounds for form submissions and navigation
- ✅ Clickable avatar and logo with sound feedback
- ✅ Fixed 50% volume for all audio
- ✅ Promise-based async audio handling
- ✅ Assets loaded from Deadlock Assets API

## Future Enhancements

Potential features to add:

### Application Features
- [ ] Caching layer for API responses (reduce load on Deadlock API)
- [ ] More chart types (radar charts, heatmaps, hero comparison radars)
- [ ] Compare multiple players side-by-side
- [ ] Item build analysis and recommendations
- [ ] Match replay links and detailed match breakdowns
- [ ] Export data to CSV/JSON
- [ ] User authentication and saved dashboards
- [ ] Mobile-responsive design improvements
- [ ] Adjustable volume control (currently fixed at 50%)
- [ ] More audio feedback for additional interactions
- [ ] Hero-specific performance insights and recommendations
- [ ] Team composition analysis

### Infrastructure
- [ ] CDN integration for static assets
- [ ] Redis caching layer for API responses
- [ ] Cloud SQL for analytics data storage
- [ ] Scheduled data refresh jobs (Cloud Scheduler)
- [ ] Cloud Storage for user-generated content
- [ ] Custom domain with Cloud Load Balancer
- [ ] Multi-region deployment for lower latency
- [ ] Monitoring dashboards and alerting (Cloud Monitoring)
- [ ] Cost optimization analysis and recommendations

---

**Last Updated**: 2026-01-22
**Project Version**: 0.2.0
**Python Version**: 3.12+
