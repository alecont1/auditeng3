/**
 * Login request payload
 * Note: Backend uses OAuth2PasswordRequestForm which expects 'username' field
 */
export interface LoginRequest {
  email: string
  password: string
}

/**
 * Registration request payload
 */
export interface RegisterRequest {
  email: string
  password: string
}

/**
 * Token response from login/register/refresh
 */
export interface TokenResponse {
  access_token: string
  token_type: string
}

/**
 * Current user information from /api/auth/me
 */
export interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
}

/**
 * Auth state for context
 */
export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}
