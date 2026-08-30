import { useState } from 'react'
import {
  Home, Package, Calculator, History, FileText, Settings, CircleUser, User,
  Plus, FolderOpen, LogOut, ShieldCheck, Bell, Palette, LifeBuoy, Phone, Mail,
  Briefcase, Search, Link2, Printer, Download, ClipboardCheck, CheckCircle2,
  AlertCircle, XCircle, AlertTriangle, SquareKanban, Save, RotateCw,
  MousePointer2, Hand, ZoomIn, ZoomOut, Ruler, Eye, SlidersHorizontal, Layers,
  Minus, RotateCcw, Newspaper, SquarePen, CirclePlus, MapPin, ChevronRight,
  ChevronLeft, ChevronDown,
} from 'lucide-react'
import heroImg from './assets/hero.png'
import trussImg from './assets/truss.png'
import cardAlpha from './assets/card-alpha.png'
import cardBeta from './assets/card-beta.png'
import blueprintImg from './assets/blueprint.png'

/* ---------------------------------- NAV ---------------------------------- */

const NAV_ITEMS = [
  { id: 'home', label: 'HOME', icon: Home },
  { id: 'build', label: 'BUILD', icon: Package },
  { id: 'cost', label: 'COST ESTIMATION', icon: Calculator },
  { id: 'history', label: 'HISTORY', icon: History },
  { id: 'standards', label: 'STANDARDS', icon: FileText },
]

function NavBar({ page, onNav, onSettings, onUser }) {
  return (
    <header className="navbar">
      <div className="nav-logo">PANAH</div>
      <nav className="nav-links">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item${page === id ? ' active' : ''}`}
            onClick={() => onNav(id)}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="nav-right">
        <button className="icon-btn" aria-label="Settings" onClick={onSettings}>
          <Settings size={20} />
        </button>
        <button className="avatar-btn" aria-label="Account" onClick={onUser}>
          <CircleUser size={19} />
        </button>
      </div>
    </header>
  )
}

function UserDropdown({ onClose, onSettings, onProjects }) {
  return (
    <>
      <div className="dropdown-backdrop" onClick={onClose} />
      <div className="user-dropdown">
        <div className="ud-head">
          <div className="ud-avatar"><User size={18} /></div>
          <div>
            <div className="ud-name">User Name</div>
            <div className="ud-mail">user@panah.engine</div>
          </div>
        </div>
        <div className="ud-divider" />
        <button className="ud-item" onClick={onSettings}>
          <Settings size={15} /> ACCOUNT SETTINGS
        </button>
        <button className="ud-item" onClick={onProjects}>
          <FolderOpen size={15} /> SAVED PROJECTS
        </button>
        <div className="ud-divider" />
        <button className="ud-item danger" onClick={onClose}>
          <LogOut size={15} /> SIGN OUT
        </button>
      </div>
    </>
  )
}

/* ---------------------------------- HOME --------------------------------- */

function HomePage({ onBuild, onProjects, onHistory }) {
  return (
    <div className="home">
      <section className="hero" style={{ backgroundImage: `url(${heroImg})` }}>
        <h1 className="hero-title">PANAH</h1>
        <p className="hero-sub">AI-Generated, Locally-Adapted, Structurally-Validated Shelter Designs</p>
        <div className="hero-actions">
          <button className="btn-green" onClick={onBuild}>
            <Plus size={16} /> START NEW BUILD
          </button>
          <button className="btn-dark" onClick={onProjects}>
            <FolderOpen size={16} /> VIEW SAVED PROJECTS
          </button>
        </div>
      </section>

      <section className="recent">
        <div className="recent-head">
          <h2>Recent Active Projects</h2>
          <button className="link-rust" onClick={onHistory}>VIEW FULL HISTORY →</button>
        </div>
        <div className="project-cards">
          <article className="project-card">
            <div className="pc-media">
              <span className="badge badge-green"><CheckCircle2 size={13} /> VALIDATED</span>
              <img src={cardAlpha} alt="Module Alpha-1 structural frame" />
            </div>
            <div className="pc-body">
              <h3>Module Alpha-1</h3>
              <div className="pc-id">#PRJ-8842-A</div>
              <div className="pc-stats">
                <div className="pc-stat">
                  <div className="pc-stat-label">PRIMARY MAT.</div>
                  <div className="pc-stat-value">Bamboo Type C</div>
                </div>
                <div className="pc-stat">
                  <div className="pc-stat-label">LOAD EST.</div>
                  <div className="pc-stat-value">450 kg/m²</div>
                </div>
              </div>
            </div>
            <div className="pc-footer">
              <button><SquarePen size={14} /> Edit</button>
              <button><Download size={14} /> Export</button>
            </div>
          </article>

          <article className="project-card">
            <div className="pc-media">
              <span className="badge badge-amber"><AlertTriangle size={13} /> REVIEW REQ.</span>
              <img src={cardBeta} alt="Foundation Beta cross-section" />
            </div>
            <div className="pc-body">
              <h3>Foundation Beta</h3>
              <div className="pc-id">#PRJ-8843-B</div>
              <div className="pc-stats">
                <div className="pc-stat">
                  <div className="pc-stat-label">PRIMARY MAT.</div>
                  <div className="pc-stat-value">Rammed Earth</div>
                </div>
                <div className="pc-stat">
                  <div className="pc-stat-label">STRESS TEST</div>
                  <div className="pc-stat-value amber">82% Marg.</div>
                </div>
              </div>
            </div>
            <div className="pc-footer">
              <button><SquarePen size={14} /> Edit</button>
              <button><SquareKanban size={14} /> Analyze</button>
            </div>
          </article>

          <article className="project-card new-schematic">
            <CirclePlus size={30} className="ns-icon" />
            <h3>New Schematic</h3>
            <p>Initialize blank canvas or import topographic survey data.</p>
          </article>
        </div>
      </section>
    </div>
  )
}

/* ---------------------------------- BUILD -------------------------------- */

const COMPLIANCE_ITEMS = [
  { tone: 'ok', icon: CheckCircle2, title: 'Seismic Load (Zone 4)', sub: 'Tolerance: > 0.8g PGA' },
  { tone: 'ok', icon: CheckCircle2, title: 'Monsoon Watertightness', sub: 'Roof Pitch: 32° (Min 25°)' },
  { tone: 'ok', icon: CheckCircle2, title: 'Material Stress Limits', sub: 'Axial Load: 4.2 MPa (Max 12 MPa)' },
  { tone: 'warn', icon: AlertCircle, title: 'Foundation Soil Bearing', sub: 'Allowable Pressure: 85 kPa (Min 75)' },
  { tone: 'fail', icon: XCircle, title: 'Wind Shear (Cat 3)', sub: 'Fail at Node J-14 (6.2 kN)' },
]

const MATERIALS_CORE = [
  { name: 'Treated Bamboo', code: 'MAT-BAM-01', qty: '120', unit: 'pcs (3m)' },
  { name: 'Steel Connectors', code: 'MAT-STL-43', qty: '48', unit: 'units' },
]

const MATERIALS_CLAD = [
  { name: 'Corrugated Tin', code: 'MAT-ROF-02', qty: '24', unit: 'sq.m' },
  { name: 'Compacted Silt', code: 'MAT-FND-SLT', qty: '3.5', unit: 'cu.m' },
]

function MaterialColumn({ heading, items, bordered }) {
  return (
    <div className={`mat-col${bordered ? ' bordered' : ''}`}>
      <div className="mat-col-head">{heading}</div>
      {items.map((m) => (
        <div className="mat-row" key={m.code}>
          <div className="mat-row-top">
            <span className="mat-name">{m.name}</span>
            <span className="mat-code">{m.code}</span>
          </div>
          <div className="mat-row-bottom">
            <input className="mat-qty" defaultValue={m.qty} />
            <span className="mat-unit">{m.unit}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function BuildPage() {
  return (
    <div className="page">
      <div className="page-head">
        <h1>PARAMETRIC DESIGN ENGINE</h1>
        <div className="page-sub">REAL-TIME LOAD DISTRIBUTION, MATERIAL CONSTRAINTS, AND SPHERE VALIDATION</div>
      </div>

      <div className="build-grid">
        <div className="build-left">
          <section className="card">
            <div className="viewport-head">
              <div className="vp-left">
                <span className="vp-active">VIEWPORT: ACTIVE</span>
                <span className="vp-sep" />
                <span className="vp-model">model_id: TSU-SH-042-B</span>
              </div>
              <span className="vp-pill">Module Alpha - 1</span>
            </div>
            <div className="viewport-body">
              <div className="vp-canvas">
                <img src={trussImg} alt="Parametric truss model with load distribution" />
              </div>
              <div className="vp-specs">
                <div className="vp-specs-title">Material Specifications</div>
                <p><strong>Primary:</strong> Treated Bamboo</p>
                <p className="latin">(Phyllostachys edulis)</p>
                <p><strong>Joints:</strong> S335 Steel</p>
              </div>
            </div>
            <div className="viewport-toolbar">
              <button className="tool-btn"><MousePointer2 size={16} /></button>
              <button className="tool-btn"><Hand size={16} /></button>
              <button className="tool-btn active"><RotateCw size={16} /></button>
              <span className="tool-sep" />
              <button className="tool-btn"><ZoomIn size={16} /></button>
              <button className="tool-btn"><ZoomOut size={16} /></button>
              <button className="tool-btn ratio">1:1</button>
              <span className="tool-sep" />
              <button className="tool-btn"><Ruler size={16} /></button>
              <button className="tool-btn"><Eye size={16} /></button>
            </div>
          </section>

          <section className="card material-card">
            <div className="material-head">
              <div className="card-title"><ClipboardCheck size={18} /> Material Input &amp; Constraints</div>
              <button className="btn-black">ADD MATERIAL</button>
            </div>
            <div className="material-body">
              <MaterialColumn heading="STRUCTURAL CORE" items={MATERIALS_CORE} />
              <MaterialColumn heading="CLADDING &amp; FOUNDATION" items={MATERIALS_CLAD} bordered />
              <div className="mat-warn-col">
                <div className="mat-warn">
                  <XCircle size={17} className="mat-warn-x" />
                  <AlertTriangle size={18} className="mat-warn-icon" />
                  <div>
                    <div className="mat-warn-title">Material Constraint Warning</div>
                    <p>
                      Current bamboo length (3m) insufficient for primary ridge
                      beam spanning 4.2m without central support pillar.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="build-right">
          <section className="card">
            <div className="card-head">
              <div className="card-title"><ClipboardCheck size={18} /> Compliance Prescreen</div>
            </div>
            <div className="compliance-body">
              {COMPLIANCE_ITEMS.map(({ tone, icon: Icon, title, sub }) => (
                <div className={`comp-item ${tone}`} key={title}>
                  <Icon size={18} className="comp-icon" />
                  <div>
                    <div className="comp-title">{title}</div>
                    <div className="comp-sub">{sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <div className="card-title"><SquareKanban size={18} /> Structural Analysis</div>
            </div>
            <div className="analysis-body">
              <div className="score-row">
                <span>OVERALL INTEGRITY SCORE</span>
                <span className="score-val">78%</span>
              </div>
              <div className="score-bar"><div style={{ width: '78%' }} /></div>

              <div className="loads">
                <div>
                  <div className="load-label">DEAD LOAD</div>
                  <div className="load-value">1,240 <small>kg</small></div>
                </div>
                <div>
                  <div className="load-label">LIVE LOAD CAP</div>
                  <div className="load-value">450 <small>kg/m²</small></div>
                </div>
              </div>

              <div className="mini-label">DEFLECTION CURVE (Z-AXIS)</div>
              <svg className="deflection" viewBox="0 0 220 74">
                <line x1="52" y1="8" x2="168" y2="8" stroke="#9aa39a" strokeDasharray="4 4" />
                <path
                  d="M14 62 C 60 62, 78 20, 110 20 C 142 20, 160 62, 206 62"
                  fill="none" stroke="#1c1c1c" strokeWidth="2"
                />
                <circle cx="110" cy="20" r="4" fill="#c0392b" />
                <text x="120" y="14" className="defl-label">Max δ: 14mm</text>
              </svg>

              <div className="mini-label">STRESS LEGEND (KILO NEWTON/M²)</div>
              <div className="stress-bar" />
              <div className="stress-ticks"><span>0.5</span><span>2.0</span><span>5.5+</span></div>

              <button className="btn-report"><Save size={14} /> VIEW REPORT</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

/* ----------------------------- COST ESTIMATION ---------------------------- */

const COST_ITEMS = [
  { name: 'Bamboo Culms', qty: '4m x Qty 24', price: '$0.00', tone: 'free', tag: 'SITE SOURCED', tagTone: 'green' },
  { name: 'Recycled Corrugated Tin', qty: '12 sheets', price: '$4.50', tone: 'paid', tag: 'BAZAAR', tagTone: 'red' },
  { name: 'Steel Fasteners', qty: 'Qty 32', price: '$0.80', tone: 'mid', tag: 'NGO DEPOT', tagTone: 'gray' },
  { name: 'Mud Fill', qty: '3.5m³', price: '$0.00', tone: 'free', tag: 'ON-SITE', tagTone: 'green' },
  { name: 'Bamboo Culms', qty: '4m x Qty 24', price: '$0.00', tone: 'free', tag: 'SITE SOURCED', tagTone: 'green' },
  { name: 'Steel Fasteners', qty: 'Qty 32', price: '$0.80', tone: 'mid', tag: 'NGO DEPOT', tagTone: 'gray' },
]

function CostPage() {
  const [shelters, setShelters] = useState(250)
  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>COST ESTIMATION MODULE</h1>
          <div className="page-sub">PROJECT: PANAH_SHELTER_V2 // PHASE: PRE-DEPLOYMENT</div>
        </div>
        <div className="total-card">
          <div className="total-label">ESTIMATED TOTAL</div>
          <div className="total-price">$84.60 <span>/ unit</span></div>
        </div>
      </div>

      <div className="cost-grid">
        <section className="card cost-card">
          <div className="cost-head">
            <h3>LOCAL MARKET COST MATRIX</h3>
            <SlidersHorizontal size={17} className="muted-icon" />
          </div>
          <div className="cost-items">
            {COST_ITEMS.map((item, i) => (
              <div className="cost-item" key={i}>
                <div className="cost-item-top">
                  <span className="cost-name">{item.name}</span>
                  <span className={`cost-price ${item.tone}`}>{item.price}</span>
                </div>
                <div className="cost-item-bottom">
                  <span className="cost-qty">{item.qty}</span>
                  <span className={`cost-tag ${item.tagTone}`}>{item.tag}</span>
                </div>
              </div>
            ))}
          </div>
          <button className="btn-logistics"><Plus size={14} /> ADD LOGISTICS OVERHEAD</button>
        </section>

        <section className="card cost-card">
          <div className="cost-head">
            <h3>EFFICIENCY ANALYTICS</h3>
            <SquareKanban size={17} className="muted-icon" />
          </div>
          <div className="eff-stats">
            <div className="eff-stat red">
              <div className="eff-label">COST / M²</div>
              <div className="eff-value">$2.82</div>
            </div>
            <div className="eff-stat amber">
              <div className="eff-label">STRUCT. RATING</div>
              <div className="eff-value">94<small>/100</small></div>
            </div>
            <div className="eff-stat green">
              <div className="eff-label">SOURCING RATIO</div>
              <div className="eff-value">72% <small>Local</small></div>
            </div>
          </div>

          <div className="mini-label">EXPENDITURE DISTRIBUTION</div>
          <div className="dist-bar">
            <div className="seg green" style={{ width: '11%' }} />
            <div className="seg brown" style={{ width: '52%' }} />
            <div className="seg amber" style={{ width: '23%' }} />
          </div>
          <div className="dist-legend">
            <span><i className="sq green" /> Local</span>
            <span><i className="sq brown" /> Commercial</span>
            <span><i className="sq amber" /> Logistics</span>
          </div>

          <div className="tradeoff">
            <div className="tradeoff-label">COST VS STRUCTURAL INTEGRITY TRADE-OFF</div>
            <svg viewBox="0 0 300 170" className="tradeoff-svg">
              <line x1="168" y1="18" x2="168" y2="150" stroke="#8b949b" strokeDasharray="5 5" />
              <path d="M6 118 C 90 108, 120 42, 170 30 S 262 20, 294 18" fill="none" stroke="#2E7D46" strokeWidth="3" />
              <path d="M6 138 C 90 128, 130 72, 180 58 S 262 46, 294 44" fill="none" stroke="#9C4A2F" strokeWidth="3" />
              <path d="M6 164 C 90 156, 130 112, 180 100 S 240 94, 264 92" fill="none" stroke="#C79A2E" strokeWidth="3" />
              <circle cx="172" cy="29" r="5" fill="#2E7D46" />
              <circle cx="158" cy="64" r="5" fill="#9C4A2F" />
              <circle cx="138" cy="110" r="5" fill="#C79A2E" />
            </svg>
            <span className="config-tag">CURRENT CONFIG</span>
          </div>
        </section>

        <section className="scale-card">
          <div className="cost-head dark">
            <h3>DEPLOYMENT SCALE</h3>
            <Layers size={17} />
          </div>
          <div className="scale-label">FAMILY SHELTERS NEEDED</div>
          <div className="stepper">
            <button onClick={() => setShelters((s) => Math.max(0, s - 10))}><Minus size={15} /></button>
            <input value={shelters} onChange={(e) => setShelters(Number(e.target.value) || 0)} />
            <button onClick={() => setShelters((s) => s + 10)}><Plus size={15} /></button>
          </div>

          <div className="budget-panel">
            <div className="budget-top">
              <div className="budget-label">TOTAL<br />BUDGET<br />REQ.</div>
              <div className="budget-value">${(shelters * 84.6).toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
            </div>
            <div className="budget-bottom">
              <div className="budget-label">MATERIAL<br />FOOTPRINT</div>
              <div className="footprint">
                <div><strong>{(shelters * 24).toLocaleString('en-US')}</strong> Bamboo</div>
                <div className="dim">{(shelters * 12).toLocaleString('en-US')} Corrugated Sht.</div>
              </div>
            </div>
          </div>

          <div className="risk-alert">
            <div className="risk-title"><AlertTriangle size={14} /> PROCUREMENT RISK ALERT</div>
            <p>Local bazaar tin supply bottleneck detected at &gt;200 units. Consider regional sourcing.</p>
          </div>

          <button className="btn-export"><Newspaper size={15} /> EXPORT AUDITABLE BOM</button>
        </section>
      </div>
    </div>
  )
}

/* --------------------------------- HISTORY -------------------------------- */

const HISTORY_ROWS = [
  {
    preview: '←', name: 'Bamboo T-Shelter Alpha', id: 'BLD-8942-A',
    location: 'Mindanao, Philippines', date: '2023-10-12', ver: 'v4.2.1', verTone: '',
    status: 'DEPLOYED', statusTone: 'deployed', dot: '●',
  },
  {
    preview: 's', name: 'Earthbag Clinic Core', id: 'MED-1105-X',
    location: 'Kathmandu Valley, Nepal', date: '2023-11-04', ver: 'v2.0.8', verTone: 'green',
    status: 'ITERATING', statusTone: 'iterating', dot: '▲',
  },
  {
    preview: 'Dashbo', name: 'Rapid Truss System Mk II', id: 'RF-7721-B',
    location: 'Global Specification', date: '2023-09-18', ver: 'v5.0.0', verTone: '',
    status: 'APPROVED', statusTone: 'approved', dot: '◇',
  },
  {
    preview: 'PROJECT', name: 'Timber Frame Mk I', id: 'BLD-1102-O', archived: true,
    location: 'Haiti', date: '2021-02-14', ver: 'v1.0.0', verTone: '',
    status: 'ARCHIVED', statusTone: 'archived', dot: '■',
  },
]

function HistoryPage() {
  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>PROJECT HISTORY</h1>
          <div className="page-sub">SEARCH THROUGH YOUR RECENT PROJECTS</div>
        </div>
        <label className="search-box">
          <Search size={16} />
          <input placeholder="Search projects..." />
        </label>
      </div>

      <div className="card history-card">
        <div className="h-row h-head">
          <span>PREVIEW</span>
          <span>PROJECT DETAILS</span>
          <span>LOCATION</span>
          <span className="right">DATE / ITERATION</span>
          <span>STATUS</span>
          <span className="center">ACTION</span>
        </div>
        {HISTORY_ROWS.map((r) => (
          <div className="h-row" key={r.id}>
            <span className="h-preview">{r.preview}</span>
            <span className="h-details">
              <span className={`h-name${r.archived ? ' archived' : ''}`}>{r.name}</span>
              <span className="h-id">ID: {r.id}</span>
            </span>
            <span className="h-location"><MapPin size={14} /> {r.location}</span>
            <span className="h-date">
              <span>{r.date}</span>
              <span className={`h-ver ${r.verTone}`}>{r.ver}</span>
            </span>
            <span className={`h-status ${r.statusTone}`}><i>{r.dot}</i> {r.status}</span>
            <span className="h-action">
              {r.archived ? <FileText size={16} /> : <RotateCcw size={16} />}
            </span>
          </div>
        ))}
        <div className="h-footer">
          <span>Showing 1-4 of 1,248 builds</span>
          <span className="h-pager">
            <button><ChevronLeft size={13} /></button>
            <button><ChevronRight size={13} /></button>
          </span>
        </div>
      </div>
    </div>
  )
}

/* -------------------------------- STANDARDS ------------------------------- */

function StandardsPage() {
  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>GUIDELINE &amp; STANDARDS</h1>
          <div className="page-sub">ENGINEERING REFERENCE MANUAL</div>
        </div>
        <div className="std-actions">
          <button><Link2 size={16} /></button>
          <button><Printer size={16} /></button>
          <button><Download size={16} /></button>
        </div>
      </div>

      <div className="std-grid">
        <aside className="card std-sidebar">
          <div className="std-side-head">
            <div className="std-handbook">SPHERE HANDBOOK V24.1</div>
            <label className="std-search">
              <Search size={13} />
              <input placeholder="Search documentation..." />
            </label>
          </div>
          <div className="std-tree">
            <div className="tree-group">
              <div className="tree-root"><ChevronRight size={13} /> <span>R 1: Foundation Beta</span></div>
              <div className="tree-children">
                <div className="tree-leaf">1.1 Humanitarian Response</div>
                <div className="tree-leaf">1.2 Effective and Timely</div>
                <div className="tree-leaf">1.3 Local Capacities</div>
              </div>
            </div>
            <div className="tree-group">
              <div className="tree-root open"><ChevronDown size={13} /> <span>R 2: Module Alpha - 1</span></div>
              <div className="tree-children">
                <div className="tree-leaf">2.1 Strategic Planning</div>
                <div className="tree-leaf active">2.2 Structural Stability <i>•</i></div>
                <div className="tree-leaf">2.3 Covered Living Space</div>
              </div>
            </div>
          </div>
        </aside>

        <section className="card std-content">
          <h1 className="std-title">2.2 Structural Stability</h1>
          <blockquote>
            Shelters and settlements must provide a secure and healthy living environment with adequate privacy,
            dignity, and protection from the climate, while supporting daily activities.
          </blockquote>

          <div className="std-section-head"><span className="k-badge">K</span><h2>Key Actions</h2></div>
          <div className="action-box">
            <div className="action-title"><span className="num">1</span> Assess structural hazards</div>
            <p>
              Identify and mitigate risks from natural hazards (e.g., earthquakes,
              floods, high winds) during site selection and construction. Ensure
              existing structures are assessed for safety before occupation.
            </p>
          </div>
          <div className="action-box">
            <div className="action-title"><span className="num">2</span> Use appropriate materials</div>
            <p>
              Select building materials and construction techniques that are
              culturally acceptable, climate-appropriate, and technically sound.
              Prioritize local materials where sustainable.
            </p>
          </div>

          <div className="std-section-head"><span className="k-badge">I</span><h2>Technical Indicators</h2></div>
          <table className="std-table">
            <thead>
              <tr><th>INDICATOR</th><th>TARGET THRESHOLD</th><th>VERIFICATION SOURCE</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Wind Load Resistance</td>
                <td className="serif">&gt; 120 km/h sustained</td>
                <td>Engineering sign-off / Field testing</td>
              </tr>
              <tr>
                <td>Snow Load Capacity (Alpine)</td>
                <td className="serif">&gt; 50 kg/m²</td>
                <td>Visual inspection / Rafter span calcs</td>
              </tr>
              <tr>
                <td>Lifespan of Emergency Shelter</td>
                <td className="serif">Minimum 6 months</td>
                <td>Material procurement logs / Post-distribution monitoring</td>
              </tr>
            </tbody>
          </table>

          <div className="std-figure">
            <img src={blueprintImg} alt="Shelter design technical drawings" />
            <div className="std-tooltip">
              <div className="std-tooltip-title">Cross-bracing requirements</div>
              <p>
                Adequate cross-bracing in both wall planes is mandatory to
                resist lateral wind loads. Refer to structural calculation matrix
                for material-specific sizing.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

/* -------------------------------- SETTINGS -------------------------------- */

const SETTINGS_TABS = [
  { id: 'profile', label: 'Profile', icon: CircleUser },
  { id: 'security', label: 'Security & Auth', icon: ShieldCheck },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette },
]

function SettingsPage() {
  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>SYSTEM PREFERENCES</h1>
          <div className="page-sub">SETTINGS AND SETUPS</div>
        </div>
        <button className="btn-black big"><Save size={14} /> COMMIT CHANGES</button>
      </div>

      <div className="settings-grid">
        <aside className="card settings-side">
          {SETTINGS_TABS.map(({ id, label, icon: Icon }, i) => (
            <button key={id} className={`side-item${i === 0 ? ' active' : ''}`}>
              <Icon size={18} /> {label}
            </button>
          ))}
          <div className="side-spacer" />
          <button className="side-item"><LifeBuoy size={18} /> Support</button>
          <button className="side-item"><Phone size={18} /> Contact Us</button>
        </aside>

        <section className="card settings-main">
          <div className="settings-main-head">
            <div>
              <h2>Operative Details</h2>
              <p>Manage your central identification parameters.</p>
            </div>
            <div className="pic-box">Pic</div>
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label>DESIGNATION / NAME</label>
              <div className="input-row">
                <input defaultValue="Dr. Aris Thorne" />
                <span className="input-icon"><Briefcase size={15} /></span>
              </div>
            </div>
            <div className="form-field">
              <label>DATE OF BIRTH</label>
              <div className="input-row">
                <input defaultValue="5th April, 2006" />
                <span className="input-icon"><ShieldCheck size={15} /></span>
              </div>
            </div>
            <div className="form-field">
              <label>CONTACT INFO</label>
              <div className="input-row">
                <input defaultValue="--" />
                <span className="input-icon"><Phone size={15} /></span>
              </div>
            </div>
            <div className="form-field span2">
              <label>EMAIL ID</label>
              <div className="input-row">
                <input defaultValue="a.thorne@system-core.net" />
                <span className="input-icon"><Mail size={15} /></span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

/* ---------------------------------- ROOT ---------------------------------- */

const ROUTES = ['home', 'build', 'cost', 'history', 'standards', 'settings']

function initialRoute() {
  const h = window.location.hash.replace(/^#\/?/, '')
  return ROUTES.includes(h) ? h : 'home'
}

export default function PanahApp() {
  const [page, setPage] = useState(() => (initialRoute() === 'settings' ? 'home' : initialRoute()))
  const [settingsOpen, setSettingsOpen] = useState(() => initialRoute() === 'settings')
  const [userOpen, setUserOpen] = useState(false)

  const nav = (p) => {
    setPage(p)
    setSettingsOpen(false)
    setUserOpen(false)
    window.location.hash = `/${p}`
  }

  const openSettings = () => {
    setSettingsOpen((v) => {
      window.location.hash = v ? `/${page}` : '/settings'
      return !v
    })
    setUserOpen(false)
  }

  return (
    <div className="panah">
      <NavBar
        page={page}
        onNav={nav}
        onSettings={openSettings}
        onUser={() => setUserOpen((v) => !v)}
      />
      {userOpen && (
        <UserDropdown
          onClose={() => setUserOpen(false)}
          onSettings={() => { setSettingsOpen(true); setUserOpen(false); window.location.hash = '/settings' }}
          onProjects={() => nav('history')}
        />
      )}
      {settingsOpen ? (
        <SettingsPage />
      ) : page === 'home' ? (
        <HomePage onBuild={() => nav('build')} onProjects={() => nav('history')} onHistory={() => nav('history')} />
      ) : page === 'build' ? (
        <BuildPage />
      ) : page === 'cost' ? (
        <CostPage />
      ) : page === 'history' ? (
        <HistoryPage />
      ) : (
        <StandardsPage />
      )}
    </div>
  )
}
