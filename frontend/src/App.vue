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
import TextStyle from '@tiptap/extension-text-style'
import FontFamily from '@tiptap/extension-font-family'

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
import api from './services/api'

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
    TextStyle,
    FontFamily,
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

// 获取操作名称
const getOperationName = (operationType) => {
  const names = {
    'generate_outline': '生成的大纲',
    'expand_content': '扩展的内容',
    'summarize': '摘要',
    'style_transfer': '风格转换后的内容',
    'grammar_check': '语法检查结果',
    'insert_text': '插入的内容',
    'replace_text': '替换后的内容',
    'replace': '替换后的内容',
    'delete_text': '删除操作',
    'format_text': '格式化后的内容',
    'none': '无操作'
  }
  return names[operationType] || '操作结果'
}

// 执行文档操作
const executeDocumentOperation = (operation) => {
  if (!editor.value) {
    console.warn('编辑器未初始化，无法执行操作')
    return
  }
  
  const { operation_type, content, position } = operation
  
  // 如果操作类型是none或没有内容，跳过
  if (operation_type === 'none' || !content) {
    return
  }
  
  try {
    switch (operation_type) {
      case 'replace_text':
      case 'REPLACE_TEXT':
        // 替换选中的文本
        if (hasSelection.value && content) {
          const { from, to } = editor.value.state.selection
          editor.value.chain()
            .focus()
            .setTextSelection({ from, to })
            .deleteSelection()
            .insertContent(content)
            .run()
          toast.success('已替换选中文本')
        } else if (position && content) {
          // 根据position替换
          const start = position.start || 0
          const end = position.end || start
          editor.value.chain()
            .focus()
            .setTextSelection({ from: start, to: end })
            .deleteSelection()
            .insertContent(content)
            .run()
          toast.success('已替换指定文本')
        }
        break
        
      case 'insert_text':
      case 'INSERT_TEXT':
        // 插入文本
        if (content) {
          if (position) {
            // 在指定位置插入
            const pos = position.start || editor.value.state.selection.from
            editor.value.chain()
              .focus()
              .setTextSelection({ from: pos, to: pos })
              .insertContent(content)
              .run()
          } else {
            // 在当前光标位置插入
            editor.value.chain()
              .focus()
              .insertContent(content)
              .run()
          }
          toast.success('已插入内容')
        }
        break
        
      case 'delete_text':
      case 'DELETE_TEXT':
        // 删除文本
        if (hasSelection.value) {
          editor.value.chain()
            .focus()
            .deleteSelection()
            .run()
          toast.success('已删除选中文本')
        } else if (position) {
          const start = position.start || 0
          const end = position.end || start
          editor.value.chain()
            .focus()
            .setTextSelection({ from: start, to: end })
            .deleteSelection()
            .run()
          toast.success('已删除指定文本')
        }
        break
        
      case 'replace':
      case 'REPLACE':
        // 全量替换
        if (content) {
          editor.value.chain()
            .focus()
            .setContent(content)
            .run()
          toast.success('已更新文档内容')
        }
        break
        
      case 'format_text':
      case 'FORMAT_TEXT':
        // 格式化文本
        if (hasSelection.value && content) {
          const { from, to } = editor.value.state.selection
          editor.value.chain()
            .focus()
            .setTextSelection({ from, to })
            .deleteSelection()
            .insertContent(content)
            .run()
          toast.success('已格式化文本')
        }
        break
        
      case 'none':
      case 'NONE':
        // 无操作
        break
        
      default:
        console.log('未处理的操作类型:', operation_type, operation)
    }
  } catch (error) {
    console.error('执行文档操作失败:', error, operation)
    toast.error(`执行操作失败: ${error.message}`)
  }
}

// AI对话
const handleSendMessage = async (message) => {
  chatMessages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })
  
  // 显示加载状态
  const loadingMessageIndex = chatMessages.value.length
  chatMessages.value.push({
    role: 'assistant',
    content: '正在思考...',
    timestamp: new Date().toISOString(),
    isLoading: true
  })
  
  try {
    // 获取选中的文本
    const selectedText = hasSelection.value ? editor.value?.state.doc.textBetween(
      editor.value.state.selection.from,
      editor.value.state.selection.to
    ) : null
    
    // 使用 HTTP API 调用后端 AI 服务
    const response = await api.post('/ai/chat', {
      message: message,
      session_id: `project_${currentProjectId.value || 'default'}`,
      // 传递文档内容，让AI能够执行操作
      document_content: editor.value?.getText() || undefined,
      selected_text: selectedText || undefined,
      selection_range: hasSelection.value ? {
        start: editor.value.state.selection.from,
        end: editor.value.state.selection.to
      } : undefined,
      project_id: currentProjectId.value || undefined
    })
    
    // 调试：打印完整响应数据
    console.log('AI API 响应:', response.data)
    console.log('响应数据结构:', {
      code: response.data.code,
      message: response.data.message,
      hasData: !!response.data.data,
      dataKeys: response.data.data ? Object.keys(response.data.data) : [],
      dataContent: response.data.data,
      // 支持两种字段名：message (ai_v2.py) 和 reply (ai.py)
      messageField: response.data.data?.message,
      replyField: response.data.data?.reply,
      messageType: typeof response.data.data?.message,
      replyType: typeof response.data.data?.reply
    })
    
    // 移除加载消息
    chatMessages.value.splice(loadingMessageIndex, 1)
    
    // 添加AI回复
    if (response.data.code === 200 && response.data.data) {
      // 支持两种字段名：message (ai_v2.py) 和 reply (ai.py)
      const replyContent = response.data.data.message || response.data.data.reply
      
      // 检查回复内容
      if (replyContent === null || replyContent === undefined) {
        console.error('AI返回null或undefined:', {
          fullResponse: response.data,
          dataObject: response.data.data,
          allKeys: Object.keys(response.data.data || {}),
          messageValue: response.data.data?.message,
          replyValue: response.data.data?.reply
        })
        chatMessages.value.push({
          role: 'assistant',
          content: `抱歉，AI返回了空内容（null/undefined）。\n\n**调试信息**:\n- 响应代码: 200\n- 数据对象存在: ${!!response.data.data}\n- 数据对象键: ${response.data.data ? Object.keys(response.data.data).join(', ') : '无'}\n- message字段值: ${response.data.data?.message}\n- reply字段值: ${response.data.data?.reply}\n\n请检查后端日志，查看LLM实际返回的内容。`,
          timestamp: new Date().toISOString()
        })
      } else if (typeof replyContent !== 'string') {
        console.error('AI返回非字符串类型:', typeof replyContent, replyContent)
        chatMessages.value.push({
          role: 'assistant',
          content: `抱歉，AI返回了意外的数据类型（${typeof replyContent}）。\n\n**调试信息**:\n${JSON.stringify(replyContent, null, 2)}`,
          timestamp: new Date().toISOString()
        })
      } else if (replyContent.trim() === '') {
        console.warn('AI返回空字符串:', response.data)
        chatMessages.value.push({
          role: 'assistant',
          content: '抱歉，AI返回了空内容。这可能是因为：\n1. API密钥配置问题\n2. 模型返回了空响应\n3. 网络问题\n\n请检查后端日志获取更多信息。',
          timestamp: new Date().toISOString()
        })
      } else {
        // 正常情况：有内容
        console.log('AI回复内容:', replyContent.substring(0, 100) + '...')
        
        // 检查是否有操作需要执行
        const operations = response.data.data.operations || []
        console.log('AI返回的操作:', operations)
        
        // 构建显示内容
        let displayContent = replyContent
        
        // 如果有操作，处理操作内容
        if (operations && operations.length > 0) {
          // 区分需要显示内容的操作和需要执行的操作
          const displayOnlyOperations = ['summarize', 'generate_outline', 'expand_content', 'style_transfer', 'grammar_check']
          
          operations.forEach(op => {
            if (!op.operation_type || op.operation_type === 'none') {
              return
            }
            
            // 如果是仅显示的操作，将内容添加到消息中
            if (displayOnlyOperations.includes(op.operation_type) && op.content && op.content.trim()) {
              const operationName = getOperationName(op.operation_type)
              displayContent += `\n\n**${operationName}**:\n${op.content}`
            }
            // 如果是需要执行的操作，执行文档修改
            else if (['replace_text', 'insert_text', 'delete_text', 'replace', 'format_text'].includes(op.operation_type)) {
              executeDocumentOperation(op)
            }
          })
        }
        
        chatMessages.value.push({
          role: 'assistant',
          content: displayContent,
          timestamp: new Date().toISOString()
        })
      }
      // 更新连接状态
      connectionStatus.value = 'connected'
    } else {
      console.error('AI服务返回错误结构:', response.data)
      throw new Error(response.data.message || 'AI服务返回错误')
    }
  } catch (error) {
    // 移除加载消息
    chatMessages.value.splice(loadingMessageIndex, 1)
    
    // 显示错误消息
    console.error('AI服务错误:', error)
    
    let errorMessage = `抱歉，AI服务暂时不可用。\n\n`
    
    if (error.response?.status === 401) {
      errorMessage += '**错误**: 未登录或登录已过期，请重新登录。'
    } else if (error.response?.status === 500) {
      errorMessage += `**错误**: ${error.response?.data?.message || '服务器内部错误'}\n\n请检查：\n1. 后端服务是否正常运行\n2. API密钥是否已正确配置`
    } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      errorMessage += '**错误**: 无法连接到后端服务\n\n请检查：\n1. 后端服务是否已启动（http://localhost:5000）\n2. 防火墙是否阻止了连接'
    } else {
      errorMessage += `**错误**: ${error.response?.data?.message || error.message || '未知错误'}\n\n请检查：\n1. 后端服务是否已启动\n2. 是否已登录\n3. API密钥是否已配置`
    }
    
    chatMessages.value.push({
      role: 'assistant',
      content: errorMessage,
      timestamp: new Date().toISOString()
    })
    
    // 根据错误类型更新连接状态
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      connectionStatus.value = 'disconnected'
    }
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
  
  // 连接 WebSocket（暂时禁用，等待后端 WebSocket 服务实现）
  // TODO: 启用 WebSocket 连接用于实时 AI 对话
  // wsService.connect('ws://localhost:5000/ws')
  
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

// 检查后端连接状态
const checkBackendConnection = async () => {
  try {
    // 尝试调用一个简单的API来检查连接
    await api.get('/user/me')
    connectionStatus.value = 'connected'
  } catch (error) {
    // 如果是401错误，说明已连接但未登录，也算连接成功
    if (error.response?.status === 401) {
      connectionStatus.value = 'connected'
    } else {
      connectionStatus.value = 'disconnected'
    }
  }
}

// 组件挂载
onMounted(() => {
  authStore.restoreUser()
  
  // 总是显示项目列表（包含登录注册）
  currentView.value = 'projects'
  
  // 检查后端连接状态
  checkBackendConnection()
  
  // 保留WebSocket事件监听（用于未来可能的WebSocket功能）
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
    // 只有在WebSocket连接时才更新状态
    // HTTP API连接状态由checkBackendConnection管理
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
