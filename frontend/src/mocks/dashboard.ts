import { MOCK_ACCESS_TOKEN } from './auth'

import type { ApiResponse } from '@/types/api'
import type {
  DashboardSummaryResponseData,
  DashboardTicketDto,
  DashboardTicketsRequest,
  DashboardTicketsResponseData,
  TicketPriority,
  TicketStatus,
} from '@/types/dashboard'

interface MockDashboardSummaryEntity {
  open_ticket_count: number
  processing_ticket_count: number
  completed_ticket_count: number
  qa_count: number
  document_count: number
  latest_knowledge_updated_at: string
}

interface MockDashboardTicketEntity {
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

const dashboardSummary: MockDashboardSummaryEntity = {
  open_ticket_count: 8,
  processing_ticket_count: 5,
  completed_ticket_count: 12,
  qa_count: 42,
  document_count: 86,
  latest_knowledge_updated_at: '2026-05-23T11:02:00+08:00',
}

const dashboardTickets: MockDashboardTicketEntity[] = [
  {
    id: 'TK-1001',
    title: '订单支付失败需要核实',
    description: '客户反馈订单支付后页面仍显示失败，需要人工核实支付状态。',
    status: 'open',
    priority: 'high',
    assignee_id: null,
    assignee_name: null,
    customer_name: '张三',
    created_at: '2026-05-23T14:20:00+08:00',
    completed_at: null,
  },
  {
    id: 'TK-1002',
    title: '账户密码重置请求',
    description: '客户无法完成密码重置，需要客服协助确认账号信息。',
    status: 'open',
    priority: 'medium',
    assignee_id: null,
    assignee_name: null,
    customer_name: '李四',
    created_at: '2026-05-23T14:25:00+08:00',
    completed_at: null,
  },
]

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 120)
  })
}

function isAuthorized(accessToken: string | null) {
  return accessToken === MOCK_ACCESS_TOKEN
}

function toDashboardSummaryDto(
  summary: MockDashboardSummaryEntity,
): DashboardSummaryResponseData {
  return {
    open_ticket_count: summary.open_ticket_count,
    processing_ticket_count: summary.processing_ticket_count,
    completed_ticket_count: summary.completed_ticket_count,
    qa_count: summary.qa_count,
    document_count: summary.document_count,
    latest_knowledge_updated_at: summary.latest_knowledge_updated_at,
  }
}

function toDashboardTicketDto(ticket: MockDashboardTicketEntity): DashboardTicketDto {
  return {
    id: ticket.id,
    title: ticket.title,
    description: ticket.description,
    status: ticket.status,
    priority: ticket.priority,
    assignee_id: ticket.assignee_id,
    assignee_name: ticket.assignee_name,
    customer_name: ticket.customer_name,
    created_at: ticket.created_at,
    completed_at: ticket.completed_at,
  }
}

export async function mockGetDashboardSummary(
  accessToken: string | null,
): Promise<ApiResponse<DashboardSummaryResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: toDashboardSummaryDto(dashboardSummary),
  }
}

export async function mockGetDashboardTickets(
  accessToken: string | null,
  request: DashboardTicketsRequest = {},
): Promise<ApiResponse<DashboardTicketsResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const limit = request.limit ?? 5
  if (!Number.isInteger(limit) || limit < 1 || limit > 20) {
    return {
      code: 400,
      message: 'limit 必须为 1 到 20 的整数',
      data: null,
    }
  }

  const items = dashboardTickets.slice(0, limit).map(toDashboardTicketDto)

  return {
    code: 200,
    message: 'success',
    data: {
      items,
    },
  }
}
