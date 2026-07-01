<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'

import { askAssistant } from '@/services/assistant'
import type {
  AssistantAnswerDto,
  AssistantAnswerType,
  AssistantContextMessage,
  AssistantReferenceDto,
} from '@/types/assistant'

interface DebugChatMessage {
  id: string
  role: 'assistant' | 'employee'
  content: string
  answer?: AssistantAnswerDto
}

const conversationId = 'debug_session_001'
const question = ref('')
const messages = ref<DebugChatMessage[]>([createGreetingMessage()])
const isAsking = ref(false)
const errorMessage = ref('')
const chatCanvas = ref<HTMLElement | null>(null)

const answerMessages = computed(() => messages.value.filter((message) => message.answer))
const latestAnswer = computed(() => {
  const answers = answerMessages.value
  return answers.length ? (answers[answers.length - 1]?.answer ?? null) : null
})
const resultStatus = computed(() =>
  latestAnswer.value?.references.length ? '引用已就绪' : latestAnswer.value ? '回答已生成' : '等待问题',
)

async function handleAskAssistant() {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion || isAsking.value) return

  const contextMessages = buildContextMessages()
  messages.value.push({
    id: `debug_employee_${Date.now()}`,
    role: 'employee',
    content: trimmedQuestion,
  })
  question.value = ''
  errorMessage.value = ''
  isAsking.value = true
  await scrollToBottom()

  const response = await askAssistant({
    question: trimmedQuestion,
    scene: 'debug',
    conversation_id: conversationId,
    context_messages: contextMessages,
  })

  if (response.code === 200 && response.data) {
    messages.value.push({
      id: `debug_assistant_${Date.now()}`,
      role: 'assistant',
      content: response.data.answer.answer,
      answer: response.data.answer,
    })
  } else {
    errorMessage.value = response.message
  }

  isAsking.value = false
  await scrollToBottom()
}

function clearConversation() {
  if (isAsking.value) return

  messages.value = [createGreetingMessage()]
  question.value = ''
  errorMessage.value = ''
}

function createGreetingMessage(): DebugChatMessage {
  return {
    id: 'debug_greeting',
    role: 'assistant',
    content: '您好，我是智能客服助理。请输入您想测试的问题，我将展示回答结果和引用来源。',
  }
}

function buildContextMessages(): AssistantContextMessage[] {
  return messages.value
    .filter((message) => message.id !== 'debug_greeting')
    .slice(-3)
    .map((message) => ({
      sender: message.role === 'employee' ? 'employee' : 'bot',
      content: message.content,
    }))
}

async function scrollToBottom() {
  await nextTick()
  if (chatCanvas.value) {
    chatCanvas.value.scrollTop = chatCanvas.value.scrollHeight
  }
}

function answerTypeLabel(type: AssistantAnswerType) {
  const labels: Record<AssistantAnswerType, string> = {
    qa_direct: '直接答案',
    clarification: '反问',
    generated: '生成答案',
  }

  return labels[type]
}

function answerTypeIcon(type: AssistantAnswerType) {
  const icons: Record<AssistantAnswerType, string> = {
    qa_direct: 'done_all',
    clarification: 'help',
    generated: 'auto_awesome',
  }

  return icons[type]
}

function referenceIcon(reference: AssistantReferenceDto) {
  return reference.type === 'qa' ? 'quiz' : 'description'
}

function referenceTitle(reference: AssistantReferenceDto) {
  return `引用来源: ${reference.type === 'qa' ? 'QA' : '文档'}：${reference.title}`
}

function referenceScore(reference: AssistantReferenceDto) {
  return `匹配度：${Math.round(reference.score * 100)}%`
}

function answerReferenceScore(answer: AssistantAnswerDto) {
  const reference = answer.references[0]
  return reference ? referenceScore(reference) : ''
}
</script>

<template>
  <section class="assistant-debug-page" aria-label="智能问答调试">
    <header class="assistant-debug-heading">
      <div>
        <h1>智能问答调试</h1>
        <p>模拟客服问题，检查回答内容、缺失信息和引用来源。</p>
      </div>
      <span>最小闭环调试</span>
    </header>

    <div class="assistant-debug-layout">
      <section class="debug-chat-panel" aria-label="对话模拟器">
        <header class="debug-panel-header">
          <h2>
            <span class="material-symbols-outlined">chat</span>
            对话模拟器
          </h2>
          <button class="text-link muted-link" type="button" :disabled="isAsking" @click="clearConversation">
            <span class="material-symbols-outlined">delete_sweep</span>
            清空会话
          </button>
        </header>

        <div ref="chatCanvas" class="debug-chat-canvas">
          <article
            v-for="message in messages"
            :key="message.id"
            class="debug-chat-message"
            :class="`debug-chat-message-${message.role}`"
          >
            <span class="debug-avatar">
              <span class="material-symbols-outlined">
                {{ message.role === 'assistant' ? 'smart_toy' : 'person' }}
              </span>
            </span>
            <div>
              <strong>{{ message.role === 'assistant' ? '系统助理' : '员工' }}</strong>
              <p>{{ message.content }}</p>
            </div>
          </article>
        </div>

        <form class="debug-input-bar" @submit.prevent="handleAskAssistant">
          <button class="debug-plus-button" type="button" aria-label="添加" disabled>
            <span class="material-symbols-outlined">add</span>
          </button>
          <input v-model="question" type="text" placeholder="输入要测试的问题" />
          <button class="debug-send-button" type="submit" :disabled="!question.trim() || isAsking">
            <span>{{ isAsking ? '发送中' : '发送' }}</span>
            <span class="material-symbols-outlined">send</span>
          </button>
        </form>
      </section>

      <aside class="debug-result-panel" aria-label="问答结果面板">
        <header class="debug-panel-header result-header">
          <h2>
            <span class="material-symbols-outlined">manage_search</span>
            问答结果面板
          </h2>
          <span class="result-status">
            <span></span>
            {{ resultStatus }}
          </span>
        </header>

        <div class="debug-result-body">
          <div v-if="errorMessage" class="ticket-feedback error inline" role="alert">
            <span class="material-symbols-outlined">error</span>
            <span>{{ errorMessage }}</span>
          </div>

          <p v-if="answerMessages.length === 0 && !errorMessage" class="debug-empty-state">
            暂无回答结果
          </p>

          <template v-else>
            <article
              v-for="(message, index) in answerMessages"
              :key="message.id"
              class="debug-answer-card"
              :class="{ 'debug-answer-card-active': message.answer === latestAnswer }"
            >
              <template v-if="message.answer">
                <header>
                  <span>第 {{ index + 1 }} 轮{{ message.answer.answer_type === 'clarification' ? '反问' : '回答' }}</span>
                  <strong v-if="message.answer.references.length">
                    {{ answerReferenceScore(message.answer) }}
                  </strong>
                  <strong v-else-if="message.answer.answer_type === 'clarification'">触发反问</strong>
                </header>

                <div class="debug-answer-section">
                  <span class="debug-answer-label">
                    {{ message.answer.answer_type === 'clarification' ? '策略动作' : '回答类型' }}
                  </span>
                  <span class="debug-answer-type" :class="`debug-answer-type-${message.answer.answer_type}`">
                    <span class="material-symbols-outlined">{{ answerTypeIcon(message.answer.answer_type) }}</span>
                    {{ answerTypeLabel(message.answer.answer_type) }}
                  </span>
                </div>

                <div v-if="message.answer.missing_fields.length" class="debug-answer-section">
                  <span class="debug-answer-label">缺失实体</span>
                  <div class="debug-missing-list">
                    <span v-for="field in message.answer.missing_fields" :key="field">
                      <span class="material-symbols-outlined">error</span>
                      {{ field }}
                    </span>
                  </div>
                </div>

                <div class="debug-answer-block">
                  <span class="debug-answer-label">
                    {{ message.answer.answer_type === 'clarification' ? '生成文案' : '回答内容' }}
                  </span>
                  <p>{{ message.answer.answer }}</p>
                </div>

                <div v-if="message.answer.context_messages_used > 0" class="debug-answer-section">
                  <span class="debug-answer-label">最近上下文</span>
                  <span class="debug-context-note">
                    已结合最近 {{ message.answer.context_messages_used }} 条上下文
                  </span>
                </div>

                <div class="debug-reference-section">
                  <span class="debug-answer-label">引用来源</span>
                  <div v-if="message.answer.references.length" class="debug-reference-list">
                    <article
                      v-for="reference in message.answer.references"
                      :key="`${message.id}_${reference.type}_${reference.source_id}`"
                    >
                      <span class="material-symbols-outlined">{{ referenceIcon(reference) }}</span>
                      <div>
                        <strong>{{ referenceTitle(reference) }}</strong>
                        <p>{{ reference.snippet }}</p>
                      </div>
                    </article>
                  </div>
                  <p v-else class="debug-no-reference">暂无引用来源</p>
                </div>
              </template>
            </article>
          </template>
        </div>
      </aside>
    </div>
  </section>
</template>
