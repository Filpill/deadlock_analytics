import json
import http.client
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)


def get_api_connection(player_id):
    """Setup API connection configuration with player_id"""
    return {
        "data-api": {
            "http_client": http.client.HTTPSConnection("api.deadlock-api.com"),
            "endpoint": {
                "match_history": f"/v1/players/{player_id}/match-history?only_stored_history=false",
                "player_stats": f"/v1/analytics/player-stats/metrics?account_ids={player_id}",
                "player_scoreboard": f"/v1/analytics/scoreboards/players?account_ids={player_id}&sort_by=matches",
                "player_performance_curve": f"/v1/analytics/player-performance-curve?account_ids={player_id}&resolution=0",
                "kill_death_stats": f"/v1/analytics/kill-death-stats?account_ids={player_id}",
                "item_stats": f"/v1/analytics/item-stats?account_ids={player_id}&bucket=no_bucket",
                "steam_search": f"/v1/players/steam-search?search_query={player_id}",
            }
        },
        "assets-api": {
            "http_client": http.client.HTTPSConnection("assets.deadlock-api.com"),
            "endpoint": {
                "heroes": "/v2/heroes",
                "items": "/v2/items",
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
    return data


def format_match_history(df, df_heroes):
    """Format match history DataFrame with hero names"""
    if df.empty:
        return df

    # Merge with hero names
    df = pd.merge(df, df_heroes[["id", "name"]], left_on="hero_id", right_on="id", how="left")
    df = df.drop(columns=["hero_id", "id"]).rename(columns={"name": "hero_name"})

    # Convert to timestamp
    df['start_ts'] = pd.to_datetime(df['start_time'], unit='s')

    return df


def create_visualizations(player_id):
    """Fetch data and create visualizations"""
    connection = get_api_connection(player_id)

    # Fetch data from all endpoints
    try:
        hero_names = get_request_data(connection, "assets-api", "heroes")
        match_history = get_request_data(connection, "data-api", "match_history")
        player_stats = get_request_data(connection, "data-api", "player_stats")
        player_performance_curve = get_request_data(connection, "data-api", "player_performance_curve")
        kill_death_stats = get_request_data(connection, "data-api", "kill_death_stats")
        steam_profile = get_request_data(connection, "data-api", "steam_search")

        if not all([hero_names, match_history]):
            return None, None, "Failed to fetch data from API"

        # Convert to DataFrames
        df_heroes = pd.json_normalize(hero_names)
        df_match_history = pd.json_normalize(match_history)
        df_match_history = format_match_history(df_match_history, df_heroes)
        df_player_performance_curve = pd.json_normalize(player_performance_curve) if player_performance_curve else pd.DataFrame()
        df_kill_death_stats = pd.json_normalize(kill_death_stats) if kill_death_stats else pd.DataFrame()
        df_player_stats = pd.json_normalize(player_stats) if player_stats else pd.DataFrame()

        charts = {}

        # Chart 1: Win/Loss over time
        if not df_match_history.empty and 'player_team' in df_match_history.columns and 'match_result' in df_match_history.columns:
            df_match_history['result'] = df_match_history.apply(
                lambda row: 'Win' if row['player_team'] == row['match_result'] else 'Loss', axis=1
            )
            fig1 = px.histogram(df_match_history, x='start_ts', color='result',
                               title='Number of Matches Played',
                               labels={'start_ts': 'Date', 'count': 'Number of Matches'},
                               color_discrete_map={'Win': '#22c55e', 'Loss': '#ef4444'},
                               nbins=30)
            fig1.update_layout(bargap=0.1)
            charts['win_loss_timeline'] = json.dumps(fig1, cls=PlotlyJSONEncoder)

        # Chart 2: Performance Curve with dropdown selector
        if not df_player_performance_curve.empty and 'game_time' in df_player_performance_curve.columns:
            print(f"Performance Curve DataFrame shape: {df_player_performance_curve.shape}")
            print(f"Performance Curve columns: {df_player_performance_curve.columns.tolist()}")

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

            print(f"Available metrics: {[m['name'] for m in metrics]}")

            # Create figure with traces for each metric
            fig3 = go.Figure()

            for i, metric in enumerate(metrics):
                print(f"Adding trace {i}: {metric['name']}, visible={i == 0}")
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
                            'title.text': f"Average {metric['name']} Over Game Time"  # Dynamic title
                        }
                    ]
                })

            print(f"Created {len(dropdown_buttons)} dropdown buttons")

            # Update layout with dropdown
            fig3.update_layout(
                title=f"Average {metrics[0]['name']} Over Game Time" if metrics else 'Player Performance Over Game Time',
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

            print(f"Performance curve chart created with {len(fig3.data)} traces")
            charts['performance_curve'] = json.dumps(fig3, cls=PlotlyJSONEncoder)

        # Chart 4: Kill/Death Location Scatter Plot
        if not df_kill_death_stats.empty and 'position_x' in df_kill_death_stats.columns:
            print(f"Kill/Death Stats DataFrame shape: {df_kill_death_stats.shape}")
            print(f"Kills > 0 count: {(df_kill_death_stats['kills'] > 0).sum()}")
            print(f"Deaths > 0 count: {(df_kill_death_stats['deaths'] > 0).sum()}")

            # Filter for kills and deaths
            df_kills = df_kill_death_stats[df_kill_death_stats['kills'] > 0].copy()
            df_deaths = df_kill_death_stats[df_kill_death_stats['deaths'] > 0].copy()

            print(f"Creating chart with {len(df_kills)} kill locations and {len(df_deaths)} death locations")

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

            print(f"Chart created with {len(fig4.data)} traces")
            charts['kd_stats'] = json.dumps(fig4, cls=PlotlyJSONEncoder)

        # Chart 4.5: Player Percentile Distribution
        if not df_player_stats.empty:
            print(f"Player stats shape: {df_player_stats.shape}")

            # Define available metrics for distribution
            metrics = []

            # Common metrics with readable names
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
            ]

            for metric_key, metric_name in metric_configs:
                if f'{metric_key}.avg' in df_player_stats.columns and f'{metric_key}.std' in df_player_stats.columns:
                    # Check if std_dev is reasonable
                    std_dev = float(df_player_stats[f'{metric_key}.std'].iloc[0])
                    if std_dev >= 0.01:  # Only include metrics with reasonable variance
                        metrics.append({
                            'key': metric_key,
                            'name': metric_name
                        })

            if metrics:
                fig4_5 = go.Figure()

                # Create traces for each metric
                for i, metric in enumerate(metrics):
                    metric_key = metric['key']

                    # Get stats
                    avg = float(df_player_stats[f'{metric_key}.avg'].iloc[0])
                    std_dev = float(df_player_stats[f'{metric_key}.std'].iloc[0])

                    # Generate normal distribution curve
                    x_range = np.linspace(avg - 4*std_dev, avg + 4*std_dev, 200)
                    y_range = stats.norm.pdf(x_range, avg, std_dev)

                    print(f"{metric_key}: avg={avg:.2f}, std={std_dev:.2f}, y_max={np.max(y_range):.6f}, x_range=({x_range[0]:.2f}, {x_range[-1]:.2f})")

                    # Get percentiles if available
                    percentiles = {}
                    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
                        col_name = f'{metric_key}.percentile{p}'
                        if col_name in df_player_stats.columns:
                            percentiles[p] = df_player_stats[col_name].iloc[0]

                    # Add distribution curve
                    fig4_5.add_trace(go.Scatter(
                        x=x_range.tolist(),
                        y=y_range.tolist(),
                        mode='lines',
                        name='Distribution',
                        line=dict(color='#66c0f4', width=4),
                        fill='tozeroy',
                        fillcolor='rgba(102, 192, 244, 0.4)',
                        visible=(i == 0),  # Only first trace visible initially
                        hovertemplate='Value: %{x:.2f}<br>Density: %{y:.4f}<extra></extra>'
                    ))

                    # Add vertical line for player's average
                    y_max = float(np.max(y_range))
                    fig4_5.add_trace(go.Scatter(
                        x=[avg, avg],
                        y=[0, y_max * 1.1],  # Extend slightly above curve
                        mode='lines',
                        name='Your Average',
                        line=dict(color='#5cc85c', width=4, dash='dash'),
                        visible=(i == 0),
                        hovertemplate=f'Your Avg: {avg:.2f}<extra></extra>'
                    ))

                    # Add -1 std deviation line
                    fig4_5.add_trace(go.Scatter(
                        x=[avg - std_dev, avg - std_dev],
                        y=[0, y_max * 1.05],
                        mode='lines',
                        name='-1 SD',
                        line=dict(color='#8f98a0', width=2, dash='dot'),
                        visible=(i == 0),
                        showlegend=True,
                        hovertemplate=f'-1 SD: {avg - std_dev:.2f}<extra></extra>'
                    ))

                    # Add +1 std deviation line
                    fig4_5.add_trace(go.Scatter(
                        x=[avg + std_dev, avg + std_dev],
                        y=[0, y_max * 1.05],
                        mode='lines',
                        name='+1 SD',
                        line=dict(color='#8f98a0', width=2, dash='dot'),
                        visible=(i == 0),
                        showlegend=True,
                        hovertemplate=f'+1 SD: {avg + std_dev:.2f}<extra></extra>'
                    ))

                # Create dropdown buttons
                dropdown_buttons = []
                for i, metric in enumerate(metrics):
                    # Create visibility array - 4 traces per metric (curve, avg, -1sd, +1sd)
                    visible = [False] * (len(metrics) * 4)
                    visible[i * 4] = True  # Distribution curve
                    visible[i * 4 + 1] = True  # Your average line
                    visible[i * 4 + 2] = True  # -1 SD line
                    visible[i * 4 + 3] = True  # +1 SD line

                    dropdown_buttons.append({
                        'label': metric['name'],
                        'method': 'update',
                        'args': [
                            {'visible': visible},
                            {
                                'xaxis.title.text': metric['name'],
                                'yaxis.title.text': 'Probability Density',
                                'title.text': f"{metric['name']} Probability Distribution Function"  # Dynamic title
                            }
                        ]
                    })

                # Update layout
                fig4_5.update_layout(
                    title=f"{metrics[0]['name']} Probability Distribution Function",
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
                        orientation='h',
                        yanchor='bottom',
                        y=-0.25,
                        xanchor='center',
                        x=0.5,
                        bgcolor='rgba(27, 40, 56, 0.9)',
                        bordercolor='#3d4e5c',
                        borderwidth=1
                    ),
                    height=600
                )

                print(f"Distribution chart created with {len(fig4_5.data)} traces")
                charts['percentile_dist'] = json.dumps(fig4_5, cls=PlotlyJSONEncoder)

        # Chart 5: Match Statistics Over Time with Weekly Rolling Average
        if not df_match_history.empty:
            print(f"Match history columns: {df_match_history.columns.tolist()}")
            print(f"Match history shape: {df_match_history.shape}")

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

            print(f"Rolling average calculated for {len(df_match_sorted)} matches")

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

            print(f"KDA trend chart created with {len(fig6.data)} traces")
            if len(fig6.data) > 0:
                print(f"First trace has {len(fig6.data[0].x)} data points")
            charts['kda_trend'] = json.dumps(fig6, cls=PlotlyJSONEncoder)

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
                    }
                    print(f"Found Steam profile: {steam_data['username']}")
                else:
                    print(f"No matching profile found for player_id: {player_id}")
            elif isinstance(steam_profile, dict):
                # Single result returned
                if str(steam_profile.get('account_id', '')) == str(player_id):
                    steam_data = {
                        'username': steam_profile.get('personaname', 'Unknown Player'),
                        'avatar_full': steam_profile.get('avatarfull', ''),
                    }

        return charts, summary, steam_data

    except Exception as e:
        print(f"Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return None, None, str(e)


@app.route('/')
def index():
    """Render the home page with input form"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Process player_id and generate visualizations"""
    player_id = request.form.get('player_id', '').strip()

    if not player_id:
        return render_template('index.html', error="Please enter a valid Player ID")

    charts, summary, steam_data = create_visualizations(player_id)

    if charts is None:
        return render_template('index.html', error=f"Error fetching data: {steam_data}")

    return render_template('results.html', player_id=player_id, charts=charts, summary=summary, steam_data=steam_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
