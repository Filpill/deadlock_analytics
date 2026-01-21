import json
import http.client

# Test heroes endpoint
print("Testing heroes endpoint...")
try:
    conn = http.client.HTTPSConnection("assets.deadlock-api.com")
    conn.request("GET", "/v2/heroes", headers={'Accept': "*/*"})
    response = conn.getresponse()

    print(f"Status: {response.status}")
    print(f"Reason: {response.reason}")

    if response.status == 200:
        data = json.loads(response.read().decode("utf-8"))
        print(f"Success! Got {len(data)} heroes")
        if len(data) > 0:
            print(f"First hero: {data[0].get('name', 'N/A')}")
    else:
        error_data = response.read()
        print(f"Error response: {error_data[:500]}")

    conn.close()
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()
