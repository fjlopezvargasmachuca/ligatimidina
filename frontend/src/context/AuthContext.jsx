import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  getCurrentPlayer,
  login as loginRequest,
  logout as logoutRequest,
} from '../api/accounts'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  async function loadCurrentUser() {
    try {
      const currentUser = await getCurrentPlayer()
      setUser(currentUser)
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        setUser(null)
      } else {
        console.error('Error obteniendo el usuario actual:', error)
        setUser(null)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCurrentUser()
  }, [])

  async function login(username, password) {
    await loginRequest(username, password)

    const currentUser = await getCurrentPlayer()
    setUser(currentUser)

    return currentUser
  }

  async function logout() {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
    }
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      refreshUser: loadCurrentUser,
    }),
    [user, loading],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth debe utilizarse dentro de AuthProvider')
  }

  return context
}