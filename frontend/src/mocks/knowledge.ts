import { MOCK_ACCESS_TOKEN } from './auth'

import type { ApiResponse } from '@/types/api'
import type {
  CreateKnowledgeQaRequest,
  CreateKnowledgeQaResponseData,
  DeleteKnowledgeQaResponseData,
  KnowledgeDocumentStatus,
  KnowledgeOverviewResponseData,
  KnowledgeQaDto,
  KnowledgeQaListRequest,
  KnowledgeQaListResponseData,
  KnowledgeQaStatus,
  KnowledgeRecentItemDto,
  KnowledgeRecentRequest,
  KnowledgeRecentResponseData,
  UpdateKnowledgeQaRequest,
  UpdateKnowledgeQaResponseData,
} from '@/types/knowledge'

interface MockKnowledgeQaEntity {
  id: string
  question: string
  answer: string
  status: KnowledgeQaStatus
  created_at: string
  updated_at: string
}

interface MockKnowledgeDocumentEntity {
  type: 'document'
  id: string
  title: string
  status: KnowledgeDocumentStatus
  updated_at: string
}

const knowledgeQaItems: MockKnowledgeQaEntity[] = [
  {
    id: 'qa_001',
    question: '支付状态为什么延迟？',
    answer: '网络波动或银行结算通道拥堵可能导致短暂延迟，建议 5 分钟后刷新订单状态。',
    status: 'enabled',
    created_at: '2026-05-23T09:30:00+08:00',
    updated_at: '2026-05-24T10:15:00+08:00',
  },
  {
    id: 'qa_002',
    question: '退款多久到账？',
    answer: '正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。',
    status: 'disabled',
    created_at: '2026-05-23T10:00:00+08:00',
    updated_at: '2026-05-23T16:10:00+08:00',
  },
  {
    id: 'qa_003',
    question: '会员权益说明',
    answer: '会员权益包含专属客服、优先处理和每月权益券，具体以订单页展示为准。',
    status: 'enabled',
    created_at: '2026-05-23T10:45:00+08:00',
    updated_at: '2026-05-23T09:45:00+08:00',
  },
]

const knowledgeDocuments: MockKnowledgeDocumentEntity[] = [
  {
    type: 'document',
    id: 'doc_001',
    title: '售后退款规则',
    status: 'completed',
    updated_at: '2026-05-23T16:30:00+08:00',
  },
  {
    type: 'document',
    id: 'doc_002',
    title: '发票申请流程.pdf',
    status: 'completed',
    updated_at: '2026-05-23T14:20:00+08:00',
  },
]

let nextQaNumber = 4

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 120)
  })
}

function isAuthorized(accessToken: string | null) {
  return accessToken === MOCK_ACCESS_TOKEN
}

function isKnowledgeQaStatus(status: string): status is KnowledgeQaStatus {
  return status === 'enabled' || status === 'disabled'
}

function nowIso() {
  return new Date().toISOString()
}

function toKnowledgeQaDto(qa: MockKnowledgeQaEntity): KnowledgeQaDto {
  return {
    id: qa.id,
    question: qa.question,
    answer: qa.answer,
    status: qa.status,
    created_at: qa.created_at,
    updated_at: qa.updated_at,
  }
}

function toRecentQaDto(qa: MockKnowledgeQaEntity): KnowledgeRecentItemDto {
  return {
    type: 'qa',
    id: qa.id,
    title: qa.question,
    status: qa.status,
    updated_at: qa.updated_at,
  }
}

function toRecentDocumentDto(document: MockKnowledgeDocumentEntity): KnowledgeRecentItemDto {
  return {
    type: document.type,
    id: document.id,
    title: document.title,
    status: document.status,
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

function latestUpdatedAt() {
  const timestamps = [
    ...knowledgeQaItems.map((item) => item.updated_at),
    ...knowledgeDocuments.map((item) => item.updated_at),
  ]

  return timestamps.sort((left, right) => right.localeCompare(left))[0] ?? ''
}

export async function mockGetKnowledgeOverview(
  accessToken: string | null,
): Promise<ApiResponse<KnowledgeOverviewResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  return {
    code: 200,
    message: 'success',
    data: {
      qa_count: knowledgeQaItems.length,
      enabled_qa_count: knowledgeQaItems.filter((item) => item.status === 'enabled').length,
      document_count: knowledgeDocuments.length,
      completed_document_count: knowledgeDocuments.filter((item) => item.status === 'completed').length,
      latest_updated_at: latestUpdatedAt(),
    },
  }
}

export async function mockGetKnowledgeRecent(
  accessToken: string | null,
  request: KnowledgeRecentRequest = {},
): Promise<ApiResponse<KnowledgeRecentResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const limit = request.limit ?? 5
  if (!Number.isInteger(limit) || limit < 1 || limit > 20) {
    return {
      code: 400,
      message: 'limit 必须为 1 到 20 的整数',
      data: null,
    }
  }

  const items = [
    ...knowledgeQaItems.map(toRecentQaDto),
    ...knowledgeDocuments.map(toRecentDocumentDto),
  ]
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
    .slice(0, limit)

  return {
    code: 200,
    message: 'success',
    data: {
      items,
    },
  }
}

export async function mockGetKnowledgeQaList(
  accessToken: string | null,
  request: KnowledgeQaListRequest = {},
): Promise<ApiResponse<KnowledgeQaListResponseData>> {
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

  if (request.status && !isKnowledgeQaStatus(request.status)) {
    return {
      code: 400,
      message: 'status 参数不合法',
      data: null,
    }
  }

  const keyword = request.keyword?.trim().toLowerCase() ?? ''
  const filteredItems = knowledgeQaItems
    .filter((item) => {
      const matchesKeyword =
        !keyword ||
        item.question.toLowerCase().includes(keyword) ||
        item.answer.toLowerCase().includes(keyword)
      const matchesStatus = !request.status || item.status === request.status
      return matchesKeyword && matchesStatus
    })
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  const start = (page - 1) * pageSize
  const items = filteredItems.slice(start, start + pageSize).map(toKnowledgeQaDto)

  return {
    code: 200,
    message: 'success',
    data: {
      items,
      total: filteredItems.length,
      page,
      page_size: pageSize,
    },
  }
}

export async function mockCreateKnowledgeQa(
  accessToken: string | null,
  request: CreateKnowledgeQaRequest,
): Promise<ApiResponse<CreateKnowledgeQaResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const question = request.question.trim()
  const answer = request.answer.trim()
  if (!question || !answer) {
    return {
      code: 400,
      message: '问题和答案不能为空',
      data: null,
    }
  }

  if (!isKnowledgeQaStatus(request.status)) {
    return {
      code: 400,
      message: 'status 参数不合法',
      data: null,
    }
  }

  const createdAt = nowIso()
  const qa: MockKnowledgeQaEntity = {
    id: `qa_${String(nextQaNumber).padStart(3, '0')}`,
    question,
    answer,
    status: request.status,
    created_at: createdAt,
    updated_at: createdAt,
  }
  nextQaNumber += 1
  knowledgeQaItems.unshift(qa)

  return {
    code: 200,
    message: 'success',
    data: {
      qa: toKnowledgeQaDto(qa),
      embedding_status: 'completed',
    },
  }
}

export async function mockUpdateKnowledgeQa(
  accessToken: string | null,
  qaId: string,
  request: UpdateKnowledgeQaRequest,
): Promise<ApiResponse<UpdateKnowledgeQaResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const qa = knowledgeQaItems.find((item) => item.id === qaId)
  if (!qa) {
    return {
      code: 404,
      message: 'QA 不存在',
      data: null,
    }
  }

  const question = request.question.trim()
  const answer = request.answer.trim()
  if (!question || !answer) {
    return {
      code: 400,
      message: '问题和答案不能为空',
      data: null,
    }
  }

  if (!isKnowledgeQaStatus(request.status)) {
    return {
      code: 400,
      message: 'status 参数不合法',
      data: null,
    }
  }

  qa.question = question
  qa.answer = answer
  qa.status = request.status
  qa.updated_at = nowIso()

  return {
    code: 200,
    message: 'success',
    data: {
      qa: toKnowledgeQaDto(qa),
      embedding_status: 'completed',
    },
  }
}

export async function mockDeleteKnowledgeQa(
  accessToken: string | null,
  qaId: string,
): Promise<ApiResponse<DeleteKnowledgeQaResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return unauthorizedResponse()
  }

  const index = knowledgeQaItems.findIndex((item) => item.id === qaId)
  if (index === -1) {
    return {
      code: 404,
      message: 'QA 不存在',
      data: null,
    }
  }

  knowledgeQaItems.splice(index, 1)

  return {
    code: 200,
    message: 'success',
    data: {
      deleted: true,
      qa_id: qaId,
    },
  }
}
