import marimo

__generated_with = "0.19.4"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import http.client
    import marimo as mo
    import pandas as pd

    player_id = "199540209" # SteamID3 Format

    connection= {

        "data-api" : {
            "http_client" : http.client.HTTPSConnection("api.deadlock-api.com"),
            "endpoint" : { 
                "match_history" : f"/v1/players/{player_id}/match-history?only_stored_history=false",
                "player_stats" : f"/v1/analytics/player-stats/metrics?account_ids={player_id}",
                "player_scoreboard" : f"/v1/analytics/scoreboards/players?account_ids={player_id}&sort_by=matches",
                "player_performance_curve" : f"/v1/analytics/player-performance-curve?account_ids={player_id}&resolution=0",
                "kill_death_stats" : f"/v1/analytics/kill-death-stats?account_ids={player_id}",
                "hero_stats" : f"/v1/analytics/hero-stats?account_ids={player_id}&bucket=no_bucket",
                "item_stats" : f"/v1/analytics/item-stats?account_ids={player_id}&bucket=no_bucket",
            }
        },

        "assets-api" : {
            "http_client" : http.client.HTTPSConnection("assets.deadlock-api.com"),
            "endpoint" : { 
                "heroes" : "/v2/heroes",
                "items" : "/v2/items",
                "images" : "/v1/images",
                "icons" : "/v1/icons",
                "sounds" : "/v1/sounds",
            }
        },

        "headers" : { 
            'Accept': "*/*" 
        }

    }
    return connection, json, mo, pd


@app.cell
def _(json, pd):
    def get_request_data(connection, api_selection, endpoint_addr):

        http_client  =  connection[api_selection]["http_client"]
        http_endpoint = connection[api_selection]["endpoint"][endpoint_addr]
        headers = connection["headers"]

        http_client.request("GET", http_endpoint, headers=headers)
        response = connection[api_selection]["http_client"].getresponse()
        raw_data = response.read()

        print(f"Request Status {response.status} | {http_endpoint}")

        if response.status != 200:
            print(f"Error: {raw_data[:200]}")  # Print first 200 chars
            return None

        data = json.loads(raw_data.decode("utf-8"))

        return data


    def move_column_position(df, col_name, col_index):

        cols = df.columns.tolist()
        cols.remove(col_name)
        cols.insert(col_index, col_name)

        return df[cols]


    def format_match_history(df):

        # Replace hero_id with hero name
        df = df.drop(columns=["hero_id", "id"]).rename(columns={"name": "hero_name"})

        # Converting to timestamp
        df['start_ts'] = pd.to_datetime(df['start_time'], unit='s')

        # Rearrange column order
        df = move_column_position(df, col_name="hero_name", col_index=2)
        df = move_column_position(df, col_name="start_ts", col_index=5)

        return df
    return format_match_history, get_request_data


@app.cell
def _(connection, get_request_data):
    hero_names = get_request_data(connection, api_selection="assets-api", endpoint_addr="heroes")
    match_history = get_request_data(connection, api_selection="data-api", endpoint_addr="match_history")
    player_stats = get_request_data(connection, api_selection="data-api", endpoint_addr="player_stats")
    player_performance_curve = get_request_data(connection, api_selection="data-api", endpoint_addr="player_performance_curve")
    kill_death_stats = get_request_data(connection, api_selection="data-api", endpoint_addr="kill_death_stats")
    hero_stats = get_request_data(connection, api_selection="data-api", endpoint_addr="hero_stats")
    item_stats = get_request_data(connection, api_selection="data-api", endpoint_addr="item_stats")
    return (
        hero_names,
        hero_stats,
        item_stats,
        kill_death_stats,
        match_history,
        player_performance_curve,
        player_stats,
    )


@app.cell
def _(
    format_match_history,
    hero_names,
    hero_stats,
    item_stats,
    kill_death_stats,
    match_history,
    pd,
    player_performance_curve,
    player_stats,
):
    # Convert to DataFrame
    df_heroes = pd.json_normalize(hero_names)
    df_match_history = pd.json_normalize(match_history)

    # Merge match data with hero names
    df = pd.merge(df_match_history, df_heroes[["id", "name"]], left_on="hero_id", right_on="id", how="left")
    df = format_match_history(df)

    df_player_stats = pd.json_normalize(player_stats)
    df_player_performance_curve = pd.json_normalize(player_performance_curve)
    df_kill_death_stats = pd.json_normalize(kill_death_stats)
    df_hero_stats = pd.json_normalize(hero_stats)
    df_item_stats = pd.json_normalize(item_stats)

    df_item_stats
    return df, df_player_performance_curve, df_player_stats


@app.cell
def _(df, mo):
    # Display the merged dataframe with hero names
    mo.ui.table(df)
    return


@app.cell
def _(df_player_stats, mo):
    mo.ui.table(df_player_stats)
    return


@app.cell
def _(df_player_performance_curve, mo):
    mo.ui.table(df_player_performance_curve)
    return


if __name__ == "__main__":
    app.run()
