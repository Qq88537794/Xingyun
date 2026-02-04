<template>
  <div class="top-bar bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <!-- 返回项目列表 -->
      <button 
        @click="$emit('back-to-projects')"
        class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        title="返回项目列表"
      >
        <ArrowLeft :size="18" />
      </button>
      
      <div class="flex items-center space-x-2">
        <h1 class="text-xl font-bold text-gray-800">行云文档</h1>
        <span v-if="projectName" class="text-sm text-gray-500">/ {{ projectName }}</span>
      </div>
      <div class="flex space-x-2">
        <button @click="$emit('new-document')" class="btn-primary">
          <FilePlus :size="16" />
          <span>新建</span>
        </button>
        <button @click="handleOpen" class="btn-secondary">
          <FolderOpen :size="16" />
          <span>打开</span>
        </button>
        <button @click="$emit('save-document')" class="btn-secondary">
          <Save :size="16" />
          <span>保存</span>
        </button>
        
        <!-- 导出下拉菜单 -->
        <div class="relative" ref="exportMenuRef">
          <button @click="showExportMenu = !showExportMenu" class="btn-secondary">
            <Download :size="16" />
            <span>导出</span>
            <ChevronDown :size="14" />
          </button>
          
          <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div 
              v-if="showExportMenu"
              class="absolute left-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50"
            >
              <button @click="handleExport('md')" class="export-menu-item">
                <FileCode :size="16" class="text-purple-500" />
                <span>Markdown (.md)</span>
              </button>
              <button @click="handleExport('docx')" class="export-menu-item">
                <FileText :size="16" class="text-blue-500" />
                <span>Word (.docx)</span>
                <span class="ml-auto text-xs text-gray-400">需后端</span>
              </button>
              <button @click="handleExport('pdf')" class="export-menu-item">
                <FileText :size="16" class="text-red-500" />
                <span>PDF (.pdf)</span>
              </button>
              <button @click="handleExport('tex')" class="export-menu-item">
                <FileCode :size="16" class="text-green-500" />
                <span>LaTeX (.tex)</span>
                <span class="ml-auto text-xs text-gray-400">需后端</span>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>
    
    <div class="flex items-center space-x-3">
      <!-- 版本快照 -->
      <button @click="$emit('show-snapshots')" class="btn-icon" title="版本快照">
        <History :size="18" />
      </button>
      
      <!-- 设置 -->
      <button @click="$emit('show-settings')" class="btn-icon" title="设置">
        <Settings :size="18" />
      </button>
      
      <!-- 视图切换 -->
      <div class="flex items-center border border-gray-200 rounded-lg">
        <button 
          @click="$emit('toggle-material-panel')"
          :class="['btn-toggle', showMaterialPanel ? 'active' : '']"
          title="材料面板"
        >
          <PanelLeft :size="16" />
        </button>
        <button 
          @click="$emit('toggle-chat-panel')"
          :class="['btn-toggle', showChatPanel ? 'active' : '']"
          title="侧边栏"
        >
          <PanelRight :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { FilePlus, FolderOpen, Save, Download, ChevronDown, FileText, FileCode, History, Settings, PanelLeft, PanelRight, ArrowLeft, MessageSquare } from 'lucide-vue-next'
import { ExportService } from '../services/export'
import { useToast } from '../composables/useToast'

const props = defineProps({
  showMaterialPanel: {
    type: Boolean,
    default: true
  },
  showChatPanel: {
    type: Boolean,
    default: true
  },
  editorJson: {
    type: Object,
    default: null
  },
  editorHtml: {
    type: String,
    default: ''
  },
  styles: {
    type: Array,
    default: () => []
  },
  projectName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'new-document', 
  'save-document', 
  'open-document',
  'toggle-material-panel',
  'toggle-chat-panel',
  'show-snapshots',
  'show-settings',
  'back-to-projects'
])

const toast = useToast()
const showExportMenu = ref(false)
const exportMenuRef = ref(null)

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (exportMenuRef.value && !exportMenuRef.value.contains(event.target)) {
    showExportMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const handleOpen = async () => {
  if (!window.electronAPI) {
    toast.warning('此功能仅在 Electron 环境下可用')
    return
  }
  
  const filePaths = await window.electronAPI.openFile()
  if (filePaths && filePaths.length > 0) {
    const result = await window.electronAPI.readFile(filePaths[0])
    if (result.success) {
      emit('open-document', result.data)
      toast.success('文档已打开')
    } else {
      toast.error('打开失败: ' + result.error)
    }
  }
}

const handleExport = async (format) => {
  showExportMenu.value = false
  
  if (!props.editorJson) {
    toast.warning('没有可导出的内容')
    return
  }
  
  switch (format) {
    case 'md':
      // 纯前端实现
      try {
        ExportService.downloadMarkdown(props.editorJson, 'document.md')
        toast.success('Markdown 导出成功')
      } catch (err) {
        toast.error('导出失败: ' + err.message)
      }
      break
      
    case 'docx':
      try {
        const fileName = props.projectName ? `${props.projectName}.docx` : 'document.docx'
        // console.log('Exporting docx with styles:', props.styles)
        if (!props.styles || props.styles.length === 0) {
            toast.info('提示: 未检测到自定义样式，将使用默认样式')
        }
        await ExportService.toWord(props.editorJson, fileName, props.styles)
        toast.success('Word 导出成功')
      } catch (err) {
        toast.error('导出失败: ' + err.message)
      }
      break
    case 'pdf':
      try {
        const fileName = props.projectName ? props.projectName : 'document'
        // Use styles prop passed from App.vue
        await ExportService.exportToPdf(props.editorHtml, fileName, props.styles)
      } catch (err) {
        toast.error('PDF导出失败: ' + err.message)
      }
      break
    case 'tex':
      try {
        const fileName = props.projectName ? props.projectName : 'document'
        await ExportService.toLaTeX(props.editorJson, fileName, props.styles)
        toast.success('LaTeX 导出成功')
      } catch (err) {
        toast.error('导出失败: ' + err.message)
      }
      break
  }
}
</script>

<style scoped>
.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 text-sm font-medium;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2 text-sm font-medium;
}

.btn-icon {
  @apply p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors;
}

.btn-toggle {
  @apply p-2 text-gray-500 hover:bg-gray-100 transition-colors;
}

.btn-toggle.active {
  @apply text-blue-600 bg-blue-50;
}

.btn-toggle:first-child {
  @apply rounded-l-lg;
}

.btn-toggle:last-child {
  @apply rounded-r-lg;
}

.export-menu-item {
  @apply w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors space-x-2;
}
</style>
