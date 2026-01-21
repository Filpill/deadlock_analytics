"""Test images endpoint"""
import json
import http.client

conn = http.client.HTTPSConnection("assets.deadlock-api.com")
endpoint = "/v1/images"

print(f"Testing: {endpoint}")
conn.request("GET", endpoint, headers={'Accept': "*/*"})
response = conn.getresponse()

print(f"Status: {response.status}")

if response.status == 200:
    data = json.loads(response.read().decode("utf-8"))

    print(f"\nResponse type: {type(data)}")

    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())[:20]}")

        # Look for hero images
        hero_keys = [k for k in data.keys() if k.startswith('heroes_')]
        print(f"\nHero image keys (first 10): {hero_keys[:10]}")

        if hero_keys:
            print(f"\nSample hero image:")
            sample_key = hero_keys[0]
            print(f"{sample_key}: {data[sample_key]}")

else:
    error = response.read()
    print(f"Error: {error[:500]}")

conn.close()
