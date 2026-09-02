import { useState } from 'react'
import { ShieldCheck, Mail, Lock, User, X, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function AuthModal({ isOpen, onClose }) {
  const { login, register, loading, authError } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('engineer')
  const [successMsg, setSuccessMsg] = useState('')

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSuccessMsg('')
    try {
      if (mode === 'login') {
        await login(email, password)
        setSuccessMsg('Authentication successful!')
        setTimeout(() => onClose(), 600)
      } else {
        await register({ email, password, full_name: fullName, role })
        setSuccessMsg('Account created & logged in!')
        setTimeout(() => onClose(), 600)
      }
    } catch (err) {
      console.warn('Auth error:', err)
    }
  }

  const useDemoCredentials = () => {
    setEmail('admin@panagah.org')
    setPassword('Admin@12345')
  }

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '16px',
    }}>
      <div style={{
        background: '#141c17',
        border: '1px solid #2e4436',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '440px',
        padding: '24px',
        position: 'relative',
        boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'transparent',
            border: 'none',
            color: '#8b949b',
            cursor: 'pointer',
          }}
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <ShieldCheck size={24} style={{ color: '#2e7d46' }} />
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#f0f3f0', margin: 0, letterSpacing: '0.04em' }}>
            {mode === 'login' ? 'PANAGAH SECURE ACCESS' : 'CREATE OPERATIVE ACCOUNT'}
          </h2>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #223328', paddingBottom: '8px' }}>
          <button
            onClick={() => setMode('login')}
            style={{
              background: 'transparent',
              border: 'none',
              color: mode === 'login' ? '#4caf50' : '#8b949b',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              borderBottom: mode === 'login' ? '2px solid #4caf50' : 'none',
              paddingBottom: '4px',
            }}
          >
            SIGN IN
          </button>
          <button
            onClick={() => setMode('register')}
            style={{
              background: 'transparent',
              border: 'none',
              color: mode === 'register' ? '#4caf50' : '#8b949b',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              borderBottom: mode === 'register' ? '2px solid #4caf50' : 'none',
              paddingBottom: '4px',
            }}
          >
            REGISTER
          </button>
        </div>

        {authError && (
          <div style={{
            background: 'rgba(231, 76, 60, 0.15)',
            border: '1px solid #e74c3c',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '12px',
            color: '#e74c3c',
            marginBottom: '14px',
          }}>
            {authError}
          </div>
        )}

        {successMsg && (
          <div style={{
            background: 'rgba(46, 125, 70, 0.2)',
            border: '1px solid #2e7d46',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '12px',
            color: '#4caf50',
            marginBottom: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}>
            <CheckCircle2 size={14} /> {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {mode === 'register' && (
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Ahmed Khan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0c120f',
                    border: '1px solid #223328',
                    borderRadius: '4px',
                    padding: '8px 12px 8px 34px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
                <User size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: '#687768' }} />
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
              Email ID
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                required
                placeholder="name@organization.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0c120f',
                  border: '1px solid #223328',
                  borderRadius: '4px',
                  padding: '8px 12px 8px 34px',
                  color: '#fff',
                  fontSize: '13px',
                }}
              />
              <Mail size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: '#687768' }} />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0c120f',
                  border: '1px solid #223328',
                  borderRadius: '4px',
                  padding: '8px 12px 8px 34px',
                  color: '#fff',
                  fontSize: '13px',
                }}
              />
              <Lock size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: '#687768' }} />
            </div>
          </div>

          {mode === 'register' && (
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
                Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0c120f',
                  border: '1px solid #223328',
                  borderRadius: '4px',
                  padding: '8px 12px',
                  color: '#fff',
                  fontSize: '13px',
                }}
              >
                <option value="engineer">Structural Engineer</option>
                <option value="reviewer">Compliance Reviewer</option>
                <option value="field_agent">Field Assessment Agent</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              background: '#2e7d46',
              border: 'none',
              borderRadius: '4px',
              padding: '10px',
              color: '#fff',
              fontWeight: 600,
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '8px',
              letterSpacing: '0.05em',
            }}
          >
            {loading ? 'AUTHENTICATING...' : mode === 'login' ? 'SIGN IN' : 'CREATE ACCOUNT'}
          </button>
        </form>

        {mode === 'login' && (
          <div style={{ marginTop: '16px', textAlign: 'center' }}>
            <button
              onClick={useDemoCredentials}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#4caf50',
                fontSize: '11px',
                cursor: 'pointer',
                textDecoration: 'underline',
              }}
            >
              Fill Demo Admin Credentials (admin@panagah.org)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
