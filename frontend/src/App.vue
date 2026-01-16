<template>
  <!-- 项目列表页面（包含登录注册） -->
  <ProjectsView
    v-if="currentView === 'projects'"
    @select-project="handleSelectProject"
  />
  
  <!-- 编辑器页面 -->
  <div v-else-if="currentView === 'editor'" class="app-container h-screen flex flex-col bg-gray-50">
    <TopBar 
      :show-material-panel="showMaterialPanel"
      :show-chat-panel="showChatPanel"
      :editor-json="editorJson"
      :project-name="currentProject?.name"
      @new-document="handleNewDocument" 
      @save-document="handleSaveDocument"
      @open-document="handleOpenDocument"
      @toggle-material-panel="showMaterialPanel = !showMaterialPanel"
      @toggle-chat-panel="showChatPanel = !showChatPanel"
      @show-snapshots="showSnapshotModal = true"
      @show-settings="showSettingsModal = true"
      @back-to-projects="handleBackToProjects"
    />
    
    <!-- 主内容区 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧边栏 - 材料管理 -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="w-0 opacity-0"
        enter-to-class="w-64 opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="w-64 opacity-100"
        leave-to-class="w-0 opacity-0"
      >
        <MaterialPanel 
          v-if="showMaterialPanel"
          :materials="materials"
          @upload="handleUploadMaterial"
          @remove="handleRemoveMaterial"
        />
      </Transition>
      
      <!-- 中间编辑区 -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- 编辑器工具栏 -->
        <EditorToolbar 
          v-if="editor"
          :editor="editor"
        />
        
        <!-- TipTap编辑器 -->
        <div class="flex-1 overflow-auto bg-white">
          <EditorContent :editor="editor" class="h-full" />
        </div>
      </div>
      
      <!-- 右侧边栏 - AI对话 -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="w-0 opacity-0"
        enter-to-class="w-80 opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="w-80 opacity-100"
        leave-to-class="w-0 opacity-0"
      >
        <ChatPanel 
          v-if="showChatPanel"
          :messages="chatMessages"
          :is-connected="connectionStatus === 'connected'"
          :has-selection="hasSelection"
          @send-message="handleSendMessage"
          @insert-to-doc="handleInsertToDoc"
        />
      </Transition>
    </div>
    
    <!-- 底部状态栏 -->
    <StatusBar 
      :word-count="wordCount"
      :connection-status="connectionStatus"
      :last-saved="lastSaved"
    />
    
    <!-- 版本快照弹窗 -->
    <SnapshotModal 
      v-if="showSnapshotModal"
      :snapshots="snapshots"
      @close="showSnapshotModal = false"
      @restore="handleRestoreSnapshot"
      @save-snapshot="handleManualSnapshot"
      @clear-all="handleClearSnapshots"
    />
    
    <!-- 设置弹窗 -->
    <SettingsModal 
      v-if="showSettingsModal"
      :settings="userSettings"
      @close="showSettingsModal = false"
      @save="handleSettingsChange"
    />
  </div>
  
  <!-- Toast 通知 - 全局显示 -->
  <ToastContainer />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Underline from '@tiptap/extension-underline'

import ProjectsView from './views/ProjectsView.vue'
import TopBar from './components/TopBar.vue'
import MaterialPanel from './components/MaterialPanel.vue'
import EditorToolbar from './components/EditorToolbar.vue'
import ChatPanel from './components/ChatPanel.vue'
import StatusBar from './components/StatusBar.vue'
import SnapshotModal from './components/SnapshotModal.vue'
import SettingsModal from './components/SettingsModal.vue'
import ToastContainer from './components/ToastContainer.vue'

import { useDocumentStore } from './stores/document'
import { useAuthStore } from './stores/auth'
import { useWebSocketService } from './services/websocket'
import { useToast } from './composables/useToast'
import { getResources, uploadResourceFromPath, deleteResource } from './services/resources'

const documentStore = useDocumentStore()
const authStore = useAuthStore()
const wsService = useWebSocketService()
const toast = useToast()

// UI状态
const showMaterialPanel = ref(true)
const showChatPanel = ref(true)
const showSnapshotModal = ref(false)
const showSettingsModal = ref(false)
const materials = ref([])
const currentProjectId = ref(null)
const currentProject = ref(null)
const currentView = ref('projects') // 'projects' | 'editor'
const chatMessages = ref([])
const connectionStatus = ref('disconnected')
const lastSaved = ref(null)
const snapshots = ref([])

// 用户设置
const userSettings = ref({
  autoSnapshot: true,
  snapshotInterval: 5,
  maxSnapshots: 30,
  autoSaveLocal: true
})

// TipTap编辑器初始化
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3, 4] },
      history: {
        depth: 100,
        newGroupDelay: 50
      }
    }),
    Underline,
    Image,
    Table.configure({ resizable: true }),
    TableRow,
    TableHeader,
    TableCell,
  ],
  content: '<p>开始编写您的文档...</p>',
  editorProps: {
    attributes: {
      class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-xl mx-auto focus:outline-none',
    },
  },
  onUpdate: ({ editor }) => {
    const json = editor.getJSON()
    documentStore.updateDocument(json)
  },
})

// 计算属性
const wordCount = computed(() => {
  if (!editor.value) return 0
  return editor.value.getText().length
})

const editorJson = computed(() => {
  return editor.value?.getJSON() || null
})

const hasSelection = computed(() => {
  if (!editor.value) return false
  const { from, to } = editor.value.state.selection
  return from !== to
})

// 自动保存快照
let autoSnapshotInterval = null

const startAutoSnapshot = () => {
  // 清除旧的定时器
  if (autoSnapshotInterval) {
    clearInterval(autoSnapshotInterval)
    autoSnapshotInterval = null
  }
  
  // 如果开启了自动快照
  if (userSettings.value.autoSnapshot) {
    const intervalMs = userSettings.value.snapshotInterval * 60 * 1000
    autoSnapshotInterval = setInterval(() => {
      if (editor.value && wordCount.value > 0) {
        saveSnapshot('自动保存')
      }
    }, intervalMs)
  }
}

// 监听设置变化，重新设置定时器
const handleSettingsChange = (newSettings) => {
  userSettings.value = { ...newSettings }
  // 保存到 localStorage
  localStorage.setItem('user_settings', JSON.stringify(userSettings.value))
  // 重新启动自动快照
  startAutoSnapshot()
}

onMounted(() => {
  // 恢复用户设置
  const savedSettings = localStorage.getItem('user_settings')
  if (savedSettings) {
    try {
      userSettings.value = { ...userSettings.value, ...JSON.parse(savedSettings) }
    } catch (e) {}
  }
  
  // 启动自动快照
  startAutoSnapshot()
})

// 保存快照
const saveSnapshot = (label = '') => {
  const json = editor.value?.getJSON()
  if (!json) return
  
  snapshots.value.push({
    content: JSON.parse(JSON.stringify(json)),
    timestamp: new Date().toISOString(),
    label
  })
  
  // 限制快照数量
  if (snapshots.value.length > userSettings.value.maxSnapshots) {
    snapshots.value.shift()
  }
  
  // 保存到 localStorage
  try {
    localStorage.setItem('doc_snapshots', JSON.stringify(snapshots.value))
  } catch (e) {
    console.warn('保存快照到 localStorage 失败')
  }
}

// 恢复快照
const handleRestoreSnapshot = (snapshot) => {
  if (snapshot.content) {
    editor.value?.commands.setContent(snapshot.content)
    showSnapshotModal.value = false
  }
}

// 手动保存快照
const handleManualSnapshot = (label) => {
  saveSnapshot(label || '手动保存')
}

// 清空快照
const handleClearSnapshots = () => {
  snapshots.value = []
  localStorage.removeItem('doc_snapshots')
}

// 文档操作
const handleNewDocument = () => {
  if (confirm('创建新文档将清空当前内容，是否继续?')) {
    // 保存当前内容为快照
    if (wordCount.value > 10) {
      saveSnapshot('新建前自动保存')
    }
    editor.value?.commands.setContent('<p>开始编写您的文档...</p>')
    documentStore.clearDocument()
    toast.success('已创建新文档')
  }
}

const handleSaveDocument = async () => {
  if (!window.electronAPI) {
    // 浏览器环境：保存到 localStorage
    const json = editor.value?.getJSON()
    localStorage.setItem('doc_content', JSON.stringify(json))
    lastSaved.value = new Date().toISOString()
    toast.success('文档已保存到本地')
    return
  }
  
  const filePath = await window.electronAPI.saveFile({
    defaultPath: 'document.json',
    filters: [
      { name: 'JSON Document', extensions: ['json'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (filePath) {
    const json = editor.value?.getJSON()
    const content = JSON.stringify(json, null, 2)
    const result = await window.electronAPI.writeFile(filePath, content)
    
    if (result.success) {
      lastSaved.value = new Date().toISOString()
      toast.success('文档保存成功')
    } else {
      toast.error('保存失败: ' + result.error)
    }
  }
}

const handleOpenDocument = (data) => {
  try {
    const json = JSON.parse(data)
    editor.value?.commands.setContent(json)
    toast.success('文档已加载')
  } catch (e) {
    toast.error('文档格式错误')
  }
}

// 材料管理
const handleUploadMaterial = async () => {
  if (!window.electronAPI) {
    toast.warning('此功能仅在 Electron 环境下可用')
    return
  }
  
  const filePaths = await window.electronAPI.openFile()
  if (filePaths && filePaths.length > 0) {
    for (const filePath of filePaths) {
      try {
        // 读取文件内容
        const fileContent = await window.electronAPI.readFileAsBuffer(filePath)
        const fileName = filePath.split(/[\\/]/).pop()
        
        // 上传到后端
        const result = await uploadResourceFromPath(
          currentProjectId.value,
          filePath,
          fileContent,
          fileName
        )
        
        if (result.resource) {
          materials.value.push(result.resource)
          toast.success(`已上传: ${fileName}`)
        }
      } catch (err) {
        console.error('上传失败:', err)
        toast.error(`上传失败: ${err.response?.data?.error || err.message}`)
      }
    }
  }
}

const handleRemoveMaterial = async (id) => {
  try {
    await deleteResource(currentProjectId.value, id)
    materials.value = materials.value.filter(m => m.id !== id)
    toast.success('素材已删除')
  } catch (err) {
    console.error('删除失败:', err)
    toast.error(`删除失败: ${err.response?.data?.error || err.message}`)
  }
}

// 从后端获取素材列表
const fetchMaterials = async () => {
  try {
    const resourceList = await getResources(currentProjectId.value)
    materials.value = resourceList
  } catch (err) {
    console.error('获取素材列表失败:', err)
    // 静默失败，不显示错误提示
  }
}

// AI对话
const handleSendMessage = async (message) => {
  chatMessages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })
  
  // 发送到后端AI服务
  if (wsService.isConnected()) {
    wsService.send({
      type: 'chat',
      message,
      context: {
        document: editor.value?.getJSON(),
        materials: materials.value,
        selection: hasSelection.value ? editor.value?.state.doc.textBetween(
          editor.value.state.selection.from,
          editor.value.state.selection.to
        ) : null
      }
    })
  } else {
    // 模拟AI响应（开发模式）
    setTimeout(() => {
      chatMessages.value.push({
        role: 'assistant',
        content: `收到您的消息："${message}"\n\n这是一个模拟响应。实际的 AI 功能需要连接后端服务。\n\n**提示**: 后端服务启动后，我将能够：\n- 根据您的材料生成内容\n- 优化和润色文字\n- 生成文档大纲\n- 回答关于文档的问题`,
        timestamp: new Date().toISOString()
      })
    }, 1500)
  }
}

// 插入AI回复到文档
const handleInsertToDoc = (content) => {
  if (editor.value) {
    editor.value.chain().focus().insertContent(content).run()
  }
}

// 认证成功处理（已移除，现在在 ProjectsView 中处理）

// 选择项目
const handleSelectProject = async (project) => {
  currentProject.value = project
  currentProjectId.value = project.id
  currentView.value = 'editor'
  
  // 连接 WebSocket
  wsService.connect('ws://localhost:8000/ws')
  
  // 获取项目素材
  await fetchMaterials()
  
  // 恢复保存的内容
  const savedContent = localStorage.getItem(`doc_content_${project.id}`)
  if (savedContent) {
    try {
      const json = JSON.parse(savedContent)
      editor.value?.commands.setContent(json)
    } catch (e) {
      console.warn('恢复文档失败')
    }
  } else {
    editor.value?.commands.setContent('<p>开始编写您的文档...</p>')
  }
  
  // 恢复快照
  const savedSnapshots = localStorage.getItem(`doc_snapshots_${project.id}`)
  if (savedSnapshots) {
    try {
      snapshots.value = JSON.parse(savedSnapshots)
    } catch (e) {
      console.warn('恢复快照失败')
    }
  } else {
    snapshots.value = []
  }
}

// 返回项目列表
const handleBackToProjects = () => {
  // 保存当前文档
  if (currentProjectId.value && editor.value) {
    const json = editor.value.getJSON()
    localStorage.setItem(`doc_content_${currentProjectId.value}`, JSON.stringify(json))
    localStorage.setItem(`doc_snapshots_${currentProjectId.value}`, JSON.stringify(snapshots.value))
  }
  
  currentView.value = 'projects'
  currentProject.value = null
  currentProjectId.value = null
  materials.value = []
  chatMessages.value = []
}

// WebSocket连接
onMounted(() => {
  authStore.restoreUser()
  
  // 总是显示项目列表（包含登录注册）
  currentView.value = 'projects'
  
  wsService.on('message', (data) => {
    if (data.type === 'chat_response') {
      chatMessages.value.push({
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toISOString()
      })
    } else if (data.type === 'document_update') {
      // 保存当前版本为快照
      saveSnapshot('AI 修改前')
      editor.value?.commands.setContent(data.content)
    }
  })
  
  wsService.on('connect', () => {
    connectionStatus.value = 'connected'
    toast.success('已连接到服务器')
  })
  
  wsService.on('disconnect', () => {
    connectionStatus.value = 'disconnected'
  })
})

onBeforeUnmount(() => {
  editor.value?.destroy()
  wsService.disconnect()
  if (autoSnapshotInterval) {
    clearInterval(autoSnapshotInterval)
  }
})
</script>

<style scoped>
.app-container {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Microsoft YaHei', sans-serif;
}
</style>
