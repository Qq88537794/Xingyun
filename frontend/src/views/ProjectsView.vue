<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- 顶部导航 -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <FileText :size="20" class="text-white" />
            </div>
            <h1 class="text-xl font-bold text-gray-900">行云文档</h1>
          </div>
          
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-600">{{ authStore.user?.username }}</span>
            <button 
              @click="handleLogout"
              class="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
            >
              <LogOut :size="16" />
              <span>退出</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 页面标题和操作 -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">我的项目</h2>
          <p class="text-gray-600 mt-1">管理您的文档项目</p>
        </div>
        <button 
          @click="showCreateModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Plus :size="18" />
          <span>新建项目</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <Loader2 :size="32" class="animate-spin text-blue-600" />
        <span class="ml-3 text-gray-600">加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="projects.length === 0" class="text-center py-20">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mb-4">
          <FolderOpen :size="40" class="text-gray-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">还没有项目</h3>
        <p class="text-gray-500 mb-6">创建您的第一个项目，开始智能文档编辑</p>
        <button 
          @click="showCreateModal = true"
          class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          创建第一个项目
        </button>
      </div>

      <!-- 项目网格 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="project in projects" 
          :key="project.id"
          class="bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow cursor-pointer group"
          @click="selectProject(project)"
        >
          <div class="p-6">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Folder :size="24" class="text-blue-600" />
              </div>
              <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  @click.stop="openEditModal(project)"
                  class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="编辑"
                >
                  <Edit2 :size="16" />
                </button>
                <button 
                  @click.stop="confirmDelete(project)"
                  class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="删除"
                >
                  <Trash2 :size="16" />
                </button>
              </div>
            </div>
            
            <h3 class="text-lg font-semibold text-gray-900 mb-2 truncate">{{ project.name }}</h3>
            <p class="text-sm text-gray-500 line-clamp-2 mb-4">
              {{ project.description || '暂无描述' }}
            </p>
            
            <div class="flex items-center justify-between text-xs text-gray-400">
              <span>{{ formatDate(project.created_at) }}</span>
              <span :class="project.status === 'active' ? 'text-green-500' : 'text-gray-400'">
                {{ project.status === 'active' ? '活跃' : '已归档' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑项目弹窗 -->
    <div v-if="showCreateModal || showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">
            {{ showEditModal ? '编辑项目' : '新建项目' }}
          </h3>
          <button 
            @click="closeModals"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <form @submit.prevent="showEditModal ? handleUpdate() : handleCreate()">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">项目名称</label>
              <input
                v-model="formData.name"
                type="text"
                required
                placeholder="输入项目名称"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">项目描述（可选）</label>
              <textarea
                v-model="formData.description"
                rows="3"
                placeholder="简单描述一下这个项目..."
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none"
              ></textarea>
            </div>
          </div>

          <div class="flex space-x-3 mt-6">
            <button
              type="button"
              @click="closeModals"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              {{ showEditModal ? '保存' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <AlertTriangle :size="32" class="text-red-600" />
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">确认删除</h3>
          <p class="text-gray-600 mb-6">
            确定要删除项目 "<span class="font-medium">{{ deleteTarget?.name }}</span>" 吗？此操作不可恢复。
          </p>
          
          <div class="flex space-x-3">
            <button
              @click="showDeleteModal = false"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              @click="handleDelete"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FileText, Plus, Folder, FolderOpen, Edit2, Trash2, X, Loader2, LogOut, AlertTriangle } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { getProjects, createProject, updateProject, deleteProject } from '../services/projects'
import { useToast } from '../composables/useToast'

const emit = defineEmits(['select-project'])

const authStore = useAuthStore()
const toast = useToast()

// 状态
const projects = ref([])
const loading = ref(true)
const submitting = ref(false)

// 弹窗状态
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const editTarget = ref(null)
const deleteTarget = ref(null)

// 表单数据
const formData = ref({
  name: '',
  description: ''
})

// 加载项目列表
const fetchProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjects()
  } catch (err) {
    console.error('获取项目列表失败:', err)
    toast.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 创建项目
const handleCreate = async () => {
  if (!formData.value.name.trim()) {
    toast.warning('请输入项目名称')
    return
  }
  
  submitting.value = true
  try {
    const result = await createProject(formData.value.name, formData.value.description)
    projects.value.unshift(result.project)
    toast.success('项目创建成功')
    closeModals()
  } catch (err) {
    console.error('创建项目失败:', err)
    toast.error(err.response?.data?.error || '创建项目失败')
  } finally {
    submitting.value = false
  }
}

// 更新项目
const handleUpdate = async () => {
  if (!formData.value.name.trim()) {
    toast.warning('请输入项目名称')
    return
  }
  
  submitting.value = true
  try {
    const result = await updateProject(editTarget.value.id, {
      name: formData.value.name,
      description: formData.value.description
    })
    
    const index = projects.value.findIndex(p => p.id === editTarget.value.id)
    if (index !== -1) {
      projects.value[index] = result.project
    }
    
    toast.success('项目更新成功')
    closeModals()
  } catch (err) {
    console.error('更新项目失败:', err)
    toast.error(err.response?.data?.error || '更新项目失败')
  } finally {
    submitting.value = false
  }
}

// 删除项目
const handleDelete = async () => {
  submitting.value = true
  try {
    await deleteProject(deleteTarget.value.id)
    projects.value = projects.value.filter(p => p.id !== deleteTarget.value.id)
    toast.success('项目删除成功')
    showDeleteModal.value = false
    deleteTarget.value = null
  } catch (err) {
    console.error('删除项目失败:', err)
    toast.error(err.response?.data?.error || '删除项目失败')
  } finally {
    submitting.value = false
  }
}

// 选择项目
const selectProject = (project) => {
  emit('select-project', project)
}

// 打开编辑弹窗
const openEditModal = (project) => {
  editTarget.value = project
  formData.value = {
    name: project.name,
    description: project.description || ''
  }
  showEditModal.value = true
}

// 确认删除
const confirmDelete = (project) => {
  deleteTarget.value = project
  showDeleteModal.value = true
}

// 关闭弹窗
const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editTarget.value = null
  formData.value = { name: '', description: '' }
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  window.location.reload()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
