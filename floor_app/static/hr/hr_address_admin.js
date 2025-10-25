(function(){
  function $(id){ return document.getElementById(id); }
  function setVal(id, v){ var el = $('id_'+id); if (el) el.value = v||""; }
  function getSelValues(sel){ return Array.from(sel.options).map(o=>o.value); }

  function composeLine1(addr){
    // Prefer house/building + road; fallback to neighbourhood/suburb
    var parts = [];
    if (addr.house_number) parts.push(addr.house_number);
    if (addr.building) parts.push(addr.building);
    if (addr.road) parts.push(addr.road);
    var s = parts.join(" ").trim();
    if (!s && (addr.neighbourhood || addr.suburb)) s = (addr.neighbourhood || addr.suburb);
    return s || "";
  }

  function fillCountry(iso2){
    var sel = $('id_country_iso2');
    if (!sel) return;
    iso2 = (iso2||"").toUpperCase();
    if (getSelValues(sel).includes(iso2)) sel.value = iso2;
  }

  function applyAddress(addr){
    // Universal
    setVal("address_line1", composeLine1(addr));
    setVal("city", addr.city || addr.town || addr.village || addr.municipality || "");
    setVal("state_region", addr.state || addr.region || addr.state_district || "");
    setVal("postal_code", addr.postcode || "");
    fillCountry(addr.country_code);

    // Structured/KSA-friendly
    setVal("street_name", addr.road || "");
    setVal("building_number", addr.house_number || addr.building || "");
    setVal("neighborhood", addr.neighbourhood || addr.suburb || "");
    // additional_number is not exposed by Nominatim; keep user editable
    // Unit number: try flat or unit info if provided by some OSM data sources
    setVal("unit_number", addr.unit || addr.flat_number || "");

    // If PO Box is detected in display name / address, attempt hint:
    var fa = $('id_full_address');
    var txt = (fa && fa.value || "").toLowerCase();
    if (/p\.?o\.?\s*box|\bpo box\b|pobox|post office box/i.test(txt)) {
      var kind = $('id_address_kind');
      if (kind) kind.value = "PO_BOX";
      // Try to extract a number
      var m = txt.match(/box\s*([0-9]{2,})/i);
      if (m) setVal("po_box", m[1]);
    } else {
      var kind = $('id_address_kind');
      if (kind && !kind.value) kind.value = "STREET";
    }
  }

  function setMarker(map, ref, lat, lng, zoom){
    var marker = ref.marker;
    if (marker) marker.setLatLng([lat, lng]);
    else {
      marker = L.marker([lat, lng], {draggable:true}).addTo(map);
      marker.on('dragend', function(){
        var p = marker.getLatLng();
        setVal("latitude",  p.lat.toFixed(6));
        setVal("longitude", p.lng.toFixed(6));
        reverseGeocode(p.lat, p.lng, function(res){
          if (res && res.address) applyAddress(res.address);
        });
      });
      ref.marker = marker;
    }
    if (zoom) map.setView([lat, lng], zoom);
    setVal("latitude",  (+lat).toFixed(6));
    setVal("longitude", (+lng).toFixed(6));
  }

  function reverseGeocode(lat, lng, cb){
    var url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&addressdetails=1`;
    fetch(url).then(r=>r.json()).then(json=>cb(json || {})).catch(()=>{});
  }

  function geocode(q, cb){
    var url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&addressdetails=1&q=${encodeURIComponent(q)}`;
    fetch(url).then(r=>r.json()).then(list=>cb(Array.isArray(list)? list[0]: null)).catch(()=>{});
  }

  function init(){
    var fa = $('id_full_address');
    var holder = document.createElement('div');
    holder.id = 'hraddr_map';
    holder.style.width = '100%';
    holder.style.height = '360px';
    if (fa && fa.parentElement) fa.parentElement.appendChild(holder);

    var map = L.map('hraddr_map').setView([24.7136, 46.6753], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap'}).addTo(map);

    var ref = {marker:null};

    // Existing lat/lng
    var lat0 = parseFloat(($('id_latitude')||{}).value);
    var lng0 = parseFloat(($('id_longitude')||{}).value);
    if (!isNaN(lat0) && !isNaN(lng0)) setMarker(map, ref, lat0, lng0, 14);

    // Click → set + reverse
    map.on('click', function(e){
      setMarker(map, ref, e.latlng.lat, e.latlng.lng, null);
      reverseGeocode(e.latlng.lat, e.latlng.lng, function(res){
        if (res && res.address) applyAddress(res.address);
      });
    });

    // Search button
    if (fa){
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'button';
      btn.style.marginTop = '6px';
      btn.textContent = 'Search on map';
      btn.onclick = function(){
        geocode(fa.value, function(res){
          if (!res) return;
          var lat = parseFloat(res.lat), lon = parseFloat(res.lon);
          setMarker(map, ref, lat, lon, 15);
          if (res.address) applyAddress(res.address);
          if (!fa.value && res.display_name) fa.value = res.display_name;
        });
      };
      fa.parentElement.appendChild(btn);
      fa.addEventListener('keydown', function(e){
        if (e.key === 'Enter'){ e.preventDefault(); btn.click(); }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function(){ if (window.L) init(); });
})();
