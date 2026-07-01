<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { label: '客服工作台', icon: 'dashboard', to: '/dashboard' },
  { label: '工单池', icon: 'list_alt', to: '/tickets' },
  { label: '我的工单', icon: 'assignment_ind', to: '/my-tickets' },
  { label: '知识库总览', icon: 'auto_stories', to: '/knowledge' },
  { label: 'QA 库管理', icon: 'quiz', to: '/knowledge/qa' },
  { label: '文档入库', icon: 'upload_file', to: '/documents' },
  { label: '智能问答调试', icon: 'smart_toy', to: '/assistant' },
]

const accountName = computed(() => authStore.user?.name ?? '')

onMounted(() => {
  void authStore.ensureCurrentUser()
})

async function handleLogout() {
  await authStore.logout()
  await router.push({ name: 'login' })
}

function isNavActive(path: string) {
  if (path === '/tickets') {
    return route.path === '/tickets' || route.name === 'ticketDetail'
  }

  return route.path === path
}
</script>

<template>
  <div class="app-shell">
    <aside class="side-nav" aria-label="主导航">
      <div class="brand">
        <span class="material-symbols-outlined brand-icon filled">support_agent</span>
        <span class="brand-copy">
          <strong>客服机器人</strong>
          <small>AI-Powered Support</small>
        </span>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          class="nav-link"
          :class="{ 'nav-link-active': isNavActive(item.to) }"
          :to="item.to"
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="workspace">
      <header class="top-bar">
        <span v-if="accountName" class="account-text">当前账号：{{ accountName }}</span>
        <div class="top-account">
          <RouterLink class="icon-button" to="/settings" title="账号与基础设置" aria-label="账号与基础设置">
            <span class="material-symbols-outlined">settings</span>
          </RouterLink>
          <button class="icon-button" type="button" title="通知" aria-label="通知">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <button class="top-logout" type="button" @click="handleLogout">退出</button>
        </div>
      </header>

      <main class="main-canvas">
        <RouterView />
      </main>
    </div>
  </div>
</template>
