<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { getKnowledgeOverview, getKnowledgeRecent } from '@/services/knowledge'
import { useAuthStore } from '@/stores/auth'
import type {
  KnowledgeOverviewResponseData,
  KnowledgeRecentItemDto,
  KnowledgeRecentType,
} from '@/types/knowledge'

const router = useRouter()
const authStore = useAuthStore()

const overview = ref<KnowledgeOverviewResponseData | null>(null)
const recentItems = ref<KnowledgeRecentItemDto[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const latestUpdatedText = computed(() => {
  if (!overview.value?.latest_updated_at) return '-'
  return formatDateTime(overview.value.latest_updated_at)
})

onMounted(async () => {
  await authStore.ensureCurrentUser()
  await loadKnowledgeOverview()
})

async function loadKnowledgeOverview() {
  isLoading.value = true
  errorMessage.value = ''

  const [overviewResponse, recentResponse] = await Promise.all([
    getKnowledgeOverview(authStore.token),
    getKnowledgeRecent(authStore.token, { limit: 5 }),
  ])

  if (overviewResponse.code === 401 || recentResponse.code === 401) {
    authStore.clearSession()
    await router.push({ name: 'login' })
    return
  }

  if (overviewResponse.code === 200 && overviewResponse.data) {
    overview.value = overviewResponse.data
  } else {
    errorMessage.value = overviewResponse.message
  }

  if (recentResponse.code === 200 && recentResponse.data) {
    recentItems.value = recentResponse.data.items
  } else if (!errorMessage.value) {
    errorMessage.value = recentResponse.message
  }

  isLoading.value = false
}

function formatDateTime(value: string) {
  const normalized = value.replace('T', ' ').replace(/(\+08:00|Z)$/, '')
  return normalized.slice(5, 16)
}

function typeLabel(type: KnowledgeRecentType) {
  return type === 'qa' ? 'QA' : 'Doc'
}

function itemTarget(item: KnowledgeRecentItemDto) {
  return item.type === 'qa' ? '/knowledge/qa' : '/documents'
}
</script>

<template>
  <section class="knowledge-page" aria-label="知识库总览">
    <header class="knowledge-overview-header">
      <div>
        <h1>知识库总览</h1>
        <p>管理和维护客服系统的核心知识数据源。</p>
      </div>
      <div class="knowledge-actions">
        <RouterLink class="knowledge-primary-button" :to="{ name: 'knowledgeQa', query: { action: 'add' } }">
          <span class="material-symbols-outlined">add</span>
          <span>新增 QA</span>
        </RouterLink>
        <RouterLink class="knowledge-secondary-button" to="/documents">
          <span class="material-symbols-outlined">upload_file</span>
          <span>上传文档</span>
        </RouterLink>
        <RouterLink class="knowledge-secondary-button" to="/assistant">
          <span class="material-symbols-outlined">smart_toy</span>
          <span>问答调试</span>
        </RouterLink>
      </div>
    </header>

    <div v-if="errorMessage" class="ticket-feedback error" role="alert">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorMessage }}</span>
    </div>

    <div class="knowledge-metric-grid" aria-label="知识库概览">
      <RouterLink class="knowledge-metric-card" to="/knowledge/qa">
        <span class="knowledge-metric-icon primary">
          <span class="material-symbols-outlined">quiz</span>
        </span>
        <span class="knowledge-metric-label">QA 数量</span>
        <strong>{{ overview?.qa_count ?? 0 }}</strong>
        <small>启用 {{ overview?.enabled_qa_count ?? 0 }}</small>
      </RouterLink>

      <RouterLink class="knowledge-metric-card" to="/documents">
        <span class="knowledge-metric-icon secondary">
          <span class="material-symbols-outlined">description</span>
        </span>
        <span class="knowledge-metric-label">文档数量</span>
        <strong>{{ overview?.document_count ?? 0 }}</strong>
        <small>已完成 {{ overview?.completed_document_count ?? 0 }}</small>
      </RouterLink>

      <article class="knowledge-metric-card">
        <span class="knowledge-metric-icon neutral">
          <span class="material-symbols-outlined">update</span>
        </span>
        <span class="knowledge-metric-label">最近更新</span>
        <strong class="knowledge-time-value">{{ latestUpdatedText }}</strong>
      </article>
    </div>

    <article class="knowledge-table-card">
      <header class="knowledge-table-header">
        <h2>最近更新知识</h2>
        <RouterLink class="text-link" to="/knowledge/qa">
          查看全部
          <span class="material-symbols-outlined">arrow_forward</span>
        </RouterLink>
      </header>

      <div class="knowledge-table-scroll">
        <table class="knowledge-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>类型</th>
              <th>更新时间</th>
              <th class="align-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="4" class="ticket-empty-cell">加载中</td>
            </tr>
            <tr v-else-if="recentItems.length === 0">
              <td colspan="4" class="ticket-empty-cell">暂无知识</td>
            </tr>
            <tr v-for="item in recentItems" v-else :key="`${item.type}_${item.id}`">
              <td class="knowledge-title-cell">{{ item.title }}</td>
              <td>
                <span class="knowledge-type-pill" :class="`knowledge-type-${item.type}`">
                  {{ typeLabel(item.type) }}
                </span>
              </td>
              <td class="knowledge-time-cell">{{ formatDateTime(item.updated_at) }}</td>
              <td class="knowledge-row-actions">
                <RouterLink class="text-link" :to="itemTarget(item)">查看</RouterLink>
                <RouterLink class="text-link" :to="itemTarget(item)">编辑</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>
