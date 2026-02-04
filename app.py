import json
import http.client
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from datetime import datetime, timedelta

app = Flask(__name__)

# Server-side cache for index page data (24 hour TTL)
_index_cache = {
    'rank_distribution': None,
    'leaderboard': None,
    'timestamp': None
}
CACHE_DURATION_HOURS = 24


def get_api_connection(player_id, hero_id=None):
    """Setup API connection configuration with player_id and optional hero_id"""
    # Build hero_ids query parameter if provided (for analytics endpoints only)
    hero_param = f"&hero_ids={hero_id}" if hero_id is not None else ""

    return {
        "data-api": {
            "http_client": http.client.HTTPSConnection("api.deadlock-api.com"),
            "endpoint": {
                # match_history: Don't filter (needed for top heroes calculation)
                "match_history": f"/v1/players/{player_id}/match-history?only_stored_history=false",
                # Analytics endpoints: Filter by hero_ids if provided
                "player_stats": f"/v1/analytics/player-stats/metrics?account_ids={player_id}{hero_param}",
                "player_scoreboard": f"/v1/analytics/scoreboards/players?account_ids={player_id}&sort_by=matches{hero_param}",
                "player_performance_curve": f"/v1/analytics/player-performance-curve?account_ids={player_id}&resolution=0{hero_param}",
                "kill_death_stats": f"/v1/analytics/kill-death-stats?account_ids={player_id}{hero_param}",
                "item_stats": f"/v1/analytics/item-stats?min_unix_timestamp=&min_matches=&account_ids={player_id}{hero_param}",
                "steam_search": f"/v1/players/steam-search?search_query={player_id}",
                # mmr_history: Don't filter (account-level stat, filtered client-side)
                "mmr_history": f"/v1/players/{player_id}/mmr-history",
                # hero_stats: Per-hero statistics (never filtered by hero_id)
                "hero_stats": f"/v1/players/{player_id}/hero-stats",
            }
        },
        "assets-api": {
            "http_client": http.client.HTTPSConnection("assets.deadlock-api.com"),
            "endpoint": {
                "heroes": "/v2/heroes",
                "items": "/v2/items",
                "ranks": "/v2/ranks",
                "images": "/v1/images",
            }
        },
        "headers": {
            'Accept': "*/*"
        }
    }


def get_match_api_connection(match_id):
    """Setup API connection configuration for match analysis"""
    return {
        "data-api": {
            "http_client": http.client.HTTPSConnection("api.deadlock-api.com"),
            "endpoint": {
                "match_metadata": f"/v1/matches/{match_id}/metadata",
            }
        },
        "assets-api": {
            "http_client": http.client.HTTPSConnection("assets.deadlock-api.com"),
            "endpoint": {
                "heroes": "/v2/heroes",
                "items": "/v2/items",
                "ranks": "/v2/ranks",
                "images": "/v1/images",
            }
        },
        "headers": {
            'Accept': "*/*"
        }
    }


def get_request_data(connection, api_selection, endpoint_addr):
    """Make HTTP request to API endpoint"""
    http_client = connection[api_selection]["http_client"]
    http_endpoint = connection[api_selection]["endpoint"][endpoint_addr]
    headers = connection["headers"]

    http_client.request("GET", http_endpoint, headers=headers)
    response = http_client.getresponse()
    raw_data = response.read()

    print(f"Request Status {response.status} | {http_endpoint}")

    if response.status != 200:
        print(f"Error: {raw_data[:200]}")
        return None

    data = json.loads(raw_data.decode("utf-8"))

    # Log data size for debugging
    if isinstance(data, list):
        print(f"  → Received {len(data)} items")
    elif isinstance(data, dict):
        print(f"  → Received dict with {len(data)} keys")

    return data


def format_match_history(df, df_heroes):
    """Format match history DataFrame with hero names"""
    if df.empty:
        return df

    # Merge with hero names
    df = pd.merge(df, df_heroes[["id", "name"]], left_on="hero_id", right_on="id", how="left")
    df = df.drop(columns=["id"]).rename(columns={"name": "hero_name"})  # Keep hero_id for filtering

    # Convert to timestamp
    df['start_ts'] = pd.to_datetime(df['start_time'], unit='s')

    return df


def add_filter_subtitle(fig, hero_name):
    """Add a subtitle annotation to a chart showing the active filter"""
    if hero_name:
        fig.add_annotation(
            text=f"<span style='color: #8f98a0'>Filter Applied: <span style='color: #66c0f4'>{hero_name}</span></span>",
            xref="paper", yref="paper",
            x=0, y=1.0,
            xanchor="left", yanchor="bottom",
            showarrow=False,
            font=dict(size=12),
            align="left"
        )
    return fig


def create_visualizations(player_id, hero_id=None):
    """Fetch data and create visualizations"""
    connection = get_api_connection(player_id, hero_id)

    # Fetch data from all endpoints
    try:
        hero_names = get_request_data(connection, "assets-api", "heroes")
        ranks_data = get_request_data(connection, "assets-api", "ranks")
        match_history = get_request_data(connection, "data-api", "match_history")
        player_stats = get_request_data(connection, "data-api", "player_stats")
        player_performance_curve = get_request_data(connection, "data-api", "player_performance_curve")
        kill_death_stats = get_request_data(connection, "data-api", "kill_death_stats")
        steam_profile = get_request_data(connection, "data-api", "steam_search")
        mmr_history = get_request_data(connection, "data-api", "mmr_history")
        item_stats = get_request_data(connection, "data-api", "item_stats")
        items_data = get_request_data(connection, "assets-api", "items")
        images_data = get_request_data(connection, "assets-api", "images")
        hero_stats = get_request_data(connection, "data-api", "hero_stats")

        if not match_history:
            return None, None, "Failed to fetch match history from API"

        # Convert to DataFrames
        df_match_history = pd.json_normalize(match_history)

        # Handle heroes endpoint gracefully (might return 500)
        if hero_names:
            df_heroes = pd.json_normalize(hero_names)
            df_match_history = format_match_history(df_match_history, df_heroes)
        else:
            # print("Warning: Heroes endpoint returned error. Using hero IDs instead of names.")
            # Add placeholder hero_name column using hero_id
            df_match_history['hero_name'] = df_match_history['hero_id'].astype(str)
            df_match_history['start_ts'] = pd.to_datetime(df_match_history['start_time'], unit='s')

        # Add result column before filtering (needed for top heroes calculation)
        if not df_match_history.empty and 'player_team' in df_match_history.columns and 'match_result' in df_match_history.columns:
            df_match_history['result'] = df_match_history.apply(
                lambda row: 'Win' if row['player_team'] == row['match_result'] else 'Loss', axis=1
            )

        # Save unfiltered copy for top heroes calculation (after adding result column)
        df_match_history_unfiltered = df_match_history.copy()

        # Apply hero filter if specified
        filtered_hero_name = None
        if hero_id is not None and not df_match_history.empty:
            # Capture hero name before filtering
            if 'hero_name' in df_match_history.columns:
                hero_match = df_match_history[df_match_history['hero_id'] == hero_id]
                if not hero_match.empty:
                    filtered_hero_name = hero_match.iloc[0]['hero_name']

            # Filter match history to selected hero
            df_match_history = df_match_history[df_match_history['hero_id'] == hero_id].copy()

            # print(f"Filtered to hero_id {hero_id} ({filtered_hero_name}): {len(df_match_history)} matches")

        df_player_performance_curve = pd.json_normalize(player_performance_curve) if player_performance_curve else pd.DataFrame()
        df_kill_death_stats = pd.json_normalize(kill_death_stats) if kill_death_stats else pd.DataFrame()
        df_player_stats = pd.json_normalize(player_stats) if player_stats else pd.DataFrame()

        # print(f"Analytics data received:")
        # print(f"  - Performance curve: {len(df_player_performance_curve)} rows")
        # print(f"  - Kill/Death stats: {len(df_kill_death_stats)} rows")
        # print(f"  - Player stats: {len(df_player_stats)} rows")

        if df_player_performance_curve.empty:
            pass
            # print("  WARNING: Performance curve data is EMPTY - chart will not display")
            # print(f"  Raw API response for performance curve: {player_performance_curve}")

        # Debug player stats when filtering
        if hero_id is not None and not df_player_stats.empty:
            # print(f"\nDEBUG: Player stats raw response sample:")
            if isinstance(player_stats, dict):
                pass
                # print(f"  kills.avg: {player_stats.get('kills', {}).get('avg', 'N/A')}")
                # print(f"  deaths.avg: {player_stats.get('deaths', {}).get('avg', 'N/A')}")
                # print(f"  First 3 keys: {list(player_stats.keys())[:3]}")
            # print(f"  DataFrame kills.avg value: {df_player_stats['kills.avg'].iloc[0] if 'kills.avg' in df_player_stats.columns else 'Column not found'}")
            # print(f"  DataFrame kills.avg type: {type(df_player_stats['kills.avg'].iloc[0]) if 'kills.avg' in df_player_stats.columns else 'N/A'}")

        charts = {}

        # Chart 1: Win/Loss over time
        if not df_match_history.empty and 'result' in df_match_history.columns:
            fig1 = px.histogram(df_match_history, x='start_ts', color='result',
                               title='Number of Matches Played',
                               labels={'start_ts': 'Date', 'count': 'Number of Matches'},
                               color_discrete_map={'Win': '#22c55e', 'Loss': '#ef4444'},
                               nbins=30)
            fig1.update_layout(bargap=0.1)
            fig1 = add_filter_subtitle(fig1, filtered_hero_name)
            charts['win_loss_timeline'] = json.dumps(fig1, cls=PlotlyJSONEncoder)
        else:
            # print("Win/Loss timeline chart NOT created - showing insufficient data message")
            # Create placeholder chart with message
            fig1 = go.Figure()
            fig1.add_annotation(
                text="Insufficient match data to present visualisation",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=16, color="#8f98a0")
            )
            fig1.update_layout(
                title='Number of Matches Played',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=400
            )
            fig1 = add_filter_subtitle(fig1, filtered_hero_name)
            charts['win_loss_timeline'] = json.dumps(fig1, cls=PlotlyJSONEncoder)

        # Chart 2: Performance Curve with dropdown selector
        if not df_player_performance_curve.empty and 'game_time' in df_player_performance_curve.columns and len(df_player_performance_curve) > 0:
            # print(f"Performance Curve DataFrame shape: {df_player_performance_curve.shape}")
            # print(f"Performance Curve columns: {df_player_performance_curve.columns.tolist()}")

            # Convert game time from seconds to minutes
            df_player_performance_curve['game_time_min'] = df_player_performance_curve['game_time'] / 60

            # Define available metrics
            metrics = []
            if 'net_worth_avg' in df_player_performance_curve.columns:
                metrics.append({
                    'name': 'Net Worth',
                    'column': 'net_worth_avg',
                    'color': '#f59e0b',
                    'yaxis_title': 'Net Worth (Souls)'
                })
            if 'kills_avg' in df_player_performance_curve.columns:
                metrics.append({
                    'name': 'Kills',
                    'column': 'kills_avg',
                    'color': '#22c55e',
                    'yaxis_title': 'Average Kills'
                })
            if 'deaths_avg' in df_player_performance_curve.columns:
                metrics.append({
                    'name': 'Deaths',
                    'column': 'deaths_avg',
                    'color': '#ef4444',
                    'yaxis_title': 'Average Deaths'
                })
            if 'assists_avg' in df_player_performance_curve.columns:
                metrics.append({
                    'name': 'Assists',
                    'column': 'assists_avg',
                    'color': '#3b82f6',
                    'yaxis_title': 'Average Assists'
                })

            # print(f"Available metrics: {[m['name'] for m in metrics]}")

            # Create figure with traces for each metric
            fig3 = go.Figure()

            for i, metric in enumerate(metrics):
                # print(f"Adding trace {i}: {metric['name']}, visible={i == 0}")
                visible_state = True if i == 0 else False

                fig3.add_trace(go.Scatter(
                    x=df_player_performance_curve['game_time_min'].tolist(),
                    y=df_player_performance_curve[metric['column']].tolist(),
                    mode='lines+markers',
                    name=metric['name'],
                    line=dict(color=metric['color'], width=3),
                    marker=dict(size=8),
                    visible=visible_state,
                    hovertemplate=metric['name'] + ': %{y:.2f}<extra></extra>'
                ))

            # Create dropdown menu buttons
            dropdown_buttons = []
            for i, metric in enumerate(metrics):
                # Create visibility array (True for selected trace, False for others)
                visible = [j == i for j in range(len(metrics))]

                dropdown_buttons.append({
                    'label': metric['name'],
                    'method': 'update',
                    'args': [
                        {'visible': visible},  # Update trace visibility
                        {
                            'yaxis.title.text': metric['yaxis_title'],
                            'title.text': f"Average {metric['name']} over Game Duration"  # Dynamic title
                        }
                    ]
                })

            # print(f"Created {len(dropdown_buttons)} dropdown buttons")

            # Update layout with dropdown
            fig3.update_layout(
                title=f"Average {metrics[0]['name']} over Game Duration" if metrics else 'Player Performance Over Game Time',
                xaxis_title='Game Time (minutes)',
                yaxis=dict(title=metrics[0]['yaxis_title'] if metrics else 'Value'),
                hovermode='x unified',
                updatemenus=[{
                    'buttons': dropdown_buttons,
                    'direction': 'down',
                    'showactive': True,
                    'x': 1.0,
                    'xanchor': 'right',
                    'y': 1.15,
                    'yanchor': 'top',
                    'bgcolor': 'white',
                    'bordercolor': '#ccc',
                    'borderwidth': 1,
                    'font': dict(size=12, color='#333333')
                }],
                showlegend=False
            )

            # print(f"Performance curve chart created with {len(fig3.data)} traces")
            fig3 = add_filter_subtitle(fig3, filtered_hero_name)
            charts['performance_curve'] = json.dumps(fig3, cls=PlotlyJSONEncoder)
        else:
            # print("Performance curve chart NOT created - showing insufficient data message")
            # Create placeholder chart with message
            fig3 = go.Figure()
            fig3.add_annotation(
                text="Insufficient match data to present visualisation",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=16, color="#8f98a0")
            )
            fig3.update_layout(
                title='Average Performance Over Game Time',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=400
            )
            fig3 = add_filter_subtitle(fig3, filtered_hero_name)
            charts['performance_curve'] = json.dumps(fig3, cls=PlotlyJSONEncoder)

        # Chart 4: Kill/Death Location Scatter Plot
        if not df_kill_death_stats.empty and 'position_x' in df_kill_death_stats.columns:
            # print(f"Kill/Death Stats DataFrame shape: {df_kill_death_stats.shape}")
            # print(f"Kills > 0 count: {(df_kill_death_stats['kills'] > 0).sum()}")
            # print(f"Deaths > 0 count: {(df_kill_death_stats['deaths'] > 0).sum()}")

            # Filter for kills and deaths
            df_kills = df_kill_death_stats[df_kill_death_stats['kills'] > 0].copy()
            df_deaths = df_kill_death_stats[df_kill_death_stats['deaths'] > 0].copy()

            # print(f"Creating chart with {len(df_kills)} kill locations and {len(df_deaths)} death locations")

            # Create scatter plot
            fig4 = go.Figure()

            # Add kill markers
            if not df_kills.empty:
                fig4.add_trace(go.Scattergl(  # Use Scattergl for better performance with many points
                    x=df_kills['position_x'].tolist(),
                    y=df_kills['position_y'].tolist(),
                    mode='markers',
                    name=f'Kills ({len(df_kills)})',
                    marker=dict(
                        size=10,
                        color='#22c55e',
                        opacity=0.8,
                        line=dict(width=1, color='#16a34a')
                    ),
                    text=['Kill' for _ in range(len(df_kills))],
                    hovertemplate='<b>Kill</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
                ))

            # Add death markers
            if not df_deaths.empty:
                fig4.add_trace(go.Scattergl(  # Use Scattergl for better performance
                    x=df_deaths['position_x'].tolist(),
                    y=df_deaths['position_y'].tolist(),
                    mode='markers',
                    name=f'Deaths ({len(df_deaths)})',
                    marker=dict(
                        size=10,
                        color='#ef4444',
                        opacity=0.8,
                        line=dict(width=1, color='#dc2626')
                    ),
                    text=['Death' for _ in range(len(df_deaths))],
                    hovertemplate='<b>Death</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
                ))

            # Update layout with minimap background
            fig4.update_layout(
                title='Kill and Death Locations',
                xaxis=dict(
                    range=[-10000, 10000],
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    visible=False
                ),
                yaxis=dict(
                    range=[-10000, 10000],
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    scaleanchor='x',
                    scaleratio=1,
                    visible=False
                ),
                images=[
                    dict(
                        source='/static/img/minimap.png',
                        xref='x',
                        yref='y',
                        x=-10000,
                        y=10000,
                        sizex=20000,
                        sizey=20000,
                        sizing='stretch',
                        opacity=1,
                        layer='below'
                    )
                ],
                plot_bgcolor='#1a1a2e',
                hovermode='closest',
                showlegend=True,
                legend=dict(
                    x=0.98,
                    y=0.98,
                    xanchor='right',
                    yanchor='top',
                    bgcolor='rgba(27, 40, 56, 0.9)',
                    bordercolor='#3d4e5c',
                    borderwidth=1,
                    font=dict(color='#c7d5e0')
                ),
                height=600,
                width=600,
                margin=dict(l=10, r=10, t=50, b=10)
            )

            # print(f"Chart created with {len(fig4.data)} traces")
            fig4 = add_filter_subtitle(fig4, filtered_hero_name)
            charts['kd_stats'] = json.dumps(fig4, cls=PlotlyJSONEncoder)
        else:
            # print("Kill/Death location chart NOT created - showing insufficient data message")
            # Create placeholder chart with message
            fig4 = go.Figure()
            fig4.add_annotation(
                text="Insufficient match data to present visualisation",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=16, color="#8f98a0")
            )
            fig4.update_layout(
                title='Kill and Death Locations',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=600,
                width=600
            )
            fig4 = add_filter_subtitle(fig4, filtered_hero_name)
            charts['kd_stats'] = json.dumps(fig4, cls=PlotlyJSONEncoder)

        # Chart 4.5: Community Percentile Distribution
        if not df_player_stats.empty:
            # print(f"Player stats shape: {df_player_stats.shape}")

            # Define available metrics for distribution
            metrics = []

            # All available metrics with readable names
            metric_configs = [
                ('kills', 'Kills'),
                ('deaths', 'Deaths'),
                ('assists', 'Assists'),
                ('kd', 'K/D Ratio'),
                ('kda', 'KDA Ratio'),
                ('net_worth', 'Net Worth (Souls)'),
                ('net_worth_per_min', 'Souls Per Minute'),
                ('last_hits', 'Last Hits'),
                ('denies', 'Denies'),
                ('player_damage', 'Player Damage'),
                ('player_damage_per_min', 'Player Damage Per Minute'),
                ('player_damage_taken_per_min', 'Damage Taken Per Minute'),
                ('player_healing', 'Player Healing'),
                ('healing', 'Total Healing'),
                ('boss_damage', 'Boss Damage'),
                ('neutral_damage', 'Neutral Damage'),
                ('creep_damage', 'Creep Damage'),
                ('accuracy', 'Accuracy (%)'),
                ('crit_shot_rate', 'Critical Hit Rate'),
                ('headshot_rate', 'Headshot Rate'),
                ('hero_bullets_hit', 'Hero Bullets Hit'),
                ('hero_bullets_hit_crit', 'Hero Crit Bullets'),
                ('level_at_first_death', 'Level at First Death'),
                ('deaths_to_neutrals', 'Deaths to Neutrals'),
            ]

            # print(f"Checking {len(metric_configs)} metrics for distribution chart")
            for metric_key, metric_name in metric_configs:
                # Check if we have percentile data to construct community distribution
                if f'{metric_key}.percentile50' in df_player_stats.columns and f'{metric_key}.avg' in df_player_stats.columns:
                    # Check if avg is valid
                    avg_val = df_player_stats[f'{metric_key}.avg'].iloc[0]
                    if avg_val is None or pd.isna(avg_val):
                        # print(f"Skipping {metric_key}: avg is None/NaN")
                        continue

                    # Only include metrics with reasonable percentile spread
                    p25_val = df_player_stats[f'{metric_key}.percentile25'].iloc[0] if f'{metric_key}.percentile25' in df_player_stats.columns else None
                    p75_val = df_player_stats[f'{metric_key}.percentile75'].iloc[0] if f'{metric_key}.percentile75' in df_player_stats.columns else None

                    # Convert to float only if not None
                    p25 = float(p25_val) if p25_val is not None and pd.notna(p25_val) else None
                    p75 = float(p75_val) if p75_val is not None and pd.notna(p75_val) else None

                    # Include if we have valid percentile spread OR if it's a core metric (kills/deaths/assists)
                    core_metrics = ['kills', 'deaths', 'assists']
                    has_valid_spread = p25 is not None and p75 is not None and (p75 - p25) > 0.01
                    is_core_metric = metric_key in core_metrics and p25 is not None and p75 is not None

                    if has_valid_spread or is_core_metric:
                        metrics.append({
                            'key': metric_key,
                            'name': metric_name
                        })
                        try:
                            pass
                            # print(f"✓ Including metric {metric_key}: avg={float(avg_val):.2f}, p25={p25:.2f}, p75={p75:.2f}, spread={p75-p25:.2f}")
                        except:
                            pass
                            # print(f"✓ Including metric {metric_key}")
                    else:
                        spread = (p75 - p25) if (p25 is not None and p75 is not None) else None
                        # print(f"✗ Skipping {metric_key}: p25={p25}, p75={p75}, spread={spread}")

            # print(f"Total valid metrics for distribution chart: {len(metrics)}")

            # Check if we have at least one metric with actual variance (non-degenerate distribution)
            has_valid_distribution = False
            for metric in metrics:
                metric_key = metric['key']
                p25_val = df_player_stats[f'{metric_key}.percentile25'].iloc[0] if f'{metric_key}.percentile25' in df_player_stats.columns else None
                p75_val = df_player_stats[f'{metric_key}.percentile75'].iloc[0] if f'{metric_key}.percentile75' in df_player_stats.columns else None

                if p25_val is not None and p75_val is not None:
                    p25 = float(p25_val) if pd.notna(p25_val) else None
                    p75 = float(p75_val) if pd.notna(p75_val) else None
                    if p25 is not None and p75 is not None and abs(p75 - p25) > 0.01:
                        has_valid_distribution = True
                        break

            if not has_valid_distribution:
                # print(f"WARNING: All metrics have degenerate distributions (no variance).")
                metrics = []  # Clear metrics to skip chart generation

            if len(metrics) == 0:
                # print(f"No valid metrics found for distribution chart - showing insufficient data message")
                # Create placeholder chart with message
                fig4_5 = go.Figure()
                fig4_5.add_annotation(
                    text="Insufficient match data to present visualisation",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor="center", yanchor="middle",
                    showarrow=False,
                    font=dict(size=16, color="#8f98a0")
                )
                fig4_5.update_layout(
                    title='Performance Compared To Community Distribution',
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=600
                )
                fig4_5 = add_filter_subtitle(fig4_5, filtered_hero_name)
                charts['percentile_dist'] = json.dumps(fig4_5, cls=PlotlyJSONEncoder)

            elif metrics:
                fig4_5 = go.Figure()

                # Create traces for each metric
                for i, metric in enumerate(metrics):
                    metric_key = metric['key']

                    # Get player's average
                    avg_col_name = f'{metric_key}.avg'
                    if avg_col_name in df_player_stats.columns:
                        avg_val = df_player_stats[avg_col_name].iloc[0]
                        player_avg = float(avg_val) if avg_val is not None and pd.notna(avg_val) else 0
                    else:
                        player_avg = 0

                    # Get community percentiles directly from API
                    percentiles = {}
                    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
                        col_name = f'{metric_key}.percentile{p}'
                        if col_name in df_player_stats.columns:
                            perc_val = df_player_stats[col_name].iloc[0]
                            if perc_val is not None and pd.notna(perc_val):
                                percentiles[p] = float(perc_val)

                    # Use P50 (median) as community mean
                    community_mean = percentiles.get(50, player_avg)

                    # Estimate std from IQR for curve visualization
                    if 25 in percentiles and 75 in percentiles:
                        iqr = percentiles[75] - percentiles[25]
                        community_std = iqr / 1.35
                    elif 10 in percentiles and 90 in percentiles:
                        p_range = percentiles[90] - percentiles[10]
                        community_std = p_range / 2.56
                    else:
                        community_std = (percentiles.get(99, community_mean) - percentiles.get(1, community_mean)) / 6

                    # Use actual percentile range for x-axis
                    if percentiles:
                        min_val = percentiles.get(1, community_mean - 3*community_std)
                        max_val = percentiles.get(99, community_mean + 3*community_std)
                        x_range = np.linspace(min_val * 0.9, max_val * 1.1, 300)
                    else:
                        x_range = np.linspace(community_mean - 4*community_std, community_mean + 4*community_std, 300)

                    y_range = stats.norm.pdf(x_range, community_mean, community_std)
                    y_max = float(np.max(y_range))

                    # Print all percentile values for verification
                    # print(f"\n{metric_key}:")
                    # print(f"  Player avg: {player_avg:.2f}")
                    # print(f"  Community percentiles (from API): {percentiles}")

                    # Calculate player's percentile rank by interpolation
                    player_percentile = 50  # Default to median
                    if percentiles and player_avg > 0:
                        sorted_percentiles = sorted(percentiles.items())

                        # Find where player falls in percentile range
                        if player_avg <= sorted_percentiles[0][1]:
                            # Below P1
                            player_percentile = 1
                        elif player_avg >= sorted_percentiles[-1][1]:
                            # Above P99
                            player_percentile = 99
                        else:
                            # Interpolate between percentiles
                            for j in range(len(sorted_percentiles) - 1):
                                p1, val1 = sorted_percentiles[j]
                                p2, val2 = sorted_percentiles[j + 1]

                                if val1 <= player_avg <= val2:
                                    # Linear interpolation
                                    if val2 != val1:
                                        player_percentile = p1 + (p2 - p1) * (player_avg - val1) / (val2 - val1)
                                    else:
                                        player_percentile = (p1 + p2) / 2
                                    break

                    # Store percentile rank in metric for annotation
                    metric['player_percentile'] = player_percentile

                    # Create annotation text
                    if player_percentile >= 50:
                        # Top X% (e.g., 75th percentile = Top 25%)
                        top_pct = 100 - player_percentile
                        metric['rank_text'] = f"Top {top_pct:.1f}%"
                    else:
                        # Bottom X% (e.g., 25th percentile = Bottom 25%)
                        metric['rank_text'] = f"Bottom {player_percentile:.1f}%"

                    # Calculate color based on percentile
                    # Green for above average (50-100), Red for below average (0-50)
                    if player_percentile >= 50:
                        # Above average: interpolate from yellow (50th) to bright green (100th)
                        # 50th percentile = #cccc00 (yellow)
                        # 100th percentile = #22ff22 (bright green)
                        ratio = (player_percentile - 50) / 50  # 0 to 1
                        r = int(0xcc - (0xcc - 0x22) * ratio)
                        g = int(0xcc + (0xff - 0xcc) * ratio)
                        b = int(0x00 + (0x22 - 0x00) * ratio)
                        metric['rank_color'] = f'#{r:02x}{g:02x}{b:02x}'
                    else:
                        # Below average: interpolate from bright red (0th) to yellow (50th)
                        # 0th percentile = #ff0000 (bright red)
                        # 50th percentile = #cccc00 (yellow)
                        ratio = player_percentile / 50  # 0 to 1
                        r = int(0xff - (0xff - 0xcc) * ratio)
                        g = int(0x00 + (0xcc - 0x00) * ratio)
                        b = 0x00
                        metric['rank_color'] = f'#{r:02x}{g:02x}{b:02x}'

                    # print(f"  Player percentile: {player_percentile:.1f} ({metric['rank_text']}, color: {metric['rank_color']})")

                    # Add distribution curve (community)
                    fig4_5.add_trace(go.Scatter(
                        x=x_range.tolist(),
                        y=y_range.tolist(),
                        mode='lines',
                        name='Community Distribution',
                        line=dict(color='#66c0f4', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(102, 192, 244, 0.2)',
                        visible=(i == 0),
                        hovertemplate='Value: %{x:.2f}<br>Density: %{y:.6f}<extra></extra>',
                        showlegend=True
                    ))

                    # Add ALL percentile markers (vertical lines)
                    percentile_colors = {
                        1: '#cc0000', 5: '#ff3333', 10: '#ff6666',
                        25: '#ff9944', 50: '#ffcc00',
                        75: '#99dd66', 90: '#66cc66', 95: '#44bb44', 99: '#22aa22'
                    }

                    # Show selected percentiles (P10, P25, P50, P75, P90)
                    for p, value in sorted(percentiles.items()):
                        # Skip P1, P5, P95, P99
                        if p not in [10, 25, 50, 75, 90]:
                            continue

                        color = percentile_colors.get(p, '#8f98a0')
                        # Vary line width - thicker for quartiles, thinner for extremes
                        if p == 50:
                            width = 3
                        elif p in [25, 75]:
                            width = 2.5
                        elif p in [10, 90]:
                            width = 2
                        else:
                            width = 1.5

                        fig4_5.add_trace(go.Scatter(
                            x=[value, value],
                            y=[0, y_max * 0.95],
                            mode='lines',
                            name=f'P{p}',
                            line=dict(color=color, width=width, dash='dot'),
                            visible=(i == 0),
                            showlegend=True,
                            hovertemplate=f'P{p}: {value:.2f}<extra></extra>'
                        ))

                    # Add player's average as bold line
                    fig4_5.add_trace(go.Scatter(
                        x=[player_avg, player_avg],
                        y=[0, y_max * 1.1],
                        mode='lines',
                        name='Your Average',
                        line=dict(color='#22ff22', width=5, dash='solid'),
                        visible=(i == 0),
                        showlegend=True,
                        hovertemplate=f'Your Avg: {player_avg:.2f}<extra></extra>'
                    ))

                # Create dropdown buttons
                dropdown_buttons = []
                for i, metric in enumerate(metrics):
                    # Count traces per metric: 1 curve + 5 percentiles (P10, P25, P50, P75, P90) + 1 player avg = 7 traces
                    traces_per_metric = 7
                    visible = [False] * (len(metrics) * traces_per_metric)

                    # Make all traces for this metric visible
                    for j in range(traces_per_metric):
                        visible[i * traces_per_metric + j] = True

                    dropdown_buttons.append({
                        'label': metric['name'],
                        'method': 'update',
                        'args': [
                            {'visible': visible},
                            {
                                'xaxis.title.text': metric['name'],
                                'yaxis.title.text': 'Probability Density',
                                'title.text': f"{metric['name']} Compared To Community Distribution",
                                'annotations[0].text': metric['rank_text'],
                                'annotations[0].font.color': metric['rank_color'],
                                'annotations[0].bordercolor': metric['rank_color']
                            }
                        ]
                    })

                # Update layout
                fig4_5.update_layout(
                    title=f"{metrics[0]['name']} Compared To Community Distribution",
                    xaxis_title=metrics[0]['name'],
                    yaxis_title='Probability Density',
                    xaxis=dict(
                        showgrid=True,
                        zeroline=True
                    ),
                    yaxis=dict(
                        showgrid=True,
                        zeroline=True,
                        rangemode='tozero'
                    ),
                    hovermode='x unified',
                    updatemenus=[{
                        'buttons': dropdown_buttons,
                        'direction': 'down',
                        'showactive': True,
                        'x': 1.0,
                        'xanchor': 'right',
                        'y': 1.10,
                        'yanchor': 'top',
                        'bgcolor': 'white',
                        'bordercolor': '#ccc',
                        'borderwidth': 1,
                        'font': dict(size=12, color='#333333')
                    }],
                    showlegend=True,
                    legend=dict(
                        orientation='v',
                        yanchor='top',
                        y=0.98,
                        xanchor='left',
                        x=0.02,
                        bgcolor='rgba(27, 40, 56, 0.9)',
                        bordercolor='#3d4e5c',
                        borderwidth=1
                    ),
                    annotations=[
                        dict(
                            text=metrics[0]['rank_text'],
                            xref='paper',
                            yref='paper',
                            x=0.98,
                            y=0.98,
                            xanchor='right',
                            yanchor='top',
                            showarrow=False,
                            font=dict(size=16, color=metrics[0]['rank_color'], family='Motiva Sans, Arial'),
                            bgcolor='rgba(27, 40, 56, 0.9)',
                            bordercolor=metrics[0]['rank_color'],
                            borderwidth=2,
                            borderpad=10
                        )
                    ],
                    height=600
                )

                # print(f"Distribution chart created with {len(fig4_5.data)} traces")
                fig4_5 = add_filter_subtitle(fig4_5, filtered_hero_name)
                charts['percentile_dist'] = json.dumps(fig4_5, cls=PlotlyJSONEncoder)

        # Chart 5: Match Statistics Over Time with Weekly Rolling Average
        if not df_match_history.empty:
            # print(f"Match history columns: {df_match_history.columns.tolist()}")
            # print(f"Match history shape: {df_match_history.shape}")

            # Sort by timestamp to get chronological order (oldest to newest)
            df_match_sorted = df_match_history.sort_values('start_ts').copy()

            # Set timestamp as index for time-based rolling window
            df_match_sorted = df_match_sorted.set_index('start_ts')

            # Calculate 7-day rolling average
            window = '7D'  # 7-day window
            df_match_sorted['kills_avg'] = df_match_sorted['player_kills'].rolling(window=window, min_periods=1).mean()
            df_match_sorted['deaths_avg'] = df_match_sorted['player_deaths'].rolling(window=window, min_periods=1).mean()
            df_match_sorted['assists_avg'] = df_match_sorted['player_assists'].rolling(window=window, min_periods=1).mean()

            # Reset index to get timestamp back as a column
            df_match_sorted = df_match_sorted.reset_index()

            # print(f"Rolling average calculated for {len(df_match_sorted)} matches")

            fig6 = go.Figure()

            # Add rolling average traces
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['kills_avg'].tolist(),
                mode='lines',
                name='Kills (7-day avg)',
                line=dict(color='#22c55e', width=3),
                hovertemplate='Kills: %{y:.1f}<extra></extra>'
            ))
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['deaths_avg'].tolist(),
                mode='lines',
                name='Deaths (7-day avg)',
                line=dict(color='#ef4444', width=3),
                hovertemplate='Deaths: %{y:.1f}<extra></extra>'
            ))
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['assists_avg'].tolist(),
                mode='lines',
                name='Assists (7-day avg)',
                line=dict(color='#3b82f6', width=3),
                hovertemplate='Assists: %{y:.1f}<extra></extra>'
            ))

            # Add raw data as faint traces (optional - shows individual match performance)
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['player_kills'].tolist(),
                mode='markers',
                name='Kills (per match)',
                marker=dict(color='#22c55e', size=4, opacity=0.3),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['player_deaths'].tolist(),
                mode='markers',
                name='Deaths (per match)',
                marker=dict(color='#ef4444', size=4, opacity=0.3),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig6.add_trace(go.Scatter(
                x=df_match_sorted['start_ts'].tolist(),
                y=df_match_sorted['player_assists'].tolist(),
                mode='markers',
                name='Assists (per match)',
                marker=dict(color='#3b82f6', size=4, opacity=0.3),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig6.update_layout(
                title='KDA Trend Over Time (7-Day Rolling Average)',
                xaxis_title='Date',
                yaxis_title='Average Count',
                hovermode='x',
                showlegend=True,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                )
            )

            # print(f"KDA trend chart created with {len(fig6.data)} traces")
            if len(fig6.data) > 0:
                pass
                # print(f"First trace has {len(fig6.data[0].x)} data points")
            fig6 = add_filter_subtitle(fig6, filtered_hero_name)
            charts['kda_trend'] = json.dumps(fig6, cls=PlotlyJSONEncoder)
        else:
            # print("KDA trend chart NOT created - showing insufficient data message")
            # Create placeholder chart with message
            fig6 = go.Figure()
            fig6.add_annotation(
                text="Insufficient match data to present visualisation",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=16, color="#8f98a0")
            )
            fig6.update_layout(
                title='KDA Trend Over Time (7-Day Rolling Average)',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=400
            )
            fig6 = add_filter_subtitle(fig6, filtered_hero_name)
            charts['kda_trend'] = json.dumps(fig6, cls=PlotlyJSONEncoder)

        # Chart 6: Rank Progression Over Time
        if mmr_history and len(mmr_history) > 0 and ranks_data:
            # print(f"Rank history records: {len(mmr_history)}")

            df_mmr = pd.json_normalize(mmr_history)
            df_mmr['start_ts'] = pd.to_datetime(df_mmr['start_time'], unit='s')
            df_mmr = df_mmr.sort_values('start_ts')

            # Create rank name mapping from ranks_data
            rank_mapping = {}
            rank_badge_mapping = {}

            # print(f"Sample rank data structure: {ranks_data[0] if ranks_data else 'None'}")

            for rank in ranks_data:
                tier = rank.get('tier')
                rank_name = rank.get('name', f'Rank {tier}')
                rank_mapping[tier] = rank_name

                # Get images - check if it's a dict or needs normalization
                images = rank.get('images', {})
                # print(f"Tier {tier} ({rank_name}) images keys: {images.keys() if isinstance(images, dict) else 'not a dict'}")

                # Look for 'lg_webp' or webp versions of large badge image (matching index page pattern)
                badge_url = ''
                if isinstance(images, dict):
                    # Prefer webp, then fallback to png
                    for key in ['lg_webp', 'large_webp', 'badge_lg_webp', 'lg', 'large', 'badge_lg']:
                        if key in images and images[key]:
                            badge_url = images[key]
                            break

                rank_badge_mapping[tier] = badge_url
                # print(f"Tier {tier} badge URL: {badge_url}")

            # print(f"Rank mapping: {rank_mapping}")

            # Add rank names to dataframe
            df_mmr['rank_name'] = df_mmr['division'].map(rank_mapping)
            df_mmr['rank_badge'] = df_mmr['division'].map(rank_badge_mapping)

            # Create precise rank value: division + (division_tier / 10)
            # This gives us 1.1, 1.2, 1.3 ... 1.6 for Initiate tiers 1-6
            df_mmr['precise_rank'] = df_mmr.apply(
                lambda row: row['division'] + (row.get('division_tier', 0) / 10.0) if pd.notna(row.get('division_tier')) else row['division'],
                axis=1
            )

            # print(f"Precise rank range: {df_mmr['precise_rank'].min():.2f} - {df_mmr['precise_rank'].max():.2f}")
            # print(f"Player score (MMR) range: {df_mmr['player_score'].min()} - {df_mmr['player_score'].max()}")

            # Set timestamp as index for rolling window
            df_mmr = df_mmr.set_index('start_ts')

            # Calculate 7-day rolling average for player_score (MMR)
            window = '7D'
            df_mmr['mmr_avg'] = df_mmr['player_score'].rolling(window=window, min_periods=1).mean()

            # Reset index
            df_mmr = df_mmr.reset_index()

            # Create combined rank label with division_tier
            df_mmr['full_rank'] = df_mmr.apply(
                lambda row: f"{row['rank_name']}" + (f" {row['division_tier']}" if pd.notna(row.get('division_tier')) and row.get('division_tier', 0) > 0 else ""),
                axis=1
            )

            # print(f"Division range: {df_mmr['division'].min()} - {df_mmr['division'].max()}")

            fig7 = go.Figure()

            # Add 7-day rolling average MMR line (bold)
            fig7.add_trace(go.Scatter(
                x=df_mmr['start_ts'].tolist(),
                y=df_mmr['mmr_avg'].tolist(),
                mode='lines',
                name='MMR (7-day avg)',
                line=dict(color='#66c0f4', width=3),
                hovertemplate='<b>MMR (7-day avg): %{y:.0f}</b><br>Date: %{x}<extra></extra>'
            ))

            # Add raw MMR points (faint markers) - using player_score
            fig7.add_trace(go.Scatter(
                x=df_mmr['start_ts'].tolist(),
                y=df_mmr['player_score'].tolist(),
                mode='markers',
                name='MMR (per match)',
                marker=dict(size=4, color='#66c0f4', opacity=0.3),
                customdata=df_mmr[['full_rank', 'player_score']].values.tolist(),
                hovertemplate='<b>%{customdata[0]}</b><br>MMR: %{customdata[1]:.0f}<br>Date: %{x}<extra></extra>',
                showlegend=False
            ))

            # Calculate average MMR for each division to position badges
            division_mmr_mapping = {}
            unique_divisions = sorted(df_mmr['division'].unique())

            for division in unique_divisions:
                # Get average MMR for this division
                division_data = df_mmr[df_mmr['division'] == division]
                avg_mmr = division_data['player_score'].mean()
                division_mmr_mapping[division] = avg_mmr
                # print(f"Division {division} ({rank_mapping.get(division)}): Avg MMR = {avg_mmr:.0f}")

            # Build rank badge images for y-axis using layout.images
            images = []

            # print(f"Building rank badges for {len(unique_divisions)} divisions")

            for division in unique_divisions:
                badge_url = rank_badge_mapping.get(division)
                rank_name = rank_mapping.get(division, f'Rank {division}')
                mmr_position = division_mmr_mapping.get(division, 0)

                # print(f"Division {division}: {rank_name}, Badge URL: {badge_url}, MMR position: {mmr_position:.0f}")

                if badge_url and mmr_position > 0:
                    # Add badge image positioned at average MMR for this division
                    images.append(dict(
                        source=badge_url,
                        xref="paper",
                        yref="y",
                        x=-0.01,  # Moved inward (was -0.03)
                        y=mmr_position,  # Position at average MMR for this division
                        sizex=0.05,  # Same size as sm badges
                        sizey=200,  # Same size as sm badges
                        xanchor="right",
                        yanchor="middle",
                        layer="above"
                    ))
                else:
                    pass
                    # print(f"WARNING: No badge URL or MMR position for division {division}")

            # print(f"Created {len(images)} badge images")
            if images:
                pass
                # print(f"First badge: {images[0]}")

            # Y-axis range should accommodate player_score (MMR) values
            y_min = df_mmr['player_score'].min()
            y_max = df_mmr['player_score'].max()

            # Add padding to y-axis range (10% below min, 10% above max)
            y_padding = (y_max - y_min) * 0.1 if (y_max > y_min) else 50
            y_range_min = max(0, y_min - y_padding)  # Don't go below 0
            y_range_max = y_max + y_padding

            fig7.update_layout(
                title='MMR Progression Over Time (7-Day Rolling Average)',
                xaxis_title='Date',
                yaxis=dict(
                    title=dict(
                        text='MMR (Player Score)',
                        standoff=35  # Push label further from axis
                    ),
                    gridcolor='#3d4e5c',
                    tickfont=dict(size=10, color='#c7d5e0'),
                    range=[y_range_min, y_range_max]  # Add padding to range
                ),
                images=images if images else [],
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                height=500,
                margin=dict(l=160)  # Increased left margin (was 140)
            )

            # print(f"MMR progression chart created with {len(unique_divisions)} rank tiers and {len(images)} badge images")
            # print(f"First badge image config: {images[0] if images else 'None'}")
            charts['mmr_history'] = json.dumps(fig7, cls=PlotlyJSONEncoder)

        # Chart 8: Hero Statistics Heatmap
        if hero_stats and len(hero_stats) > 0 and hero_names:
            # print(f"Hero stats records: {len(hero_stats)}")

            # Convert to DataFrame
            df_hero_stats = pd.json_normalize(hero_stats)
            # print(f"Hero stats columns: {df_hero_stats.columns.tolist()}")

            # Merge with hero names and icons
            df_hero_stats = pd.merge(
                df_hero_stats,
                df_heroes[['id', 'name', 'images.icon_hero_card']],
                left_on='hero_id',
                right_on='id',
                how='left'
            )

            # Sort by matches played (descending) - default sort
            df_hero_stats = df_hero_stats.sort_values('matches_played', ascending=False)

            # Filter to only heroes with matches > 0
            df_hero_stats = df_hero_stats[df_hero_stats['matches_played'] > 0]

            # Calculate win rate and convert percentage metrics
            df_hero_stats['win_rate'] = (df_hero_stats['wins'] / df_hero_stats['matches_played'] * 100).round(2)
            if 'accuracy' in df_hero_stats.columns:
                df_hero_stats['accuracy'] = (df_hero_stats['accuracy'] * 100).round(2)
            if 'crit_shot_rate' in df_hero_stats.columns:
                df_hero_stats['crit_shot_rate'] = (df_hero_stats['crit_shot_rate'] * 100).round(2)

            # Select metrics: any column ending with per_match, per_min, per_soul, plus win_rate, accuracy, crit_shot_rate
            metric_columns = []
            for col in df_hero_stats.columns:
                if col.endswith('_per_match') or col.endswith('_per_min') or col.endswith('_per_soul'):
                    metric_columns.append(col)

            # Add specific metrics
            for col in ['win_rate', 'accuracy', 'crit_shot_rate']:
                if col in df_hero_stats.columns:
                    metric_columns.append(col)

            # Sort metrics alphabetically
            metric_columns.sort()

            # print(f"Selected metrics: {metric_columns}")

            # Calculate averages for each metric across all heroes
            metric_avgs = {}
            for col in metric_columns + ['win_rate']:
                if col in df_hero_stats.columns:
                    metric_avgs[col] = df_hero_stats[col].mean()

            # print(f"Metric averages: {metric_avgs}")

            # Prepare data for heatmap
            hero_names_list = df_hero_stats['name'].tolist()
            hero_icons = df_hero_stats['images.icon_hero_card'].tolist()
            hero_matches_played = df_hero_stats['matches_played'].tolist()

            # Create heatmap data matrix
            heatmap_data = []
            heatmap_text = []  # For hover text
            metric_labels = []

            # Custom label mapping for better readability
            label_mapping = {
                'kills_per_min': 'Kills/Min',
                'deaths_per_min': 'Deaths/Min',
                'assists_per_min': 'Assists/Min',
                'denies_per_min': 'Denies/Min',
                'denies_per_match': 'Denies/Match',
                'networth_per_min': 'Souls/Min',
                'last_hits_per_min': 'Last Hits/Min',
                'damage_per_min': 'Dmg/Min',
                'damage_per_soul': 'Dmg/Soul',
                'damage_taken_per_soul': 'Dmg Taken/Soul',
                'creeps_per_min': 'Creeps/Min',
                'obj_damage_per_min': 'Obj Dmg/Min',
                'obj_damage_per_soul': 'Obj Dmg/Soul',
                'win_rate': 'Win Rate %',
                'accuracy': 'Accuracy %',
                'crit_shot_rate': 'Crit Rate %'
            }

            for col in metric_columns:
                if col in df_hero_stats.columns:
                    values = df_hero_stats[col].tolist()
                    heatmap_data.append(values)

                    # Create hover text
                    hover_values = [f"{val:.2f}" for val in values]
                    heatmap_text.append(hover_values)

                    # Use custom label or fallback to formatted column name
                    label = label_mapping.get(col, col.replace('_', ' ').title())
                    metric_labels.append(label)

            # Transpose data (metrics on x-axis, heroes on y-axis)
            heatmap_data = list(map(list, zip(*heatmap_data)))
            heatmap_text = list(map(list, zip(*heatmap_text)))

            # Create custom colorscale: blue (below avg) -> white (avg) -> red (above avg)
            # Normalize data relative to averages for colorscale
            normalized_data = []
            for i, hero_row in enumerate(heatmap_data):
                normalized_row = []
                for j, value in enumerate(hero_row):
                    metric_col = metric_columns[j] if j < len(metric_columns) else None
                    if metric_col and metric_col in metric_avgs:
                        avg = metric_avgs[metric_col]
                        if avg > 0:
                            # Normalize: -1 (half of avg) to +1 (double of avg)
                            normalized = (value - avg) / avg
                            normalized = max(-1, min(1, normalized))  # Clamp to [-1, 1]
                        else:
                            normalized = 0
                    else:
                        normalized = 0
                    normalized_row.append(normalized)
                normalized_data.append(normalized_row)

            fig8 = go.Figure(data=go.Heatmap(
                z=normalized_data,
                x=metric_labels,
                y=hero_names_list,
                text=heatmap_text,
                texttemplate='%{text}',
                textfont={"size": 11, "color": "#1b2838"},  # Darker text for visibility
                customdata=[[matches] for matches in hero_matches_played],  # Store matches for filtering
                colorscale=[
                    [0.0, '#4a9eff'],    # Blue (below average)
                    [0.5, '#ffffff'],    # White (average)
                    [1.0, '#ff4a4a']     # Red (above average)
                ],
                zmid=0,  # Center colorscale at 0 (average)
                colorbar=dict(
                    title="vs Avg",
                    tickvals=[-1, 0, 1],
                    ticktext=['Below', 'Avg', 'Above']
                ),
                hovertemplate='<b>%{y}</b><br>%{x}: %{text}<extra></extra>'
            ))

            # Add hero icons on y-axis
            images = []
            for i, (hero_name, icon_url) in enumerate(zip(hero_names_list, hero_icons)):
                if icon_url:
                    images.append(dict(
                        source=icon_url,
                        xref="paper",
                        yref="y",
                        x=-0.015,  # Positioned outside the plot area
                        y=i,
                        sizex=0.04,  # Increased from 0.025
                        sizey=0.9,   # Increased from 0.8
                        xanchor="right",
                        yanchor="middle",
                        layer="above"
                    ))

            # Create filter buttons for minimum matches
            filter_buttons = []
            thresholds = [0, 5, 10, 25, 50, 100, 200]

            for threshold in thresholds:
                label = f"All Heroes" if threshold == 0 else f"≥{threshold} Matches"
                filter_buttons.append(dict(
                    label=label,
                    method='skip',  # We'll handle filtering in JavaScript
                    args=[threshold]
                ))

            # Create annotations for matches played next to hero icons
            annotations = []
            for i, (hero_name, matches) in enumerate(zip(hero_names_list, hero_matches_played)):
                annotations.append(dict(
                    text=f"({matches})",
                    xref="paper",
                    yref="y",
                    x=-0.045,  # Position to the right of hero icon
                    y=i,
                    xanchor="right",
                    yanchor="middle",
                    showarrow=False,
                    font=dict(size=10, color='#c7d5e0')
                ))

            # Add filter label annotation
            annotations.append(dict(
                text="Minimum games played:",
                xref="paper",
                yref="paper",
                x=0.87,
                y=1.08,
                xanchor="right",
                yanchor="top",
                showarrow=False,
                font=dict(size=12, color='#c7d5e0')
            ))

            fig8.update_layout(
                title='Hero Performance Heatmap (Click metric to sort)',
                xaxis=dict(
                    title='Metrics (Click to Sort)',
                    side='bottom'
                ),
                yaxis=dict(
                    title='',
                    tickmode='array',
                    tickvals=list(range(len(hero_names_list))),
                    ticktext=[''] * len(hero_names_list),  # Hide tick labels (icons replace them)
                    autorange='reversed',  # Most played at top
                    side='left'
                ),
                updatemenus=[
                    dict(
                        type='dropdown',
                        direction='down',
                        x=1.0,
                        xanchor='right',
                        y=1.08,
                        yanchor='top',
                        showactive=True,
                        buttons=filter_buttons,
                        bgcolor='rgba(27, 40, 56, 0.9)',
                        bordercolor='#3d4e5c',
                        font=dict(color='#c7d5e0', size=11)
                    )
                ],
                annotations=annotations,
                images=images,
                height=max(800, len(hero_names_list) * 40),  # Increased from 30 to 40 per hero, min from 600 to 800
                margin=dict(l=80, r=100, t=100, b=80)  # Adjusted top margin
            )

            # print(f"Hero heatmap created with {len(hero_names_list)} heroes and {len(metric_labels)} metrics")
            charts['hero_heatmap'] = json.dumps(fig8, cls=PlotlyJSONEncoder)

        # Player Stats Summary (calculated from match history)
        summary = {}
        if not df_match_history.empty and 'result' in df_match_history.columns:
            wins = (df_match_history['result'] == 'Win').sum()
            losses = (df_match_history['result'] == 'Loss').sum()
            total_matches = len(df_match_history)
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

            summary = {
                'total_matches': total_matches,
                'wins': wins,
                'losses': losses,
                'win_rate': f"{win_rate:.1f}%",
                'avg_kills': f"{df_match_history['player_kills'].mean():.1f}",
                'avg_deaths': f"{df_match_history['player_deaths'].mean():.1f}",
                'avg_assists': f"{df_match_history['player_assists'].mean():.1f}",
            }

        # Calculate top 5 heroes by games played (use unfiltered data)
        top_heroes = []
        # print(f"Top heroes check: df_match_history_unfiltered empty={df_match_history_unfiltered.empty}, hero_names={bool(hero_names)}, has hero_name={'hero_name' in df_match_history_unfiltered.columns if not df_match_history_unfiltered.empty else 'N/A'}")

        if not df_match_history_unfiltered.empty and hero_names and 'hero_name' in df_match_history_unfiltered.columns:
            # Group by hero_name and calculate stats (using unfiltered data)
            hero_stats = df_match_history_unfiltered.groupby('hero_name').agg({
                'match_id': 'count',  # Total matches
                'result': lambda x: (x == 'Win').sum()  # Total wins
            }).rename(columns={'match_id': 'matches', 'result': 'wins'})

            # Calculate win rate
            hero_stats['win_rate'] = (hero_stats['wins'] / hero_stats['matches'] * 100).round(1)

            # Sort by matches played and get top 5
            hero_stats = hero_stats.sort_values('matches', ascending=False).head(5)

            # Create heroes DataFrame for lookup
            df_heroes = pd.json_normalize(hero_names) if hero_names else pd.DataFrame()

            # Build top heroes list with icons from heroes endpoint
            for hero_name, hero_stats_row in hero_stats.iterrows():
                # Get hero data including images
                hero_info = df_heroes[df_heroes['name'] == hero_name]
                icon_url = None
                hero_id_value = None

                if not hero_info.empty:
                    hero_row = hero_info.iloc[0]
                    hero_id_value = int(hero_row['id'])  # Store hero_id
                    # print(f"Hero {hero_name} has ID: {hero_id_value}")

                    # Access flattened image columns (json_normalize creates 'images.key_name' columns)
                    # Try different image types in order of preference
                    for img_key in ['images.icon_hero_card', 'images.icon_image_small', 'images.minimap_image', 'images.selection_image']:
                        if img_key in hero_row.index and pd.notna(hero_row[img_key]) and hero_row[img_key]:
                            icon_url = hero_row[img_key]
                            # print(f"Found icon for {hero_name}: {img_key}")
                            break
                else:
                    pass
                    # print(f"WARNING: Hero {hero_name} not found in heroes endpoint!")

                if not icon_url:
                    pass
                    # print(f"No icon found for {hero_name}")

                if hero_id_value is not None:
                    top_heroes.append({
                        'name': hero_name,
                        'hero_id': hero_id_value,  # Include hero_id
                        'matches': int(hero_stats_row['matches']),
                        'win_rate': f"{hero_stats_row['win_rate']:.1f}%",
                        'icon_url': icon_url
                    })
                else:
                    pass
                    # print(f"Skipping {hero_name} - no hero_id found")

            # print(f"Top 5 heroes calculated: {[h['name'] for h in top_heroes]}")

        # Get ALL matches with all metrics for pagination
        recent_matches = []
        if not df_match_history.empty and hero_names:
            # Sort by start time (most recent first) - get ALL matches
            df_recent = df_match_history.sort_values('start_time', ascending=False)

            # Create heroes DataFrame for lookup if not already created
            if 'df_heroes' not in locals():
                df_heroes = pd.json_normalize(hero_names) if hero_names else pd.DataFrame()

            for idx, match in df_recent.iterrows():
                # Get hero icon
                hero_name = match['hero_name'] if 'hero_name' in match.index else 'Unknown'
                hero_info = df_heroes[df_heroes['name'] == hero_name] if not df_heroes.empty else pd.DataFrame()
                icon_url = None

                if not hero_info.empty:
                    hero_row = hero_info.iloc[0]
                    # Try to get small icon
                    for img_key in ['images.icon_image_small', 'images.icon_hero_card', 'images.minimap_image']:
                        if img_key in hero_row.index and pd.notna(hero_row[img_key]) and hero_row[img_key]:
                            icon_url = hero_row[img_key]
                            break

                # Format match data using correct column names
                recent_matches.append({
                    'match_id': int(match['match_id']) if 'match_id' in match.index else 0,
                    'start_time': int(match['start_time']) if 'start_time' in match.index else 0,
                    'hero_name': hero_name,
                    'hero_icon': icon_url,
                    'result': match['result'] if 'result' in match.index else 'Unknown',
                    'kills': int(match['player_kills']) if 'player_kills' in match.index else 0,
                    'deaths': int(match['player_deaths']) if 'player_deaths' in match.index else 0,
                    'assists': int(match['player_assists']) if 'player_assists' in match.index else 0,
                    'net_worth': int(match['net_worth']) if 'net_worth' in match.index else 0,
                    'last_hits': int(match['last_hits']) if 'last_hits' in match.index else 0,
                    'denies': int(match['denies']) if 'denies' in match.index else 0,
                    'duration_s': int(match['match_duration_s']) if 'match_duration_s' in match.index else 0
                })

            # print(f"Recent matches prepared: {len(recent_matches)} matches")

        # Calculate top 10 items by matches played
        top_items = []
        # print(f"Top items check: item_stats={bool(item_stats)}, items_data={bool(items_data)}")

        if item_stats and items_data:
            # Normalize to DataFrames
            df_item_stats = pd.json_normalize(item_stats)
            df_items = pd.json_normalize(items_data)

            # print(f"Item stats shape: {df_item_stats.shape}, Items data shape: {df_items.shape}")
            # print(f"Item stats columns: {df_item_stats.columns.tolist() if not df_item_stats.empty else 'empty'}")

            # Show sample of item_stats data
            if not df_item_stats.empty:
                pass
                # print(f"Sample item_stats (first 3 rows):")
                # print(df_item_stats[['item_id', 'matches', 'wins', 'losses']].head(3).to_string())

            # Filter out items with zero matches
            if not df_item_stats.empty and 'matches' in df_item_stats.columns:
                # print(f"Before filtering: {len(df_item_stats)} items")
                df_item_stats = df_item_stats[df_item_stats['matches'] > 0]
                # print(f"After filtering (matches > 0): {len(df_item_stats)} items")

            # Merge item stats with item metadata
            if not df_item_stats.empty and not df_items.empty:
                df_items_merged = pd.merge(
                    df_item_stats,
                    df_items,
                    left_on='item_id',
                    right_on='id',
                    how='left'
                )

                # print(f"Merged items shape: {df_items_merged.shape}")
                # print(f"Merged items columns: {df_items_merged.columns.tolist()[:10]}...")  # First 10 columns
                # print(f"Items with missing names: {df_items_merged['name'].isna().sum() if 'name' in df_items_merged.columns else 'name column missing'}")

                # Calculate win rate
                if 'wins' in df_items_merged.columns and 'matches' in df_items_merged.columns:
                    df_items_merged['win_rate'] = (df_items_merged['wins'] / df_items_merged['matches'] * 100).round(1)

                    # Sort by matches descending and take top 10
                    df_top_items = df_items_merged.sort_values('matches', ascending=False).head(10)

                    # Build top items list
                    for _, item_row in df_top_items.iterrows():
                        # Get item name
                        item_name = item_row.get('name', 'Unknown Item')

                        # Convert item name to snake_case for image key matching
                        item_name_snake = item_name.lower().replace(' ', '_').replace('-', '_')

                        # Try to find matching image in images endpoint with _sm_webp suffix
                        icon_url = None
                        if images_data:
                            # Try weapon, spirit, and vitality categories
                            for category in ['weapon', 'spirit', 'vitality']:
                                image_key = f'items_{category}_{item_name_snake}_sm_webp'
                                if image_key in images_data:
                                    icon_url = images_data[image_key]
                                    break

                        top_items.append({
                            'name': item_name,
                            'icon_url': icon_url,
                            'matches': int(item_row['matches']),
                            'win_rate': f"{item_row['win_rate']:.1f}%"
                        })

                    # print(f"Top 10 items calculated: {[i['name'] for i in top_items]}")

        # Extract rank badge from latest game
        rank_badge_url = None
        rank_name = None
        rank_division_tier = None
        if mmr_history and len(mmr_history) > 0 and ranks_data:
            # Get latest game (last in list)
            latest_game = mmr_history[-1]
            division = latest_game.get('division')  # This is the tier (0-11)
            division_tier = latest_game.get('division_tier', 0)  # This is the subrank (1-6)

            # print(f"Player division: {division}, division_tier: {division_tier}")

            # Find matching rank in ranks_data
            for rank in ranks_data:
                if rank.get('tier') == division:
                    rank_name = rank.get('name', 'Unknown')
                    rank_division_tier = division_tier
                    images = rank.get('images', {})

                    # Get subrank badge if division_tier exists
                    if division_tier > 0:
                        badge_key = f'small_subrank{division_tier}'
                        rank_badge_url = images.get(badge_key) or images.get('small')
                    else:
                        rank_badge_url = images.get('small')

                    # print(f"Matched rank: {rank_name} (division {division}, tier {division_tier})")
                    # print(f"Badge URL: {rank_badge_url}")
                    break

        # Extract Steam profile data
        steam_data = {}
        if steam_profile:
            # Filter results to find the matching account_id
            if isinstance(steam_profile, list) and len(steam_profile) > 0:
                # Find the profile that matches the player_id
                matching_profile = None
                for profile in steam_profile:
                    # Check if account_id matches (convert to string for comparison)
                    if str(profile.get('account_id', '')) == str(player_id):
                        matching_profile = profile
                        break

                if matching_profile:
                    steam_data = {
                        'username': matching_profile.get('personaname', 'Unknown Player'),
                        'avatar_full': matching_profile.get('avatarfull', ''),
                        'rank_badge': rank_badge_url,
                        'rank_name': rank_name,
                        'rank_division_tier': rank_division_tier,
                    }
                    # print(f"Found Steam profile: {steam_data['username']}")
                else:
                    pass
                    # print(f"No matching profile found for player_id: {player_id}")
            elif isinstance(steam_profile, dict):
                # Single result returned
                if str(steam_profile.get('account_id', '')) == str(player_id):
                    steam_data = {
                        'username': steam_profile.get('personaname', 'Unknown Player'),
                        'avatar_full': steam_profile.get('avatarfull', ''),
                        'rank_badge': rank_badge_url,
                        'rank_name': rank_name,
                        'rank_division_tier': rank_division_tier,
                    }

        return charts, summary, steam_data, top_heroes, top_items, filtered_hero_name, recent_matches

    except Exception as e:
        # print(f"Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return None, None, str(e), [], [], None, []


def get_rank_distribution():
    """Fetch and create rank distribution chart for the index page"""
    try:
        import time
        from datetime import datetime, timedelta

        # Calculate timestamp for 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        min_timestamp = int(thirty_days_ago.timestamp())

        # Fetch rank distribution data
        connection = http.client.HTTPSConnection("api.deadlock-api.com")
        endpoint = f"/v1/players/mmr/distribution?min_unix_timestamp={min_timestamp}"
        headers = {'Accept': "*/*"}

        connection.request("GET", endpoint, headers=headers)
        response = connection.getresponse()
        raw_data = response.read()

        print(f"Rank distribution request status: {response.status}")

        if response.status != 200:
            print(f"Error fetching rank distribution: {raw_data[:200]}")
            return None

        data = json.loads(raw_data.decode("utf-8"))

        if not data:
            print("No rank distribution data available")
            return None

        # Also fetch ranks data for names
        connection_ranks = http.client.HTTPSConnection("assets.deadlock-api.com")
        connection_ranks.request("GET", "/v2/ranks", headers=headers)
        ranks_response = connection_ranks.getresponse()
        ranks_data = json.loads(ranks_response.read().decode("utf-8"))

        # Create rank mapping, color mapping, and badge mapping
        rank_mapping = {}
        rank_color_mapping = {}
        rank_badge_mapping = {}

        # Color palette matching the badge colors from the image
        default_colors = [
            '#4a5f73',  # 0: Obscurus - dark gray (not shown in image)
            '#cd7f32',  # 1: Initiate - bronze/brown
            '#8b5a8e',  # 2: Seeker - purple
            '#4a9eff',  # 3: Alchemist - blue
            '#4ade80',  # 4: Arcanist - green
            '#d97706',  # 5: Ritualist - orange/copper
            '#dc2626',  # 6: Emissary - red/crimson
            '#a855f7',  # 7: Archon - violet/purple
            '#b8860b',  # 8: Oracle - bronze/dark gold
            '#9ca3af',  # 9: Phantom - silver/gray
            '#fbbf24',  # 10: Ascendant - gold
            '#22d3ee',  # 11: Eternus - cyan/turquoise
        ]

        # print(f"Sample rank data: {ranks_data[0] if ranks_data else 'None'}")

        for rank in ranks_data:
            tier = rank.get('tier')
            rank_name = rank.get('name', f'Rank {tier}')
            rank_mapping[tier] = rank_name

            # Get badge image - look for 'lg' (large) badge
            images = rank.get('images', {})

            # Debug: print image keys
            if tier < 3:  # Only print first 3 for debugging
                pass
                # print(f"Tier {tier} ({rank_name}) images keys: {images.keys() if isinstance(images, dict) else 'not a dict'}")

            badge_url = ''

            # Look for 'lg_webp' or webp versions of large badge image
            if isinstance(images, dict):
                # Prefer webp, then fallback to png
                for key in ['lg_webp', 'large_webp', 'badge_lg_webp', 'lg', 'large', 'badge_lg']:
                    if key in images and images[key]:
                        badge_url = images[key]
                        # print(f"  Tier {tier}: Found badge at key '{key}': {badge_url[:80]}...")
                        break

            rank_badge_mapping[tier] = badge_url

            # Assign color
            rank_color = default_colors[tier] if tier < len(default_colors) else '#66c0f4'
            rank_color_mapping[tier] = rank_color

        # print(f"Rank badge mapping: {rank_badge_mapping}")
        # print(f"Rank color mapping: {rank_color_mapping}")

        # Process distribution data
        df_dist = pd.json_normalize(data)
        # print(f"Distribution data shape: {df_dist.shape}")
        # print(f"Distribution columns: {df_dist.columns.tolist()}")
        # print(f"Rank value range: {df_dist['rank'].min()} to {df_dist['rank'].max()}")
        # print(f"Available tier mappings: {list(rank_mapping.keys())}")

        # Rank encoding formula (from MMR history endpoint data):
        # rank = (division * 10) + division_tier
        # Example: rank 15 = division 1, tier 5 (Initiate 5)
        #          rank 21 = division 2, tier 1 (Seeker 1)
        #          rank 34 = division 3, tier 4 (Alchemist 4)

        df_dist['tier'] = df_dist['rank'] // 10  # Division (0-11)
        df_dist['subtier'] = df_dist['rank'] % 10  # Division tier (1-6)

        # print(f"\n=== RANK DISTRIBUTION ===")
        # print(f"Total ranks: {len(df_dist)}")
        # print(f"Rank range: {df_dist['rank'].min()} to {df_dist['rank'].max()}")
        # print(f"Tier range: {df_dist['tier'].min()} to {df_dist['tier'].max()}")
        # print(f"\nFirst 15 ranks:")
        # print(df_dist[['rank', 'tier', 'subtier', 'players']].head(15).to_string())

        # Map tier to rank names and colors
        df_dist['rank_name'] = df_dist['tier'].map(rank_mapping)
        df_dist['color'] = df_dist['tier'].map(rank_color_mapping)

        # Create full rank name with subtier (e.g., "Initiate 1", "Seeker 3")
        df_dist['full_rank_name'] = df_dist.apply(
            lambda row: f"{row['rank_name']} {row['subtier']}" if pd.notna(row['rank_name']) and row['subtier'] > 0 else row['rank_name'],
            axis=1
        )

        df_dist = df_dist.sort_values('rank')

        # Calculate percentage metrics
        total_players = df_dist['players'].sum()
        df_dist['player_pct'] = (df_dist['players'] / total_players * 100).round(2)

        # Calculate cumulative percentage from the TOP (highest ranks first)
        # Reverse order for cumulative sum, then reverse back
        df_dist_reversed = df_dist.iloc[::-1].copy()
        df_dist_reversed['cumulative_players'] = df_dist_reversed['players'].cumsum()
        df_dist_reversed['top_pct'] = (df_dist_reversed['cumulative_players'] / total_players * 100).round(2)

        # Merge back to original order
        df_dist = df_dist_reversed.iloc[::-1].reset_index(drop=True)

        # print(f"Total players: {total_players:,}")
        # print(f"Sample with percentages:")
        # print(df_dist[['rank', 'full_rank_name', 'players', 'player_pct', 'top_pct']].head(10).to_string())

        # Create bar chart using full rank names with color coding
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_dist['full_rank_name'].tolist(),
            y=df_dist['players'].tolist(),
            marker=dict(
                color=df_dist['color'].tolist(),  # Use tier-specific colors
                line=dict(color='#1b2838', width=1)
            ),
            customdata=df_dist[['player_pct', 'top_pct']].values.tolist(),
            hovertemplate=(
                '<b>%{x}</b><br>'
                'Players: %{y:,}<br>'
                '% of player pop.: %{customdata[0]:.2f}%<br>'
                'Top %{customdata[1]:.2f}% of player base'
                '<extra></extra>'
            )
        ))

        # Add badge images at division boundaries (centered on 3rd subtier)
        images = []

        # Find positions for each tier's 3rd subtier (or middle position)
        tier_positions = {}  # Map tier to list of positions

        for position, (idx, row) in enumerate(df_dist.iterrows()):
            tier = row['tier']
            subtier = row['subtier']

            if tier not in tier_positions:
                tier_positions[tier] = []
            tier_positions[tier].append({'position': position, 'subtier': subtier})

        # Calculate center position for each tier (prefer subtier 3, or middle of available)
        x_positions = {}
        for tier, positions_list in tier_positions.items():
            # Look for subtier 3
            subtier_3 = [p for p in positions_list if p['subtier'] == 3]
            if subtier_3:
                x_positions[tier] = subtier_3[0]['position']
            else:
                # Use middle position if subtier 3 doesn't exist
                middle_idx = len(positions_list) // 2
                x_positions[tier] = positions_list[middle_idx]['position']

        # print(f"Badge positions (centered on 3rd subtier): {x_positions}")

        # Add badge images above the first bar of each division
        for tier, x_pos in x_positions.items():
            badge_url = rank_badge_mapping.get(tier)
            rank_name = rank_mapping.get(tier, f'Rank {tier}')

            # print(f"Tier {tier} ({rank_name}): position={x_pos}, badge_url={badge_url}")

            if badge_url:
                # Oracle (8), Phantom (9), Ascendant (10), Eternus (11) need larger size
                # because their badge images have different dimensions
                if tier >= 8:
                    badge_sizex = 6  # Double width for high ranks
                    badge_sizey = 0.24  # Double height for high ranks
                else:
                    badge_sizex = 3  # Normal width for other ranks
                    badge_sizey = 0.12  # Normal height for other ranks

                # Add image at the x-axis position (bar index)
                images.append(dict(
                    source=badge_url,
                    xref="x",
                    yref="paper",
                    x=x_pos,  # Bar position (0, 1, 2, 3...)
                    y=1.08,   # Above the chart
                    sizex=badge_sizex,  # Width in bar units
                    sizey=badge_sizey,  # Height relative to chart
                    xanchor="center",
                    yanchor="bottom",
                    layer="above"
                ))
                # print(f"  → Added badge image at position {x_pos}")

        # print(f"Total badge images added: {len(images)}")

        fig.update_layout(
            xaxis_title='Rank',
            yaxis_title='Number of Players',
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=10)
            ),
            height=600,  # Taller to match input container height
            showlegend=False,
            margin=dict(t=100, b=20, l=20, r=10),  # Minimal margins to fill container
            images=images if images else []
        )

        # print(f"Final chart layout images count: {len(fig.layout.images) if hasattr(fig.layout, 'images') else 0}")

        # print(f"Chart created successfully with {len(df_dist)} ranks")
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    except Exception as e:
        # print(f"Error creating rank distribution chart: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_leaderboard():
    """Fetch top 100 players from Statlocker API"""
    try:
        connection = http.client.HTTPSConnection("statlocker.gg")
        connection.request("GET", "/api/leaderboard/get-pp-rankings/?version=2")
        response = connection.getresponse()
        raw_data = response.read()

        print(f"Statlocker API request status: {response.status}")

        if response.status != 200:
            print(f"Error fetching leaderboard: {raw_data[:200]}")
            return []

        data = json.loads(raw_data.decode("utf-8"))

        # Data is nested inside a "data" key
        players = data.get("data", []) if isinstance(data, dict) else data

        # Return top 40 players with normalized field names
        leaderboard = []
        for player in players[:40]:
            leaderboard.append({
                'rank': player.get('rank'),
                'account_id': player.get('accountId'),
                'username': player.get('name'),
                'avatar_url': player.get('avatarUrl'),
                'performance_rank': player.get('performanceRankMessage'),
                'pp_score': player.get('ppScore')
            })

        print(f"  → Leaderboard: {len(leaderboard)} players loaded")
        return leaderboard

    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        import traceback
        traceback.print_exc()
        return []


def create_match_visualizations(match_id, player_slot=None):
    """Fetch match data and create visualizations for match analysis"""
    connection = get_match_api_connection(match_id)

    try:
        # Fetch data from API endpoints
        match_data = get_request_data(connection, "data-api", "match_metadata")
        hero_names = get_request_data(connection, "assets-api", "heroes")
        ranks_data = get_request_data(connection, "assets-api", "ranks")
        items_data = get_request_data(connection, "assets-api", "items")
        images_data = get_request_data(connection, "assets-api", "images")

        if not match_data or 'match_info' not in match_data:
            return None, "Failed to fetch match data from API", None, None, None

        match_info = match_data['match_info']

        # Convert to DataFrames
        df_heroes = pd.json_normalize(hero_names) if hero_names else pd.DataFrame()
        df_ranks = pd.json_normalize(ranks_data) if ranks_data else pd.DataFrame()
        df_items = pd.json_normalize(items_data) if items_data else pd.DataFrame()

        # Filter items to only include upgrades (exclude abilities and weapons)
        if not df_items.empty and 'type' in df_items.columns:
            df_items = df_items[df_items['type'] == 'upgrade']

        # Process players data
        df_players = pd.json_normalize(match_info['players'])

        # Enrich with hero names
        if not df_heroes.empty:
            df_players = pd.merge(df_players, df_heroes[['id', 'name', 'class_name']],
                                 left_on='hero_id', right_on='id', how='left', suffixes=('', '_hero'))
            df_players = df_players.rename(columns={'name': 'hero_name'})

        # Add result column
        winning_team = match_info.get('winning_team', 0)
        df_players['result'] = df_players['team'].apply(lambda t: 'Win' if t == winning_team else 'Loss')

        # Identify filtered player
        filtered_player_info = None
        if player_slot is not None and not df_players.empty:
            player_match = df_players[df_players['player_slot'] == player_slot]
            if not player_match.empty:
                player = player_match.iloc[0]
                filtered_player_info = {
                    'player_slot': player_slot,
                    'hero_name': player.get('hero_name', 'Unknown'),
                    'account_id': player.get('account_id', 'N/A')
                }

        # Process time-series stats
        all_stats = []
        for player in match_info['players']:
            if 'stats' in player:
                for stat in player['stats']:
                    stat['player_slot'] = player['player_slot']
                    stat['team'] = player['team']
                    stat['hero_id'] = player['hero_id']
                    all_stats.append(stat)

        df_stats = pd.DataFrame(all_stats) if all_stats else pd.DataFrame()

        # Enrich stats with hero names
        if not df_stats.empty and not df_heroes.empty:
            df_stats = pd.merge(df_stats, df_heroes[['id', 'name']],
                               left_on='hero_id', right_on='id', how='left', suffixes=('', '_hero'))
            df_stats = df_stats.rename(columns={'name': 'hero_name'})

        charts = {}

        # Charts will be added here in future iterations

        # Match Summary
        duration_s = match_info.get('duration_s', 0)
        start_time = match_info.get('start_time', 0)

        # Format start_time as readable date
        from datetime import datetime
        start_datetime = datetime.fromtimestamp(start_time) if start_time > 0 else None
        start_date_formatted = start_datetime.strftime('%B %d, %Y at %H:%M') if start_datetime else 'Unknown'

        # Extract patron logos from images endpoint
        # Team 0 (Blue) = Archmother (team2 logo), Team 1 (Orange) = Hidden King (team1 logo)
        patron_logo_team0 = images_data.get('hud_core_team2_patron_logo_webp') if images_data else None
        patron_logo_team1 = images_data.get('hud_core_team1_patron_logo_webp') if images_data else None

        # Build rank badge mapping (division/tier → base badge URL, matching player page logic)
        rank_badge_mapping = {}
        if ranks_data:
            for rank in ranks_data:
                tier = rank.get('tier')
                images = rank.get('images', {})
                badge_url = ''
                if isinstance(images, dict):
                    # Use base badge (no subrank) for team averages
                    for key in ['large_webp', 'large']:
                        if key in images and images[key]:
                            badge_url = images[key]
                            break
                rank_badge_mapping[tier] = badge_url

        # Decode average_badge to tier: tier = badge // 10
        # Badge 41 → tier 4 (Arcanist), Badge 70 → tier 7 (Archon), etc.
        avg_badge_0 = match_info.get('average_badge_team0')
        avg_badge_1 = match_info.get('average_badge_team1')

        tier_0 = avg_badge_0 // 10 if avg_badge_0 is not None else None
        tier_1 = avg_badge_1 // 10 if avg_badge_1 is not None else None

        rank_badge_team0 = rank_badge_mapping.get(tier_0, '')
        rank_badge_team1 = rank_badge_mapping.get(tier_1, '')

        print(f"[RANK DEBUG] average_badge_team0: {avg_badge_0} → tier {tier_0}, badge URL: {rank_badge_team0}")
        print(f"[RANK DEBUG] average_badge_team1: {avg_badge_1} → tier {tier_1}, badge URL: {rank_badge_team1}")

        match_summary = {
            'match_id': match_info.get('match_id', match_id),
            'duration_s': duration_s,
            'duration_formatted': f"{duration_s // 60}:{duration_s % 60:02d}",
            'start_time': start_time,
            'start_date_formatted': start_date_formatted,
            'winning_team': winning_team,
            'game_mode': {1: 'Standard', 4: 'Street Brawl'}.get(match_info.get('game_mode'), 'Unknown'),
            'patron_logo_team0': patron_logo_team0,
            'patron_logo_team1': patron_logo_team1,
            'rank_badge_team0': rank_badge_team0,
            'rank_badge_team1': rank_badge_team1,
        }

        # Calculate player damage, boss damage, and total healing from final stats (last entry in stats array)
        if not df_stats.empty:
            # Get final stats (last timestamp) for each player
            final_stats = df_stats.groupby('player_slot').last().reset_index()

            # Calculate total healing (player_healing + teammate_barriering - self_damage)
            healing_cols = []
            if 'player_healing' in final_stats.columns:
                healing_cols.append('player_healing')
            if 'teammate_barriering' in final_stats.columns:
                healing_cols.append('teammate_barriering')

            if healing_cols:
                final_stats['total_healing'] = final_stats[healing_cols].fillna(0).sum(axis=1)

                # Subtract self_damage if available
                if 'self_damage' in final_stats.columns:
                    final_stats['total_healing'] = final_stats['total_healing'] - final_stats['self_damage'].fillna(0)
            else:
                final_stats['total_healing'] = 0

            # Select columns to merge
            merge_cols = ['player_slot']
            if 'player_damage' in final_stats.columns:
                merge_cols.append('player_damage')
            if 'boss_damage' in final_stats.columns:
                merge_cols.append('boss_damage')
            merge_cols.append('total_healing')

            # Merge with players to get team info
            df_players_with_damage = pd.merge(df_players, final_stats[merge_cols],
                                              on='player_slot', how='left')
        else:
            df_players_with_damage = df_players.copy()
            df_players_with_damage['player_damage'] = 0
            df_players_with_damage['boss_damage'] = 0
            df_players_with_damage['total_healing'] = 0

        # Team Stats
        team_stats = {
            'team0': {
                'kills': int(df_players[df_players['team'] == 0]['kills'].sum()) if not df_players.empty else 0,
                'deaths': int(df_players[df_players['team'] == 0]['deaths'].sum()) if not df_players.empty else 0,
                'assists': int(df_players[df_players['team'] == 0]['assists'].sum()) if not df_players.empty else 0,
                'net_worth': int(df_players[df_players['team'] == 0]['net_worth'].sum()) if not df_players.empty else 0,
                'player_damage': int(df_players_with_damage[df_players_with_damage['team'] == 0]['player_damage'].sum()) if not df_players_with_damage.empty else 0,
                'ability_points': int(df_players[df_players['team'] == 0]['ability_points'].sum()) if not df_players.empty and 'ability_points' in df_players.columns else 0,
            },
            'team1': {
                'kills': int(df_players[df_players['team'] == 1]['kills'].sum()) if not df_players.empty else 0,
                'deaths': int(df_players[df_players['team'] == 1]['deaths'].sum()) if not df_players.empty else 0,
                'assists': int(df_players[df_players['team'] == 1]['assists'].sum()) if not df_players.empty else 0,
                'net_worth': int(df_players[df_players['team'] == 1]['net_worth'].sum()) if not df_players.empty else 0,
                'player_damage': int(df_players_with_damage[df_players_with_damage['team'] == 1]['player_damage'].sum()) if not df_players_with_damage.empty else 0,
                'ability_points': int(df_players[df_players['team'] == 1]['ability_points'].sum()) if not df_players.empty and 'ability_points' in df_players.columns else 0,
            }
        }

        # Determine which team leads each metric
        team_stats['best'] = {}
        for metric in ['kills', 'deaths', 'assists', 'net_worth', 'player_damage', 'ability_points']:
            if team_stats['team0'][metric] > team_stats['team1'][metric]:
                team_stats['best'][metric] = 'team0'
            elif team_stats['team1'][metric] > team_stats['team0'][metric]:
                team_stats['best'][metric] = 'team1'

        # Player Scoreboard
        player_scoreboard = []
        if not df_players_with_damage.empty:
            for player in df_players_with_damage.itertuples():
                # Get hero icon URL
                hero_name = player.hero_name if hasattr(player, 'hero_name') else 'Unknown'
                icon_url = None

                if not df_heroes.empty and hero_name != 'Unknown':
                    hero_info = df_heroes[df_heroes['name'] == hero_name]
                    if not hero_info.empty:
                        hero_row = hero_info.iloc[0]
                        # Try multiple image fields in order of preference
                        for img_key in ['images.icon_image_small', 'images.icon_hero_card', 'images.minimap_image']:
                            if img_key in hero_row.index and pd.notna(hero_row[img_key]) and hero_row[img_key]:
                                icon_url = hero_row[img_key]
                                break

                # Get final items (not sold) from match_info players data
                final_items = []
                player_data = None
                for p in match_info['players']:
                    if p['player_slot'] == player.player_slot:
                        player_data = p
                        break

                if player_data and 'items' in player_data and player_data['items']:
                    # Ensure items is iterable (list/array)
                    items_list = player_data['items']
                    if isinstance(items_list, (list, tuple)):
                        # Collect unique item_ids that haven't been sold
                        seen_item_ids = set()
                        for item in items_list:
                            if isinstance(item, dict) and item.get('sold_time_s', 0) == 0:
                                item_id = item.get('item_id')
                                if item_id:
                                    seen_item_ids.add(item_id)

                        # Match unique item_ids with items API data (filtered to upgrades only)
                        for item_id in seen_item_ids:
                            if not df_items.empty:
                                item_info = df_items[df_items['id'] == item_id]
                                if not item_info.empty:
                                    item_row = item_info.iloc[0]
                                    item_icon = None

                                    item_name = item_row['name'] if 'name' in item_row.index else 'Unknown Item'

                                    # Convert item name to snake_case for image key matching
                                    item_name_snake = item_name.lower().replace(' ', '_').replace('-', '_')

                                    # Try to find matching image in images endpoint with _sm_webp suffix
                                    if images_data:
                                        # Try weapon, spirit, and vitality categories
                                        for category in ['weapon', 'spirit', 'vitality']:
                                            image_key = f'items_{category}_{item_name_snake}_sm_webp'
                                            if image_key in images_data:
                                                item_icon = images_data[image_key]
                                                break

                                    if item_icon:
                                        final_items.append({
                                            'name': item_name,
                                            'icon': item_icon
                                        })

                player_scoreboard.append({
                    'player_slot': player.player_slot,
                    'team': player.team,
                    'hero_name': hero_name,
                    'hero_icon': icon_url,
                    'account_id': player.account_id if hasattr(player, 'account_id') else 'N/A',
                    'kills': int(player.kills) if hasattr(player, 'kills') else 0,
                    'deaths': int(player.deaths) if hasattr(player, 'deaths') else 0,
                    'assists': int(player.assists) if hasattr(player, 'assists') else 0,
                    'net_worth': int(player.net_worth) if hasattr(player, 'net_worth') else 0,
                    'last_hits': int(player.last_hits) if hasattr(player, 'last_hits') else 0,
                    'denies': int(player.denies) if hasattr(player, 'denies') else 0,
                    'player_damage': int(player.player_damage) if hasattr(player, 'player_damage') else 0,
                    'boss_damage': int(player.boss_damage) if hasattr(player, 'boss_damage') else 0,
                    'player_healing': int(player.total_healing) if hasattr(player, 'total_healing') else 0,
                    'result': player.result if hasattr(player, 'result') else 'Unknown',
                    'mvp_rank': int(player.mvp_rank) if hasattr(player, 'mvp_rank') and pd.notna(player.mvp_rank) else None,
                    'final_items': final_items,
                    'best_stats': []
                })

        # Sort player scoreboard by player_slot
        player_scoreboard = sorted(player_scoreboard, key=lambda x: x['player_slot'])

        # Highlight the highest value in each stat column
        for stat in ['kills', 'deaths', 'assists', 'net_worth', 'last_hits', 'denies', 'player_damage', 'boss_damage', 'player_healing']:
            max_val = max((p[stat] for p in player_scoreboard), default=0)
            if max_val > 0:
                for p in player_scoreboard:
                    if p[stat] == max_val:
                        p['best_stats'].append(stat)

        return charts, match_summary, team_stats, player_scoreboard, filtered_player_info

    except Exception as e:
        print(f"Error in create_match_visualizations: {e}")
        import traceback
        traceback.print_exc()
        return None, str(e), None, None, None


@app.route('/')
def index():
    """Render the home page with input form and rank distribution"""
    global _index_cache

    # Check if cache is valid (within 24 hours)
    cache_valid = False
    if _index_cache['timestamp']:
        cache_age = datetime.now() - _index_cache['timestamp']
        cache_valid = cache_age < timedelta(hours=CACHE_DURATION_HOURS)

    # Use cached data if valid, otherwise fetch fresh data
    if cache_valid:
        print("Using cached index page data")
        rank_distribution_chart = _index_cache['rank_distribution']
        leaderboard_data = _index_cache['leaderboard']
    else:
        print("Fetching fresh index page data")
        rank_distribution_chart = get_rank_distribution()
        leaderboard_data = get_leaderboard()

        # Update cache
        _index_cache['rank_distribution'] = rank_distribution_chart
        _index_cache['leaderboard'] = leaderboard_data
        _index_cache['timestamp'] = datetime.now()

    return render_template('index.html', rank_distribution=rank_distribution_chart, leaderboard=leaderboard_data)


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Process player_id and generate visualizations"""
    # Handle both form submission and query params
    if request.method == 'POST':
        player_id = request.form.get('player_id', '').strip()
    else:  # GET request
        player_id = request.args.get('player_id', '').strip()

    hero_id = request.args.get('hero_id', type=int)  # Optional filter (None if not provided)

    if not player_id:
        return render_template('index.html', error="Please enter a valid Player ID")

    charts, summary, steam_data, top_heroes, top_items, filtered_hero_name, recent_matches = create_visualizations(player_id, hero_id)

    if charts is None:
        return render_template('index.html', error=f"Error fetching data: {steam_data}")

    return render_template('results.html',
                          player_id=player_id,
                          hero_id=hero_id,
                          filtered_hero_name=filtered_hero_name,
                          charts=charts,
                          summary=summary,
                          steam_data=steam_data,
                          top_heroes=top_heroes,
                          top_items=top_items,
                          recent_matches=recent_matches)


@app.route('/match-analysis', methods=['GET', 'POST'])
def match_analysis():
    """Process match_id and generate match visualizations"""
    # Handle both form submission and query params
    if request.method == 'POST':
        match_id = request.form.get('match_id', '').strip()
    else:  # GET request
        match_id = request.args.get('match_id', '').strip()

    player_slot = request.args.get('player_slot', type=int)  # Optional filter (None if not provided)

    if not match_id:
        return render_template('index.html', error="Please enter a valid Match ID")

    charts, match_summary, team_stats, player_scoreboard, filtered_player_info = create_match_visualizations(match_id, player_slot)

    if charts is None:
        return render_template('index.html', error=f"Error fetching match data: {match_summary}")

    return render_template('match.html',
                          match_id=match_id,
                          player_slot=player_slot,
                          filtered_player_info=filtered_player_info,
                          charts=charts,
                          match_summary=match_summary,
                          team_stats=team_stats,
                          player_scoreboard=player_scoreboard)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
