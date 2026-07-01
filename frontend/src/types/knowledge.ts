export type KnowledgeQaStatus = 'enabled' | 'disabled'
export type KnowledgeDocumentStatus = 'processing' | 'completed' | 'failed'
export type KnowledgeRecentType = 'qa' | 'document'

export interface KnowledgeOverviewResponseData {
  qa_count: number
  enabled_qa_count: number
  document_count: number
  completed_document_count: number
  latest_updated_at: string
}

export interface KnowledgeRecentItemDto {
  type: KnowledgeRecentType
  id: string
  title: string
  status: KnowledgeQaStatus | KnowledgeDocumentStatus
  updated_at: string
}

export interface KnowledgeRecentRequest {
  limit?: number
}

export interface KnowledgeRecentResponseData {
  items: KnowledgeRecentItemDto[]
}

export interface KnowledgeQaDto {
  id: string
  question: string
  answer: string
  status: KnowledgeQaStatus
  created_at: string
  updated_at: string
}

export interface KnowledgeQaListRequest {
  keyword?: string
  status?: KnowledgeQaStatus
  page?: number
  page_size?: number
}

export interface KnowledgeQaListResponseData {
  items: KnowledgeQaDto[]
  total: number
  page: number
  page_size: number
}

export interface CreateKnowledgeQaRequest {
  question: string
  answer: string
  status: KnowledgeQaStatus
}

export interface UpdateKnowledgeQaRequest {
  question: string
  answer: string
  status: KnowledgeQaStatus
}

export interface CreateKnowledgeQaResponseData {
  qa: KnowledgeQaDto
  embedding_status: 'completed' | 'fallback'
}

export interface UpdateKnowledgeQaResponseData {
  qa: KnowledgeQaDto
  embedding_status: 'completed' | 'fallback'
}

export interface DeleteKnowledgeQaResponseData {
  deleted: boolean
  qa_id: string
}
