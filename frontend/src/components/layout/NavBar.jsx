import { Home, Package, Calculator, History, FileText, Settings, CircleUser } from 'lucide-react'

const NAV_ITEMS = [
  { id: 'home', label: 'HOME', icon: Home },
  { id: 'build', label: 'BUILD', icon: Package },
  { id: 'cost', label: 'COST ESTIMATION', icon: Calculator },
  { id: 'history', label: 'HISTORY', icon: History },
  { id: 'standards', label: 'STANDARDS', icon: FileText },
]

export default function NavBar({ page, onNav, onSettings, onUser }) {
  return (
    <header className="navbar">
      <div className="nav-logo" onClick={() => onNav('home')} style={{ cursor: 'pointer' }}>
        PANAH
      </div>
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
