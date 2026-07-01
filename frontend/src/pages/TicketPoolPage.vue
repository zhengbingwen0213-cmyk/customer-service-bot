<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { claimTicket, getTickets } from '@/services/tickets'
import { useAuthStore } from '@/stores/auth'
import type {
  TicketListItemDto,
  TicketPriority,
  TicketsListRequest,
  TicketStatus,
} from '@/types/tickets'

const authStore = useAuthStore()
const router = useRouter()

const tickets = ref<TicketListItemDto[]>([])
const total = ref(0)
const keyword = ref('')
const priorityFilter = ref<TicketPriority | ''>('')
const statusFilter = ref<TicketStatus | ''>('open')
const isLoading = ref(true)
const claimingTicketId = ref<string | null>(null)
const feedbackMessage = ref('')
const errorMessage = ref('')

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadTickets()
})

watch([keyword, priorityFilter, statusFilter], () => {
  void loadTickets()
})

async function loadTickets() {
  isLoading.value = true
  errorMessage.value = ''

  const request: TicketsListRequest = {
    scope: 'pool',
    keyword: keyword.value,
    page: 1,
    page_size: 20,
  }

  if (statusFilter.value) {
    request.status = statusFilter.value
  }

  if (priorityFilter.value) {
    request.priority = priorityFilter.value
  }

  const response = await getTickets(authStore.token, request)

  if (response.code === 401) {
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (response.code === 200 && response.data) {
    tickets.value = response.data.items
    total.value = response.data.total
  } else {
    tickets.value = []
    total.value = 0
    errorMessage.value = response.message
  }

  isLoading.value = false
}

async function handleClaim(ticketId: string) {
  if (claimingTicketId.value) return

  if (!authStore.user?.id) {
    errorMessage.value = '当前账号信息不可用'
    return
  }

  claimingTicketId.value = ticketId
  feedbackMessage.value = ''
  errorMessage.value = ''

  const response = await claimTicket(authStore.token, ticketId, {
    employee_id: authStore.user.id,
  })

  if (response.code === 401) {
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (response.code === 200 && response.data) {
    tickets.value = tickets.value.filter((ticket) => ticket.id !== response.data?.ticket.id)
    total.value = Math.max(0, total.value - 1)
    feedbackMessage.value = '接取成功'
  } else {
    errorMessage.value = response.message
  }

  claimingTicketId.value = null
}

function resetFilters() {
  keyword.value = ''
  priorityFilter.value = ''
  statusFilter.value = 'open'
  void loadTickets()
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
}

function priorityLabel(priority: TicketPriority) {
  const labels: Record<TicketPriority, string> = {
    high: '高',
    medium: '中',
    low: '低',
  }

  return labels[priority]
}

function statusLabel(status: TicketStatus) {
  const labels: Record<TicketStatus, string> = {
    open: '待接取',
    processing: '处理中',
    completed: '已完成',
  }

  return labels[status]
}
</script>

<template>
  <section class="ticket-page" aria-label="工单池">
    <header class="ticket-page-header">
      <h1>工单池</h1>
    </header>

    <form class="ticket-filter-card" @submit.prevent="loadTickets">
      <label class="ticket-field ticket-search-field">
        <span>搜索工单</span>
        <span class="ticket-input-wrap">
          <span class="material-symbols-outlined">search</span>
          <input v-model="keyword" type="search" placeholder="搜索编号、标题..." />
        </span>
      </label>

      <label class="ticket-field">
        <span>优先级</span>
        <select v-model="priorityFilter">
          <option value="">全部</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </label>

      <label class="ticket-field">
        <span>状态</span>
        <select v-model="statusFilter">
          <option value="">全部</option>
          <option value="open">待接取</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
        </select>
      </label>

      <div class="ticket-filter-actions">
        <button class="secondary-action-button" type="button" @click="resetFilters">重置</button>
        <button class="query-action-button" type="submit">查询</button>
      </div>
    </form>

    <div v-if="feedbackMessage" class="ticket-feedback success" role="status">
      <span class="material-symbols-outlined">check_circle</span>
      <span>{{ feedbackMessage }}</span>
    </div>
    <div v-if="errorMessage" class="ticket-feedback error" role="alert">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorMessage }}</span>
    </div>

    <article class="ticket-table-card">
      <div class="ticket-table-scroll">
        <table class="ticket-data-table ticket-pool-table">
          <thead>
            <tr>
              <th>工单编号</th>
              <th>标题</th>
              <th>优先级</th>
              <th>状态</th>
              <th>创建时间</th>
              <th class="align-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="6" class="ticket-empty-cell">加载中</td>
            </tr>
            <tr v-else-if="tickets.length === 0">
              <td colspan="6" class="ticket-empty-cell">暂无工单</td>
            </tr>
            <template v-else>
              <tr v-for="ticket in tickets" :key="ticket.id">
                <td class="ticket-id-cell">{{ ticket.id }}</td>
                <td>
                  <RouterLink class="ticket-title-link" :to="`/tickets/${ticket.id}`">
                    {{ ticket.title }}
                  </RouterLink>
                </td>
                <td>
                  <span class="priority-pill" :class="`priority-${ticket.priority}`">
                    {{ priorityLabel(ticket.priority) }}
                  </span>
                </td>
                <td>
                  <span class="ticket-status-pill" :class="`ticket-status-${ticket.status}`">
                    {{ statusLabel(ticket.status) }}
                  </span>
                </td>
                <td class="ticket-time-cell">{{ formatDate(ticket.created_at) }}</td>
                <td class="ticket-actions-cell">
                  <button
                    class="text-link"
                    type="button"
                    :disabled="claimingTicketId === ticket.id"
                    @click="handleClaim(ticket.id)"
                  >
                    {{ claimingTicketId === ticket.id ? '接取中' : '接取' }}
                  </button>
                  <RouterLink class="text-link muted-link" :to="`/tickets/${ticket.id}`">
                    查看
                  </RouterLink>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <footer class="ticket-table-footer">
        <span>共 {{ total }} 条记录</span>
        <div class="pager">
          <button type="button" disabled aria-label="上一页">
            <span class="material-symbols-outlined">chevron_left</span>
          </button>
          <button class="pager-current" type="button">1</button>
          <button type="button" disabled aria-label="下一页">
            <span class="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </footer>
    </article>
  </section>
</template>
