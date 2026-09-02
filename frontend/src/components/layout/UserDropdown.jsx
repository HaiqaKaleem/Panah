import { User, Settings, FolderOpen, LogOut, LogIn } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function UserDropdown({ onClose, onSettings, onProjects, onOpenAuth }) {
  const { user, isAuthenticated, logout } = useAuth()

  const handleSignOut = () => {
    logout()
    onClose()
  }

  return (
    <>
      <div className="dropdown-backdrop" onClick={onClose} />
      <div className="user-dropdown">
        <div className="ud-head">
          <div className="ud-avatar">
            <User size={18} />
          </div>
          <div>
            <div className="ud-name">{user?.full_name || 'Operative User'}</div>
            <div className="ud-mail">{user?.email || 'user@panah.engine'}</div>
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
        {isAuthenticated ? (
          <button className="ud-item danger" onClick={handleSignOut}>
            <LogOut size={15} /> SIGN OUT
          </button>
        ) : (
          <button className="ud-item" onClick={onOpenAuth || onSettings}>
            <LogIn size={15} /> SIGN IN / REGISTER
          </button>
        )}
      </div>
    </>
  )
}
