<template>
  <div class="material-panel w-64 bg-white border-r border-gray-200 flex flex-col">
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-800 mb-3">参考材料</h2>
      <button @click="$emit('upload')" class="w-full btn-upload">
        <Upload :size="16" />
        <span>上传材料</span>
      </button>
    </div>
    
    <!-- 材料统计 -->
    <div v-if="materials.length > 0" class="px-4 py-2 bg-gray-50 border-b border-gray-200">
      <div class="flex items-center justify-between text-xs text-gray-500">
        <span>共 {{ materials.length }} 个文件</span>
        <button 
          @click="handleBatchProcess"
          class="text-blue-600 hover:text-blue-700"
          title="需要后端支持"
        >
          批量解析
        </button>
      </div>
    </div>
    
    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="materials.length === 0" class="text-center text-gray-400 mt-8">
        <FileText :size="48" class="mx-auto mb-2 opacity-50" />
        <p class="text-sm">暂无材料</p>
        <p class="text-xs mt-2">支持 DOCX、PDF、TXT、MD、HTML</p>
      </div>
      
      <div v-else class="space-y-2">
        <div 
          v-for="material in materials" 
          :key="material.id"
          class="material-item"
          @click="handlePreview(material)"
        >
          <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
              <div class="flex items-center space-x-2">
                <component 
                  :is="getFileIcon(getMaterialType(material))" 
                  :size="16" 
                  :class="getFileIconClass(getMaterialType(material))" 
                  class="flex-shrink-0" 
                />
                <p class="text-sm font-medium text-gray-800 truncate">
                  {{ getMaterialName(material) }}
                </p>
              </div>
              <div class="flex items-center space-x-2 mt-1">
                <span class="text-xs text-gray-500">
                  {{ formatFileType(getMaterialType(material)) }}
                </span>
                <!-- 处理状态 -->
                <span :class="getStatusClass(getMaterialStatus(material))" class="text-xs flex items-center">
                  <Loader2 v-if="getMaterialStatus(material) === 'processing'" :size="10" class="animate-spin mr-1" />
                  <CheckCircle v-else-if="getMaterialStatus(material) === 'ready' || getMaterialStatus(material) === 'indexed'" :size="10" class="mr-1" />
                  <Clock v-else-if="getMaterialStatus(material) === 'pending'" :size="10" class="mr-1" />
                  {{ getStatusText(getMaterialStatus(material)) }}
                </span>
              </div>
            </div>
            <div class="flex items-center space-x-1 ml-2">
              <button 
                @click.stop="handlePreview(material)"
                class="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                title="预览"
              >
                <Eye :size="14" />
              </button>
              <button 
                @click.stop="$emit('remove', material.id)"
                class="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="删除"
              >
                <X :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部操作 -->
    <div v-if="materials.length > 0" class="p-3 border-t border-gray-200 bg-gray-50">
      <button 
        @click="handleGenerateFromMaterials"
        class="w-full px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2 text-sm"
        title="需要后端支持"
      >
        <Sparkles :size="16" />
        <span>基于材料生成文档</span>
      </button>
    </div>
    
    <!-- 材料预览弹窗 -->
    <MaterialPreviewModal 
      v-if="previewMaterial"
      :material="previewMaterial"
      @close="previewMaterial = null"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, FileText, FileCode, File, X, Eye, Loader2, CheckCircle, Clock, Sparkles } from 'lucide-vue-next'
import MaterialPreviewModal from './MaterialPreviewModal.vue'
import { useToast } from '../composables/useToast'

defineProps({
  materials: {
    type: Array,
    default: () => []
  }
})

defineEmits(['upload', 'remove'])

const toast = useToast()
const previewMaterial = ref(null)

const fileIcons = {
  docx: FileText,
  pdf: FileText,
  txt: FileText,
  md: FileCode,
  html: FileCode
}

const fileIconClasses = {
  docx: 'text-blue-500',
  pdf: 'text-red-500',
  txt: 'text-gray-500',
  md: 'text-purple-500',
  html: 'text-orange-500'
}

const getFileIcon = (type) => fileIcons[type] || File
const getFileIconClass = (type) => fileIconClasses[type] || 'text-gray-500'

const formatFileType = (type) => {
  const types = {
    'docx': 'Word',
    'pdf': 'PDF',
    'txt': '文本',
    'md': 'Markdown',
    'html': 'HTML'
  }
  return types[type] || type.toUpperCase()
}

const getStatusClass = (status) => {
  const classes = {
    pending: 'text-gray-400',
    processing: 'text-blue-500',
    ready: 'text-green-500',
    error: 'text-red-500'
  }
  return classes[status] || 'text-gray-400'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '解析中',
    parsing: '解析中',
    ready: '已就绪',
    indexed: '已索引',
    error: '解析失败'
  }
  return texts[status] || ''
}

// 字段兼容辅助函数（支持后端返回格式和本地格式）
const getMaterialName = (material) => {
  return material.name || material.filename || 'Unknown'
}

const getMaterialType = (material) => {
  if (material.type) return material.type
  // 从 filename 或 mime_type 提取类型
  const filename = material.filename || ''
  const ext = filename.split('.').pop()?.toLowerCase()
  return ext || 'file'
}

const getMaterialStatus = (material) => {
  return material.status || material.parsing_status || 'pending'
}

const handlePreview = (material) => {
  previewMaterial.value = material
}

// 需要后端支持的功能
const handleBatchProcess = () => {
  toast.warning('批量解析功能需要后端支持')
}

const handleGenerateFromMaterials = () => {
  toast.warning('基于材料生成文档功能需要后端支持')
}
</script>

<style scoped>
.btn-upload {
  @apply px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors flex items-center justify-center space-x-2 text-sm font-medium;
}

.material-item {
  @apply p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer;
}
</style>
