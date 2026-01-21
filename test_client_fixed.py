"""Test using the official deadlock-api-client with correct imports"""
import sys
sys.path.insert(0, '.venv/lib/python3.12/site-packages')

try:
    from deadlock_api_client import ApiClient, Configuration
    from deadlock_api_client.api import heroes_api
    from deadlock_api_client.api import players_api

    print("Testing heroes endpoint with official client...")

    # Create configuration for assets API
    config = Configuration(
        host="https://assets.deadlock-api.com"
    )

    # Get heroes
    with ApiClient(config) as api_client:
        api_instance = heroes_api.HeroesApi(api_client)
        result = api_instance.get_heroes_v2()
        print(f"Heroes endpoint: Success! Got {len(result)} heroes")
        if len(result) > 0:
            first_hero = result[0]
            print(f"First hero: {first_hero.get('name') if isinstance(first_hero, dict) else getattr(first_hero, 'name', 'N/A')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
