import { defineStore } from 'pinia'

import { getCurrentUser, login as loginService, logout as logoutService } from '@/services/auth'
import type { UserDto } from '@/types/auth'
import { isMockApiEnabled } from '@/utils/runtime'

const TOKEN_KEY = 'customer_service_bot_token'
const USER_KEY = 'customer_service_bot_user'

function readStoredUser(): UserDto | null {
  const value = window.localStorage.getItem(USER_KEY)
  if (!value) return null

  try {
    return JSON.parse(value) as UserDto
  } catch {
    window.localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: window.localStorage.getItem(TOKEN_KEY),
    user: readStoredUser(),
    isLoading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async login(username: string, password: string) {
      this.isLoading = true

      try {
        const response = await loginService({ username, password })
        if (response.code !== 200 || !response.data) {
          throw new Error(response.message)
        }

        this.token = response.data.access_token
        this.user = response.data.user
        window.localStorage.setItem(TOKEN_KEY, response.data.access_token)
        window.localStorage.setItem(USER_KEY, JSON.stringify(response.data.user))
      } finally {
        this.isLoading = false
      }
    },
    async ensureCurrentUser() {
      if (!this.token) return
      if (this.user && isMockApiEnabled()) return

      const response = await getCurrentUser(this.token)
      if (response.code !== 200 || !response.data) {
        this.clearSession()
        return
      }

      this.user = response.data.user
      window.localStorage.setItem(USER_KEY, JSON.stringify(response.data.user))
    },
    async logout() {
      const accessToken = this.token
      if (accessToken) {
        await logoutService({ access_token: accessToken }).catch(() => undefined)
      }
      this.clearSession()
    },
    clearSession() {
      this.token = null
      this.user = null
      window.localStorage.removeItem(TOKEN_KEY)
      window.localStorage.removeItem(USER_KEY)
    },
  },
})
