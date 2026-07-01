<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''

  try {
    await authStore.login(username.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.push(redirect)
  } catch {
    errorMessage.value = '账号或密码错误'
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-visual" aria-label="客服机器人">
      <div class="login-visual-content">
        <div class="login-logo">
          <span class="material-symbols-outlined filled">smart_toy</span>
        </div>
        <h1>客服机器人</h1>
        <p>知识库驱动的人机协作客服台</p>
        <div class="login-tags">
          <span>
            <span class="material-symbols-outlined">receipt_long</span>
            工单处理
          </span>
          <span>
            <span class="material-symbols-outlined">auto_awesome</span>
            AI 辅助回答
          </span>
          <span>
            <span class="material-symbols-outlined">library_books</span>
            知识库检索
          </span>
        </div>
      </div>
      <p class="system-footnote">SYSTEM CORE v2.4.0 // INITIALIZING WORKSPACE...</p>
    </section>

    <section class="login-panel" aria-label="系统登录">
      <div class="login-card">
        <div class="mobile-logo">
          <span class="material-symbols-outlined filled">smart_toy</span>
        </div>
        <div class="login-title">
          <h2>系统登录</h2>
          <p>请输入您的操作凭据以继续</p>
        </div>

        <form class="login-form" @submit.prevent="handleSubmit">
          <label class="field-group" for="username">
            <span>登录名</span>
            <span class="field-control">
              <span class="material-symbols-outlined">person</span>
              <input
                id="username"
                v-model.trim="username"
                autocomplete="username"
                name="username"
                placeholder="请输入..."
                required
                type="text"
              />
            </span>
          </label>

          <label class="field-group" for="password">
            <span>密码</span>
            <span class="field-control">
              <span class="material-symbols-outlined">lock</span>
              <input
                id="password"
                v-model="password"
                autocomplete="current-password"
                name="password"
                placeholder="请输入..."
                required
                type="password"
              />
            </span>
          </label>

          <div class="error-message" :class="{ visible: errorMessage }" role="alert" aria-live="polite">
            <span class="material-symbols-outlined">error</span>
            <p>{{ errorMessage || '账号或密码错误' }}</p>
          </div>

          <button class="primary-button" type="submit" :disabled="authStore.isLoading">
            <span>登录</span>
            <span class="material-symbols-outlined">arrow_forward</span>
          </button>
        </form>
      </div>
    </section>
  </div>
</template>
