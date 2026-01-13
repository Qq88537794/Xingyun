<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900">个人资料</h2>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <X :size="20" class="text-gray-500" />
        </button>
      </div>
      
      <!-- 内容 -->
      <div class="p-6">
        <div class="flex items-start space-x-6 mb-6">
          <!-- 头像 -->
          <div class="flex-shrink-0">
            <div class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-bold">
              {{ userInitials }}
            </div>
            <button class="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium">
              更换头像
            </button>
          </div>
          
          <!-- 基本信息 -->
          <div class="flex-1">
            <form @submit.prevent="handleSave" class="space-y-4">
              <!-- 姓名 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">姓名</label>
                <input
                  v-model="formData.fullName"
                  type="text"
                  required
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
              
              <!-- 用户名 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                <input
                  v-model="formData.username"
                  type="text"
                  required
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
              
              <!-- 邮箱 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                <input
                  v-model="formData.email"
                  type="email"
                  required
                  disabled
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                />
                <p class="text-xs text-gray-500 mt-1">邮箱不可修改</p>
              </div>
              
              <!-- 个人简介 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">个人简介</label>
                <textarea
                  v-model="formData.bio"
                  rows="3"
                  placeholder="介绍一下自己..."
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
                ></textarea>
              </div>
              
              <!-- 错误提示 -->
              <div v-if="authStore.error" class="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
                <AlertCircle :size="18" class="text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                <span class="text-sm text-red-700">{{ authStore.error }}</span>
              </div>
              
              <!-- 成功提示 -->
              <div v-if="saveSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg flex items-start">
                <CheckCircle :size="18" class="text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                <span class="text-sm text-green-700">保存成功！</span>
              </div>
              
              <!-- 按钮 -->
              <div class="flex space-x-3">
                <button
                  type="submit"
                  :disabled="authStore.loading"
                  class="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  <Loader2 v-if="authStore.loading" :size="18" class="animate-spin mr-2" />
                  {{ authStore.loading ? '保存中...' : '保存更改' }}
                </button>
                <button
                  type="button"
                  @click="$emit('close')"
                  class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </div>
        
        <!-- 修改密码 -->
        <div class="border-t border-gray-200 pt-6 mt-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">修改密码</h3>
          <button
            @click="showPasswordModal = true"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            修改密码
          </button>
        </div>
        
        <!-- 账户信息 -->
        <div class="border-t border-gray-200 pt-6 mt-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">账户信息</h3>
          <div class="space-y-2 text-sm text-gray-600">
            <p>注册时间: {{ formatDate(authStore.user?.createdAt) }}</p>
            <p>最后登录: {{ formatDate(authStore.user?.lastLogin) }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 修改密码弹窗 -->
    <ChangePasswordModal 
      v-if="showPasswordModal"
      @close="showPasswordModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { X, AlertCircle, CheckCircle, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import ChangePasswordModal from './ChangePasswordModal.vue'

defineEmits(['close'])

const authStore = useAuthStore()

const formData = ref({
  fullName: '',
  username: '',
  email: '',
  bio: ''
})

const saveSuccess = ref(false)
const showPasswordModal = ref(false)

const userInitials = computed(() => {
  const name = formData.value.fullName || 'U'
  return name.charAt(0).toUpperCase()
})

onMounted(() => {
  // 初始化表单数据
  if (authStore.user) {
    formData.value = {
      fullName: authStore.user.fullName || '',
      username: authStore.user.username || '',
      email: authStore.user.email || '',
      bio: authStore.user.bio || ''
    }
  }
})

const handleSave = async () => {
  saveSuccess.value = false
  
  const result = await authStore.updateProfile({
    fullName: formData.value.fullName,
    username: formData.value.username,
    bio: formData.value.bio
  })
  
  if (result.success) {
    saveSuccess.value = true
    setTimeout(() => {
      saveSuccess.value = false
    }, 3000)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}
</script>
