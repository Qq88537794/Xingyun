<template>
  <div class="relative" ref="menuContainer">
    <!-- 用户头像按钮 -->
    <button 
      @click.stop="toggleMenu"
      class="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
    >
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-medium">
        {{ userInitials }}
      </div>
      <div class="text-left hidden md:block">
        <p class="text-sm font-medium text-gray-900">{{ authStore.user?.fullName }}</p>
        <p class="text-xs text-gray-500">{{ authStore.user?.email }}</p>
      </div>
      <ChevronDown :size="16" class="text-gray-500" />
    </button>
    
    <!-- 下拉菜单 -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div 
        v-if="showMenu"
        @click.stop
        class="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50"
      >
        <!-- 用户信息 -->
        <div class="px-4 py-3 border-b border-gray-200">
          <p class="text-sm font-medium text-gray-900">{{ authStore.user?.fullName }}</p>
          <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
        </div>
        
        <!-- 菜单项 -->
        <button
          @click="handleMenuClick('profile')"
          class="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <User :size="16" class="mr-3 text-gray-500" />
          个人资料
        </button>
        
        <button
          @click="handleMenuClick('settings')"
          class="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <Settings :size="16" class="mr-3 text-gray-500" />
          设置
        </button>
        
        <button
          @click="handleMenuClick('documents')"
          class="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <FileText :size="16" class="mr-3 text-gray-500" />
          我的文档
        </button>
        
        <div class="border-t border-gray-200 my-1"></div>
        
        <button
          @click="handleLogout"
          class="w-full flex items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut :size="16" class="mr-3" />
          退出登录
        </button>
      </div>
    </Transition>
    
    <!-- 个人中心弹窗 -->
    <ProfileModal 
      v-if="showProfileModal"
      @close="showProfileModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { User, Settings, FileText, LogOut, ChevronDown } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import ProfileModal from './ProfileModal.vue'

const authStore = useAuthStore()

const showMenu = ref(false)
const showProfileModal = ref(false)
const menuContainer = ref(null)

// 用户名首字母
const userInitials = computed(() => {
  const name = authStore.user?.fullName || authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})

// 切换菜单
const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (menuContainer.value && !menuContainer.value.contains(event.target)) {
    showMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const handleMenuClick = (action) => {
  showMenu.value = false
  
  switch (action) {
    case 'profile':
      showProfileModal.value = true
      break
    case 'settings':
      // TODO: 打开设置页面
      console.log('打开设置')
      break
    case 'documents':
      // TODO: 打开文档列表
      console.log('打开文档列表')
      break
  }
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    authStore.logout()
    showMenu.value = false
    window.location.reload()
  }
}
</script>
