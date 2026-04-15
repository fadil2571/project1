import requests

# Test with correct Emsifa district ID for Godean
# First, get districts for Sleman (regency)
districts = requests.get(
    "https://emsifa.github.io/api-wilayah-indonesia/api/districts/3404.json",
    timeout=5
).json()

godean = None
for d in districts:
    if "GODEAN" in d["name"].upper():
        godean = d
        break

if godean:
    print(f"Found district: {godean['name']} (ID: {godean['id']})")
    
    # Get villages for Godean
    villages = requests.get(
        f"https://emsifa.github.io/api-wilayah-indonesia/api/villages/{godean['id']}.json",
        timeout=5
    ).json()
    print(f"\nEmsifa villages for {godean['name']}: {len(villages)}")
    for v in villages:
        print(f"  {v['id']} - {v['name']}")
    
    # Get postcodes from RajaOngkir Komerce
    ro = requests.get(
        "https://rajaongkir.komerce.id/api/v1/destination/domestic-destination",
        params={"search": godean["name"], "limit": 50},
        headers={"key": "X38ie90K9de223926b6170bdfAoO46H2"},
        timeout=10
    ).json()
    ro_data = ro.get("data", [])
    print(f"\nRajaOngkir results for '{godean['name']}': {len(ro_data)}")
    
    postcode_map = {}
    for item in ro_data:
        v_name = item.get("subdistrict_name", "").upper().strip()
        pc = item.get("zip_code", "")
        print(f"  {v_name} -> {pc}")
        if v_name and pc:
            if v_name not in postcode_map:
                postcode_map[v_name] = []
            if pc not in postcode_map[v_name]:
                postcode_map[v_name].append(pc)
    
    print(f"\nMatching results:")
    for v in villages:
        name = v["name"].upper().strip()
        pcs = postcode_map.get(name, [])
        print(f"  {name} => {pcs}")
else:
    print("Godean district not found")
