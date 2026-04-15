import os

file_path = r'c:\Users\User\Documents\SEMESTER-6\!KOPMASSHOP\FADIL\templates\storefront\order\checkout.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the q calculation logic
old_line = 'var q = (district && district.length > 2) ? district : city;'
new_line = "var q = ((district || '') + ' ' + (city || '')).replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '').replace(/,/g, '').replace(/\d+/g, '').trim();"

if old_line in content:
    new_content = content.replace(old_line, new_line)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success: Line replaced.")
else:
    # Try with different whitespace if direct match fails
    import re
    pattern = r'var q = \(district && district\.length > 2\) \? district : city;'
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_line, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: Line replaced with regex.")
    else:
        print("Error: Line not found.")
