"""Test MMR history endpoint"""
import json
import http.client
import pandas as pd

player_id = "199540209"

conn = http.client.HTTPSConnection("api.deadlock-api.com")
endpoint = f"/v1/players/{player_id}/mmr-history"

print(f"Testing: {endpoint}")
conn.request("GET", endpoint, headers={'Accept': "*/*"})
response = conn.getresponse()

print(f"Status: {response.status}")

if response.status == 200:
    data = json.loads(response.read().decode("utf-8"))

    print(f"\nResponse type: {type(data)}")

    if isinstance(data, list):
        print(f"Number of records: {len(data)}")
        if len(data) > 0:
            print(f"\nFirst record:")
            print(json.dumps(data[0], indent=2))

            print(f"\nLast record:")
            print(json.dumps(data[-1], indent=2))

            # Convert to DataFrame to see structure
            df = pd.json_normalize(data)
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"\nFirst 3 rows:")
            print(df.head(3))

            # Check for timestamp column
            if 'timestamp' in df.columns or 'match_time' in df.columns or 'time' in df.columns:
                print(f"\nTimestamp column found!")

    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        print(json.dumps(data, indent=2)[:500])

else:
    error = response.read()
    print(f"Error: {error[:500]}")

conn.close()
