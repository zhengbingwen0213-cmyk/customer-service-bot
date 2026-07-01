import { MOCK_ACCESS_TOKEN } from './auth'

import type { ApiResponse } from '@/types/api'
import type {
  DeleteDocumentResponseData,
  DocumentDetailDto,
  DocumentDetailResponseData,
  DocumentListItemDto,
  DocumentListRequest,
  DocumentListResponseData,
  DocumentStatus,
  UploadDocumentRequest,
  UploadedDocumentDto,
  UploadDocumentResponseData,
} from '@/types/documents'

interface MockDocumentEntity {
  id: string
  name: string
  status: DocumentStatus
  chunk_count: number
  uploaded_by: string
  created_at: string
  updated_at: string
}

const documents: MockDocumentEntity[] = [
  {
    id: 'doc_001',
    name: '售后政策说明.pdf',
    status: 'completed',
    chunk_count: 12,
    uploaded_by: '客服一组员工',
    created_at: '2026-05-23T11:00:00+08:00',
    updated_at: '2026-05-23T11:02:00+08:00',
  },
  {
    id: 'doc_002',
    name: '会员权益手册.docx',
    status: 'processing',
    chunk_count: 0,
    uploaded_by: '客服一组员工',
    created_at: '2026-05-23T15:05:10+08:00',
    updated_at: '2026-05-23T15:05:10+08:00',
  },
  {
    id: 'doc_003',
    name: '支付问题处理指南.pdf',
    status: 'failed',
    chunk_count: 0,
    uploaded_by: '客服一组员工',
    created_at: '2026-05-23T11:20:05+08:00',
    updated_at: '2026-05-23T11:20:05+08:00',
  },
]

let nextDocumentNumber = 4

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 160)
  })
}

function isAuthorized(accessToken: string | null) {
  return accessToken === MOCK_ACCESS_TOKEN
}

function isDocumentStatus(status: string): status is DocumentStatus {
  return status === 'processing' || status === 'completed' || status === 'failed'
}

function nowIso() {
  return new Date().toISOString()
}

function toDocumentListItemDto(document: MockDocumentEntity): DocumentListItemDto {
  return {
    id: document.id,
    name: document.name,
    status: document.status,
    chunk_count: document.chunk_count,
    uploaded_by: document.uploaded_by,
    created_at: document.created_at,
    updated_at: document.updated_at,
  }
}

function toUploadedDocumentDto(document: MockDocumentEntity): UploadedDocumentDto {
  return {
    id: document.id,
    name: document.name,
    status: document.status,
    chunk_count: document.chunk_count,
    uploaded_by: document.uploaded_by,
    created_at: document.created_at,
    updated_at: document.updated_at,
  }
}

function toDocumentDetailDto(document: MockDocumentEntity): DocumentDetailDto {
  return {
    id: document.id,
    name: document.name,
    status: document.status,
    chunk_count: document.chunk_count,
    uploaded_by: document.uploaded_by,
    created_at: document.created_at,
    updated_at: document.updated_at,
  }
}

function unauthorizedResponse<TData>(): ApiResponse<TData> {
  return {
    code: 401,
    message: '登录状态已失效',
    data: null,
  }
}

export async function mockGetDocuments(
  accessToken: string | null,
  request: DocumentListRequest = {},
): Promise<ApiResponse<DocumentListResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const page = request.page ?? 1
  const pageSize = request.page_size ?? 20
  if (!Number.isInteger(page) || page < 1 || !Number.isInteger(pageSize) || pageSize < 1) {
    return {
      code: 400,
      message: '分页参数不合法',
      data: null,
    }
  }

  if (request.status && !isDocumentStatus(request.status)) {
    return {
      code: 400,
      message: 'status 参数不合法',
      data: null,
    }
  }

  const keyword = request.keyword?.trim().toLowerCase() ?? ''
  const filteredDocuments = documents
    .filter((document) => {
      const matchesKeyword = !keyword || document.name.toLowerCase().includes(keyword)
      const matchesStatus = !request.status || document.status === request.status
      return matchesKeyword && matchesStatus
    })
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  const start = (page - 1) * pageSize
  const items = filteredDocuments.slice(start, start + pageSize).map(toDocumentListItemDto)

  return {
    code: 200,
    message: 'success',
    data: {
      items,
      total: filteredDocuments.length,
      page,
      page_size: pageSize,
    },
  }
}

export async function mockUploadDocument(
  accessToken: string | null,
  request: UploadDocumentRequest,
): Promise<ApiResponse<UploadDocumentResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const fileName = (request.name || request.file.name).trim()
  if (!fileName) {
    return {
      code: 400,
      message: '文件不能为空',
      data: null,
    }
  }

  const timestamp = nowIso()
  const document: MockDocumentEntity = {
    id: `doc_${String(nextDocumentNumber).padStart(3, '0')}`,
    name: fileName,
    status: 'processing',
    chunk_count: 0,
    uploaded_by: '客服一组员工',
    created_at: timestamp,
    updated_at: timestamp,
  }
  nextDocumentNumber += 1
  documents.unshift(document)

  return {
    code: 200,
    message: 'success',
    data: {
      document: toUploadedDocumentDto(document),
    },
  }
}

export async function mockGetDocument(
  accessToken: string | null,
  documentId: string,
): Promise<ApiResponse<DocumentDetailResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const document = documents.find((item) => item.id === documentId)
  if (!document) {
    return {
      code: 404,
      message: '文档不存在',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      document: toDocumentDetailDto(document),
    },
  }
}

export async function mockDeleteDocument(
  accessToken: string | null,
  documentId: string,
): Promise<ApiResponse<DeleteDocumentResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const index = documents.findIndex((item) => item.id === documentId)
  if (index === -1) {
    return {
      code: 404,
      message: '文档不存在',
      data: null,
    }
  }

  documents.splice(index, 1)

  return {
    code: 200,
    message: 'success',
    data: {
      deleted: true,
      document_id: documentId,
    },
  }
}
