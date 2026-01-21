"""Test using the official deadlock-api-client"""

try:
    from deadlock_api_client import ApiClient, Configuration
    from deadlock_api_client.api.heroes_api import HeroesApi

    print("Testing with official deadlock-api-client...")

    # Create configuration
    config = Configuration(
        host="https://assets.deadlock-api.com"
    )

    # Create API client
    with ApiClient(config) as api_client:
        heroes_api = HeroesApi(api_client)

        # Get heroes
        heroes = heroes_api.get_heroes_v2()
        print(f"Success! Got {len(heroes)} heroes")
        if len(heroes) > 0:
            print(f"First hero: {heroes[0].name if hasattr(heroes[0], 'name') else 'N/A'}")

except ImportError as e:
    print(f"Import error: {e}")
    print("\nTrying alternative import...")

    try:
        import deadlock_api_client
        print(f"Available attributes: {dir(deadlock_api_client)}")
    except ImportError:
        print("deadlock_api_client not installed")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
