<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { askAssistant } from '@/services/assistant'
import { getDashboardSummary, getDashboardTickets } from '@/services/dashboard'
import { useAuthStore } from '@/stores/auth'
import type { AssistantAnswerDto, AssistantReferenceDto, AssistantReferenceType } from '@/types/assistant'
import type { DashboardSummaryResponseData, DashboardTicketDto, TicketStatus } from '@/types/dashboard'

interface SummaryCard {
  label: string
  icon: string
  value: number
  tone: 'error' | 'primary' | 'secondary' | 'neutral'
  note?: string
}

interface AssistantMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  references: AssistantReferenceDto[]
  missingFields: string[]
}

const router = useRouter()
const authStore = useAuthStore()
const summary = ref<DashboardSummaryResponseData | null>(null)
const tickets = ref<DashboardTicketDto[]>([])
const question = ref('')
const isLoading = ref(true)
const isAsking = ref(false)
const assistantError = ref('')
const assistantMessages = ref<AssistantMessage[]>([])

const summaryCards = computed<SummaryCard[]>(() => {
  const current = summary.value
  const qaCount = current?.qa_count ?? 0
  const documentCount = current?.document_count ?? 0

  return [
    {
      label: '待接工单',
      icon: 'pending_actions',
      value: current?.open_ticket_count ?? 0,
      tone: 'error',
    },
    {
      label: '处理中',
      icon: 'autorenew',
      value: current?.processing_ticket_count ?? 0,
      tone: 'primary',
    },
    {
      label: '已完成',
      icon: 'check_circle',
      value: current?.completed_ticket_count ?? 0,
      tone: 'secondary',
    },
    {
      label: '知识总数',
      icon: 'library_books',
      value: qaCount + documentCount,
      tone: 'neutral',
      note: `QA ${qaCount} / 文档 ${documentCount}`,
    },
  ]
})

onMounted(async () => {
  assistantMessages.value = [
    {
      id: 'assistant_intro',
      role: 'assistant',
      content: '可以直接输入客服问题，我会基于当前知识库给出建议回答。',
      references: [],
      missingFields: [],
    },
  ]

  try {
    const [summaryResponse, ticketsResponse] = await Promise.all([
      getDashboardSummary(authStore.token),
      getDashboardTickets(authStore.token, { limit: 2 }),
    ])

    if (summaryResponse.code === 401 || ticketsResponse.code === 401) {
      authStore.clearSession()
      await router.push({ name: 'login' })
      return
    }

    if (summaryResponse.code === 200 && summaryResponse.data) {
      summary.value = summaryResponse.data
    }

    if (ticketsResponse.code === 200 && ticketsResponse.data) {
      tickets.value = ticketsResponse.data.items
    }
  } finally {
    isLoading.value = false
  }
})

function toAssistantMessage(answer: AssistantAnswerDto): AssistantMessage {
  return {
    id: `answer_${Date.now()}`,
    role: 'assistant',
    content: answer.answer,
    references: answer.references,
    missingFields: answer.missing_fields,
  }
}

function statusLabel(status: TicketStatus) {
  const labels: Record<TicketStatus, string> = {
    open: '待接单',
    processing: '处理中',
    completed: '已完成',
  }

  return labels[status]
}

function statusClass(status: TicketStatus) {
  const classes: Record<TicketStatus, string> = {
    open: 'status-open',
    processing: 'status-processing',
    completed: 'status-completed',
  }

  return classes[status]
}

function referenceTypeLabel(type: AssistantReferenceType) {
  const labels: Record<AssistantReferenceType, string> = {
    qa: 'QA',
    document: '文档',
  }

  return labels[type]
}

async function handleAskAssistant() {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion || isAsking.value) return

  assistantError.value = ''
  assistantMessages.value.push({
    id: `question_${Date.now()}`,
    role: 'user',
    content: trimmedQuestion,
    references: [],
    missingFields: [],
  })
  question.value = ''
  isAsking.value = true

  try {
    const response = await askAssistant({
      question: trimmedQuestion,
      scene: 'quick',
    })

    if (response.code === 401) {
      authStore.clearSession()
      await router.push({ name: 'login' })
      return
    }

    if (response.code === 200 && response.data) {
      assistantMessages.value.push(toAssistantMessage(response.data.answer))
      return
    }

    assistantError.value = response.message || '智能助手暂时无法回答，请稍后重试。'
  } catch {
    assistantError.value = '智能助手暂时无法回答，请检查网络后重试。'
  } finally {
    isAsking.value = false
  }
}
</script>

<template>
  <section class="dashboard-page" aria-label="客服工作台">
    <header class="dashboard-heading">
      <div>
        <h1>客服工作台</h1>
        <p>实时查看待处理工单、知识库规模与 AI 辅助回答状态。</p>
      </div>
    </header>

    <div class="metric-grid" aria-label="工作概览">
      <article
        v-for="card in summaryCards"
        :key="card.label"
        class="metric-card"
        :class="`metric-card-${card.tone}`"
      >
        <div class="metric-label">
          <span class="material-symbols-outlined">{{ card.icon }}</span>
          <span>{{ card.label }}</span>
        </div>
        <strong>{{ card.value }}</strong>
        <small v-if="card.note">{{ card.note }}</small>
      </article>
    </div>

    <div class="dashboard-grid">
      <div class="dashboard-main">
        <article class="dashboard-panel ticket-panel">
          <header class="panel-header">
            <h2>待处理工单</h2>
            <RouterLink class="text-link" to="/tickets">查看全部</RouterLink>
          </header>

          <div class="ticket-table-wrap">
            <table class="ticket-table">
              <thead>
                <tr>
                  <th>工单号</th>
                  <th>标题</th>
                  <th>发起人</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="isLoading">
                  <td colspan="5">加载中</td>
                </tr>
                <tr v-for="ticket in tickets" :key="ticket.id">
                  <td class="ticket-id">{{ ticket.id }}</td>
                  <td>{{ ticket.title }}</td>
                  <td class="muted-cell">{{ ticket.customer_name }}</td>
                  <td>
                    <span class="status-pill" :class="statusClass(ticket.status)">
                      {{ statusLabel(ticket.status) }}
                    </span>
                  </td>
                  <td>
                    <RouterLink class="text-link" :to="`/tickets/${ticket.id}`">查看</RouterLink>
                  </td>
                </tr>
                <tr v-if="!isLoading && tickets.length === 0">
                  <td colspan="5">暂无待处理工单</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <div class="quick-actions" aria-label="知识库快捷入口">
          <RouterLink class="quick-action" to="/knowledge/qa">
            <span class="material-symbols-outlined">quiz</span>
            <span>QA 库</span>
          </RouterLink>
          <RouterLink class="quick-action" to="/documents">
            <span class="material-symbols-outlined">upload_file</span>
            <span>文档入库</span>
          </RouterLink>
          <RouterLink class="quick-action" to="/assistant">
            <span class="material-symbols-outlined">smart_toy</span>
            <span>问答调试</span>
          </RouterLink>
        </div>
      </div>

      <aside class="assistant-panel" aria-label="智能助手">
        <header class="assistant-header">
          <div>
            <span class="material-symbols-outlined filled">auto_awesome</span>
            <h2>智能助手</h2>
          </div>
        </header>

        <div class="assistant-body">
          <article
            v-for="message in assistantMessages"
            :key="message.id"
            class="assistant-message"
            :class="`assistant-message-${message.role}`"
          >
            <span class="material-symbols-outlined">
              {{ message.role === 'assistant' ? 'smart_toy' : 'person' }}
            </span>
            <div>
              <p>{{ message.content }}</p>
              <div v-if="message.missingFields.length" class="missing-field-list">
                <strong>还需要补充</strong>
                <span v-for="field in message.missingFields" :key="field">{{ field }}</span>
              </div>
              <div v-if="message.references.length" class="reference-list">
                <strong>引用来源</strong>
                <div v-for="reference in message.references" :key="reference.source_id">
                  <span>{{ referenceTypeLabel(reference.type) }} · {{ reference.title }}</span>
                  <small>{{ reference.snippet }}</small>
                </div>
              </div>
            </div>
          </article>
          <p v-if="assistantError" class="assistant-error">{{ assistantError }}</p>
        </div>

        <form class="assistant-input" @submit.prevent="handleAskAssistant">
          <input v-model="question" type="text" placeholder="请输入客服问题..." />
          <button type="submit" :disabled="!question.trim() || isAsking" aria-label="发送">
            <span class="material-symbols-outlined">send</span>
          </button>
        </form>
      </aside>
    </div>
  </section>
</template>
