import axios, { type AxiosResponse } from 'axios'

import api from '@/services/api'
import type { ApiResponse } from '@/types/api'
import type {
  ClaimTicketRequest,
  ClaimTicketResponseData,
  CompleteTicketRequest,
  CompleteTicketResponseData,
  SendTicketMessageRequest,
  SendTicketMessageResponseData,
  TicketDetailResponseData,
  TicketMessagesResponseData,
  TicketsListRequest,
  TicketsListResponseData,
} from '@/types/tickets'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getTickets(
  accessToken: string | null,
  params: TicketsListRequest = {},
): Promise<ApiResponse<TicketsListResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetTickets } = await import('@/mocks')
    return mockGetTickets(accessToken, params)
  }

  return unwrapApiResponse(
    api.get('/tickets', {
      ...authConfig(accessToken),
      params: toTicketQueryParams(params),
    }),
  )
}

export async function getTicketDetail(
  accessToken: string | null,
  ticketId: string,
): Promise<ApiResponse<TicketDetailResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetTicketDetail } = await import('@/mocks')
    return mockGetTicketDetail(accessToken, ticketId)
  }

  return unwrapApiResponse(
    api.get(`/tickets/${encodeURIComponent(ticketId)}`, authConfig(accessToken)),
  )
}

export async function claimTicket(
  accessToken: string | null,
  ticketId: string,
  payload: ClaimTicketRequest,
): Promise<ApiResponse<ClaimTicketResponseData>> {
  if (isMockApiEnabled()) {
    const { mockClaimTicket } = await import('@/mocks')
    return mockClaimTicket(accessToken, ticketId, payload)
  }

  return unwrapApiResponse(
    api.post(`/tickets/${encodeURIComponent(ticketId)}/claim`, payload, authConfig(accessToken)),
  )
}

export async function completeTicket(
  accessToken: string | null,
  ticketId: string,
  payload: CompleteTicketRequest,
): Promise<ApiResponse<CompleteTicketResponseData>> {
  if (isMockApiEnabled()) {
    const { mockCompleteTicket } = await import('@/mocks')
    return mockCompleteTicket(accessToken, ticketId, payload)
  }

  return unwrapApiResponse(
    api.post(`/tickets/${encodeURIComponent(ticketId)}/complete`, payload, authConfig(accessToken)),
  )
}

export async function getTicketMessages(
  accessToken: string | null,
  ticketId: string,
): Promise<ApiResponse<TicketMessagesResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetTicketMessages } = await import('@/mocks')
    return mockGetTicketMessages(accessToken, ticketId)
  }

  return unwrapApiResponse(
    api.get(`/tickets/${encodeURIComponent(ticketId)}/messages`, authConfig(accessToken)),
  )
}

export async function sendTicketMessage(
  accessToken: string | null,
  ticketId: string,
  payload: SendTicketMessageRequest,
): Promise<ApiResponse<SendTicketMessageResponseData>> {
  if (isMockApiEnabled()) {
    const { mockSendTicketMessage } = await import('@/mocks')
    return mockSendTicketMessage(accessToken, ticketId, payload)
  }

  return unwrapApiResponse(
    api.post(`/tickets/${encodeURIComponent(ticketId)}/messages`, payload, authConfig(accessToken)),
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

function toTicketQueryParams(params: TicketsListRequest): Record<string, string | number> {
  const queryParams: Record<string, string | number> = {}

  if (params.scope) queryParams.scope = params.scope
  if (params.status) queryParams.status = params.status
  if (params.priority) queryParams.priority = params.priority
  if (params.keyword) queryParams.keyword = params.keyword
  if (params.page) queryParams.page = params.page
  if (params.page_size) queryParams.page_size = params.page_size

  return queryParams
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
