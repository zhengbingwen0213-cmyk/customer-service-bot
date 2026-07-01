import axios, { type AxiosResponse } from 'axios'

import type { ApiResponse } from '@/types/api'
import type {
  DeleteDocumentResponseData,
  DocumentDetailResponseData,
  DocumentListRequest,
  DocumentListResponseData,
  UploadDocumentRequest,
  UploadDocumentResponseData,
} from '@/types/documents'
import api from './api'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getDocuments(
  accessToken: string | null,
  params: DocumentListRequest = {},
): Promise<ApiResponse<DocumentListResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetDocuments } = await import('@/mocks')
    return mockGetDocuments(accessToken, params)
  }

  return unwrapApiResponse(
    api.get('/documents', {
      ...authConfig(accessToken),
      params: toDocumentQueryParams(params),
    }),
  )
}

export async function uploadDocument(
  accessToken: string | null,
  payload: UploadDocumentRequest,
): Promise<ApiResponse<UploadDocumentResponseData>> {
  if (isMockApiEnabled()) {
    const { mockUploadDocument } = await import('@/mocks')
    return mockUploadDocument(accessToken, payload)
  }

  const formData = new FormData()
  formData.append('file', payload.file)
  if (payload.name) {
    formData.append('name', payload.name)
  }

  const config = authConfig(accessToken)
  return unwrapApiResponse(
    api.post('/documents', formData, {
      ...config,
      headers: {
        ...config.headers,
        'Content-Type': 'multipart/form-data',
      },
    }),
  )
}

export async function getDocument(
  accessToken: string | null,
  documentId: string,
): Promise<ApiResponse<DocumentDetailResponseData>> {
  if (isMockApiEnabled()) {
    const { mockGetDocument } = await import('@/mocks')
    return mockGetDocument(accessToken, documentId)
  }

  return unwrapApiResponse(
    api.get(`/documents/${encodeURIComponent(documentId)}`, authConfig(accessToken)),
  )
}

export async function deleteDocument(
  accessToken: string | null,
  documentId: string,
): Promise<ApiResponse<DeleteDocumentResponseData>> {
  if (isMockApiEnabled()) {
    const { mockDeleteDocument } = await import('@/mocks')
    return mockDeleteDocument(accessToken, documentId)
  }

  return unwrapApiResponse(
    api.delete(`/documents/${encodeURIComponent(documentId)}`, authConfig(accessToken)),
  )
}

function authConfig(accessToken: string | null): { headers?: Record<string, string> } {
  if (!accessToken) return {}
  return {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  }
}

function toDocumentQueryParams(params: DocumentListRequest): Record<string, string | number> {
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
