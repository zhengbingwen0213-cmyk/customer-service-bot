export type DocumentStatus = 'processing' | 'completed' | 'failed'

export interface DocumentListItemDto {
  id: string
  name: string
  status: DocumentStatus
  chunk_count: number
  uploaded_by: string
  created_at: string
  updated_at: string
}

export interface UploadedDocumentDto {
  id: string
  name: string
  status: DocumentStatus
  chunk_count: number
  uploaded_by: string
  created_at: string
  updated_at: string
}

export interface DocumentDetailDto {
  id: string
  name: string
  status: DocumentStatus
  chunk_count: number
  uploaded_by: string
  created_at: string
  updated_at: string
}

export interface DocumentListRequest {
  keyword?: string
  status?: DocumentStatus
  page?: number
  page_size?: number
}

export interface UploadDocumentRequest {
  file: File
  name?: string
}

export interface DocumentListResponseData {
  items: DocumentListItemDto[]
  total: number
  page: number
  page_size: number
}

export interface UploadDocumentResponseData {
  document: UploadedDocumentDto
}

export interface DocumentDetailResponseData {
  document: DocumentDetailDto
}

export interface DeleteDocumentResponseData {
  deleted: boolean
  document_id: string
}
