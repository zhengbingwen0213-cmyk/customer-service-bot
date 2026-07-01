import axios, { type AxiosResponse } from 'axios'

import api from '@/services/api'
import type { ApiResponse } from '@/types/api'
import type {
  AuthMeResponseData,
  LoginRequest,
  LoginResponseData,
  LogoutRequest,
  LogoutResponseData,
} from '@/types/auth'
import { isMockApiEnabled } from '@/utils/runtime'

export async function login(payload: LoginRequest): Promise<ApiResponse<LoginResponseData>> {
  if (isMockApiEnabled()) {
    const { mockLogin } = await import('@/mocks')
    return mockLogin(payload)
  }

  return unwrapApiResponse(api.post('/auth/login', payload))
}

export async function getCurrentUser(
  accessToken: string | null,
): Promise<ApiResponse<AuthMeResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetCurrentUser } = await import('@/mocks')
    return mockGetCurrentUser(accessToken)
  }

  return unwrapApiResponse(
    api.get('/auth/me', authConfig(accessToken)),
  )
}

export async function logout(payload: LogoutRequest): Promise<ApiResponse<LogoutResponseData>> {
  if (isMockApiEnabled()) {
    const { mockLogout } = await import('@/mocks')
    return mockLogout(payload)
  }

  return unwrapApiResponse(
    api.post('/auth/logout', payload, authConfig(payload.access_token)),
  )
}

function authConfig(accessToken: string | null) {
  if (!accessToken) return {}
  return {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  }
}

async function unwrapApiResponse<TData>(
  request: Promise<AxiosResponse<ApiResponse<TData>>>,
): Promise<ApiResponse<TData>> {
  try {
    const response = await request
    return response.data
  } catch (error) {
    if (axios.isAxiosError<ApiResponse<TData>>(error) && error.response?.data) {
      return error.response.data
    }
    throw error
  }
}
