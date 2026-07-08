/**
 * stores/authStore.ts
 * T16 ✅  Zustand auth store — tokens, user, logout.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  user:         User | null
  accessToken:  string | null
  refreshToken: string | null
  isAuthenticated: boolean
  setUser:      (user: User) => void
  setTokens:    (access: string, refresh: string) => void
  logout:       () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user:            null,
      accessToken:     null,
      refreshToken:    null,
      isAuthenticated: false,

      setUser: (user) => set({ user }),

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true }),

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false })
        window.location.href = '/login'
      },
    }),
    {
      name:    'trademind-auth',
      partialize: (s) => ({
        accessToken:  s.accessToken,
        refreshToken: s.refreshToken,
        user:         s.user,
        isAuthenticated: s.isAuthenticated,
      }),
    }
  )
)
