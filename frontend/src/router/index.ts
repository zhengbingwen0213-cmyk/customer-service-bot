import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/components/AppLayout.vue'
import AssistantDebugPage from '@/pages/AssistantDebugPage.vue'
import DashboardPage from '@/pages/DashboardPage.vue'
import DocumentsPage from '@/pages/DocumentsPage.vue'
import KnowledgeOverviewPage from '@/pages/KnowledgeOverviewPage.vue'
import KnowledgeQaPage from '@/pages/KnowledgeQaPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import MyTicketsPage from '@/pages/MyTicketsPage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'
import TicketDetailPage from '@/pages/TicketDetailPage.vue'
import TicketPoolPage from '@/pages/TicketPoolPage.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
    },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardPage,
        },
        {
          path: 'tickets',
          name: 'tickets',
          component: TicketPoolPage,
        },
        {
          path: 'tickets/:ticketId',
          name: 'ticketDetail',
          component: TicketDetailPage,
        },
        {
          path: 'my-tickets',
          name: 'myTickets',
          component: MyTicketsPage,
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: KnowledgeOverviewPage,
        },
        {
          path: 'knowledge/qa',
          name: 'knowledgeQa',
          component: KnowledgeQaPage,
        },
        {
          path: 'documents',
          name: 'documents',
          component: DocumentsPage,
        },
        {
          path: 'assistant',
          name: 'assistant',
          component: AssistantDebugPage,
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsPage,
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
