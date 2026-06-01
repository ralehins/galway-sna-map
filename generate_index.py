"""Generate index.html for GitHub Pages with embedded school data and vacancy overlay."""
import csv
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "..", "13_School_Map_Dashboard", "galway_schools_data.csv")
OUT_PATH = os.path.join(BASE, "index.html")

# Load school data
with open(CSV_PATH, encoding="utf-8") as f:
    schools = list(csv.DictReader(f))

school_json = json.dumps(schools, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Galway SNA School Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
        .header {{ background: #1a5276; color: white; padding: 10px 15px; text-align: center; position: sticky; top: 0; z-index: 1100; }}
        .header h1 {{ font-size: 16px; margin-bottom: 2px; }}
        .header p {{ font-size: 11px; opacity: 0.8; }}
        .controls {{ background: white; padding: 10px 12px; border-bottom: 1px solid #ddd; z-index: 1000; }}
        .controls-row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 8px; }}
        .controls-row:last-child {{ margin-bottom: 0; }}
        .control-group {{ display: flex; align-items: center; gap: 5px; }}
        .control-group label {{ font-size: 12px; font-weight: 600; color: #333; white-space: nowrap; }}
        .control-group select, .control-group input[type="text"] {{ font-size: 13px; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; background: white; }}
        .search-box {{ flex: 1; min-width: 150px; }}
        .search-box input {{ width: 100%; font-size: 13px; padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; }}
        .filter-checks {{ display: flex; flex-wrap: wrap; gap: 6px 12px; }}
        .filter-checks label {{ font-size: 11px; display: flex; align-items: center; gap: 3px; cursor: pointer; }}
        .filter-checks input[type="checkbox"] {{ width: 14px; height: 14px; }}
        .btn-row {{ display: flex; gap: 6px; flex-wrap: wrap; }}
        .btn {{ font-size: 11px; padding: 5px 10px; border: 1px solid #1a5276; background: white; color: #1a5276; border-radius: 4px; cursor: pointer; white-space: nowrap; }}
        .btn:hover {{ background: #1a5276; color: white; }}
        .btn.active {{ background: #1a5276; color: white; }}
        .map-list-container {{ display: flex; width: 100%; height: calc(100vh - 280px); min-height: 300px; }}
        #map {{ flex: 1; min-width: 0; }}
        .school-list-panel {{ width: 50%; max-width: 420px; background: white; border-left: 2px solid #ddd; display: flex; flex-direction: column; overflow: hidden; transition: width 0.25s ease, max-width 0.25s ease; }}
        .school-list-panel.hidden {{ width: 0; max-width: 0; border-left: none; }}
        .list-header {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; background: #1a5276; color: white; font-size: 13px; font-weight: 600; flex-shrink: 0; }}
        .list-header .list-count {{ font-weight: 400; font-size: 11px; opacity: 0.85; }}
        .list-close-btn {{ background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0 4px; line-height: 1; }}
        .list-sort {{ display: flex; gap: 4px; padding: 6px 10px; background: #f0f4f8; border-bottom: 1px solid #ddd; flex-shrink: 0; }}
        .list-sort button {{ font-size: 10px; padding: 3px 8px; border: 1px solid #aaa; background: white; border-radius: 3px; cursor: pointer; }}
        .list-sort button.active {{ background: #1a5276; color: white; border-color: #1a5276; }}
        .school-list {{ flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; }}
        .school-list-item {{ padding: 8px 10px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; gap: 8px; align-items: flex-start; }}
        .school-list-item:hover {{ background: #f0f6fc; }}
        .school-list-item.has-vacancy {{ background: #eafaf1; border-left: 3px solid #27ae60; }}
        .school-list-item.has-vacancy:hover {{ background: #d5f5e3; }}
        .list-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; }}
        .list-info {{ flex: 1; min-width: 0; }}
        .list-name {{ font-size: 12px; font-weight: 600; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .list-meta {{ font-size: 10px; color: #777; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .list-badges {{ display: flex; gap: 4px; margin-top: 3px; flex-wrap: wrap; }}
        .list-badge {{ font-size: 9px; padding: 1px 5px; border-radius: 3px; font-weight: 600; }}
        .list-empty {{ padding: 20px; text-align: center; color: #999; font-size: 12px; }}
        .summary {{ background: white; padding: 8px 12px; border-top: 1px solid #ddd; display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 11px; color: #555; }}
        .summary .stat {{ display: flex; gap: 4px; }}
        .summary .stat-value {{ font-weight: 700; color: #333; }}
        .stat-suitable .stat-value {{ color: #2471a3; }}
        .stat-vacancy .stat-value {{ color: #27ae60; }}
        .legend {{ background: white; padding: 6px 12px; border-top: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 10px; color: #666; }}
        .legend-item {{ display: flex; align-items: center; gap: 4px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
        .dot-blue {{ background: #2471a3; }}
        .dot-orange {{ background: #e67e22; }}
        .dot-grey {{ background: #aaa; }}
        .dot-red {{ background: #e74c3c; }}
        .dot-green {{ background: #27ae60; border: 2px solid #1e8449; }}
        .school-popup {{ font-size: 12px; line-height: 1.5; max-width: 280px; }}
        .school-popup h3 {{ font-size: 13px; margin-bottom: 4px; color: #1a5276; }}
        .school-popup .official-name {{ font-size: 11px; color: #777; margin-bottom: 6px; }}
        .school-popup .info-row {{ display: flex; gap: 4px; }}
        .school-popup .info-label {{ font-weight: 600; color: #555; min-width: 90px; }}
        .school-popup .info-value {{ color: #333; }}
        .school-popup .tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
        .tag-yes {{ background: #d4efdf; color: #27ae60; }}
        .tag-no {{ background: #fadbd8; color: #c0392b; }}
        .tag-maybe {{ background: #fdebd0; color: #e67e22; }}
        .tag-unknown {{ background: #eee; color: #888; }}
        .tag-vacancy {{ background: #27ae60; color: white; }}
        .school-popup a {{ color: #2471a3; }}
        .btn-toggle-list {{ font-size: 11px; padding: 5px 10px; border: 1px solid #1a5276; background: #1a5276; color: white; border-radius: 4px; cursor: pointer; white-space: nowrap; }}
        .btn-toggle-list:hover {{ background: #154360; }}
        .btn-toggle-list.list-off {{ background: white; color: #1a5276; }}
        .vacancy-banner {{ background: #27ae60; color: white; padding: 6px 12px; text-align: center; font-size: 12px; }}
        .vacancy-banner a {{ color: #d5f5e3; }}
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 14px; }}
            .map-list-container {{ height: calc(100vh - 320px); flex-direction: column; }}
            .school-list-panel {{ width: 100%; max-width: 100%; border-left: none; border-top: 2px solid #ddd; height: 50%; }}
            .school-list-panel.hidden {{ height: 0; }}
            .controls {{ padding: 8px 10px; }}
        }}
        .collapse-toggle {{ display: none; text-align: center; padding: 4px; background: #eee; font-size: 11px; cursor: pointer; color: #555; }}
        @media (max-width: 600px) {{ .collapse-toggle {{ display: block; }} .controls.collapsed .controls-row:not(:first-child) {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Galway SNA School Map</h1>
        <p>Primary Schools &middot; County Galway &middot; Live Vacancy Highlights</p>
    </div>
    <div class="vacancy-banner" id="vacancyBanner">Loading vacancy data...</div>

    <div class="controls" id="controlsPanel">
        <div class="controls-row">
            <div class="control-group">
                <label for="radiusSelect">Radius:</label>
                <select id="radiusSelect">
                    <option value="5">5 km</option>
                    <option value="10">10 km</option>
                    <option value="15" selected>15 km</option>
                    <option value="20">20 km</option>
                    <option value="30">30 km</option>
                    <option value="50">50 km</option>
                    <option value="0">All</option>
                </select>
            </div>
            <div class="search-box">
                <input type="text" id="searchBox" placeholder="Search school, roll number, or town...">
            </div>
        </div>
        <div class="controls-row">
            <div class="filter-checks">
                <label><input type="checkbox" id="chkSuitable" checked> <span style="color:#2471a3">&#9679;</span> Suitable</label>
                <label><input type="checkbox" id="chkMaybe" checked> <span style="color:#e67e22">&#9679;</span> Maybe</label>
                <label><input type="checkbox" id="chkUnsuitable"> <span style="color:#aaa">&#9679;</span> Unsuitable</label>
                <label><input type="checkbox" id="chkUnknown" checked> <span style="color:#888">&#9679;</span> Unknown</label>
                <label><input type="checkbox" id="chkSNAOnly"> SNA alloc only</label>
                <label><input type="checkbox" id="chkVacancyOnly"> <span style="color:#27ae60;font-weight:bold">&#9679;</span> Active vacancy only</label>
            </div>
        </div>
        <div class="controls-row">
            <div class="btn-row">
                <button class="btn" id="btnReset">Reset</button>
                <button class="btn" id="btnFitAll">Fit All</button>
                <button class="btn" id="btnFitRadius">Fit Radius</button>
                <button class="btn-toggle-list" id="btnToggleList">&#9776; List</button>
            </div>
        </div>
    </div>
    <div class="collapse-toggle" id="collapseToggle">&#9660; Filters</div>

    <div class="map-list-container">
        <div id="map"></div>
        <div class="school-list-panel" id="listPanel">
            <div class="list-header">
                <span>Schools <span class="list-count" id="listCount"></span></span>
                <button class="list-close-btn" id="btnCloseList">&times;</button>
            </div>
            <div class="list-sort">
                <button class="active" data-sort="distance">Distance</button>
                <button data-sort="name">Name</button>
                <button data-sort="priority">Priority</button>
                <button data-sort="sna">SNA</button>
                <button data-sort="vacancy">Vacancy</button>
            </div>
            <div class="school-list" id="schoolList"></div>
        </div>
    </div>

    <div class="summary" id="summaryPanel">
        <div class="stat"><span>Total:</span> <span class="stat-value" id="statTotal">0</span></div>
        <div class="stat"><span>In radius:</span> <span class="stat-value" id="statInRadius">0</span></div>
        <div class="stat stat-suitable"><span>Suitable:</span> <span class="stat-value" id="statSuitable">0</span></div>
        <div class="stat stat-vacancy"><span>Active vacancies:</span> <span class="stat-value" id="statVacancy">0</span></div>
    </div>

    <div class="legend">
        <div class="legend-item"><span class="legend-dot dot-blue"></span> Suitable</div>
        <div class="legend-item"><span class="legend-dot dot-orange"></span> Maybe</div>
        <div class="legend-item"><span class="legend-dot dot-grey"></span> Unsuitable</div>
        <div class="legend-item"><span class="legend-dot dot-green"></span> Active SNA Vacancy</div>
        <div class="legend-item"><span class="legend-dot dot-red"></span> Home</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
    const HOME_LAT = 53.28533405929237;
    const HOME_LNG = -8.985587668067396;
    const SCHOOL_DATA = {school_json};

    let allSchools = [];
    let vacancyMap = {{}};  // roll_number -> vacancy info
    let markers = [];
    let markerMap = {{}};
    let filteredSchools = [];
    let radiusCircle = null;
    let listSort = 'distance';

    function haversine(lat1, lon1, lat2, lon2) {{
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2)*Math.sin(dLat/2) + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)*Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }}

    function getMarkerColor(s) {{
        if (s._hasVacancy) return '#27ae60';
        if (s.Suitable_For_Candidate === 'Yes') return '#2471a3';
        if (s.Suitable_For_Candidate === 'Maybe') return '#e67e22';
        if (s.Suitable_For_Candidate === 'No') return '#aaaaaa';
        return '#888888';
    }}

    function getMarkerSize(s) {{
        return s._hasVacancy ? 24 : 20;
    }}

    function createCircleIcon(color, size) {{
        const r = size / 2;
        return L.divIcon({{
            className: 'custom-marker',
            html: '<svg width="'+size+'" height="'+size+'" viewBox="0 0 '+size+' '+size+'"><circle cx="'+r+'" cy="'+r+'" r="'+(r-2)+'" fill="'+color+'" stroke="white" stroke-width="2" opacity="0.9"/></svg>',
            iconSize: [size, size],
            iconAnchor: [r, r],
            popupAnchor: [0, -r]
        }});
    }}

    function esc(str) {{ if (!str) return ''; const el = document.createElement('span'); el.textContent = str; return el.innerHTML; }}
    function suitTag(v) {{ if(v==='Yes') return '<span class="tag tag-yes">Yes</span>'; if(v==='No') return '<span class="tag tag-no">No</span>'; if(v==='Maybe') return '<span class="tag tag-maybe">Maybe</span>'; return '<span class="tag tag-unknown">?</span>'; }}

    function buildPopup(s) {{
        let html = '<div class="school-popup">';
        html += '<h3>'+esc(s.School_Name_Display)+'</h3>';
        if (s.School_Name_Official && s.School_Name_Official !== s.School_Name_Display) html += '<div class="official-name">'+esc(s.School_Name_Official)+'</div>';
        if (s._hasVacancy) {{
            const v = vacancyMap[s.Roll_Number];
            html += '<div style="background:#27ae60;color:white;padding:4px 8px;border-radius:4px;margin-bottom:6px;font-weight:600;font-size:11px;">';
            html += '&#9989; ACTIVE SNA VACANCY — '+esc(v.post_type);
            if (v.closing_date) html += ' — Closes: '+esc(v.closing_date);
            html += '<br><a href="https://www.educationposts.ie/post/view/'+esc(v.post_id)+'" target="_blank" style="color:#d5f5e3;">View on EducationPosts</a>';
            html += '</div>';
        }}
        html += '<div class="info-row"><span class="info-label">Roll No:</span><span class="info-value">'+esc(s.Roll_Number)+'</span></div>';
        html += '<div class="info-row"><span class="info-label">Address:</span><span class="info-value">'+esc(s.Address||s.Town_Area)+'</span></div>';
        html += '<div class="info-row"><span class="info-label">Language:</span><span class="info-value">'+esc(s.Language_Label)+'</span></div>';
        html += '<div class="info-row"><span class="info-label">Suitable:</span><span class="info-value">'+suitTag(s.Suitable_For_Candidate)+'</span></div>';
        html += '<div class="info-row"><span class="info-label">SNA Alloc:</span><span class="info-value">'+(s.SNA_Allocation_Value? esc(s.SNA_Allocation_Value)+' posts':'?')+'</span></div>';
        if (s._distance !== undefined && s._distance !== Infinity) html += '<div class="info-row"><span class="info-label">Distance:</span><span class="info-value">'+s._distance.toFixed(1)+' km</span></div>';
        html += '</div>';
        return html;
    }}

    // Init map
    const map = L.map('map', {{ center: [HOME_LAT, HOME_LNG], zoom: 11, zoomControl: true }});
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap',
        maxZoom: 18
    }}).addTo(map);

    const homeIcon = L.divIcon({{
        className: 'home-marker',
        html: '<svg width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#e74c3c" stroke="white" stroke-width="2"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="12" font-weight="bold">H</text></svg>',
        iconSize: [24, 24], iconAnchor: [12, 12]
    }});
    L.marker([HOME_LAT, HOME_LNG], {{ icon: homeIcon, zIndexOffset: 1000 }}).addTo(map).bindPopup('<b>Home</b>');

    // Load schools
    allSchools = SCHOOL_DATA.filter(s => s.Roll_Number && s.Roll_Number.trim());
    allSchools.forEach(s => {{
        const lat = parseFloat(s.Latitude), lng = parseFloat(s.Longitude);
        if (!isNaN(lat) && !isNaN(lng)) {{ s._lat = lat; s._lng = lng; s._hasCoords = true; s._distance = haversine(HOME_LAT, HOME_LNG, lat, lng); }}
        else {{ s._hasCoords = false; s._distance = Infinity; }}
        s._hasVacancy = false;
    }});

    // Load vacancies
    fetch('vacancies.json').then(r => r.json()).then(data => {{
        const banner = document.getElementById('vacancyBanner');
        if (data && data.vacancies) {{
            data.vacancies.forEach(v => {{
                if (v.roll_number) vacancyMap[v.roll_number] = v;
            }});
            allSchools.forEach(s => {{ s._hasVacancy = !!vacancyMap[s.Roll_Number]; }});
            const count = data.vacancies.length;
            const dt = data.scraped_at ? new Date(data.scraped_at).toLocaleDateString() : '?';
            banner.innerHTML = '&#9989; <strong>'+count+' active SNA vacancies</strong> in Galway (updated '+dt+')';
        }} else {{
            banner.textContent = 'No vacancy data available';
        }}
        applyFilters();
    }}).catch(() => {{
        document.getElementById('vacancyBanner').textContent = 'Vacancy data unavailable';
        applyFilters();
    }});

    function applyFilters() {{
        const radius = parseInt(document.getElementById('radiusSelect').value);
        const search = document.getElementById('searchBox').value.trim().toLowerCase();
        const showSuitable = document.getElementById('chkSuitable').checked;
        const showMaybe = document.getElementById('chkMaybe').checked;
        const showUnsuitable = document.getElementById('chkUnsuitable').checked;
        const showUnknown = document.getElementById('chkUnknown').checked;
        const snaOnly = document.getElementById('chkSNAOnly').checked;
        const vacancyOnly = document.getElementById('chkVacancyOnly').checked;

        markers.forEach(m => map.removeLayer(m));
        markers = []; markerMap = {{}}; filteredSchools = [];
        if (radiusCircle) {{ map.removeLayer(radiusCircle); radiusCircle = null; }}

        if (radius > 0) {{
            radiusCircle = L.circle([HOME_LAT, HOME_LNG], {{ radius: radius*1000, color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.05, weight: 2, dashArray: '5,5' }}).addTo(map);
        }}

        let inRadius=0, suitable=0, vacCount=0;
        allSchools.forEach(s => {{
            if (!s._hasCoords) return;
            if (radius > 0 && s._distance > radius) return;
            inRadius++;
            if (s.Suitable_For_Candidate === 'Yes') suitable++;
            if (s._hasVacancy) vacCount++;

            const suit = s.Suitable_For_Candidate;
            if (suit==='Yes' && !showSuitable) return;
            if (suit==='Maybe' && !showMaybe) return;
            if (suit==='No' && !showUnsuitable) return;
            if (!['Yes','Maybe','No'].includes(suit) && !showUnknown) return;
            if (snaOnly && s.Has_SNA_Allocation !== 'Yes') return;
            if (vacancyOnly && !s._hasVacancy) return;

            if (search) {{
                const hay = [s.School_Name_Display, s.School_Name_Official, s.Roll_Number, s.Town_Area, s.Address].join(' ').toLowerCase();
                if (!hay.includes(search)) return;
            }}

            const color = getMarkerColor(s);
            const size = getMarkerSize(s);
            const icon = createCircleIcon(color, size);
            const marker = L.marker([s._lat, s._lng], {{ icon: icon, zIndexOffset: s._hasVacancy ? 500 : 0 }}).bindPopup(buildPopup(s), {{ maxWidth: 300 }}).addTo(map);
            markers.push(marker);
            markerMap[s.Roll_Number] = marker;
            filteredSchools.push(s);
        }});

        document.getElementById('statTotal').textContent = allSchools.length;
        document.getElementById('statInRadius').textContent = inRadius;
        document.getElementById('statSuitable').textContent = suitable;
        document.getElementById('statVacancy').textContent = vacCount;
        renderSchoolList();
    }}

    function renderSchoolList() {{
        const container = document.getElementById('schoolList');
        const countEl = document.getElementById('listCount');
        const sorted = filteredSchools.slice();

        if (listSort==='distance') sorted.sort((a,b)=>(a._distance||9999)-(b._distance||9999));
        else if (listSort==='name') sorted.sort((a,b)=>(a.School_Name_Display||'').localeCompare(b.School_Name_Display||''));
        else if (listSort==='priority') {{ const po={{'High':0,'Medium':1,'Low':2,'Not suitable':3}}; sorted.sort((a,b)=>(po[a.Priority]||4)-(po[b.Priority]||4)); }}
        else if (listSort==='sna') sorted.sort((a,b)=>(parseFloat(b.SNA_Allocation_Value)||0)-(parseFloat(a.SNA_Allocation_Value)||0));
        else if (listSort==='vacancy') sorted.sort((a,b)=>(b._hasVacancy?1:0)-(a._hasVacancy?1:0) || (a._distance||9999)-(b._distance||9999));

        countEl.textContent = '('+sorted.length+')';
        if (!sorted.length) {{ container.innerHTML = '<div class="list-empty">No matches</div>'; return; }}

        let html = '';
        sorted.forEach(s => {{
            const color = getMarkerColor(s);
            const dist = s._distance!==Infinity ? s._distance.toFixed(1)+' km' : '?';
            const sna = s.SNA_Allocation_Value ? s.SNA_Allocation_Value+' posts' : '';
            const vacClass = s._hasVacancy ? ' has-vacancy' : '';
            html += '<div class="school-list-item'+vacClass+'" data-roll="'+esc(s.Roll_Number)+'">';
            html += '<div class="list-dot" style="background:'+color+'"></div>';
            html += '<div class="list-info">';
            html += '<div class="list-name">'+esc(s.School_Name_Display)+'</div>';
            html += '<div class="list-meta">'+esc(s.Town_Area)+' &middot; '+dist+(sna?' &middot; '+sna:'')+'</div>';
            html += '<div class="list-badges">';
            if (s._hasVacancy) {{ const v=vacancyMap[s.Roll_Number]; html += '<span class="list-badge tag-vacancy">VACANCY'+(v.closing_date?' — '+v.closing_date:'')+'</span> '; }}
            html += '<span class="list-badge tag-unknown">'+esc(s.Language_Label)+'</span>';
            if (s.Has_SNA_Allocation==='Yes') html += '<span class="list-badge tag-yes">SNA</span>';
            html += '</div></div></div>';
        }});
        container.innerHTML = html;

        container.querySelectorAll('.school-list-item').forEach(el => {{
            el.addEventListener('click', function() {{
                const marker = markerMap[this.getAttribute('data-roll')];
                if (marker) {{ map.setView(marker.getLatLng(), 14); marker.openPopup(); }}
            }});
        }});
    }}

    // Event listeners
    ['radiusSelect','searchBox','chkSuitable','chkMaybe','chkUnsuitable','chkUnknown','chkSNAOnly','chkVacancyOnly'].forEach(id => {{
        const el = document.getElementById(id);
        el.addEventListener(el.type==='checkbox'?'change': el.tagName==='SELECT'?'change':'input', applyFilters);
    }});

    document.getElementById('btnReset').addEventListener('click', () => {{
        document.getElementById('radiusSelect').value = '15';
        document.getElementById('searchBox').value = '';
        document.getElementById('chkSuitable').checked = true;
        document.getElementById('chkMaybe').checked = true;
        document.getElementById('chkUnsuitable').checked = false;
        document.getElementById('chkUnknown').checked = true;
        document.getElementById('chkSNAOnly').checked = false;
        document.getElementById('chkVacancyOnly').checked = false;
        applyFilters(); map.setView([HOME_LAT, HOME_LNG], 11);
    }});
    document.getElementById('btnFitAll').addEventListener('click', () => {{ if(markers.length) map.fitBounds(L.featureGroup(markers).getBounds().pad(0.1)); }});
    document.getElementById('btnFitRadius').addEventListener('click', () => {{ if(radiusCircle) map.fitBounds(radiusCircle.getBounds()); else map.setView([HOME_LAT,HOME_LNG],11); }});
    document.getElementById('btnToggleList').addEventListener('click', function() {{ document.getElementById('listPanel').classList.toggle('hidden'); this.classList.toggle('list-off'); setTimeout(()=>map.invalidateSize(),300); }});
    document.getElementById('btnCloseList').addEventListener('click', () => {{ document.getElementById('listPanel').classList.add('hidden'); document.getElementById('btnToggleList').classList.add('list-off'); setTimeout(()=>map.invalidateSize(),300); }});
    document.querySelectorAll('.list-sort button').forEach(btn => {{ btn.addEventListener('click', function() {{ document.querySelectorAll('.list-sort button').forEach(b=>b.classList.remove('active')); this.classList.add('active'); listSort=this.getAttribute('data-sort'); renderSchoolList(); }}); }});
    document.getElementById('collapseToggle').addEventListener('click', () => document.getElementById('controlsPanel').classList.toggle('collapsed'));
    window.addEventListener('resize', () => map.invalidateSize());

    // Initial render (without vacancies — they load async)
    applyFilters();
    </script>
</body>
</html>'''

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Generated: {OUT_PATH} ({len(html)//1024} KB)")
