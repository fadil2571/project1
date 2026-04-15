import json

with open('backup_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

addr_count = 0
order_count = 0

for item in data:
    if item['model'] == 'panel_admin.address':
        fields = item['fields']
        # Ensure sub_district and village exist
        for field in ['sub_district', 'village']:
            if field not in fields or fields[field] is None:
                fields[field] = ""
                addr_count += 1
        # Clean up 'district' if it exists in the JSON fields but not in model (loaddata will ignore it anyway, but clean is better)
        if 'district' in fields:
            del fields['district']
    
    elif item['model'] == 'panel_admin.order':
        fields = item['fields']
        # Ensure shipping_sub_district and shipping_village exist
        for field in ['shipping_sub_district', 'shipping_village']:
            if field not in fields or fields[field] is None:
                fields[field] = ""
                order_count += 1
        # Clean up 'shipping_district'
        if 'shipping_district' in fields:
            del fields['shipping_district']

with open('backup_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print(f"Updated fields in Address records")
print(f"Updated fields in Order records")
