import axios, { type AxiosResponse } from 'axios'

import api from '@/services/api'
import type { ApiResponse } from '@/types/api'
import type {
  DashboardSummaryResponseData,
  DashboardTicketsRequest,
  DashboardTicketsResponseData,
} from '@/types/dashboard'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getDashboardSummary(
  accessToken: string | null,
): Promise<ApiResponse<DashboardSummaryResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetDashboardSummary } = await import('@/mocks')
    return mockGetDashboardSummary(accessToken)
  }

  return unwrapApiResponse(
    api.get('/dashboard/summary', authConfig(accessToken)),
  )
}

export async function getDashboardTickets(
  accessToken: string | null,
  params: DashboardTicketsRequest = {},
): Promise<ApiResponse<DashboardTicketsResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetDashboardTickets } = await import('@/mocks')
    return mockGetDashboardTickets(accessToken, params)
  }

  return unwrapApiResponse(
    api.get('/dashboard/tickets', {
      ...authConfig(accessToken),
      params,
    }),
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
