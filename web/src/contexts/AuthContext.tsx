import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react'
import api, { getToken, setToken, removeToken, hasToken } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest, AuthState } from '@/types'

interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(getToken())
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!token && !!user

  /**
   * Fetch current user from /api/auth/me
   */
  const refreshUser = useCallback(async () => {
    if (!hasToken()) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const response = await api.get<User>('/auth/me')
      setUser(response.data)
    } catch {
      // Token invalid or expired
      removeToken()
      setTokenState(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Login with email and password
   */
  const login = useCallback(async (credentials: LoginRequest) => {
    // Backend expects OAuth2PasswordRequestForm (form data, not JSON)
    const formData = new URLSearchParams()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await api.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    )

    const { access_token } = response.data
    setToken(access_token)
    setTokenState(access_token)

    // Fetch user info after login
    await refreshUser()
  }, [refreshUser])

  /**
   * Register new account
   */
  const register = useCallback(async (data: RegisterRequest) => {
    const response = await api.post<{ access_token: string; token_type: string }>(
      '/auth/register',
      data
    )

    const { access_token } = response.data
    setToken(access_token)
    setTokenState(access_token)

    // Fetch user info after registration
    await refreshUser()
  }, [refreshUser])

  /**
   * Logout - clear token and user
   */
  const logout = useCallback(() => {
    removeToken()
    setTokenState(null)
    setUser(null)
  }, [])

  // On mount, try to restore session
  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  // Listen for 401 events from API interceptor
  useEffect(() => {
    const handleLogout = () => logout()
    window.addEventListener('auth:logout', handleLogout)
    return () => window.removeEventListener('auth:logout', handleLogout)
  }, [logout])

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
