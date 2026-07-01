import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { isMockApiEnabled } from './utils/runtime'
import './assets/main.css'

document.documentElement.dataset.apiMode = isMockApiEnabled() ? 'mock' : 'real'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
