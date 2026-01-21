"""Test ranks endpoint"""
import json
import http.client

conn = http.client.HTTPSConnection("assets.deadlock-api.com")
endpoint = "/v2/ranks"

print(f"Testing: {endpoint}")
conn.request("GET", endpoint, headers={'Accept': "*/*"})
response = conn.getresponse()

print(f"Status: {response.status}")

if response.status == 200:
    data = json.loads(response.read().decode("utf-8"))

    print(f"\nResponse type: {type(data)}")

    if isinstance(data, list):
        print(f"Number of ranks: {len(data)}")
        if len(data) > 0:
            print(f"\nFirst rank:")
            print(json.dumps(data[0], indent=2))

            print(f"\nLast rank:")
            print(json.dumps(data[-1], indent=2))

            print(f"\nAll rank names:")
            for rank in data:
                print(f"  Rank {rank.get('rank', 'N/A')}: {rank.get('name', 'N/A')}")

    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        print(json.dumps(data, indent=2)[:1000])

else:
    error = response.read()
    print(f"Error: {error[:500]}")

conn.close()
