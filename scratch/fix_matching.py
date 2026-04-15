import os

file_path = r'c:\Users\User\Documents\SEMESTER-6\!KOPMASSHOP\FADIL\templates\storefront\order\checkout.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Improved Matching logic
import re

old_block = """          if (district) {
            match = items.find(it => (it.subdistrict_name || '').toLowerCase().includes(district.toLowerCase()));
          }
          if (!match) {
            match = items.find(it => (it.city_name || it.city || it.name || '').toLowerCase().includes(city.toLowerCase()));
          }"""

new_block = """          var q_dist = (district || '').toLowerCase().replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '').trim();
          var q_cty = (city || '').toLowerCase().replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '').trim();
          if (q_dist) {
            match = items.find(it => (it.subdistrict_name || it.city_name || '').toLowerCase().includes(q_dist));
          }
          if (!match && q_cty) {
            match = items.find(it => (it.city_name || it.city || it.name || '').toLowerCase().includes(q_cty));
          }"""

if old_block in content:
    new_content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success: Block replaced.")
else:
    # Use regex for flexibility with whitespace
    pattern = r'if\s*\(district\)\s*\{\s*match\s*=\s*items\.find\(it\s*=>\s*\(it\.subdistrict_name\s*\|\|\s*\'\'\)\.toLowerCase\(\)\.includes\(district\.toLowerCase\(\)\)\);\s*\}\s*if\s*\(!match\)\s*\{\s*match\s*=\s*items\.find\(it\s*=>\s*\(it\.city_name\s*\|\|\s*it\.city\s*\|\|\s*it\.name\s*\|\|\s*\'\'\)\.toLowerCase\(\)\.includes\(city\.toLowerCase\(\)\)\);\s*\}'
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_block, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: Block replaced with regex.")
    else:
        print("Error: Block not found.")
