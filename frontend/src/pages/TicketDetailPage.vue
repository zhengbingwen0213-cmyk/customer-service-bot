<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { askAssistant } from '@/services/assistant'
import {
  completeTicket,
  getTicketDetail,
  getTicketMessages,
  sendTicketMessage,
} from '@/services/tickets'
import { useAuthStore } from '@/stores/auth'
import type {
  AssistantAnswerDto,
  AssistantAskRequest,
  AssistantContextMessage,
  AssistantReferenceDto,
} from '@/types/assistant'
import type {
  SendTicketMessageRequest,
  TicketDetailDto,
  TicketMessageDto,
  TicketPriority,
  TicketStatus,
} from '@/types/tickets'
import { isMockApiEnabled } from '@/utils/runtime'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isMockMode = isMockApiEnabled()

const ticket = ref<TicketDetailDto | null>(null)
const messages = ref<TicketMessageDto[]>([])
const assistantAnswer = ref<AssistantAnswerDto | null>(null)
const replyContent = ref('')
const completionSummary = ref('')
const adoptedAssistantAnswerId = ref<string | null>(null)
const referencePanel = ref<HTMLElement | null>(null)
const isLoading = ref(true)
const isAssistantLoading = ref(false)
const isSending = ref(false)
const isCompleting = ref(false)
const errorMessage = ref('')
const assistantErrorMessage = ref('')
const feedbackMessage = ref('')
const referencesHighlighted = ref(false)

const assistantParagraphs = computed(() =>
  assistantAnswer.value?.answer.split(/\n+/).filter(Boolean) ?? [],
)

const assistantReferences = computed(() => assistantAnswer.value?.references ?? [])

const assistantStatusText = computed(() => {
  if (isAssistantLoading.value) return '分析中'
  if (assistantErrorMessage.value) return '分析失败'
  if (assistantAnswer.value) return '分析完成'
  return '待生成'
})

const canComplete = computed(
  () =>
    Boolean(ticket.value) &&
    ticket.value?.status !== 'completed' &&
    ticket.value?.assignee_id === authStore.user?.id,
)

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadTicketDetail()
})

async function loadTicketDetail() {
  isLoading.value = true
  errorMessage.value = ''
  feedbackMessage.value = ''

  const ticketId = getRouteTicketId()
  if (!ticketId) {
    errorMessage.value = '工单不存在'
    isLoading.value = false
    return
  }

  const detailResponse = await getTicketDetail(authStore.token, ticketId)

  if (detailResponse.code === 401) {
    await redirectToLogin()
    return
  }

  if (detailResponse.code !== 200 || !detailResponse.data) {
    errorMessage.value = detailResponse.message
    isLoading.value = false
    return
  }

  ticket.value = detailResponse.data.ticket

  const messagesResponse = await getTicketMessages(authStore.token, ticketId)

  if (messagesResponse.code === 401) {
    await redirectToLogin()
    return
  }

  if (messagesResponse.code === 200 && messagesResponse.data) {
    messages.value = messagesResponse.data.items
  } else {
    errorMessage.value = messagesResponse.message
  }

  isLoading.value = false
  await loadAssistantSuggestion()
}

async function loadAssistantSuggestion() {
  if (!ticket.value) return

  isAssistantLoading.value = true
  assistantErrorMessage.value = ''
  referencesHighlighted.value = false

  const latestCustomerMessage = [...messages.value]
    .reverse()
    .find((message) => message.sender === 'customer')
  const contextMessages: AssistantContextMessage[] = messages.value.slice(-3).map((message) => ({
    sender: message.sender,
    content: message.content,
  }))
  const payload: AssistantAskRequest = {
    question: latestCustomerMessage?.content ?? ticket.value.description,
    scene: 'ticket',
    ticket_id: ticket.value.id,
    context_messages: contextMessages,
  }
  try {
    const response = await askAssistant(payload)

    if (response.code === 200 && response.data) {
      assistantAnswer.value = response.data.answer
    } else {
      assistantAnswer.value = null
      assistantErrorMessage.value = response.message || 'AI 建议生成失败，请稍后重试'
    }
  } catch {
    assistantAnswer.value = null
    assistantErrorMessage.value = 'AI 建议生成失败，请检查后端服务后重试'
  } finally {
    isAssistantLoading.value = false
  }
}

function getRouteTicketId() {
  const ticketIdParam = route.params.ticketId
  return Array.isArray(ticketIdParam) ? ticketIdParam[0] : ticketIdParam
}

async function redirectToLogin() {
  authStore.clearSession()
  await router.push({ name: 'login' })
}

function formatDate(value: string | null) {
  if (!value) return '-'
  const normalized = value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
  return normalized.slice(0, 16)
}

function formatTime(value: string) {
  const match = value.match(/T(\d{2}:\d{2})/)
  return match?.[1] ?? formatDate(value)
}

function priorityLabel(priority: TicketPriority) {
  const labels: Record<TicketPriority, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级',
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

function referenceIcon(reference: AssistantReferenceDto) {
  return reference.type === 'qa' ? 'quiz' : 'description'
}

function referenceTypeLabel(reference: AssistantReferenceDto) {
  return reference.type === 'qa' ? 'QA 来源' : '文档来源'
}

function answerTypeLabel(answerType: AssistantAnswerDto['answer_type']) {
  const labels: Record<AssistantAnswerDto['answer_type'], string> = {
    qa_direct: '知识库直答',
    clarification: '需要补充信息',
    generated: '生成建议',
  }

  return labels[answerType]
}

function handleApplySuggestion() {
  if (!assistantAnswer.value) return

  replyContent.value = assistantAnswer.value.answer
  adoptedAssistantAnswerId.value = assistantAnswer.value.answer_id
  feedbackMessage.value = '已采用 AI 建议'
  errorMessage.value = ''
}

function handleViewReferences() {
  if (!assistantReferences.value.length) return

  referencePanel.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  referencesHighlighted.value = true
  feedbackMessage.value = '引用来源已展示'
}

async function handleSendReply() {
  const content = replyContent.value.trim()
  const currentTicket = ticket.value
  if (!content || isSending.value || !currentTicket || currentTicket.status === 'completed') return

  isSending.value = true
  errorMessage.value = ''
  feedbackMessage.value = ''

  const payload: SendTicketMessageRequest = {
    content,
  }

  if (adoptedAssistantAnswerId.value) {
    payload.used_assistant_answer_id = adoptedAssistantAnswerId.value
  }

  const response = await sendTicketMessage(authStore.token, currentTicket.id, payload)

  if (response.code === 401) {
    isSending.value = false
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data) {
    messages.value.push(response.data.message)
    replyContent.value = ''
    adoptedAssistantAnswerId.value = null
    feedbackMessage.value = '回复已发送'
  } else {
    errorMessage.value = response.message
  }

  isSending.value = false
}

async function handleCompleteTicket() {
  if (!ticket.value || isCompleting.value || ticket.value.status === 'completed') return

  if (!authStore.user?.id) {
    errorMessage.value = '当前账号信息不可用'
    return
  }

  const summary = completionSummary.value.trim()
  if (!summary) {
    errorMessage.value = '请填写处理摘要'
    return
  }

  isCompleting.value = true
  errorMessage.value = ''
  feedbackMessage.value = ''

  const response = await completeTicket(authStore.token, ticket.value.id, {
    employee_id: authStore.user.id,
    summary,
  })

  if (response.code === 401) {
    isCompleting.value = false
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data) {
    ticket.value = {
      ...ticket.value,
      status: response.data.ticket.status,
      completed_at: response.data.ticket.completed_at,
    }
    completionSummary.value = ''
    feedbackMessage.value = '工单已完成'
  } else {
    errorMessage.value = response.message
  }

  isCompleting.value = false
}
</script>

<template>
  <section class="ticket-workbench-page" aria-label="工单详情">
    <header class="ticket-workbench-heading">
      <div class="ticket-breadcrumb">
        <RouterLink to="/my-tickets">我的工单</RouterLink>
        <span class="material-symbols-outlined">chevron_right</span>
        <strong>工单详情 {{ ticket?.id ?? '' }}</strong>
      </div>
      <span v-if="isMockMode" class="mock-badge">[Mock] 演示数据</span>
    </header>

    <article v-if="isLoading" class="ticket-detail-state-card">
      <p>加载中</p>
    </article>

    <article v-else-if="errorMessage && !ticket" class="ticket-detail-state-card">
      <p>{{ errorMessage }}</p>
    </article>

    <div v-else-if="ticket" class="ticket-workbench-grid">
      <aside class="ticket-info-panel">
        <div class="ticket-info-title">
          <div>
            <h1>{{ ticket.id }}</h1>
            <p>创建时间: {{ formatDate(ticket.created_at) }}</p>
          </div>
          <span class="priority-pill" :class="`priority-${ticket.priority}`">
            {{ priorityLabel(ticket.priority) }}
          </span>
        </div>

        <div class="ticket-status-line">
          <span :class="`ticket-status-dot ticket-status-dot-${ticket.status}`"></span>
          <span>{{ statusLabel(ticket.status) }}</span>
        </div>

        <dl class="ticket-info-list">
          <div>
            <dt>客户信息</dt>
            <dd>{{ ticket.customer.name }}（客户编号 {{ ticket.customer.id }}）</dd>
            <small>{{ ticket.customer.level }}</small>
          </div>
          <div>
            <dt>客户问题</dt>
            <dd>{{ ticket.title }}</dd>
          </div>
          <div>
            <dt>工单描述</dt>
            <dd>{{ ticket.description }}</dd>
          </div>
          <div>
            <dt>关联订单</dt>
            <dd class="ticket-order-id">{{ ticket.related_order_id }}</dd>
          </div>
          <div v-if="ticket.completed_at">
            <dt>完成时间</dt>
            <dd>{{ formatDate(ticket.completed_at) }}</dd>
          </div>
        </dl>

        <div v-if="ticket.status !== 'completed'" class="ticket-complete-form">
          <label for="completion-summary">处理摘要</label>
          <textarea
            id="completion-summary"
            v-model="completionSummary"
            :disabled="!canComplete || isCompleting"
            placeholder="填写本次处理结论。"
          ></textarea>
          <button
            class="ticket-complete-button"
            type="button"
            :disabled="!canComplete || isCompleting || !completionSummary.trim()"
            @click="handleCompleteTicket"
          >
            <span class="material-symbols-outlined">check_circle</span>
            {{ isCompleting ? '完成中' : '完成工单' }}
          </button>
        </div>
        <button v-else class="ticket-complete-button" type="button" disabled>
          <span class="material-symbols-outlined">check_circle</span>
          已完成
        </button>
      </aside>

      <section class="conversation-panel" aria-label="会话记录">
        <header class="conversation-header">
          <h2>
            <span class="material-symbols-outlined">forum</span>
            会话记录
          </h2>
        </header>

        <div class="conversation-list">
          <article
            v-for="message in messages"
            :key="message.id"
            class="conversation-message"
            :class="`conversation-message-${message.sender}`"
          >
            <span>{{ message.sender_name }} • {{ formatTime(message.created_at) }}</span>
            <p>{{ message.content }}</p>
          </article>
          <p v-if="messages.length === 0" class="conversation-empty">暂无会话记录</p>
        </div>

        <form class="reply-editor" @submit.prevent="handleSendReply">
          <div class="reply-toolbar">
            <button
              class="assistant-adopt-button"
              type="button"
              :disabled="!assistantAnswer || ticket.status === 'completed'"
              @click="handleApplySuggestion"
            >
              <span class="material-symbols-outlined">smart_toy</span>
              采用 AI 建议
            </button>
          </div>
          <textarea
            v-model="replyContent"
            :disabled="ticket.status === 'completed'"
            placeholder="输入回复内容，采用 AI 建议后会自动填入。"
          ></textarea>
          <div class="reply-footer">
            <span>输入后点击发送记录。</span>
            <button
              type="submit"
              :disabled="!replyContent.trim() || isSending || ticket.status === 'completed'"
            >
              {{ isSending ? '发送中' : '发送' }}
            </button>
          </div>
        </form>
      </section>

      <aside class="ticket-ai-column">
        <section class="ticket-ai-panel" aria-label="AI 智能辅助">
          <header>
            <h2>
              <span class="material-symbols-outlined filled">auto_awesome</span>
              AI 智能辅助
            </h2>
            <span class="ticket-ai-status">{{ assistantStatusText }}</span>
          </header>

          <div class="ticket-ai-body">
            <p v-if="isAssistantLoading" class="detail-placeholder">建议生成中</p>
            <div v-else-if="assistantErrorMessage" class="assistant-error-state">
              <p class="detail-placeholder">{{ assistantErrorMessage }}</p>
              <button type="button" @click="loadAssistantSuggestion">重新生成</button>
            </div>

            <template v-else-if="assistantAnswer">
              <div class="assistant-suggestion">
                <div class="assistant-suggestion-heading">
                  <h3>建议回复内容</h3>
                  <span>{{ answerTypeLabel(assistantAnswer.answer_type) }}</span>
                </div>
                <div class="assistant-suggestion-content">
                  <p v-for="paragraph in assistantParagraphs" :key="paragraph">
                    {{ paragraph }}
                  </p>
                </div>
                <div
                  v-if="assistantAnswer.missing_fields.length"
                  class="assistant-missing-fields"
                >
                  <strong>需补充信息</strong>
                  <ul>
                    <li v-for="field in assistantAnswer.missing_fields" :key="field">
                      {{ field }}
                    </li>
                  </ul>
                </div>
              </div>

              <div
                ref="referencePanel"
                class="assistant-reference-section"
                :class="{ highlighted: referencesHighlighted }"
              >
                <h3>知识库引用来源</h3>
                <div class="assistant-reference-list">
                  <article
                    v-for="reference in assistantReferences"
                    :key="reference.source_id"
                    class="assistant-reference-card"
                  >
                    <span class="material-symbols-outlined">{{ referenceIcon(reference) }}</span>
                    <div>
                      <strong>{{ reference.title }}</strong>
                      <span>{{ referenceTypeLabel(reference) }}</span>
                      <small>{{ reference.snippet }}</small>
                    </div>
                  </article>
                  <p v-if="assistantReferences.length === 0" class="detail-placeholder">
                    暂无引用来源
                  </p>
                </div>
              </div>
            </template>
          </div>
        </section>

        <section class="ticket-quick-panel" aria-label="快捷操作">
          <h3>快捷操作</h3>
          <div>
            <button
              type="button"
              :disabled="!assistantAnswer || ticket.status === 'completed'"
              @click="handleApplySuggestion"
            >
              采用建议
            </button>
            <button
              type="button"
              :disabled="assistantReferences.length === 0"
              @click="handleViewReferences"
            >
              查看引用
            </button>
            <button type="button" :disabled="!canComplete || isCompleting" @click="handleCompleteTicket">
              完成工单
            </button>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="feedbackMessage" class="ticket-feedback success ticket-detail-feedback" role="status">
      <span class="material-symbols-outlined">check_circle</span>
      <span>{{ feedbackMessage }}</span>
    </div>
    <div v-if="errorMessage && ticket" class="ticket-feedback error ticket-detail-feedback" role="alert">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorMessage }}</span>
    </div>
  </section>
</template>
