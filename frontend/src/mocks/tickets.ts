import { MOCK_ACCESS_TOKEN } from './auth'

import type { ApiResponse } from '@/types/api'
import type {
  ClaimTicketRequest,
  ClaimTicketResponseData,
  ClaimedTicketDto,
  CompletedTicketDto,
  CompleteTicketRequest,
  CompleteTicketResponseData,
  SendTicketMessageRequest,
  SendTicketMessageResponseData,
  TicketCustomerDto,
  TicketDetailDto,
  TicketDetailResponseData,
  TicketListItemDto,
  TicketMessageDto,
  TicketMessageSender,
  TicketMessagesResponseData,
  TicketPriority,
  TicketsListRequest,
  TicketsListResponseData,
  TicketStatus,
} from '@/types/tickets'

interface MockTicketEntity {
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

interface MockTicketMessageEntity {
  id: string
  ticket_id: string
  sender: TicketMessageSender
  sender_name: string
  content: string
  created_at: string
}

const MOCK_EMPLOYEE_ID = 'user_001'
const MOCK_EMPLOYEE_NAME = '客服一组员工'
const CLAIMED_AT = '2026-05-23T14:35:00+08:00'
const COMPLETED_AT = '2026-05-23T15:10:00+08:00'

const tickets: MockTicketEntity[] = [
  {
    id: 'TK-1001',
    title: '无法登录系统账号',
    description: '客户反馈多次输入正确账号密码后仍提示登录失败，需要人工核实账号状态。',
    status: 'open',
    priority: 'high',
    assignee_id: null,
    assignee_name: null,
    customer: {
      id: 'customer_101',
      name: '张三',
      level: '企业客户',
    },
    related_order_id: '20231024001',
    created_at: '2023-10-24T09:12:33+08:00',
    completed_at: null,
  },
  {
    id: 'TK-1002',
    title: '报表数据导出异常',
    description: '客户在导出经营报表时页面长时间无响应，下载文件为空。',
    status: 'open',
    priority: 'medium',
    assignee_id: null,
    assignee_name: null,
    customer: {
      id: 'customer_102',
      name: '李四',
      level: '普通客户',
    },
    related_order_id: '20231024002',
    created_at: '2023-10-24T09:45:10+08:00',
    completed_at: null,
  },
  {
    id: 'TK-1005',
    title: '会员支付后未生效',
    description: '客户反馈在 APP 内购买年度会员，支付宝已扣款，但账户状态未更新，且没有收到订单确认短信。',
    status: 'processing',
    priority: 'high',
    assignee_id: MOCK_EMPLOYEE_ID,
    assignee_name: MOCK_EMPLOYEE_NAME,
    customer: {
      id: 'customer_001',
      name: '张三',
      level: 'VIP 会员',
    },
    related_order_id: '20260523001',
    created_at: '2026-05-23T14:30:00+08:00',
    completed_at: null,
  },
  {
    id: 'TK-1003',
    title: '支付回调延迟问题排查',
    description: '客户反馈支付回调延迟，当前订单状态与支付渠道状态不一致。',
    status: 'processing',
    priority: 'high',
    assignee_id: MOCK_EMPLOYEE_ID,
    assignee_name: MOCK_EMPLOYEE_NAME,
    customer: {
      id: 'customer_103',
      name: '赵六',
      level: '企业客户',
    },
    related_order_id: '20231027003',
    created_at: '2023-10-27T14:32:01+08:00',
    completed_at: null,
  },
  {
    id: 'TK-1004',
    title: '企业实名认证驳回咨询',
    description: '客户提交企业实名认证后被驳回，需要确认驳回原因和补充材料。',
    status: 'completed',
    priority: 'medium',
    assignee_id: MOCK_EMPLOYEE_ID,
    assignee_name: MOCK_EMPLOYEE_NAME,
    customer: {
      id: 'customer_104',
      name: '钱七',
      level: '企业客户',
    },
    related_order_id: '20231027004',
    created_at: '2023-10-27T10:50:00+08:00',
    completed_at: '2023-10-27T11:15:44+08:00',
  },
  {
    id: 'TK-1006',
    title: '发票开具失败 (税务系统超时)',
    description: '客户提交发票开具申请后提示税务系统超时，需要客服跟进处理。',
    status: 'processing',
    priority: 'low',
    assignee_id: MOCK_EMPLOYEE_ID,
    assignee_name: MOCK_EMPLOYEE_NAME,
    customer: {
      id: 'customer_106',
      name: '孙八',
      level: '普通客户',
    },
    related_order_id: '20231027006',
    created_at: '2023-10-27T09:40:12+08:00',
    completed_at: null,
  },
]

const ticketMessages: Record<string, MockTicketMessageEntity[]> = {
  'TK-1001': [
    {
      id: 'msg_1001_001',
      ticket_id: 'TK-1001',
      sender: 'customer',
      sender_name: '张三',
      content: '我多次输入正确账号密码后还是提示登录失败，麻烦帮我看一下。',
      created_at: '2026-05-23T09:15:00+08:00',
    },
  ],
  'TK-1002': [
    {
      id: 'msg_1002_001',
      ticket_id: 'TK-1002',
      sender: 'customer',
      sender_name: '李四',
      content: '导出经营报表一直没有响应，最后下载下来的文件也是空的。',
      created_at: '2026-05-23T09:48:00+08:00',
    },
  ],
  'TK-1003': [
    {
      id: 'msg_1003_001',
      ticket_id: 'TK-1003',
      sender: 'customer',
      sender_name: '赵六',
      content: '支付渠道已经扣款，但订单状态还是待支付。',
      created_at: '2026-05-23T14:33:00+08:00',
    },
    {
      id: 'msg_1003_002',
      ticket_id: 'TK-1003',
      sender: 'employee',
      sender_name: MOCK_EMPLOYEE_NAME,
      content: '您好，我先核对支付渠道回调和订单状态。',
      created_at: '2026-05-23T14:36:00+08:00',
    },
  ],
  'TK-1004': [
    {
      id: 'msg_1004_001',
      ticket_id: 'TK-1004',
      sender: 'customer',
      sender_name: '钱七',
      content: '企业实名认证被驳回了，想确认需要补什么材料。',
      created_at: '2026-05-23T10:52:00+08:00',
    },
    {
      id: 'msg_1004_002',
      ticket_id: 'TK-1004',
      sender: 'employee',
      sender_name: MOCK_EMPLOYEE_NAME,
      content: '您好，已根据驳回原因说明需要补充的材料。',
      created_at: '2026-05-23T11:10:00+08:00',
    },
  ],
  'TK-1005': [
    {
      id: 'msg_1005_001',
      ticket_id: 'TK-1005',
      sender: 'customer',
      sender_name: '张三',
      content: '你好，我刚刚在 APP 里购买了年费会员，支付宝显示已经付款成功了，但是回到 APP 看，还是普通会员，没有生效。',
      created_at: '2026-05-23T14:32:00+08:00',
    },
    {
      id: 'msg_1005_002',
      ticket_id: 'TK-1005',
      sender: 'bot',
      sender_name: '系统回复',
      content: '您好，收到您的反馈。系统可能存在网络延迟，请您提供一下订单号，我马上帮您确认。',
      created_at: '2026-05-23T14:33:00+08:00',
    },
    {
      id: 'msg_1005_003',
      ticket_id: 'TK-1005',
      sender: 'customer',
      sender_name: '张三',
      content: '好的，订单号是 20260523001。你们核实一下，如果不行能退款吗？',
      created_at: '2026-05-23T14:34:00+08:00',
    },
  ],
  'TK-1006': [
    {
      id: 'msg_1006_001',
      ticket_id: 'TK-1006',
      sender: 'customer',
      sender_name: '孙八',
      content: '提交发票申请后页面提示税务系统超时。',
      created_at: '2026-05-23T09:42:00+08:00',
    },
  ],
}

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 120)
  })
}

function isAuthorized(accessToken: string | null) {
  return accessToken === MOCK_ACCESS_TOKEN
}

function toTicketListItemDto(ticket: MockTicketEntity): TicketListItemDto {
  return {
    id: ticket.id,
    title: ticket.title,
    description: ticket.description,
    status: ticket.status,
    priority: ticket.priority,
    assignee_id: ticket.assignee_id,
    assignee_name: ticket.assignee_name,
    customer_name: ticket.customer.name,
    created_at: ticket.created_at,
    completed_at: ticket.completed_at,
  }
}

function toTicketDetailDto(ticket: MockTicketEntity): TicketDetailDto {
  return {
    id: ticket.id,
    title: ticket.title,
    description: ticket.description,
    status: ticket.status,
    priority: ticket.priority,
    assignee_id: ticket.assignee_id,
    assignee_name: ticket.assignee_name,
    customer: {
      id: ticket.customer.id,
      name: ticket.customer.name,
      level: ticket.customer.level,
    },
    related_order_id: ticket.related_order_id,
    created_at: ticket.created_at,
    completed_at: ticket.completed_at,
  }
}

function toClaimedTicketDto(ticket: MockTicketEntity, updatedAt: string): ClaimedTicketDto {
  return {
    id: ticket.id,
    status: 'processing',
    assignee_id: ticket.assignee_id ?? MOCK_EMPLOYEE_ID,
    assignee_name: ticket.assignee_name ?? MOCK_EMPLOYEE_NAME,
    updated_at: updatedAt,
  }
}

function toCompletedTicketDto(ticket: MockTicketEntity): CompletedTicketDto {
  return {
    id: ticket.id,
    status: 'completed',
    completed_at: ticket.completed_at ?? COMPLETED_AT,
  }
}

function toTicketMessageDto(message: MockTicketMessageEntity): TicketMessageDto {
  return {
    id: message.id,
    ticket_id: message.ticket_id,
    sender: message.sender,
    sender_name: message.sender_name,
    content: message.content,
    created_at: message.created_at,
  }
}

function matchesKeyword(ticket: MockTicketEntity, keyword: string) {
  const normalizedKeyword = keyword.trim().toLowerCase()
  if (!normalizedKeyword) return true

  return (
    ticket.id.toLowerCase().includes(normalizedKeyword) ||
    ticket.title.toLowerCase().includes(normalizedKeyword) ||
    ticket.description.toLowerCase().includes(normalizedKeyword)
  )
}

function paginate<TItem>(items: TItem[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}

function nowAsContractDateTime() {
  const now = new Date()
  const shanghaiTime = new Date(now.getTime() + 8 * 60 * 60 * 1000)
  return shanghaiTime.toISOString().replace(/\.\d{3}Z$/, '+08:00')
}

function findTicket(ticketId: string) {
  return tickets.find((item) => item.id === ticketId)
}

export async function mockGetTickets(
  accessToken: string | null,
  request: TicketsListRequest = {},
): Promise<ApiResponse<TicketsListResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const scope = request.scope ?? 'pool'
  const page = request.page ?? 1
  const pageSize = request.page_size ?? 20

  if (page < 1 || pageSize < 1) {
    return {
      code: 400,
      message: 'page 或 page_size 参数不合法',
      data: null,
    }
  }

  const scopedTickets = tickets.filter((ticket) => {
    if (scope === 'mine') {
      return ticket.assignee_id === MOCK_EMPLOYEE_ID && ticket.status !== 'open'
    }

    return ticket.status === 'open' && ticket.assignee_id === null
  })

  const filteredTickets = scopedTickets.filter((ticket) => {
    const statusMatched = request.status ? ticket.status === request.status : true
    const priorityMatched = request.priority ? ticket.priority === request.priority : true
    const keywordMatched = request.keyword ? matchesKeyword(ticket, request.keyword) : true

    return statusMatched && priorityMatched && keywordMatched
  })

  return {
    code: 200,
    message: 'success',
    data: {
      items: paginate(filteredTickets, page, pageSize).map(toTicketListItemDto),
      total: filteredTickets.length,
      page,
      page_size: pageSize,
    },
  }
}

export async function mockGetTicketDetail(
  accessToken: string | null,
  ticketId: string,
): Promise<ApiResponse<TicketDetailResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const ticket = findTicket(ticketId)
  if (!ticket) {
    return {
      code: 404,
      message: '工单不存在',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      ticket: toTicketDetailDto(ticket),
    },
  }
}

export async function mockClaimTicket(
  accessToken: string | null,
  ticketId: string,
  request: ClaimTicketRequest,
): Promise<ApiResponse<ClaimTicketResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const ticket = findTicket(ticketId)
  if (!ticket) {
    return {
      code: 404,
      message: '工单不存在',
      data: null,
    }
  }

  if (ticket.status !== 'open' || ticket.assignee_id) {
    return {
      code: 400,
      message: '工单已被接取',
      data: null,
    }
  }

  ticket.status = 'processing'
  ticket.assignee_id = request.employee_id
  ticket.assignee_name = MOCK_EMPLOYEE_NAME

  return {
    code: 200,
    message: 'success',
    data: {
      ticket: toClaimedTicketDto(ticket, CLAIMED_AT),
    },
  }
}

export async function mockCompleteTicket(
  accessToken: string | null,
  ticketId: string,
  request: CompleteTicketRequest,
): Promise<ApiResponse<CompleteTicketResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const ticket = findTicket(ticketId)
  if (!ticket) {
    return {
      code: 404,
      message: '工单不存在',
      data: null,
    }
  }

  if (ticket.assignee_id !== request.employee_id) {
    return {
      code: 403,
      message: '只能完成当前账号已接取的工单',
      data: null,
    }
  }

  ticket.status = 'completed'
  ticket.completed_at = COMPLETED_AT

  return {
    code: 200,
    message: 'success',
    data: {
      ticket: toCompletedTicketDto(ticket),
    },
  }
}

export async function mockGetTicketMessages(
  accessToken: string | null,
  ticketId: string,
): Promise<ApiResponse<TicketMessagesResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const ticket = findTicket(ticketId)
  if (!ticket) {
    return {
      code: 404,
      message: '工单不存在',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      items: (ticketMessages[ticketId] ?? []).map(toTicketMessageDto),
    },
  }
}

export async function mockSendTicketMessage(
  accessToken: string | null,
  ticketId: string,
  request: SendTicketMessageRequest,
): Promise<ApiResponse<SendTicketMessageResponseData>> {
  await wait()

  if (!isAuthorized(accessToken)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  const ticket = findTicket(ticketId)
  if (!ticket) {
    return {
      code: 404,
      message: '工单不存在',
      data: null,
    }
  }

  const content = request.content.trim()
  if (!content) {
    return {
      code: 400,
      message: '回复内容不能为空',
      data: null,
    }
  }

  const messages = ticketMessages[ticketId] ?? []
  const message: MockTicketMessageEntity = {
    id: `msg_${ticketId.replace(/\D/g, '')}_${String(messages.length + 1).padStart(3, '0')}`,
    ticket_id: ticketId,
    sender: 'employee',
    sender_name: MOCK_EMPLOYEE_NAME,
    content,
    created_at: nowAsContractDateTime(),
  }

  messages.push(message)
  ticketMessages[ticketId] = messages

  return {
    code: 200,
    message: 'success',
    data: {
      message: toTicketMessageDto(message),
    },
  }
}
