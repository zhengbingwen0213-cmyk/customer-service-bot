import axios, { type AxiosResponse } from 'axios'

import type { ApiResponse } from '@/types/api'
import type {
  CreateKnowledgeQaRequest,
  CreateKnowledgeQaResponseData,
  DeleteKnowledgeQaResponseData,
  KnowledgeOverviewResponseData,
  KnowledgeQaListRequest,
  KnowledgeQaListResponseData,
  KnowledgeRecentRequest,
  KnowledgeRecentResponseData,
  UpdateKnowledgeQaRequest,
  UpdateKnowledgeQaResponseData,
} from '@/types/knowledge'
import api from './api'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getKnowledgeOverview(
  accessToken: string | null,
): Promise<ApiResponse<KnowledgeOverviewResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetKnowledgeOverview } = await import('@/mocks')
    return mockGetKnowledgeOverview(accessToken)
  }

  return unwrapApiResponse(api.get('/knowledge/overview', authConfig(accessToken)))
}

export async function getKnowledgeRecent(
  accessToken: string | null,
  params: KnowledgeRecentRequest = {},
): Promise<ApiResponse<KnowledgeRecentResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetKnowledgeRecent } = await import('@/mocks')
    return mockGetKnowledgeRecent(accessToken, params)
  }

  return unwrapApiResponse(
    api.get('/knowledge/recent', {
      ...authConfig(accessToken),
      params: toRecentQueryParams(params),
    }),
  )
}

export async function getKnowledgeQaList(
  accessToken: string | null,
  params: KnowledgeQaListRequest = {},
): Promise<ApiResponse<KnowledgeQaListResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetKnowledgeQaList } = await import('@/mocks')
    return mockGetKnowledgeQaList(accessToken, params)
  }

  return unwrapApiResponse(
    api.get('/knowledge/qa', {
      ...authConfig(accessToken),
      params: toQaQueryParams(params),
    }),
  )
}

export async function createKnowledgeQa(
  accessToken: string | null,
  payload: CreateKnowledgeQaRequest,
): Promise<ApiResponse<CreateKnowledgeQaResponseData>> {
  if (isMockApiEnabled()) {
    const { mockCreateKnowledgeQa } = await import('@/mocks')
    return mockCreateKnowledgeQa(accessToken, payload)
  }

  return unwrapApiResponse(api.post('/knowledge/qa', payload, authConfig(accessToken)))
}

export async function updateKnowledgeQa(
  accessToken: string | null,
  qaId: string,
  payload: UpdateKnowledgeQaRequest,
): Promise<ApiResponse<UpdateKnowledgeQaResponseData>> {
  if (isMockApiEnabled()) {
    const { mockUpdateKnowledgeQa } = await import('@/mocks')
    return mockUpdateKnowledgeQa(accessToken, qaId, payload)
  }

  return unwrapApiResponse(
    api.put(`/knowledge/qa/${encodeURIComponent(qaId)}`, payload, authConfig(accessToken)),
  )
}

export async function deleteKnowledgeQa(
  accessToken: string | null,
  qaId: string,
): Promise<ApiResponse<DeleteKnowledgeQaResponseData>> {
  if (isMockApiEnabled()) {
    const { mockDeleteKnowledgeQa } = await import('@/mocks')
    return mockDeleteKnowledgeQa(accessToken, qaId)
  }

  return unwrapApiResponse(
    api.delete(`/knowledge/qa/${encodeURIComponent(qaId)}`, authConfig(accessToken)),
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

function toRecentQueryParams(params: KnowledgeRecentRequest): Record<string, number> {
  const queryParams: Record<string, number> = {}
  if (params.limit) queryParams.limit = params.limit
  return queryParams
}

function toQaQueryParams(params: KnowledgeQaListRequest): Record<string, string | number> {
  const queryParams: Record<string, string | number> = {}

  if (params.keyword) queryParams.keyword = params.keyword
  if (params.status) queryParams.status = params.status
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
