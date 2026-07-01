<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createKnowledgeQa,
  deleteKnowledgeQa,
  getKnowledgeQaList,
  updateKnowledgeQa,
} from '@/services/knowledge'
import { useAuthStore } from '@/stores/auth'
import type {
  CreateKnowledgeQaRequest,
  KnowledgeQaDto,
  KnowledgeQaListRequest,
  KnowledgeQaStatus,
} from '@/types/knowledge'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const qaItems = ref<KnowledgeQaDto[]>([])
const total = ref(0)
const keyword = ref('')
const isLoading = ref(true)
const isSaving = ref(false)
const deletingQaId = ref<string | null>(null)
const feedbackMessage = ref('')
const errorMessage = ref('')
const modalErrorMessage = ref('')
const isModalOpen = ref(false)
const editingQa = ref<KnowledgeQaDto | null>(null)
const formQuestion = ref('')
const formAnswer = ref('')
const formStatus = ref<KnowledgeQaStatus>('enabled')

const modalTitle = computed(() => (editingQa.value ? '编辑 QA' : '新增 QA'))
const submitText = computed(() => (editingQa.value ? '保存更改' : '保存更改'))
const answerLength = computed(() => formAnswer.value.length)

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadQaItems()

  if (route.query.action === 'add') {
    openCreateModal()
  }
})

watch(keyword, () => {
  void loadQaItems()
})

async function loadQaItems() {
  isLoading.value = true
  errorMessage.value = ''

  const request: KnowledgeQaListRequest = {
    page: 1,
    page_size: 20,
  }

  const trimmedKeyword = keyword.value.trim()
  if (trimmedKeyword) {
    request.keyword = trimmedKeyword
  }

  const response = await getKnowledgeQaList(authStore.token, request)

  if (response.code === 401) {
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (response.code === 200 && response.data) {
    qaItems.value = response.data.items
    total.value = response.data.total
  } else {
    qaItems.value = []
    total.value = 0
    errorMessage.value = response.message
  }

  isLoading.value = false
}

function openCreateModal() {
  editingQa.value = null
  formQuestion.value = ''
  formAnswer.value = ''
  formStatus.value = 'enabled'
  modalErrorMessage.value = ''
  isModalOpen.value = true
}

function openEditModal(qa: KnowledgeQaDto) {
  editingQa.value = qa
  formQuestion.value = qa.question
  formAnswer.value = qa.answer
  formStatus.value = qa.status
  modalErrorMessage.value = ''
  isModalOpen.value = true
}

function closeModal() {
  if (isSaving.value) return

  isModalOpen.value = false
  modalErrorMessage.value = ''
}

async function handleSubmit() {
  const question = formQuestion.value.trim()
  const answer = formAnswer.value.trim()
  if (!question || !answer || isSaving.value) {
    modalErrorMessage.value = '问题和答案不能为空'
    return
  }

  isSaving.value = true
  modalErrorMessage.value = ''
  feedbackMessage.value = ''
  errorMessage.value = ''

  const payload: CreateKnowledgeQaRequest = {
    question,
    answer,
    status: formStatus.value,
  }

  const response = editingQa.value
    ? await updateKnowledgeQa(authStore.token, editingQa.value.id, payload)
    : await createKnowledgeQa(authStore.token, payload)

  if (response.code === 401) {
    isSaving.value = false
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (response.code === 200 && response.data) {
    feedbackMessage.value = editingQa.value ? 'QA 已更新' : 'QA 已新增'
    isModalOpen.value = false
    await loadQaItems()
  } else {
    modalErrorMessage.value = response.message
  }

  isSaving.value = false
}

async function handleDelete(qaId: string) {
  if (deletingQaId.value) return

  deletingQaId.value = qaId
  feedbackMessage.value = ''
  errorMessage.value = ''

  const response = await deleteKnowledgeQa(authStore.token, qaId)

  if (response.code === 401) {
    deletingQaId.value = null
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (response.code === 200 && response.data?.deleted) {
    feedbackMessage.value = 'QA 已删除'
    await loadQaItems()
  } else {
    errorMessage.value = response.message
  }

  deletingQaId.value = null
}

function formatDateTime(value: string) {
  const normalized = value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
  return normalized.slice(0, 16)
}

function statusLabel(status: KnowledgeQaStatus) {
  const labels: Record<KnowledgeQaStatus, string> = {
    enabled: '启用',
    disabled: '停用',
  }

  return labels[status]
}
</script>

<template>
  <section class="knowledge-page qa-page" aria-label="QA 库管理">
    <header class="qa-page-heading">
      <div>
        <h1>QA 库管理</h1>
        <p>维护标准问答，供客服回复和智能助手检索使用。</p>
      </div>
    </header>

    <div class="qa-action-bar">
      <label class="qa-search-wrap" aria-label="搜索问题或答案摘要">
        <span class="material-symbols-outlined">search</span>
        <input v-model="keyword" type="search" placeholder="搜索问题或答案摘要..." />
      </label>

      <div class="qa-toolbar-actions">
        <button class="knowledge-primary-button" type="button" @click="openCreateModal">
          <span class="material-symbols-outlined">add</span>
          <span>新增 QA</span>
        </button>
      </div>
    </div>

    <div v-if="feedbackMessage" class="ticket-feedback success" role="status">
      <span class="material-symbols-outlined">check_circle</span>
      <span>{{ feedbackMessage }}</span>
    </div>
    <div v-if="errorMessage" class="ticket-feedback error" role="alert">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorMessage }}</span>
    </div>

    <article class="knowledge-table-card">
      <div class="knowledge-table-scroll">
        <table class="knowledge-table qa-table">
          <thead>
            <tr>
              <th>问题</th>
              <th>答案摘要</th>
              <th>状态</th>
              <th>更新时间</th>
              <th class="align-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="5" class="ticket-empty-cell">加载中</td>
            </tr>
            <tr v-else-if="qaItems.length === 0">
              <td colspan="5" class="ticket-empty-cell">暂无 QA</td>
            </tr>
            <tr v-for="qa in qaItems" v-else :key="qa.id">
              <td class="knowledge-title-cell">{{ qa.question }}</td>
              <td class="qa-answer-cell">{{ qa.answer }}</td>
              <td>
                <span class="qa-status-pill" :class="`qa-status-${qa.status}`">
                  {{ statusLabel(qa.status) }}
                </span>
              </td>
              <td class="knowledge-time-cell">{{ formatDateTime(qa.updated_at) }}</td>
              <td class="knowledge-row-actions">
                <button class="text-link" type="button" @click="openEditModal(qa)">编辑</button>
                <button
                  class="text-link danger-link"
                  type="button"
                  :disabled="deletingQaId === qa.id"
                  @click="handleDelete(qa.id)"
                >
                  {{ deletingQaId === qa.id ? '删除中' : '删除' }}
                </button>
              </td>
            </tr>
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

    <div v-if="isModalOpen" class="qa-modal-overlay" role="presentation">
      <form class="qa-modal-card" @submit.prevent="handleSubmit">
        <header class="qa-modal-header">
          <h2>{{ modalTitle }}</h2>
          <button class="icon-button" type="button" aria-label="关闭" @click="closeModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>

        <div class="qa-modal-body">
          <label class="qa-form-field">
            <span><strong>*</strong> 问题</span>
            <input v-model="formQuestion" type="text" />
          </label>

          <label class="qa-form-field">
            <span><strong>*</strong> 答案摘要</span>
            <textarea v-model="formAnswer" rows="4" maxlength="500"></textarea>
            <small>{{ answerLength }} / 500</small>
          </label>

          <label class="qa-form-field">
            <span>状态</span>
            <select v-model="formStatus">
              <option value="enabled">启用</option>
              <option value="disabled">停用</option>
            </select>
          </label>

          <div v-if="modalErrorMessage" class="ticket-feedback error inline" role="alert">
            <span class="material-symbols-outlined">error</span>
            <span>{{ modalErrorMessage }}</span>
          </div>
        </div>

        <footer class="qa-modal-footer">
          <button class="knowledge-secondary-button" type="button" @click="closeModal">取消</button>
          <button class="knowledge-primary-button" type="submit" :disabled="isSaving">
            {{ isSaving ? '保存中' : submitText }}
          </button>
        </footer>
      </form>
    </div>
  </section>
</template>
