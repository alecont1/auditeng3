import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'

const TOKEN_KEY = 'auditeng_token'

/**
 * Get stored auth token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Store auth token
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * Remove auth token
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * Check if token exists
 */
export function hasToken(): boolean {
  return !!getToken()
}

/**
 * Get base URL for API requests.
 * - Production: Uses VITE_API_URL environment variable
 * - Development: Empty string (uses Vite proxy)
 */
function getBaseURL(): string {
  let envUrl = import.meta.env.VITE_API_URL
  if (envUrl) {
    // Ensure URL has protocol - auto-add https:// if missing
    // This prevents treating the URL as a relative path
    if (!envUrl.startsWith('http://') && !envUrl.startsWith('https://')) {
      envUrl = `https://${envUrl}`
    }
    // Production: Use full URL, ensure /api prefix
    return envUrl.endsWith('/api') ? envUrl : `${envUrl}/api`
  }
  // Development: Empty baseURL uses Vite proxy (/api -> localhost:8000)
  return '/api'
}

/**
 * Axios instance configured for AuditEng API
 */
export const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor: inject auth token
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * Response interceptor: handle errors
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Handle 401 Unauthorized - clear token and redirect to login
    if (error.response?.status === 401) {
      removeToken()
      // Dispatch custom event for auth context to handle
      window.dispatchEvent(new CustomEvent('auth:logout'))
    }

    // Re-throw with better error message
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

export default api
