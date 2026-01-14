<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <div :class="['p-2 rounded-lg', fileTypeStyle.bg]">
            <component :is="fileTypeStyle.icon" :size="20" :class="fileTypeStyle.text" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900">{{ material.name }}</h2>
            <p class="text-sm text-gray-500">{{ fileTypeStyle.label }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <X :size="20" class="text-gray-500" />
        </button>
      </div>
      
      <!-- 内容区 -->
      <div class="flex-1 overflow-auto p-4">
        <!-- 加载中 -->
        <div v-if="loading" class="flex items-center justify-center h-64">
          <Loader2 :size="32" class="animate-spin text-blue-500" />
          <span class="ml-3 text-gray-500">加载中...</span>
        </div>
        
        <!-- 错误提示 -->
        <div v-else-if="error" class="flex flex-col items-center justify-center h-64 text-gray-500">
          <AlertCircle :size="48" class="mb-3 text-red-400" />
          <p>{{ error }}</p>
        </div>
        
        <!-- 文本内容预览 -->
        <div v-else-if="isTextFile" class="prose prose-sm max-w-none">
          <pre class="bg-gray-50 p-4 rounded-lg overflow-auto text-sm whitespace-pre-wrap">{{ content }}</pre>
        </div>
        
        <!-- 不支持预览 -->
        <div v-else class="flex flex-col items-center justify-center h-64 text-gray-500">
          <FileQuestion :size="48" class="mb-3 text-gray-400" />
          <p>此文件类型暂不支持预览</p>
          <p class="text-sm mt-2">支持预览: TXT, MD, HTML</p>
        </div>
      </div>
      
      <!-- 底部操作栏 -->
      <div class="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
        <div class="text-sm text-gray-500">
          <span v-if="content">{{ content.length }} 字符</span>
        </div>
        <div class="flex space-x-2">
          <!-- 需要后端：解析并添加到知识库 -->
          <button 
            @click="handleAddToKnowledge"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 text-sm"
            title="需要后端支持"
          >
            <Database :size="16" />
            <span>添加到知识库</span>
          </button>
          <!-- 需要后端：AI 分析材料 -->
          <button 
            @click="handleAnalyze"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 text-sm"
            title="需要后端支持"
          >
            <Sparkles :size="16" />
            <span>AI 分析</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { X, Loader2, AlertCircle, FileQuestion, FileText, FileCode, Database, Sparkles } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  material: {
    type: Object,
    required: true
  }
})

defineEmits(['close'])

const toast = useToast()

const loading = ref(true)
const error = ref(null)
const content = ref('')

const fileTypeConfig = {
  txt: { icon: FileText, label: '文本文件', bg: 'bg-gray-100', text: 'text-gray-600' },
  md: { icon: FileCode, label: 'Markdown', bg: 'bg-purple-100', text: 'text-purple-600' },
  html: { icon: FileCode, label: 'HTML 文档', bg: 'bg-orange-100', text: 'text-orange-600' },
  docx: { icon: FileText, label: 'Word 文档', bg: 'bg-blue-100', text: 'text-blue-600' },
  pdf: { icon: FileText, label: 'PDF 文档', bg: 'bg-red-100', text: 'text-red-600' }
}

const fileTypeStyle = computed(() => {
  return fileTypeConfig[props.material.type] || { icon: FileText, label: '未知类型', bg: 'bg-gray-100', text: 'text-gray-600' }
})

const isTextFile = computed(() => {
  return ['txt', 'md', 'html'].includes(props.material.type)
})

onMounted(async () => {
  if (!isTextFile.value) {
    loading.value = false
    return
  }
  
  try {
    if (window.electronAPI) {
      const result = await window.electronAPI.readFile(props.material.path)
      if (result.success) {
        content.value = result.data
      } else {
        error.value = result.error
      }
    } else {
      error.value = '仅在 Electron 环境下可预览本地文件'
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})

// 需要后端支持的功能
const handleAddToKnowledge = () => {
  toast.warning('添加到知识库功能需要后端支持')
}

const handleAnalyze = () => {
  toast.warning('AI 分析功能需要后端支持')
}
</script>
