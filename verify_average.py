"""Verify which endpoint is correct by calculating from match history"""
import json
import http.client

player_id = "199540209"

# Get match history
conn = http.client.HTTPSConnection("api.deadlock-api.com")
endpoint = f"/v1/players/{player_id}/match-history?only_stored_history=false"

print(f"Fetching match history: {endpoint}")
conn.request("GET", endpoint, headers={'Accept': "*/*"})
response = conn.getresponse()

if response.status == 200:
    matches = json.loads(response.read().decode("utf-8"))

    print(f"\nMatch History:")
    print(f"  Total matches: {len(matches)}")

    # Calculate average kills from match history
    total_kills = sum(match['player_kills'] for match in matches)
    avg_kills = total_kills / len(matches) if matches else 0

    print(f"  Total kills: {total_kills}")
    print(f"  Calculated average: {avg_kills:.6f}")

    # Compare with API endpoints
    print(f"\n{'='*60}")
    print("COMPARISON:")
    print('='*60)
    print(f"Match history calculation:  {avg_kills:.6f}")
    print(f"account_id (singular):      6.393668")
    print(f"account_ids (plural):       7.666667")

    # Determine which is closer
    diff_singular = abs(avg_kills - 6.393668)
    diff_plural = abs(avg_kills - 7.666667)

    print(f"\nDifference from singular: {diff_singular:.6f}")
    print(f"Difference from plural:   {diff_plural:.6f}")

    if diff_singular < diff_plural:
        print(f"\n✓ SINGULAR (account_id) is CORRECT!")
    else:
        print(f"\n✓ PLURAL (account_ids) is CORRECT!")

else:
    print(f"Error: {response.status}")

conn.close()
