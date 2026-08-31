#!/usr/bin/env python
"""Build docs/app.html with exact screenshot copies embedded as base64."""
import base64, os

SCREENSHOTS = [
    ('docs/screenshots/01_dashboard.jpeg', 'dashboard', 'Dashboard'),
    ('docs/screenshots/02_requirements.jpeg', 'requirements', 'Requirements'),
    ('docs/screenshots/03_materials.jpeg', 'materials', 'Materials'),
    ('docs/screenshots/04_generation.jpeg', 'generation', 'Generation'),
    ('docs/screenshots/05_3d_workspace.jpeg', 'library', 'Material Library'),
    ('docs/screenshots/06_validation.jpeg', 'validation', 'Validation'),
    ('docs/screenshots/07_review.jpeg', 'review', 'Review'),
]

images = {}
for path, key, label in SCREENSHOTS:
    with open(path, 'rb') as f:
        images[key] = {'data': base64.b64encode(f.read()).decode(), 'label': label}

# Build screen HTML blocks
screen_blocks = ""
for i, (path, key, label) in enumerate(SCREENSHOTS):
    b64 = images[key]['data']
    active = ' active' if i == 0 else ''
    screen_blocks += f'  <div class="screen{active}" id="s-{key}">\n'
    screen_blocks += f'    <img src="data:image/jpeg;base64,{b64}" alt="{label}" onclick="zoom(this.src)">\n'
    screen_blocks += f'  </div>\n'

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PANAH — Humanitarian Shelter Platform</title>
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap");
*{margin:0;padding:0;box-sizing:border-box}
:root{--nav:#0C252A;--green:#40916C;--gold:#D4A373;--dark:#1D1D1D}
html,body{height:100%;overflow:hidden;font-family:"Inter",system-ui,sans-serif;background:#000}

/* NAV BAR - matches screenshot nav exactly */
.nav{height:40px;background:var(--nav);display:flex;align-items:center;padding:0 20px;gap:16px;position:fixed;top:0;left:0;right:0;z-index:1000;border-bottom:1px solid rgba(255,255,255,0.05)}
.nav .brand{font-weight:800;font-size:14px;color:#fff;letter-spacing:2.5px;text-transform:uppercase;cursor:pointer}
.nav-links{display:flex;gap:2px;margin-left:16px}
.nav-link{padding:6px 14px;border-radius:6px;font-size:11.5px;font-weight:500;color:rgba(255,255,255,0.5);cursor:pointer;display:flex;align-items:center;gap:5px;transition:all .2s;user-select:none}
.nav-link:hover{color:rgba(255,255,255,0.8);background:rgba(255,255,255,0.05)}
.nav-link.active{color:#fff;background:rgba(255,255,255,0.1)}
.nav-link svg{width:12px;height:12px;opacity:.5}
.nav-spacer{flex:1}
.nav-icon{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:center;cursor:pointer;color:rgba(255,255,255,0.4);font-size:12px;transition:background .2s}
.nav-icon:hover{background:rgba(255,255,255,0.12)}
.nav-icon.active-user{background:var(--green);color:#fff}

/* SCREEN CONTAINER */
.screens{position:fixed;top:40px;left:0;right:0;bottom:0}
.screen{position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:#000}
.screen.active{display:flex}
.screen img{max-width:100%;max-height:100%;object-fit:contain;cursor:pointer;transition:opacity .15s}
.screen img:hover{opacity:.97}

/* ZOOM OVERLAY */
.zoom-overlay{display:none;position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,0.92);cursor:zoom-out;align-items:center;justify-content:center}
.zoom-overlay.show{display:flex}
.zoom-overlay img{max-width:95vw;max-height:95vh;object-fit:contain;border-radius:4px;box-shadow:0 8px 40px rgba(0,0,0,0.5)}

/* SCREEN INDICATOR */
.screen-indicator{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:500;padding:6px 14px;background:rgba(12,37,42,0.85);border-radius:20px;backdrop-filter:blur(10px)}
.dot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.2);cursor:pointer;transition:all .2s}
.dot.active{background:var(--green);box-shadow:0 0 8px rgba(64,145,108,0.5)}

/* SCREEN LABEL */
.screen-label{position:fixed;bottom:48px;left:50%;transform:translateX(-50%);font-size:11px;color:rgba(255,255,255,0.35);letter-spacing:1.5px;text-transform:uppercase;z-index:500;font-weight:500;pointer-events:none}

/* KEYBOARD HINTS */
.kb-hints{position:fixed;bottom:18px;right:16px;font-size:10px;color:rgba(255,255,255,0.18);z-index:500;display:flex;gap:8px;pointer-events:none}
.kb-hints span{background:rgba(255,255,255,0.06);padding:3px 8px;border-radius:4px;font-family:monospace}

/* TRANSITION */
.screen{animation:none}
</style>
</head>
<body>

<!-- NAV BAR -->
<div class="nav">
  <div class="brand" onclick="go(0)">PANAH</div>
  <div class="nav-links">
    <div class="nav-link" data-idx="0" onclick="go(0)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>Home</div>
    <div class="nav-link" data-idx="1" onclick="go(1)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>Build</div>
    <div class="nav-link" data-idx="2" onclick="go(2)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>Materials</div>
    <div class="nav-link" data-idx="4" onclick="go(4)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>Material Library</div>
    <div class="nav-link" data-idx="3" onclick="go(3)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>History</div>
    <div class="nav-link" data-idx="5" onclick="go(5)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>Standards</div>
    <div class="nav-link" data-idx="6" onclick="go(6)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>Review</div>
  </div>
  <div class="nav-spacer"></div>
  <div class="nav-icon">&#9881;</div>
  <div class="nav-icon active-user">W</div>
</div>

<!-- SCREENS -->
<div class="screens">
''' + screen_blocks + r'''</div>

<!-- ZOOM OVERLAY -->
<div class="zoom-overlay" id="zoomOverlay" onclick="this.classList.remove('show')">
  <img id="zoomImg" src="" alt="Zoomed">
</div>

<!-- SCREEN INDICATOR DOTS -->
<div class="screen-indicator" id="dots"></div>
<div class="screen-label" id="screenLabel"></div>

<div class="kb-hints">
  <span>&larr; &rarr;</span> Navigate
  <span>Space</span> Next
  <span>Click</span> Zoom
  <span>Esc</span> Close
</div>

<script>
const screens = [
  {key:"dashboard",label:"Dashboard"},
  {key:"requirements",label:"Requirements"},
  {key:"materials",label:"Materials"},
  {key:"generation",label:"Generation"},
  {key:"library",label:"Material Library"},
  {key:"validation",label:"Validation"},
  {key:"review",label:"Review"}
];

// Nav mapping: which nav-link index corresponds to which screen index
const navMap = {0:0, 1:1, 2:2, 4:3, 3:4, 5:5, 6:6};
const reverseNav = {};
Object.entries(navMap).forEach(([k,v]) => reverseNav[v] = parseInt(k));

let current = 0;

function go(idx) {
  if(idx < 0 || idx >= screens.length) return;
  
  // Hide zoom if open
  document.getElementById("zoomOverlay").classList.remove("show");
  
  // Switch screens
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById("s-" + screens[idx].key).classList.add("active");
  
  // Update nav
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  const navIdx = reverseNav[idx];
  if(navIdx !== undefined) {
    document.querySelectorAll(".nav-link")[navIdx].classList.add("active");
  }
  
  // Update dots
  document.querySelectorAll(".dot").forEach((d,i) => d.classList.toggle("active", i===idx));
  
  // Update label
  document.getElementById("screenLabel").textContent = screens[idx].label;
  
  current = idx;
}

function zoom(src) {
  document.getElementById("zoomImg").src = src;
  document.getElementById("zoomOverlay").classList.add("show");
}

// Build dots
const dotsEl = document.getElementById("dots");
screens.forEach((s,i) => {
  const d = document.createElement("div");
  d.className = "dot" + (i===0 ? " active" : "");
  d.onclick = () => go(i);
  dotsEl.appendChild(d);
});

// Keyboard navigation
document.addEventListener("keydown", e => {
  if(document.getElementById("zoomOverlay").classList.contains("show")) {
    if(e.key === "Escape") document.getElementById("zoomOverlay").classList.remove("show");
    return;
  }
  if(e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); go(current+1); }
  if(e.key === "ArrowLeft") { e.preventDefault(); go(current-1); }
  if(e.key === "Home") { e.preventDefault(); go(0); }
  if(e.key === "End") { e.preventDefault(); go(screens.length-1); }
});

// Initialize
go(0);
</script>
</body>
</html>
'''

with open('docs/app.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"Written docs/app.html ({len(HTML):,} bytes)")
