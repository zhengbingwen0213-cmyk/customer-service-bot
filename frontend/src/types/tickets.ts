export type TicketStatus = 'open' | 'processing' | 'completed'
export type TicketPriority = 'low' | 'medium' | 'high'
export type TicketScope = 'pool' | 'mine'
export type TicketMessageSender = 'customer' | 'bot' | 'employee'

export interface TicketCustomerDto {
  id: string
  name: string
  level: string
}

export interface TicketListItemDto {
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

export interface TicketsListRequest {
  scope?: TicketScope
  status?: TicketStatus
  priority?: TicketPriority
  keyword?: string
  page?: number
  page_size?: number
}

export interface TicketsListResponseData {
  items: TicketListItemDto[]
  total: number
  page: number
  page_size: number
}

export interface TicketDetailDto {
  id: string
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  assignee_id: string | null
  assignee_name: string | null
  customer: TicketCustomerDto
  related_order_id: string
  created_at: string
  completed_at: string | null
}

export interface TicketDetailResponseData {
  ticket: TicketDetailDto
}

export interface ClaimTicketRequest {
  employee_id: string
}

export interface ClaimedTicketDto {
  id: string
  status: 'processing'
  assignee_id: string
  assignee_name: string
  updated_at: string
}

export interface ClaimTicketResponseData {
  ticket: ClaimedTicketDto
}

export interface CompletedTicketDto {
  id: string
  status: 'completed'
  completed_at: string
}

export interface CompleteTicketRequest {
  employee_id: string
  summary: string
}

export interface CompleteTicketResponseData {
  ticket: CompletedTicketDto
}

export interface TicketMessageDto {
  id: string
  ticket_id: string
  sender: TicketMessageSender
  sender_name: string
  content: string
  created_at: string
}

export interface TicketMessagesResponseData {
  items: TicketMessageDto[]
}

export interface SendTicketMessageRequest {
  content: string
  used_assistant_answer_id?: string
}

export interface SendTicketMessageResponseData {
  message: TicketMessageDto
}
