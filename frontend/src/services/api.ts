import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('customer_service_bot_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = String(error.config?.url ?? '')
    const isLoginRequest = requestUrl.includes('/auth/login')

    if (error.response?.status === 401 && !isLoginRequest) {
      window.localStorage.removeItem('customer_service_bot_token')
      window.localStorage.removeItem('customer_service_bot_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api
