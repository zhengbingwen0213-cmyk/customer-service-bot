import axios, { type AxiosResponse } from 'axios'

import api from '@/services/api'
import type { ApiResponse } from '@/types/api'
import type { SettingsAccountResponseData } from '@/types/settings'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getAccountSettings(
  accessToken: string | null,
): Promise<ApiResponse<SettingsAccountResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetAccountSettings } = await import('@/mocks')
    return mockGetAccountSettings(accessToken)
  }

  return unwrapApiResponse(
    api.get('/settings/account', authConfig(accessToken)),
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
