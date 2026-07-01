<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { deleteDocument, getDocument, getDocuments, uploadDocument } from '@/services/documents'
import { useAuthStore } from '@/stores/auth'
import type {
  DocumentListItemDto,
  DocumentListRequest,
  DocumentStatus,
  UploadedDocumentDto,
} from '@/types/documents'

const router = useRouter()
const authStore = useAuthStore()

const documents = ref<DocumentListItemDto[]>([])
const total = ref(0)
const keyword = ref('')
const statusFilter = ref<DocumentStatus | ''>('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isLoading = ref(true)
const isUploading = ref(false)
const deletingDocumentId = ref<string | null>(null)
const refreshingDocumentId = ref<string | null>(null)
const feedbackMessage = ref('')
const errorMessage = ref('')

const selectedFileLabel = computed(() => selectedFile.value?.name ?? '尚未选择文档')

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadDocuments()
})

watch([keyword, statusFilter], () => {
  void loadDocuments()
})

async function loadDocuments() {
  isLoading.value = true
  errorMessage.value = ''

  const request: DocumentListRequest = {
    page: 1,
    page_size: 20,
  }

  const trimmedKeyword = keyword.value.trim()
  if (trimmedKeyword) {
    request.keyword = trimmedKeyword
  }

  if (statusFilter.value) {
    request.status = statusFilter.value
  }

  const response = await getDocuments(authStore.token, request)

  if (response.code === 401) {
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data) {
    documents.value = response.data.items
    total.value = response.data.total
  } else {
    documents.value = []
    total.value = 0
    errorMessage.value = response.message
  }

  isLoading.value = false
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  feedbackMessage.value = ''
  errorMessage.value = ''
}

async function handleUpload() {
  if (isUploading.value) return

  const file = selectedFile.value
  if (!file) {
    errorMessage.value = '请先选择文档'
    feedbackMessage.value = ''
    return
  }

  isUploading.value = true
  errorMessage.value = ''
  feedbackMessage.value = ''

  const response = await uploadDocument(authStore.token, {
    file,
    name: file.name,
  })

  if (response.code === 401) {
    isUploading.value = false
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data) {
    documents.value = [toDocumentListItem(response.data.document), ...documents.value]
    total.value += 1
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    feedbackMessage.value = '文档已加入入库任务队列'
  } else {
    errorMessage.value = response.message
  }

  isUploading.value = false
}

async function handleRefreshDocument(documentId: string) {
  if (refreshingDocumentId.value) return

  refreshingDocumentId.value = documentId
  feedbackMessage.value = ''
  errorMessage.value = ''

  const response = await getDocument(authStore.token, documentId)

  if (response.code === 401) {
    refreshingDocumentId.value = null
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data) {
    const refreshedDocument = response.data.document
    documents.value = documents.value.map((document) =>
      document.id === documentId ? toDocumentListItem(refreshedDocument) : document,
    )
    feedbackMessage.value = '文档状态已刷新'
  } else {
    errorMessage.value = response.message
  }

  refreshingDocumentId.value = null
}

async function handleDeleteDocument(documentId: string) {
  if (deletingDocumentId.value) return

  deletingDocumentId.value = documentId
  feedbackMessage.value = ''
  errorMessage.value = ''

  const response = await deleteDocument(authStore.token, documentId)

  if (response.code === 401) {
    deletingDocumentId.value = null
    await redirectToLogin()
    return
  }

  if (response.code === 200 && response.data?.deleted) {
    documents.value = documents.value.filter((document) => document.id !== response.data?.document_id)
    total.value = Math.max(0, total.value - 1)
    feedbackMessage.value = '文档已删除'
  } else {
    errorMessage.value = response.message
  }

  deletingDocumentId.value = null
}

async function redirectToLogin() {
  authStore.clearSession()
  await router.push({ name: 'login' })
}

function toDocumentListItem(document: UploadedDocumentDto): DocumentListItemDto {
  return {
    id: document.id,
    name: document.name,
    status: document.status,
    chunk_count: document.chunk_count,
    uploaded_by: document.uploaded_by,
    created_at: document.created_at,
    updated_at: document.updated_at,
  }
}

function statusLabel(status: DocumentStatus) {
  const labels: Record<DocumentStatus, string> = {
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }

  return labels[status]
}

function documentIcon(name: string) {
  const lowerName = name.toLowerCase()
  if (lowerName.endsWith('.pdf')) return 'picture_as_pdf'
  if (lowerName.endsWith('.md') || lowerName.endsWith('.markdown')) return 'markdown'
  return 'article'
}

function formatDateTime(value: string) {
  const normalized = value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
  return normalized.slice(0, 16)
}
</script>

<template>
  <section class="documents-page" aria-label="文档入库">
    <header class="document-page-heading">
      <div>
        <h1>文档入库</h1>
        <p>上传客服知识文档并查看入库处理状态。</p>
      </div>
    </header>

    <form class="document-upload-panel" @submit.prevent="handleUpload">
      <div class="document-upload-icon">
        <span class="material-symbols-outlined">cloud_upload</span>
      </div>
      <div class="document-upload-copy">
        <h2>将文档拖拽至此处，或</h2>
        <p>支持 .pdf, .txt, .md, .markdown 格式，单文件不超过 50MB</p>
      </div>
      <input
        ref="fileInput"
        class="visually-hidden-input"
        accept=".pdf,.txt,.md,.markdown"
        type="file"
        @change="handleFileChange"
      />
      <div class="document-upload-actions">
        <button class="knowledge-primary-button" type="button" @click="openFilePicker">
          <span class="material-symbols-outlined">folder_open</span>
          <span>选择文档</span>
        </button>
        <button class="knowledge-secondary-button" type="submit" :disabled="!selectedFile || isUploading">
          <span class="material-symbols-outlined">upload_file</span>
          <span>{{ isUploading ? '上传中' : '上传' }}</span>
        </button>
      </div>
      <p class="document-selected-file">{{ selectedFileLabel }}</p>
    </form>

    <div v-if="feedbackMessage" class="ticket-feedback success" role="status">
      <span class="material-symbols-outlined">check_circle</span>
      <span>{{ feedbackMessage }}</span>
    </div>
    <div v-if="errorMessage" class="ticket-feedback error" role="alert">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorMessage }}</span>
    </div>

    <article class="knowledge-table-card document-table-card">
      <header class="knowledge-table-header document-table-header">
        <div class="document-table-title">
          <span class="material-symbols-outlined">list</span>
          <h2>入库任务队列</h2>
        </div>
        <div class="document-toolbar-actions">
          <label class="qa-search-wrap document-search-wrap" aria-label="搜索文档名称">
            <span class="material-symbols-outlined">search</span>
            <input v-model="keyword" type="search" placeholder="搜索文档名称..." />
          </label>
          <label class="document-status-filter">
            <span class="material-symbols-outlined">filter_list</span>
            <select v-model="statusFilter" aria-label="筛选">
              <option value="">筛选</option>
              <option value="processing">处理中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
          </label>
        </div>
      </header>

      <div class="knowledge-table-scroll">
        <table class="knowledge-table document-table">
          <thead>
            <tr>
              <th>文档名称</th>
              <th>入库状态</th>
              <th>切片数量</th>
              <th>上传人</th>
              <th>更新时间</th>
              <th class="align-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="6" class="ticket-empty-cell">加载中</td>
            </tr>
            <tr v-else-if="documents.length === 0">
              <td colspan="6" class="ticket-empty-cell">暂无文档</td>
            </tr>
            <tr v-for="document in documents" v-else :key="document.id">
              <td class="document-name-cell">
                <span
                  class="material-symbols-outlined"
                  :class="document.status === 'failed' ? 'document-icon-error' : 'document-icon-primary'"
                >
                  {{ documentIcon(document.name) }}
                </span>
                <span>{{ document.name }}</span>
              </td>
              <td>
                <span class="document-status-pill" :class="`document-status-${document.status}`">
                  <span class="material-symbols-outlined">
                    {{ document.status === 'processing' ? 'sync' : document.status === 'completed' ? 'check_circle' : 'error' }}
                  </span>
                  {{ statusLabel(document.status) }}
                </span>
              </td>
              <td>{{ document.chunk_count }}</td>
              <td class="knowledge-time-cell">{{ document.uploaded_by }}</td>
              <td class="knowledge-time-cell">{{ formatDateTime(document.updated_at) }}</td>
              <td class="knowledge-row-actions">
                <button
                  class="text-link"
                  type="button"
                  :disabled="refreshingDocumentId === document.id"
                  @click="handleRefreshDocument(document.id)"
                >
                  {{ refreshingDocumentId === document.id ? '刷新中' : '刷新' }}
                </button>
                <button
                  class="text-link danger-link"
                  type="button"
                  :disabled="deletingDocumentId === document.id"
                  @click="handleDeleteDocument(document.id)"
                >
                  {{ deletingDocumentId === document.id ? '删除中' : '删除' }}
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
  </section>
</template>
