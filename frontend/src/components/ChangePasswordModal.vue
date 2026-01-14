<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-900">修改密码</h2>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <X :size="20" class="text-gray-500" />
        </button>
      </div>
      
      <!-- 内容 -->
      <div class="p-6">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- 旧密码 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">当前密码</label>
            <div class="relative">
              <Lock :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.oldPassword"
                :type="showOldPassword ? 'text' : 'password'"
                required
                placeholder="输入当前密码"
                class="w-full pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
              <button
                type="button"
                @click="showOldPassword = !showOldPassword"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <Eye v-if="!showOldPassword" :size="18" />
                <EyeOff v-else :size="18" />
              </button>
            </div>
          </div>
          
          <!-- 新密码 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">新密码</label>
            <div class="relative">
              <Lock :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                required
                minlength="6"
                placeholder="至少6位字符"
                class="w-full pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
              <button
                type="button"
                @click="showNewPassword = !showNewPassword"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <Eye v-if="!showNewPassword" :size="18" />
                <EyeOff v-else :size="18" />
              </button>
            </div>
          </div>
          
          <!-- 确认新密码 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">确认新密码</label>
            <div class="relative">
              <Lock :size="18" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="formData.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                required
                placeholder="再次输入新密码"
                class="w-full pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                :class="{ 'border-red-500': formData.confirmPassword && formData.newPassword !== formData.confirmPassword }"
              />
              <button
                type="button"
                @click="showConfirmPassword = !showConfirmPassword"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <Eye v-if="!showConfirmPassword" :size="18" />
                <EyeOff v-else :size="18" />
              </button>
            </div>
            <p v-if="formData.confirmPassword && formData.newPassword !== formData.confirmPassword" class="text-xs text-red-500 mt-1">
              密码不匹配
            </p>
          </div>
          
          <!-- 错误提示 -->
          <div v-if="authStore.error" class="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle :size="18" class="text-red-500 mt-0.5 mr-2 flex-shrink-0" />
            <span class="text-sm text-red-700">{{ authStore.error }}</span>
          </div>
          
          <!-- 成功提示 -->
          <div v-if="changeSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg flex items-start">
            <CheckCircle :size="18" class="text-green-500 mt-0.5 mr-2 flex-shrink-0" />
            <span class="text-sm text-green-700">密码修改成功！</span>
          </div>
          
          <!-- 按钮 -->
          <div class="flex space-x-3 pt-2">
            <button
              type="submit"
              :disabled="authStore.loading || !isFormValid"
              class="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Loader2 v-if="authStore.loading" :size="18" class="animate-spin mr-2" />
              {{ authStore.loading ? '修改中...' : '确认修改' }}
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { X, Lock, Eye, EyeOff, AlertCircle, CheckCircle, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

defineEmits(['close'])

const authStore = useAuthStore()

const formData = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const changeSuccess = ref(false)

const isFormValid = computed(() => {
  return formData.value.oldPassword &&
         formData.value.newPassword.length >= 6 &&
         formData.value.newPassword === formData.value.confirmPassword
})

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  changeSuccess.value = false
  
  const result = await authStore.changePassword({
    oldPassword: formData.value.oldPassword,
    newPassword: formData.value.newPassword
  })
  
  if (result.success) {
    changeSuccess.value = true
    formData.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    
    setTimeout(() => {
      changeSuccess.value = false
    }, 3000)
  }
}
</script>
