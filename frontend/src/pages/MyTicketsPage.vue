<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { getTickets } from '@/services/tickets'
import { useAuthStore } from '@/stores/auth'
import type { TicketListItemDto, TicketsListRequest, TicketStatus } from '@/types/tickets'

const authStore = useAuthStore()
const router = useRouter()

const tickets = ref<TicketListItemDto[]>([])
const total = ref(0)
const keyword = ref('')
const selectedStatus = ref<TicketStatus | ''>('')
const isLoading = ref(true)
const errorMessage = ref('')

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadTickets()
})

watch([keyword, selectedStatus], () => {
  void loadTickets()
})

async function loadTickets() {
  isLoading.value = true
  errorMessage.value = ''

  const request: TicketsListRequest = {
    scope: 'mine',
    keyword: keyword.value,
    page: 1,
    page_size: 20,
  }

  if (selectedStatus.value) {
    request.status = selectedStatus.value
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

function toggleStatus(status: TicketStatus) {
  selectedStatus.value = selectedStatus.value === status ? '' : status
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
}

function ticketUpdatedAt(ticket: TicketListItemDto) {
  return formatDate(ticket.completed_at ?? ticket.created_at)
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
  <section class="ticket-page" aria-label="我的工单">
    <header class="ticket-page-header">
      <h1>我的工单</h1>
      <div class="my-ticket-header-actions">
        <div class="segment-control" aria-label="状态筛选">
          <button
            type="button"
            :class="{ active: selectedStatus === 'processing' }"
            @click="toggleStatus('processing')"
          >
            处理中
          </button>
          <button
            type="button"
            :class="{ active: selectedStatus === 'completed' }"
            @click="toggleStatus('completed')"
          >
            已完成
          </button>
        </div>
      </div>
    </header>

    <article class="ticket-table-card">
      <div class="my-ticket-toolbar">
        <label class="ticket-input-wrap compact">
          <span class="material-symbols-outlined">search</span>
          <input v-model="keyword" type="search" placeholder="搜索工单..." />
        </label>
        <button class="filter-action-button" type="button" @click="loadTickets">
          <span class="material-symbols-outlined">filter_list</span>
          筛选
        </button>
      </div>

      <div v-if="errorMessage" class="ticket-feedback error inline" role="alert">
        <span class="material-symbols-outlined">error</span>
        <span>{{ errorMessage }}</span>
      </div>

      <div class="ticket-table-scroll">
        <table class="ticket-data-table my-ticket-table">
          <thead>
            <tr>
              <th>工单编号</th>
              <th>标题</th>
              <th>状态</th>
              <th>更新时间</th>
              <th class="align-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="5" class="ticket-empty-cell">加载中</td>
            </tr>
            <tr v-else-if="tickets.length === 0">
              <td colspan="5" class="ticket-empty-cell">暂无工单</td>
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
                  <span class="ticket-status-pill" :class="`ticket-status-${ticket.status}`">
                    {{ statusLabel(ticket.status) }}
                  </span>
                </td>
                <td class="ticket-time-cell">{{ ticketUpdatedAt(ticket) }}</td>
                <td class="ticket-actions-cell single-action">
                  <RouterLink class="text-link" :to="`/tickets/${ticket.id}`">查看</RouterLink>
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
