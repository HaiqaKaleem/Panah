import { useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { ProjectProvider } from './context/ProjectContext'
import NavBar from './components/layout/NavBar'
import UserDropdown from './components/layout/UserDropdown'
import AuthModal from './components/common/AuthModal'

import HomePage from './pages/HomePage'
import BuildPage from './pages/BuildPage'
import CostPage from './pages/CostPage'
import HistoryPage from './pages/HistoryPage'
import StandardsPage from './pages/StandardsPage'
import SettingsPage from './pages/SettingsPage'

const ROUTES = ['home', 'build', 'cost', 'history', 'standards', 'settings']

function initialRoute() {
  const h = window.location.hash.replace(/^#\/?/, '')
  return ROUTES.includes(h) ? h : 'home'
}

function PanahAppContent() {
  const [page, setPage] = useState(() => (initialRoute() === 'settings' ? 'home' : initialRoute()))
  const [settingsOpen, setSettingsOpen] = useState(() => initialRoute() === 'settings')
  const [userOpen, setUserOpen] = useState(false)
  const [authModalOpen, setAuthModalOpen] = useState(false)

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
          onSettings={() => {
            setSettingsOpen(true)
            setUserOpen(false)
            window.location.hash = '/settings'
          }}
          onProjects={() => nav('history')}
          onOpenAuth={() => {
            setUserOpen(false)
            setAuthModalOpen(true)
          }}
        />
      )}

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />

      {settingsOpen ? (
        <SettingsPage onOpenAuth={() => setAuthModalOpen(true)} />
      ) : page === 'home' ? (
        <HomePage
          onBuild={() => nav('build')}
          onProjects={() => nav('history')}
          onHistory={() => nav('history')}
        />
      ) : page === 'build' ? (
        <BuildPage />
      ) : page === 'cost' ? (
        <CostPage />
      ) : page === 'history' ? (
        <HistoryPage onNavigateToBuild={() => nav('build')} />
      ) : (
        <StandardsPage />
      )}
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ProjectProvider>
        <PanahAppContent />
      </ProjectProvider>
    </AuthProvider>
  )
}
