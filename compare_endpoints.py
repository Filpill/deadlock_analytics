"""Compare account_id vs account_ids parameter"""
import json
import http.client

player_id = "199540209"

def test_endpoint(param_name):
    """Test an endpoint and return the response"""
    conn = http.client.HTTPSConnection("api.deadlock-api.com")
    endpoint = f"/v1/analytics/player-stats/metrics?{param_name}={player_id}"

    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print('='*60)

    try:
        conn.request("GET", endpoint, headers={'Accept': "*/*"})
        response = conn.getresponse()

        print(f"Status: {response.status}")

        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))

            # Check response structure
            print(f"Response type: {type(data)}")

            if isinstance(data, dict):
                print(f"Number of keys: {len(data.keys())}")

                if 'kills' in data:
                    kills_data = data['kills']
                    print(f"\nKills data:")
                    print(f"  avg: {kills_data.get('avg')}")
                    print(f"  std: {kills_data.get('std')}")
                    print(f"  percentile50: {kills_data.get('percentile50')}")

                # Check for metadata that might indicate freshness
                if 'metadata' in data:
                    print(f"\nMetadata: {data['metadata']}")

                if 'match_count' in data:
                    print(f"Match count: {data['match_count']}")

            elif isinstance(data, list):
                print(f"Response is a list with {len(data)} items")
                if len(data) > 0:
                    print(f"First item type: {type(data[0])}")
                    if isinstance(data[0], dict) and 'kills' in data[0]:
                        print(f"kills.avg from first item: {data[0]['kills'].get('avg')}")

            return data
        else:
            error = response.read()
            print(f"Error: {error[:500]}")
            return None

    except Exception as e:
        print(f"Exception: {e}")
        return None
    finally:
        conn.close()

# Test both parameters
print("\n" + "="*60)
print("COMPARING account_id vs account_ids")
print("="*60)

result_singular = test_endpoint("account_id")
result_plural = test_endpoint("account_ids")

# Summary comparison
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if result_singular and result_plural:
    if isinstance(result_singular, dict) and isinstance(result_plural, dict):
        if 'kills' in result_singular and 'kills' in result_plural:
            avg_singular = result_singular['kills'].get('avg')
            avg_plural = result_plural['kills'].get('avg')

            print(f"\naccount_id (singular):  kills.avg = {avg_singular}")
            print(f"account_ids (plural):   kills.avg = {avg_plural}")

            if avg_singular != avg_plural:
                print(f"\n⚠️  VALUES ARE DIFFERENT!")
                print(f"Difference: {abs(avg_singular - avg_plural):.4f}")
            else:
                print(f"\n✓ Values match!")
