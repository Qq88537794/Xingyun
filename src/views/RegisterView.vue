<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="max-w-md w-full mx-4">
      <!-- Logo和标题 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
          <FileText :size="32" class="text-white" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900">行云文档</h1>
        <p class="text-gray-600 mt-2">创建您的账户</p>
      </div>
      
      <!-- 注册表单 -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">注册账户</h2>
        
        <!-- 错误提示 -->
        <div v-if="authStore.error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle :size="18" class="text-red-500 mt-0.5 mr-2 flex-shrink-0" />
          <span class="text-sm text-red-700">{{ authStore.error }}</span>
        </div>
        
        <form @submit.prevent="handleRegister" class="space-y-4">
          <!-- 用户名 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
            <div class="relative">
              <User :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.username"
                type="text"
                required
                minlength="3"
                placeholder="输入用户名"
                class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>
          
          <!-- 邮箱 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
            <div class="relative">
              <Mail :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.email"
                type="email"
                required
                placeholder="your@email.com"
                class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>
          
          <!-- 密码 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
            <div class="relative">
              <Lock :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                required
                minlength="3"
                placeholder="至少3位字符"
                class="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <Eye v-if="!showPassword" :size="18" />
                <EyeOff v-else :size="18" />
              </button>
            </div>
          </div>
          
          <!-- 注册按钮 -->
          <button
            type="submit"
            :disabled="authStore.loading || !isFormValid"
            class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <Loader2 v-if="authStore.loading" :size="18" class="animate-spin mr-2" />
            {{ authStore.loading ? '注册中...' : '注册' }}
          </button>
        </form>
        
        <!-- 分割线 -->
        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-300"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white text-gray-500">或</span>
          </div>
        </div>
        
        <!-- 登录链接 -->
        <div class="text-center">
          <span class="text-gray-600">已有账户? </span>
          <button @click="$emit('switch-to-login')" class="text-blue-600 hover:text-blue-700 font-medium">
            立即登录
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FileText, User, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['switch-to-login', 'register-success'])

const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: ''
})

const showPassword = ref(false)

// 表单验证
const isFormValid = computed(() => {
  return formData.value.username.length >= 3 &&
         formData.value.email &&
         formData.value.password.length >= 3
})

const handleRegister = async () => {
  if (!isFormValid.value) return
  
  const result = await authStore.register({
    username: formData.value.username,
    email: formData.value.email,
    password: formData.value.password
  })
  
  if (result.success) {
    emit('register-success')
  }
}
</script>
