<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getAccountSettings } from '@/services/settings'
import { useAuthStore } from '@/stores/auth'
import type { SettingsAccountResponseData } from '@/types/settings'

const router = useRouter()
const authStore = useAuthStore()
const accountSettings = ref<SettingsAccountResponseData | null>(null)

const user = computed(() => accountSettings.value?.user ?? null)
const system = computed(() => accountSettings.value?.system ?? null)

onMounted(async () => {
  const response = await getAccountSettings(authStore.token)
  if (response.code === 200 && response.data) {
    accountSettings.value = response.data
    return
  }

  authStore.clearSession()
  await router.push({ name: 'login' })
})

async function handleLogout() {
  await authStore.logout()
  await router.push({ name: 'login' })
}
</script>

<template>
  <section class="settings-page">
    <div class="settings-container">
      <div class="page-heading">
        <div>
          <h1>账号与基础设置</h1>
          <p>查看当前账号、数据库和模型服务状态。</p>
        </div>
      </div>

      <article v-if="user && system" class="settings-card">
        <div class="profile-section">
          <div class="avatar">
            <span class="material-symbols-outlined">person</span>
          </div>
          <div>
            <h2>{{ user.name }}</h2>
            <p>当前登录账号</p>
          </div>
        </div>

        <div class="settings-grid account-grid">
          <span>当前账号：</span>
          <strong>{{ user.name }}</strong>

          <span>登录名：</span>
          <strong>{{ user.username }}</strong>
        </div>

        <div class="settings-grid system-grid">
          <span>数据库：</span>
          <strong>{{ system.database }}</strong>

          <span>模型服务：</span>
          <strong>{{ system.model_provider }}</strong>

          <span>聊天模型：</span>
          <strong>{{ system.chat_model }}</strong>

          <span>Embedding 模型：</span>
          <strong>{{ system.embedding_model }}</strong>

          <span>Embedding 维度：</span>
          <strong>{{ system.embedding_dimensions }}</strong>

          <span>API Key 配置：</span>
          <strong>{{ system.api_key_configured ? '已配置' : '未配置' }}</strong>
        </div>

        <div class="settings-actions">
          <button class="danger-button" type="button" @click="handleLogout">
            <span class="material-symbols-outlined">logout</span>
            退出登录
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
