export type TicketStatus = 'open' | 'processing' | 'completed'
export type TicketPriority = 'low' | 'medium' | 'high'

export interface DashboardSummaryResponseData {
  open_ticket_count: number
  processing_ticket_count: number
  completed_ticket_count: number
  qa_count: number
  document_count: number
  latest_knowledge_updated_at: string
}

export interface DashboardTicketDto {
  id: string
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  assignee_id: string | null
  assignee_name: string | null
  customer_name: string
  created_at: string
  completed_at: string | null
}

export interface DashboardTicketsResponseData {
  items: DashboardTicketDto[]
}

export interface DashboardTicketsRequest {
  limit?: number
}
