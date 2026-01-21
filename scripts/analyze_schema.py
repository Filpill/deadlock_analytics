import json
import http.client
import pandas as pd

player_id = "199540209"  # Sample player ID

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
                "hero_stats": f"/v1/analytics/hero-stats?account_ids={player_id}&bucket=no_bucket",
                "item_stats": f"/v1/analytics/item-stats?account_ids={player_id}&bucket=no_bucket",
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

    print(f"\nRequest Status {response.status} | {http_endpoint}")

    if response.status != 200:
        print(f"Error: {raw_data[:200]}")
        return None

    data = json.loads(raw_data.decode("utf-8"))
    return data


# Fetch data
connection = get_api_connection(player_id)

print("="*80)
print("FETCHING DATA FROM API ENDPOINTS")
print("="*80)

endpoints = {
    "heroes": ("assets-api", "heroes"),
    "match_history": ("data-api", "match_history"),
    "player_stats": ("data-api", "player_stats"),
    "player_performance_curve": ("data-api", "player_performance_curve"),
    "kill_death_stats": ("data-api", "kill_death_stats"),
    "hero_stats": ("data-api", "hero_stats"),
    "item_stats": ("data-api", "item_stats"),
}

data_results = {}
for name, (api, endpoint) in endpoints.items():
    data = get_request_data(connection, api, endpoint)
    data_results[name] = data

print("\n" + "="*80)
print("ANALYZING SCHEMAS")
print("="*80)

# Analyze each dataset
for name, data in data_results.items():
    print(f"\n{'='*80}")
    print(f"ENDPOINT: {name}")
    print(f"{'='*80}")

    if data is None:
        print("❌ No data returned")
        continue

    if isinstance(data, list):
        print(f"✓ Type: List with {len(data)} items")
        if len(data) > 0:
            df = pd.json_normalize(data)
            print(f"✓ DataFrame shape: {df.shape}")
            print(f"\nColumns ({len(df.columns)}):")
            print("-" * 80)
            for col in df.columns:
                dtype = df[col].dtype
                non_null = df[col].count()
                sample = df[col].iloc[0] if len(df) > 0 else None
                print(f"  • {col:40s} | {str(dtype):15s} | {non_null}/{len(df)} non-null")
                if sample is not None and str(dtype) != 'object':
                    print(f"    Sample: {sample}")

            print(f"\nFirst row sample:")
            print("-" * 80)
            print(json.dumps(df.head(1).to_dict('records')[0] if len(df) > 0 else "Empty", indent=2))

            print(f"\nBasic statistics:")
            print("-" * 80)
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                print(df[numeric_cols].describe())
            else:
                print("No numeric columns")

    elif isinstance(data, dict):
        print(f"✓ Type: Dictionary with {len(data)} keys")
        print(f"\nKeys: {list(data.keys())}")

        # Try to normalize if it looks like it has records
        try:
            df = pd.json_normalize(data)
            print(f"✓ Can be converted to DataFrame: {df.shape}")
            print(f"\nColumns: {list(df.columns)}")
        except:
            print("Cannot convert to DataFrame directly")
            print("\nSample data:")
            print(json.dumps(data, indent=2)[:500])

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
