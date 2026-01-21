"""Test MMR history endpoint"""
import json
import http.client

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

            print(f"\nSample of 5 records:")
            for i, record in enumerate(data[:5]):
                print(f"Record {i}: {record}")

    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        print(json.dumps(data, indent=2)[:1000])

else:
    error = response.read()
    print(f"Error: {error[:500]}")

conn.close()
