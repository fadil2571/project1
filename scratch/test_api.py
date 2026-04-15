import requests
import sys

try:
    url = 'https://emsifa.github.io/api-wilayah-indonesia/api/provinces.json'
    print(f"Testing URL: {url}")
    r = requests.get(url, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Count: {len(data)}")
        print(f"First: {data[0]}")
    else:
        print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
