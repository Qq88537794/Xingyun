<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="max-w-md w-full mx-4">
      <!-- Logo和标题 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
          <FileText :size="32" class="text-white" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900">行云文档</h1>
        <p class="text-gray-600 mt-2">智能文档处理平台</p>
      </div>
      
      <!-- 登录表单 -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">登录账户</h2>
        
        <!-- 错误提示 -->
        <div v-if="authStore.error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle :size="18" class="text-red-500 mt-0.5 mr-2 flex-shrink-0" />
          <span class="text-sm text-red-700">{{ authStore.error }}</span>
        </div>
        
        <form @submit.prevent="handleLogin" class="space-y-4">
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
                placeholder="••••••••"
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
          
          <!-- 记住我 -->
          <div class="flex items-center justify-between">
            <label class="flex items-center">
              <input type="checkbox" v-model="rememberMe" class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
              <span class="ml-2 text-sm text-gray-600">记住我</span>
            </label>
            <a href="#" class="text-sm text-blue-600 hover:text-blue-700">忘记密码?</a>
          </div>
          
          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <Loader2 v-if="authStore.loading" :size="18" class="animate-spin mr-2" />
            {{ authStore.loading ? '登录中...' : '登录' }}
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
        
        <!-- 注册链接 -->
        <div class="text-center">
          <span class="text-gray-600">还没有账户? </span>
          <button @click="$emit('switch-to-register')" class="text-blue-600 hover:text-blue-700 font-medium">
            立即注册
          </button>
        </div>
      </div>
      
      <!-- 底部信息 -->
      <p class="text-center text-sm text-gray-500 mt-6">
        登录即表示您同意我们的 <a href="#" class="text-blue-600 hover:underline">服务条款</a> 和 <a href="#" class="text-blue-600 hover:underline">隐私政策</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FileText, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['switch-to-register', 'login-success'])

const authStore = useAuthStore()

const formData = ref({
  email: '',
  password: ''
})

const showPassword = ref(false)
const rememberMe = ref(false)

const handleLogin = async () => {
  const result = await authStore.login(formData.value)
  
  if (result.success) {
    emit('login-success')
  }
}
</script>
