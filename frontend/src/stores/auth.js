import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // 用户信息
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // 加载状态
  const loading = ref(false)
  const error = ref(null)

  // API基础URL
  const API_BASE_URL = 'http://localhost:5000/api'

  // 开发模式：模拟后端（设置为true可以不依赖后端测试前端）
  const DEV_MODE = false

  // 设置axios默认配置
  const setupAxios = () => {
    if (token.value) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  // 注册
  const register = async (userData) => {
    loading.value = true
    error.value = null

    try {
      if (DEV_MODE) {
        console.log('开发模式：注册用户', userData)

        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))

        // 模拟注册成功
        const mockToken = 'mock_token_' + Date.now()
        const mockUser = {
          id: Date.now(),
          username: userData.username,
          email: userData.email,
          description: '',
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString()
        }

        token.value = mockToken
        user.value = mockUser

        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))

        console.log('注册成功', mockUser)
        loading.value = false
        return { success: true }
      }

      const response = await axios.post(`${API_BASE_URL}/auth/register`, {
        username: userData.username,
        email: userData.email,
        password: userData.password
      })

      // 注册成功后自动登录
      token.value = response.data.access_token
      user.value = response.data.user

      // 保存到localStorage
      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))

      setupAxios()

      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.error || '注册失败，请重试'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // 登录
  const login = async (credentials) => {
    loading.value = true
    error.value = null

    try {
      if (DEV_MODE) {
        console.log('开发模式：登录用户', credentials.email)

        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))

        // 模拟登录成功
        const mockToken = 'mock_token_' + Date.now()
        const mockUser = {
          id: Date.now(),
          username: credentials.email.split('@')[0],
          email: credentials.email,
          description: '',
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString()
        }

        token.value = mockToken
        user.value = mockUser

        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))

        console.log('登录成功', mockUser)
        loading.value = false
        return { success: true }
      }

      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        username: credentials.email,  // 后端支持用邮箱或用户名登录
        password: credentials.password
      })

      token.value = response.data.access_token
      user.value = response.data.user

      // 保存到localStorage
      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))

      setupAxios()

      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.error || '登录失败，请检查邮箱和密码'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = () => {
    user.value = null
    token.value = null

    localStorage.removeItem('token')
    localStorage.removeItem('user')

    delete axios.defaults.headers.common['Authorization']
  }

  // 从localStorage恢复用户信息
  const restoreUser = () => {
    const savedUser = localStorage.getItem('user')
    const savedToken = localStorage.getItem('token')

    if (savedUser && savedToken) {
      try {
        user.value = JSON.parse(savedUser)
        token.value = savedToken
        setupAxios()
      } catch (err) {
        console.error('恢复用户信息失败:', err)
        logout()
      }
    }
  }

  // 手动设置用户信息和token（用于外部登录/注册）
  const setUser = (userData, authToken) => {
    user.value = userData
    token.value = authToken

    localStorage.setItem('token', authToken)
    localStorage.setItem('user', JSON.stringify(userData))

    setupAxios()
  }

  // 更新用户信息
  const updateProfile = async (profileData) => {
    loading.value = true
    error.value = null

    try {
      if (DEV_MODE) {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 800))

        // 更新本地用户信息
        user.value = {
          ...user.value,
          ...profileData
        }
        localStorage.setItem('user', JSON.stringify(user.value))

        return { success: true }
      }

      const response = await axios.put(`${API_BASE_URL}/user/profile`, profileData)

      user.value = response.data.user
      localStorage.setItem('user', JSON.stringify(user.value))

      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.error || '更新失败'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // 修改密码
  const changePassword = async (passwordData) => {
    loading.value = true
    error.value = null

    try {
      if (DEV_MODE) {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 800))

        // 模拟密码修改成功
        return { success: true }
      }

      await axios.post(`${API_BASE_URL}/user/change-password`, {
        oldPassword: passwordData.oldPassword,
        newPassword: passwordData.newPassword
      })

      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.error || '修改密码失败'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    loading,
    error,
    register,
    login,
    logout,
    restoreUser,
    setUser,
    updateProfile,
    changePassword
  }
})
