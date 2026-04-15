import os
import re

file_path = r'c:\Users\User\Documents\SEMESTER-6\!KOPMASSHOP\FADIL\templates\storefront\order\checkout.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add caching logic to autoLookupDestination
# 2. Add 429 handling

old_lookup = """  function autoLookupDestination(city, district, zip) {
    function clean(str) {
      if (!str) return '';
      return str.split(',')[0]
                .replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '')
                .replace(/\d+/g, '')
                .trim();
    }

    var q_district = clean(district);
    var q_city = clean(city);
    var q = q_district || q_city;

    var statusEl = document.getElementById('destStatusText');
    statusEl.innerHTML = '⏳ Mencari lokasi RajaOngkir...';
    
    fetch('/api/shipping/search-destination/?search=' + encodeURIComponent(q))
      .then(r => r.json())
      .then(data => {
        var items = [];
        if (data.success && data.data) {
          if (Array.isArray(data.data)) items = data.data;
          else if (data.data.rajaongkir && data.data.rajaongkir.results) items = data.data.rajaongkir.results;
        }
        
        if (items.length > 0) {
          var match = null;
          var q_dist = (district || '').toLowerCase().replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '').trim();
          var q_cty = (city || '').toLowerCase().replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '').trim();
          if (q_dist) {
            match = items.find(it => (it.subdistrict_name || it.city_name || '').toLowerCase().includes(q_dist));
          }
          if (!match && q_cty) {
            match = items.find(it => (it.city_name || it.city || it.name || '').toLowerCase().includes(q_cty));
          }
          var best = match || items[0];
          destId.value = best.id || best.city_id || best.subdistrict_id || '';
          var label = best.subdistrict_name ? (best.subdistrict_name + ', ' + (best.city_name || best.city || '')) : (best.city_name || best.name || '');
          destSearch.value = label;
          statusEl.innerHTML = '📍 <strong>' + label + '</strong>';
          checkCalcReady();
          if (destId.value && courierSelect.value) {
            setTimeout(() => { btnCalc.click(); }, 300);
          }
        } 
        else if (q === q_district && q_city && q_district !== q_city) {
          autoLookupDestination(city, '', zip);
        } else {
          statusEl.innerHTML = '<span style="color:red">⚠️ Lokasi tidak ditemukan.</span>';
          document.getElementById('destSearchWrapper').style.display = 'block';
        }
      })
      .catch(() => {
        statusEl.innerHTML = '<span style="color:red">⚠️ Gagal memuat data.</span>';
        document.getElementById('destSearchWrapper').style.display = 'block';
      });
  }"""

new_lookup = """  var destCache = {}; // Simple cache to prevent rate limits

  function autoLookupDestination(city, district, zip) {
    function clean(str) {
      if (!str) return '';
      return str.split(',')[0]
                .replace(/kabupaten|kota|kab\.?|kec\.?|kecamatan/gi, '')
                .replace(/\d+/g, '')
                .trim();
    }

    var q_district = clean(district);
    var q_city = clean(city);
    var q = q_district || q_city;
    var cacheKey = q.toLowerCase();

    var statusEl = document.getElementById('destStatusText');

    if (destCache[cacheKey]) {
      var best = destCache[cacheKey];
      destId.value = best.id;
      destSearch.value = best.label;
      statusEl.innerHTML = '📍 <strong>' + best.label + '</strong>';
      checkCalcReady();
      if (destId.value && courierSelect.value) setTimeout(() => { btnCalc.click(); }, 300);
      return;
    }

    statusEl.innerHTML = '⏳ Mencari lokasi...';
    
    fetch('/api/shipping/search-destination/?search=' + encodeURIComponent(q))
      .then(r => {
        if (r.status === 429) throw new Error('LIMIT');
        return r.json();
      })
      .then(data => {
        var items = [];
        if (data.success && data.data) {
          if (Array.isArray(data.data)) items = data.data;
          else if (data.data.rajaongkir && data.data.rajaongkir.results) items = data.data.rajaongkir.results;
        }
        
        if (items.length > 0) {
          var match = null;
          var q_dist = q_district.toLowerCase();
          var q_cty = q_city.toLowerCase();
          if (q_dist) {
            match = items.find(it => (it.subdistrict_name || it.city_name || '').toLowerCase().includes(q_dist));
          }
          if (!match && q_cty) {
            match = items.find(it => (it.city_name || it.city || it.name || '').toLowerCase().includes(q_cty));
          }
          var bestItem = match || items[0];
          var id = bestItem.id || bestItem.city_id || bestItem.subdistrict_id || '';
          var label = bestItem.subdistrict_name ? (bestItem.subdistrict_name + ', ' + (bestItem.city_name || bestItem.city || '')) : (bestItem.city_name || bestItem.name || '');
          
          destId.value = id;
          destSearch.value = label;
          statusEl.innerHTML = '📍 <strong>' + label + '</strong>';
          
          // Save to cache
          destCache[cacheKey] = { id: id, label: label };
          
          checkCalcReady();
          if (destId.value && courierSelect.value) {
            setTimeout(() => { btnCalc.click(); }, 300);
          }
        } 
        else if (q === q_district && q_city && q_district !== q_city) {
          autoLookupDestination(city, '', zip);
        } else {
          statusEl.innerHTML = '<span style="color:red">⚠️ Lokasi tidak ditemukan.</span>';
          document.getElementById('destSearchWrapper').style.display = 'block';
        }
      })
      .catch(err => {
        if (err.message === 'LIMIT') {
          statusEl.innerHTML = '<span style="color:orange">⚠️ Limit tercapai. Silakan ketik manual.</span>';
        } else {
          statusEl.innerHTML = '<span style="color:red">⚠️ Gagal memuat data.</span>';
        }
        document.getElementById('destSearchWrapper').style.display = 'block';
      });
  }"""

# Use a simpler replacement since the block is large
pattern = re.escape(old_lookup).replace(r'\ ', r'\s+')
if re.search(pattern, content, re.MULTILINE):
    new_content = re.sub(pattern, new_lookup, content, flags=re.MULTILINE)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success: Caching and 429 logic added.")
else:
    # Fallback to direct string find if regex fails
    if old_lookup in content:
        new_content = content.replace(old_lookup, new_lookup)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: Caching and 429 logic added (Direct String).")
    else:
        # Final fallback: try to find start and end of function
        start_marker = "function autoLookupDestination(city, district, zip) {"
        end_marker = "  courierSelect.addEventListener('change', function() {"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            pre = content[:start_idx]
            post = content[end_idx:]
            new_content = pre + new_lookup + "\n\n" + post
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Success: Caching and 429 logic added (Marker search).")
        else:
            print("Error: Function not found.")
