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
├── templates/                  # HTML templates for Flask
│   ├── index.html             # Landing page with player ID input
│   └── results.html           # Analytics dashboard with charts
├── static/                     # Static assets
│   └── img/
│       ├── minimap.png        # Deadlock minimap image (512x512px)
│       └── deadlock-logo.png  # Deadlock logo for branding
├── scripts/                    # Analysis scripts and notebooks
│   ├── deadlock_notebook.py  # Original marimo notebook
│   └── analyze_schema.py     # API schema analysis tool
├── docs/                       # Documentation
│   └── api_schema_reference.md # Comprehensive API schema documentation
├── __marimo__/                 # Marimo notebook cache and sessions
│   └── session/               # Session data
├── .venv/                     # Virtual environment (managed by uv)
├── .claude                    # Claude Code configuration
├── .gitignore                 # Git ignore patterns
├── .python-version            # Python version specification (3.12)
├── pyproject.toml             # Project dependencies and metadata
├── uv.lock                    # Locked dependency versions
├── CLAUDE.md                  # This file
└── README.md                  # Project readme
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
3. View interactive analytics dashboard with Steam profile, 5 KPI tiles, and 5 visualizations

## Flask Web Application

### Features

The Flask application provides a comprehensive player analytics dashboard with Steam-themed UI:

#### Header Section
- **Player Profile** (left side):
  - Steam avatar (120x120px) with blue border and glow effect
  - Username (displayed in large font)
  - Steam ID (below username)
- **Deadlock Logo** (center): Positioned at 45% vertical alignment
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

#### Chart 4: Player Percentile Distribution (Interactive Dropdown)
- **Type**: Normal distribution curve with dropdown selector (600px height)
- **Metrics Available**: Kills, Deaths, Assists, K/D, KDA, Net Worth, Souls Per Minute, Last Hits, Denies, Player Damage, Player Damage Per Minute
- **Description**:
  - Blue filled curve: Normal distribution
  - Green dashed line: Player's average
  - Gray dotted lines: ±1 standard deviation
- **Dynamic Title**: "{Metric} Probability Distribution Function" (e.g., "Kills Probability Distribution Function")
- **Important Note**: Shows player's personal variance across their own matches, NOT community distribution
- **Purpose**: Visualize performance consistency and variance
- **Layout**: Side-by-side with Kill/Death Locations chart

#### Chart 5: KDA Trend Over Time
- **Type**: Line chart with 7-day rolling average
- **Description**:
  - Bold lines: 7-day rolling average (Kills, Deaths, Assists)
  - Faint scatter points: Individual match performance (hover disabled)
  - Color coded: Kills (green), Deaths (red), Assists (blue)
- **Purpose**: Track skill progression and performance improvement over time
- **Title**: "KDA Trend Over Time (7-Day Rolling Average)"

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

#### `/analyze` (POST)
- Accepts `player_id` form parameter
- Fetches data from multiple API endpoints
- Processes data with pandas
- Generates Plotly visualizations
- Renders analytics dashboard

### Data Processing Pipeline

1. **Input Validation**: Validate player ID format (SteamID3)
2. **API Calls**: Fetch data from 7 endpoints:
   - `/v2/heroes` - Hero names and metadata
   - `/v1/players/{id}/match-history` - Match details
   - `/v1/players/steam-search?search_query={id}` - Steam profile data
   - `/v1/analytics/player-stats/metrics` - Player statistics with percentiles
   - `/v1/analytics/player-performance-curve` - Performance metrics over game time
   - `/v1/analytics/kill-death-stats` - Spatial kill/death coordinates
3. **Data Transformation**:
   - Convert to pandas DataFrames with `json_normalize()`
   - Filter steam-search results by matching account_id
   - Extract Steam username and full-size avatar
   - Join hero names with match data
   - Calculate win/loss from match_result
   - Apply 7-day rolling window for KDA trend
   - Sort by timestamp for chronological display
   - Generate normal distribution curves using scipy.stats
   - Filter metrics with std_dev < 0.01 to avoid flat curves
4. **Visualization**: Generate Plotly charts with PlotlyJSONEncoder
   - Apply Steam theme using JavaScript `applySteamTheme()` function
   - Dynamic chart titles based on dropdown selections
   - Preserve chart properties while applying colors
5. **Rendering**: Pass charts, summary stats, and Steam profile to HTML template

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
| `/v2/heroes` | Hero metadata | List of 53 heroes with names, images, stats |
| `/v1/players/{id}/match-history` | Match details | List of matches (21 columns per match) |
| `/v1/players/steam-search` | Steam profile lookup | List of matching profiles with username, avatars |
| `/v1/analytics/player-stats/metrics` | Player statistics | Averages, std dev, and percentiles for all metrics |
| `/v1/analytics/player-performance-curve` | Performance over game time | 12 time intervals with avg stats |
| `/v1/analytics/kill-death-stats` | Kill/death locations | List of map coordinates with counts |

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

## Future Enhancements

Potential features to add:

- [ ] Caching layer for API responses
- [ ] More chart types (radar charts, heatmaps)
- [ ] Compare multiple players
- [ ] Hero-specific performance analysis
- [ ] Item build analysis
- [ ] Match replay links
- [ ] Export data to CSV/JSON
- [ ] User authentication and saved dashboards
- [ ] Real-time data refresh
- [ ] Mobile-responsive design improvements

---

**Last Updated**: 2026-01-21
**Project Version**: 0.1.0
**Python Version**: 3.12+
