import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除本地存储
      const hadToken = !!localStorage.getItem('token')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 只有在之前有 token 的情况下才刷新页面（避免重复刷新）
      if (hadToken) {
        console.warn('Token 已过期或无效，请重新登录')
        // 延迟刷新，让错误信息有机会显示
        setTimeout(() => {
          window.location.reload()
        }, 100)
      }
    }
    return Promise.reject(error)
  }
)

export default api
