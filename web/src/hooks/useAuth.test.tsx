import { renderHook } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useAuth } from './useAuth'
import { AuthContext } from '@/contexts/AuthContext'
import type { ReactNode } from 'react'

describe('useAuth', () => {
  it('throws error when used outside AuthProvider', () => {
    // Suppress React error boundary console.error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth must be used within an AuthProvider'
    )

    consoleSpy.mockRestore()
  })

  it('returns context value when used inside AuthProvider', () => {
    // Create a simple mock context value
    const mockContextValue = {
      user: { id: '1', email: 'test@example.com', full_name: 'Test User', role: 'engineer' as const },
      token: 'mock-token',
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    }

    // Create wrapper that provides the mock context
    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthContext.Provider value={mockContextValue}>
        {children}
      </AuthContext.Provider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current).toBeDefined()
    expect(result.current.user).toEqual(mockContextValue.user)
    expect(result.current.token).toBe('mock-token')
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.login).toBeDefined()
    expect(result.current.logout).toBeDefined()
  })

  it('returns loading state correctly', () => {
    const mockContextValue = {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    }

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthContext.Provider value={mockContextValue}>
        {children}
      </AuthContext.Provider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })
})
