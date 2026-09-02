import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../api/auth'

const AuthContext = createContext(null)

const DEMO_USER = {
  id: 'usr_demo_01',
  email: 'a.thorne@system-core.net',
  full_name: 'Dr. Aris Thorne',
  role: 'engineer',
  is_active: true,
  organization: 'Panah Shelter Systems',
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(DEMO_USER)
  const [token, setToken] = useState(() => localStorage.getItem('panah_auth_token'))
  const [loading, setLoading] = useState(false)
  const [authError, setAuthError] = useState(null)

  // Fetch current user if token exists
  const fetchUser = useCallback(async () => {
    const savedToken = localStorage.getItem('panah_auth_token')
    if (!savedToken) return

    setLoading(true)
    try {
      const userData = await authApi.getMe()
      setUser(userData)
      setAuthError(null)
    } catch {
      // If token invalid, clear it and fall back to demo user
      localStorage.removeItem('panah_auth_token')
      setToken(null)
      setUser(DEMO_USER)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = async (email, password) => {
    setLoading(true)
    setAuthError(null)
    try {
      const res = await authApi.login(email, password)
      if (res.access_token) {
        localStorage.setItem('panah_auth_token', res.access_token)
        setToken(res.access_token)
        setUser(res.user || { email, full_name: email.split('@')[0], role: 'engineer' })
      }
      return res
    } catch (err) {
      setAuthError(err.message || 'Login failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (formData) => {
    setLoading(true)
    setAuthError(null)
    try {
      const res = await authApi.register(formData)
      // Auto login after register
      if (formData.email && formData.password) {
        return await login(formData.email, formData.password)
      }
      return res
    } catch (err) {
      setAuthError(err.message || 'Registration failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('panah_auth_token')
    setToken(null)
    setUser(DEMO_USER)
  }

  const updateProfile = (updates) => {
    setUser((prev) => ({ ...prev, ...updates }))
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        authError,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
