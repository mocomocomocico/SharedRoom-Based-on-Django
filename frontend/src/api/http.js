// 统一 HTTP 客户端：集中处理 API 前缀、JWT token 注入和 401 自动刷新。
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求发出前统一带上 access token，避免每个接口重复写请求头。
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// access token 过期时尝试用 refresh token 换新 token；失败则回到登录页。
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refreshToken = localStorage.getItem('refresh_token')

    if (error.response?.status === 401 && refreshToken && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const res = await axios.post('/api/token/refresh/', { refresh: refreshToken })
        localStorage.setItem('access_token', res.data.access)
        originalRequest.headers.Authorization = `Bearer ${res.data.access}`
        return http(originalRequest)
      } catch (refreshError) {
        localStorage.clear()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default http
