<template>
  <!-- 项目列表页面（包含登录注册） -->
  <ProjectsView
    v-if="currentView === 'projects'"
    @select-project="handleSelectProject"
  />
  
  <!-- 编辑器页面 -->
  <div v-else-if="currentView === 'editor'" class="app-container h-screen flex flex-col bg-gray-50">
    <TopBar 
      :show-workspace-panel="showWorkspacePanel"
      :show-chat-panel="showChatPanel"
      :editor-json="editorJson"
      :editor-html="editorHtml"
      :styles="docStyles"
      :project-name="currentProject?.name"
      @new-document="handleNewDocument"  
      @save-document="handleSaveDocument"
      @open-document="handleOpenDocument"
      @import-document="handleImportDocument"
      @toggle-workspace-panel="showWorkspacePanel = !showWorkspacePanel"
      @toggle-chat-panel="showChatPanel = !showChatPanel"
      @show-snapshots="showSnapshotModal = true"
      @show-settings="showSettingsModal = true"
      @back-to-projects="handleBackToProjects"
    />
    
    <!-- 主内容区 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧边栏 - 工作区 -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="!w-0 opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="!w-0 opacity-0"
      >
        <aside 
            v-if="showWorkspacePanel"
            class="flex-shrink-0 flex flex-col relative border-r border-gray-200 bg-white"
            :style="{ width: leftSidebarWidth + 'px' }"
        >
            <!-- Header -->
            <div class="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <div class="flex items-center space-x-2">
                    <FolderOpen :size="16" class="text-blue-600" />
                    <span class="text-sm font-medium text-gray-800">工作区</span>
                </div>
                <button 
                  @click="showWorkspacePanel = false" 
                  class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
                >
                    <X :size="14" />
                </button>
            </div>

            <!-- Content Area -->
            <div class="flex-1 overflow-hidden">
                <WorkspacePanel 
                  class="h-full w-full"
                  :documents="workspaceDocuments"
                  :active-document-id="activeDocumentId"
                  @select-document="handleSelectDocument"
                  @create-document="handleCreateDocument"
                  @rename-document="handleRenameDocument"
                  @delete-document="handleDeleteDocument"
                />
            </div>

            <!-- Resizer Handle -->
            <div 
                class="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-blue-400 z-50 opacity-0 hover:opacity-100 transition-opacity translate-x-1/2"
                @mousedown.prevent="startResizeLeft"
            ></div>
        </aside>
      </Transition>
      
      <!-- 中间编辑区 -->
      <div class="flex-1 flex flex-col overflow-hidden relative">
        <!-- 编辑器工具栏 -->
        <EditorToolbar 
          v-if="editor"
          :editor="editor"
          :styles="docStyles"
          :system-fonts="systemFonts"
          @edit-style="handleEditStyle"
        />
        
        <!-- TipTap编辑器 -->
        <div class="flex-1 overflow-auto bg-white relative">
          <EditorContent 
            :editor="editor" 
            class="h-full"
            @contextmenu.prevent="showCustomContextMenu"
          />
          
          <!-- 自定义右键菜单 -->
          <div
            v-if="contextMenuVisible"
            :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
            class="fixed bg-white border border-gray-200 rounded-lg shadow-xl py-1 z-[9999] min-w-[160px]"
            @click.stop
          >
            <button
              @click="handleContextMenuAction('cut')"
              class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
              :disabled="!hasSelection"
              :class="{ 'opacity-50 cursor-not-allowed': !hasSelection }"
            >
              <span>✂️</span>
              <span>剪切</span>
              <span class="ml-auto text-xs text-gray-400">Ctrl+X</span>
            </button>
            <button
              @click="handleContextMenuAction('copy')"
              class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
              :disabled="!hasSelection"
              :class="{ 'opacity-50 cursor-not-allowed': !hasSelection }"
            >
              <span>📋</span>
              <span>复制</span>
              <span class="ml-auto text-xs text-gray-400">Ctrl+C</span>
            </button>
            <button
              @click="handleContextMenuAction('paste')"
              class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
            >
              <span>📄</span>
              <span>粘贴</span>
              <span class="ml-auto text-xs text-gray-400">Ctrl+V</span>
            </button>
            <div class="border-t border-gray-200 my-1"></div>
            <button
              @click="handleContextMenuAction('selectAll')"
              class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
            >
              <span>📝</span>
              <span>全选</span>
              <span class="ml-auto text-xs text-gray-400">Ctrl+A</span>
            </button>
          </div>
        </div>
      </div>
          <!-- 点击提示覆盖层 - 已禁用，因为会干扰右键菜单 -->
          <!-- 
          <div
            v-if="showClickPrompt"
            @click.stop="handleEditorClick"
            class="absolute inset-0 bg-blue-500 bg-opacity-10 backdrop-blur-sm flex items-center justify-center cursor-pointer z-50 animate-fade-in"
            style="pointer-events: none;"
          >
            <div class="bg-white rounded-lg shadow-2xl p-8 max-w-md mx-4 text-center animate-bounce-in" style="pointer-events: auto;" @click.stop="handleEditorClick">
              <div class="text-6xl mb-4">👆</div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">点击这里继续编辑</h3>
              <p class="text-gray-600 mb-4">点击编辑器区域即可开始输入</p>
              <div class="text-sm text-gray-500">或按任意键开始输入</div>
            </div>
          </div>
          -->
      
      <!-- 右侧统一侧边栏 -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="!w-0 opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="!w-0 opacity-0"
      >
        <aside 
            v-if="showRightSidebar" 
            class="bg-white border-l border-gray-200 flex flex-col h-full shadow-sm z-10 flex-shrink-0 relative"
            :style="{ width: rightSidebarWidth + 'px' }"
        >
            <!-- Resizer Handle -->
            <div 
                class="absolute top-0 left-0 w-1 h-full cursor-col-resize hover:bg-blue-400 z-50 opacity-0 hover:opacity-100 transition-opacity -translate-x-1/2"
                @mousedown.prevent="startResizeRight"
            ></div>

            <!-- Tab Header -->
            <div class="flex border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <button 
                  @click="activeSidebarTab = 'chat'" 
                  class="flex-1 py-3 text-sm font-medium flex items-center justify-center space-x-2 border-b-2 transition-colors duration-200"
                  :class="activeSidebarTab === 'chat' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'"
                >
                    <MessageSquare :size="16" />
                    <span>AI 助手</span>
                </button>
                <button @click="showRightSidebar = false" class="px-3 text-gray-400 hover:text-gray-600 hover:bg-gray-200 transition-colors border-l border-gray-200">
                    <X :size="16" />
                </button>
            </div>

            <!-- Content Area -->
            <div class="flex-1 overflow-hidden relative">
                 <ChatPanel 
                  v-show="activeSidebarTab === 'chat'"
                  class="h-full w-full"
                  :messages="chatMessages"
                  :is-connected="connectionStatus === 'connected'"
                  :has-selection="hasSelection"
                  @send-message="handleSendMessage"
                  @insert-to-doc="handleInsertToDoc"
                  @locate-in-doc="handleLocateInDoc"
                />
            </div>
        </aside>
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
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import { X, MessageSquare, Paintbrush, FolderOpen } from 'lucide-vue-next' // Add icons
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Underline from '@tiptap/extension-underline'
import TextStyle from '@tiptap/extension-text-style'
import FontFamily from '@tiptap/extension-font-family'
import { FontSize } from './extensions/FontSize'
import { Color } from './extensions/Color'

import ProjectsView from './views/ProjectsView.vue'
import TopBar from './components/TopBar.vue'
import MaterialPanel from './components/MaterialPanel.vue'
import WorkspacePanel from './components/WorkspacePanel.vue'
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
import { uploadImage } from './services/image'
import { WorkspaceService } from './services/workspace'
import api from './services/api'

// API基础URL - 直接指向后端服务器
const API_BASE_URL = 'http://localhost:5000'

const documentStore = useDocumentStore()
const authStore = useAuthStore()
const wsService = useWebSocketService()
const toast = useToast()

// 工作区服务
const workspaceService = ref(null)
const workspaceDocuments = ref([])
const activeDocumentId = ref(null)

// UI状态
const showWorkspacePanel = ref(true)
const showMaterialPanel = ref(false)
const showRightSidebar = ref(true) // Unified sidebar state
const activeSidebarTab = ref('chat') // 'chat' | 'style'

const showChatPanel = computed({
    get: () => showRightSidebar.value && activeSidebarTab.value === 'chat',
    set: (val) => {
        if (val) {
            showRightSidebar.value = true
            activeSidebarTab.value = 'chat'
        } else {
             // If trying to close chat, check if we should close sidebar or switch?
             // Usually triggered by toggle, so close.
             showRightSidebar.value = false
        }
    }
})
// Deprecated individual refs but keeping variables for compatibility if referenced
const showStylePanel = computed({
    get: () => showRightSidebar.value && activeSidebarTab.value === 'style',
    set: (val) => {
        if (val) {
            showRightSidebar.value = true
            activeSidebarTab.value = 'style'
        } else {
            showRightSidebar.value = false
        }
    }
})

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

// Sidebar Resizing
const leftSidebarWidth = ref(256)
const rightSidebarWidth = ref(320)
const isResizingLeft = ref(false)
const isResizingRight = ref(false)

const startResizeLeft = () => {
    isResizingLeft.value = true
    document.body.style.cursor = 'col-resize'
    document.body.classList.add('select-none')
}

const startResizeRight = () => {
    isResizingRight.value = true
    document.body.style.cursor = 'col-resize'
    document.body.classList.add('select-none')
}

const handleGlobalMouseMove = (e) => {
    if (isResizingLeft.value) {
        // Limit width between 200 and 600
        const newWidth = Math.max(200, Math.min(600, e.clientX))
        leftSidebarWidth.value = newWidth
    }
    if (isResizingRight.value) {
        // Calculate width from right
        const containerWidth = document.body.clientWidth
        const newWidth = Math.max(240, Math.min(800, containerWidth - e.clientX))
        rightSidebarWidth.value = newWidth
    }
}

const handleGlobalMouseUp = () => {
    if (isResizingLeft.value || isResizingRight.value) {
        isResizingLeft.value = false
        isResizingRight.value = false
        document.body.style.cursor = ''
        document.body.classList.remove('select-none')
    }
}

// 默认样式列表 - 如果父组件没有传入，使用默认值
const defaultStyles = [
    { id: 'paragraph', label: '正文', element: 'p', style: { fontSize: 16, lineHeight: 1.6, color: '#374151', bold: false, italic: false, marginTop: 0, marginBottom: 0.75, fontFamily: 'Microsoft YaHei' } },
    { id: 'heading1', label: '标题 1', element: 'h1', level: 1, style: { fontSize: 32, lineHeight: 1.2, color: '#111827', bold: true, italic: false, marginTop: 1, marginBottom: 0.5, fontFamily: 'Microsoft YaHei' } },
    { id: 'heading2', label: '标题 2', element: 'h2', level: 2, style: { fontSize: 24, lineHeight: 1.3, color: '#1f2937', bold: true, italic: false, marginTop: 0.83, marginBottom: 0.5, fontFamily: 'Microsoft YaHei' } },
    { id: 'heading3', label: '标题 3', element: 'h3', level: 3, style: { fontSize: 18.72, lineHeight: 1.4, color: '#374151', bold: true, italic: false, marginTop: 1, marginBottom: 0.5, fontFamily: 'Microsoft YaHei' } },
]

// 样式管理
const docStyles = ref([...defaultStyles]) // Initialize with copy of default styles

const systemFonts = ref([])
const editingStyle = ref(null)

const handleEditStyle = (styleItem) => {
    editingStyle.value = JSON.parse(JSON.stringify(styleItem)) // copy
    activeSidebarTab.value = 'style'
    showRightSidebar.value = true
}

const handleSaveStyle = (updatedStyle) => {
    const index = docStyles.value.findIndex(s => s.id === updatedStyle.id)
    if (index !== -1) {
        docStyles.value[index] = { ...docStyles.value[index], ...updatedStyle }
        
        // 应用样式更改到编辑器 DOM (通过注入 CSS)
        updateEditorStyles()
        
        toast.success(`已更新样式: ${updatedStyle.id}`)
    }
    // Don't close sidebar, maybe switch back to chat or stay?
    // User often wants to see result. Stay in style tab looks good.
    // Or clear selection.
    editingStyle.value = null 
}

// 简单的 CSS 注入机制
const updateEditorStyles = () => {
    let styleEl = document.getElementById('editor-custom-styles')
    if (!styleEl) {
        styleEl = document.createElement('style')
        styleEl.id = 'editor-custom-styles'
        document.head.appendChild(styleEl)
    }
    
    let css = ''
    docStyles.value.forEach(ds => {
        // Selector: .ProseMirror h1, .ProseMirror p
        let selector = `.ProseMirror ${ds.element}`
        if (ds.id === 'paragraph') selector = '.ProseMirror p' 
        // Note: multiple headings might map to same element if we had custom classes, but here we assume standard mapping
        
        css += `${selector} {
            font-size: ${ds.style.fontSize}px;
            line-height: ${ds.style.lineHeight};
            color: ${ds.style.color};
            font-weight: ${ds.style.bold ? 'bold' : 'normal'};
            font-style: ${ds.style.italic ? 'italic' : 'normal'};
            margin-top: ${ds.style.marginTop}em;
            margin-bottom: ${ds.style.marginBottom}em;
            font-family: ${ds.style.fontFamily || 'inherit'};
        }\n`
    })
    
    styleEl.textContent = css
}


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
    FontSize,
    Color,
    Image,
    Table.configure({ resizable: true }),
    TableRow,
    TableHeader,
    TableCell,
  ],
  content: '',
  editable: true,
  autofocus: false, // 禁用自动聚焦，手动控制
  editorProps: {
    attributes: {
      class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-xl mx-auto focus:outline-none',
      tabindex: '0', // 确保编辑器可以通过tab键聚焦
      oncontextmenu: 'return true;', // 明确允许右键菜单
    },
    // 完全不处理contextmenu事件，让浏览器自然处理
    // handleDOMEvents: {
    //   contextmenu: (view, event) => {
    //     return false
    //   }
    // },
    handlePaste: (view, event, slice) => {
        const items = (event.clipboardData || event.originalEvent.clipboardData).items
        for (const item of items) {
            if (item.type.indexOf('image') === 0) {
                event.preventDefault()
                const file = item.getAsFile()
                if (file) {
                    uploadImage(file).then(url => {
                        const { schema } = view.state
                        const node = schema.nodes.image.create({ src: url })
                        const transaction = view.state.tr.replaceSelectionWith(node)
                        view.dispatch(transaction)
                        toast.success('图片已粘贴并上传')
                    }).catch(err => {
                        toast.error('图片粘贴失败')
                    })
                }
                return true
            }
        }
        return false
    },
    handleDrop: (view, event, slice, moved) => {
        if (!moved && event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
            const file = event.dataTransfer.files[0]
            if (file.type.startsWith('image/')) {
                event.preventDefault()
                uploadImage(file).then(url => {
                     const { schema } = view.state
                     // 计算释放位置
                     const coordinates = view.posAtCoords({ left: event.clientX, top: event.clientY })
                     if (coordinates) {
                         const node = schema.nodes.image.create({ src: url })
                         const transaction = view.state.tr.insert(coordinates.pos, node)
                         view.dispatch(transaction)
                     }
                     toast.success('图片已上传')
                }).catch(err => {
                    toast.error('图片上传失败')
                })
                return true
            }
        }
        return false
    }
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

const editorHtml = computed(() => {
  return editor.value?.getHTML() || ''
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
    editor.value?.commands.setContent('')
    documentStore.clearDocument()
    toast.success('已创建新文档')
  }
}

const handleSaveDocument = async () => {
  if (!window.electronAPI) {
    // 浏览器环境：保存到 localStorage
    const json = editor.value?.getJSON()
    
    // 构建包含样式的数据包
    const dataToSave = {
      version: '1.0',
      content: json,
      styles: docStyles.value, // 保存当前项目的自定义样式
      updated_at: new Date().toISOString()
    }
    
    // 如果有项目ID，保存到特定的项目key
    if (currentProjectId.value) {
      localStorage.setItem(`doc_data_${currentProjectId.value}`, JSON.stringify(dataToSave))
    }
    // 同时更新全局 doc_content 作为最后一次编辑的备份（兼容旧逻辑，但不建议依赖）
    localStorage.setItem('doc_content', JSON.stringify(json))
    
    lastSaved.value = new Date().toISOString()
    toast.success('文档与配置已保存到本地缓存')
    return
  }
  
  const filePath = await window.electronAPI.saveFile({
    defaultPath: currentProject.value ? `${currentProject.value.name}.json` : 'document.json',
    filters: [
      { name: 'Xingyun Document', extensions: ['json'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (filePath) {
    const json = editor.value?.getJSON()
    // 构建包含样式的数据包
    const dataToSave = {
      version: '1.0',
      content: json,
      styles: docStyles.value, // 保存当前项目的自定义样式
      updated_at: new Date().toISOString()
    }
    
    const content = JSON.stringify(dataToSave, null, 2)
    const result = await window.electronAPI.writeFile(filePath, content)
    
    if (result.success) {
      lastSaved.value = new Date().toISOString()
      toast.success('文档保存成功 (包含样式配置)')
    } else {
      toast.error('保存失败: ' + result.error)
    }
  }
}

const handleOpenDocument = (data) => {
  try {
    const parsedData = JSON.parse(data)
    
    // 检查是否是新格式（包含 version/content/styles）
    if (parsedData.version && parsedData.content) {
       editor.value?.commands.setContent(parsedData.content)
       
       if (parsedData.styles && Array.isArray(parsedData.styles)) {
         docStyles.value = parsedData.styles
         // 强制更新样式渲染
         setTimeout(() => updateEditorStyles(), 100)
         toast.success('文档与样式配置已加载')
       } else {
         toast.success('文档已加载 (无自定义样式)')
       }
    } else {
      // 兼容旧格式（纯 TipTap JSON）
      editor.value?.commands.setContent(parsedData)
      toast.success('文档已加载 (旧格式)')
    }
  } catch (e) {
    console.error('Open error:', e)
    toast.error('文档格式错误')
  }
}

// 导入外部文档到工作区
const handleImportDocument = async () => {
  if (!workspaceService.value) {
    toast.warning('工作区未初始化')
    return
  }

  // 创建文件选择input
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.docx,.doc,.pdf,.md,.markdown,.txt,.text'
  
  input.onchange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      toast.info('正在导入文档...')
      
      // 使用document-import服务导入
      const { importDocument } = await import('./services/document-import.js')
      const result = await importDocument(file, (progress, message) => {
        console.log(`导入进度: ${progress}% - ${message}`)
      })

      if (result.success && result.content) {
        // 创建新文档并保存内容
        const docName = result.filename?.replace(/\.[^/.]+$/, '') || '导入的文档'
        const newDoc = workspaceService.value.createDocument(docName)
        
        // 保存内容到新文档
        workspaceService.value.saveDocument(newDoc.id, result.content)
        
        // 更新文档列表
        workspaceDocuments.value = workspaceService.value.getAllDocuments()
        
        // 切换到新文档
        activeDocumentId.value = newDoc.id
        
        // 更新编辑器
        editor.value?.commands.setContent(result.content)
        
        toast.success(`已导入: ${docName}`)
      } else {
        toast.error(result.error || '导入失败')
      }
    } catch (error) {
      console.error('导入文档失败:', error)
      toast.error('导入文档失败: ' + error.message)
    }
  }

  input.click()
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

// 加载聊天历史记录
const loadChatHistory = async (documentId) => {
  console.log('=== 加载聊天历史记录 ===')
  console.log('documentId:', documentId)
  
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      console.log('未找到token，跳过加载历史记录')
      chatMessages.value = []
      return
    }
    
    const url = `${API_BASE_URL}/api/ai/history?days=3&limit=50&document_id=${documentId}`
    console.log('请求URL:', url)
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    console.log('响应状态:', response.status)
    
    if (response.ok) {
      const data = await response.json()
      console.log('响应数据:', data)
      
      if (data.code === 200 && data.data.records.length > 0) {
        console.log(`找到 ${data.data.records.length} 条历史记录`)
        
        // 清空当前消息
        chatMessages.value = []
        
        // 按时间排序（从旧到新）
        const records = data.data.records.reverse()
        
        // 添加历史记录到消息列表
        records.forEach(record => {
          // 添加用户消息
          if (record.user_message) {
            chatMessages.value.push({
              role: 'user',
              content: record.user_message,
              timestamp: record.created_at
            })
          }
          
          // 添加AI响应
          chatMessages.value.push({
            role: 'assistant',
            content: record.ai_response,
            timestamp: record.created_at
          })
        })
        
        console.log(`已加载 ${chatMessages.value.length} 条消息`)
        toast.success(`已加载 ${records.length} 条历史对话`)
      } else {
        console.log('没有找到历史记录')
        chatMessages.value = []
      }
    } else {
      console.error('加载历史记录失败，状态码:', response.status)
      chatMessages.value = []
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    chatMessages.value = []
  }
  
  console.log('=== 加载历史记录完成 ===')
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
      document_id: activeDocumentId.value || undefined,  // 修正：使用activeDocumentId
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
              // 检查message中是否已经包含了operation.content的内容
              // 如果message很短（少于100字）且operation.content很长，说明内容主要在operation中
              if (replyContent.length < 100 && op.content.length > 100) {
                // 直接使用operation.content作为主要内容，不添加额外标记
                displayContent = `${replyContent}\n\n${op.content}`
              } else if (!replyContent.includes(op.content.substring(0, Math.min(50, op.content.length)))) {
                // 如果message中不包含operation.content的开头部分，说明是分开的
                // 检查是否已经在displayContent中（避免重复添加）
                if (!displayContent.includes(op.content.substring(0, Math.min(50, op.content.length)))) {
                  displayContent += `\n\n${op.content}`
                }
              }
              // 否则，message中已经包含了完整内容，不需要重复添加
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

// AI智能定位
const tryAILocate = async (outlineTitle, documentText, fullOutlinePath = null) => {
  try {
    console.log('🤖 调用AI智能定位API...')
    console.log('  - 大纲标题:', outlineTitle)
    console.log('  - 完整路径:', fullOutlinePath)
    console.log('  - 文档长度:', documentText.length)
    
    // 显示明显的加载提示（不自动关闭）
    const loadingToastId = toast.info('🔍 AI智能定位中，请稍候...', 0)
    
    const requestBody = {
      outline_title: outlineTitle,
      document_text: documentText,
      full_outline_path: fullOutlinePath,  // 传递完整路径
      top_n: 3,
      use_ai: true  // 使用AI语义匹配
    }
    
    console.log('  - 请求体:', JSON.stringify(requestBody).substring(0, 200) + '...')
    
    const response = await fetch(`${API_BASE_URL}/api/ai/locate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })
    
    console.log('  - 响应状态:', response.status, response.statusText)
    
    // 关闭加载提示
    toast.remove(loadingToastId)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('  - 响应错误:', errorText)
      toast.error(`❌ AI定位失败: HTTP ${response.status}`, 5000)
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }
    
    const result = await response.json()
    console.log('  - 响应数据:', result)
    
    if (result.success && result.matches && result.matches.length > 0) {
      const bestMatch = result.matches[0]
      const method = result.method === 'ai_semantic' ? 'AI语义匹配' : '关键词匹配'
      
      console.log(`✅ ${method}找到匹配!`)
      console.log('  - 匹配分数:', bestMatch.score.toFixed(2))
      console.log('  - 位置:', bestMatch.position)
      console.log('  - 长度:', bestMatch.length)
      console.log('  - 文本:', bestMatch.text.substring(0, 50) + '...')
      if (bestMatch.reason) {
        console.log('  - 原因:', bestMatch.reason)
      }
      
      // 使用AI找到的位置进行定位
      if (editor.value) {
        editor.value
          .chain()
          .focus()
          .setTextSelection({
            from: bestMatch.position,
            to: bestMatch.position + bestMatch.length
          })
          .run()
        
        // 滚动到可见区域
        nextTick(() => {
          const editorElement = document.querySelector('.ProseMirror')
          if (editorElement) {
            const selection = window.getSelection()
            if (selection && selection.rangeCount > 0) {
              const range = selection.getRangeAt(0)
              const rect = range.getBoundingClientRect()
              const editorRect = editorElement.getBoundingClientRect()
              const scrollTop = editorElement.scrollTop + rect.top - editorRect.top - (editorRect.height / 2) + (rect.height / 2)
              
              editorElement.scrollTo({
                top: scrollTop,
                behavior: 'smooth'
              })
            }
          }
        })
        
        // 显示明显的成功提示
        const methodIcon = result.method === 'ai_semantic' ? '🤖' : '🔍'
        const methodName = result.method === 'ai_semantic' ? 'AI语义' : '关键词'
        const matchPercent = (bestMatch.score * 100).toFixed(0)
        
        toast.success(`${methodIcon} ${methodName}定位成功！(匹配度: ${matchPercent}%)`, 3000)
      }
    } else {
      console.warn('❌ AI未找到匹配')
      console.warn('  - 响应结果:', result)
      const method = result.method === 'ai_semantic' ? 'AI语义匹配' : '关键词匹配'
      const errorMsg = result.error || '未找到相关内容'
      
      // 显示明显的失败提示
      toast.warning(`⚠️ ${method}失败: ${errorMsg}`, 4000)
    }
    
    console.log('=== AI智能定位结束 ===')
  } catch (error) {
    console.error('❌ AI智能定位失败:', error)
    console.error('  - 错误类型:', error.name)
    console.error('  - 错误消息:', error.message)
    console.error('  - 错误堆栈:', error.stack)
    
    // 关闭加载提示
    if (typeof loadingToastId !== 'undefined') {
      toast.remove(loadingToastId)
    }
    
    // 根据错误类型给出更具体的提示
    let errorMessage = 'AI智能定位失败'
    let errorIcon = '❌'
    
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      errorMessage = '无法连接到后端服务，请检查后端是否运行'
      errorIcon = '🔌'
    } else if (error.message.includes('HTTP 500')) {
      errorMessage = '后端服务错误，请查看后端日志'
      errorIcon = '⚠️'
    } else if (error.message.includes('HTTP 400')) {
      errorMessage = '请求参数错误'
      errorIcon = '⚠️'
    } else {
      errorMessage = `AI智能定位失败: ${error.message}`
    }
    
    toast.error(`${errorIcon} ${errorMessage}`, 5000)
  }
}

// 在文档中定位到指定文本
const handleLocateInDoc = (locateData) => {
  console.log('=== handleLocateInDoc 开始 ===')
  
  // 兼容旧的字符串参数和新的对象参数
  let searchText, fullPath
  if (typeof locateData === 'string') {
    searchText = locateData
    fullPath = locateData
  } else {
    searchText = locateData.searchText
    fullPath = locateData.fullPath || locateData.searchText
  }
  
  console.log('1. 接收到的搜索文本:', searchText)
  console.log('2. 完整大纲路径:', fullPath)
  console.log('3. 搜索文本类型:', typeof searchText)
  console.log('4. 搜索文本长度:', searchText?.length)
  
  if (!editor.value || !searchText) {
    console.warn('❌ 编辑器未初始化或搜索文本为空')
    toast.warning('无法定位：编辑器未初始化或搜索文本为空')
    return
  }

  try {
    const { state } = editor.value
    const { doc } = state
    const searchLower = searchText.toLowerCase().trim()
    
    console.log('4. 转换为小写:', searchLower)
    
    // 移除可能的编号前缀（如 "1. "、"- "、"• "）
    // 注意：传入的searchText可能已经是纯标题，也可能包含编号
    const cleanSearchText = searchLower.replace(/^(\d+(\.\d+)*[\s\u3000]|[-•]\s)/, '').trim()
    
    console.log('5. 清理后的搜索文本:', cleanSearchText)
    console.log('6. 清理后的长度:', cleanSearchText.length)
    
    // 如果清理后为空，使用原始文本
    const finalSearchText = cleanSearchText || searchLower
    
    console.log('7. 最终搜索文本:', finalSearchText)
    
    // 获取文档的完整文本
    // 使用 editor.getText() 方法，它会正确处理换行符
    const fullDocText = editor.value.getText({ blockSeparator: '\n' })
    
    console.log('7. 文档总长度:', fullDocText.length)
    console.log('8. 文档前100字符:', fullDocText.substring(0, 100))
    console.log('9. 换行符数量:', (fullDocText.match(/\n/g) || []).length)
    
    let found = false
    let foundPos = null
    let foundLength = 0
    let nodeCount = 0
    let textNodeCount = 0
    
    // 准备多个搜索变体
    const searchVariants = []
    
    // 提取所有关键词（用于检查是否需要精确匹配）
    const allKeywords = cleanSearchText
      .replace(/[的和与及、，。！？；：""''（）【】《》]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length >= 2)
    
    // 检测是否包含技术名称（需要精确匹配）
    const techNames = ['NAS', 'SAN', 'HDFS', 'Ceph', 'NDB', 'MySQL', 'Hadoop', 'Oracle', 'MongoDB']
    // 注意：cleanSearchText 是小写的，所以需要转换为大写进行比较
    const hasTechName = techNames.some(tech => cleanSearchText.toUpperCase().includes(tech))
    
    console.log('8. 关键词分析:', {
      allKeywords,
      hasTechName,
      cleanSearchText
    })
    
    // 如果包含技术名称，只使用完整文本匹配（不使用部分关键词）
    if (hasTechName) {
      console.log('⚠️ 检测到技术名称，使用精确匹配模式')
      
      // 变体1: 完整文本
      searchVariants.push({ text: cleanSearchText, name: '完整文本', requireAll: true })
      
      // 变体2: 移除所有空格和标点
      const noSpaces = cleanSearchText.replace(/[\s\u3000、，。！？；：""''（）【】《》]/g, '')
      if (noSpaces.length >= 3 && noSpaces !== cleanSearchText) {
        searchVariants.push({ text: noSpaces, name: '无空格标点', requireAll: true })
      }
    } else {
      // 普通文本，使用多种匹配策略
      
      // 变体1: 清理后的文本
      searchVariants.push({ text: cleanSearchText, name: '清理后文本', requireAll: false })
      
      // 变体2: 移除所有空格和标点
      const noSpaces = cleanSearchText.replace(/[\s\u3000、，。！？；：""''（）【】《》]/g, '')
      if (noSpaces.length >= 3 && noSpaces !== cleanSearchText) {
        searchVariants.push({ text: noSpaces, name: '无空格标点', requireAll: false })
      }
      
      // 变体3: 提取主要关键词（最长的词）
      if (cleanSearchText.length >= 4 && allKeywords.length > 0) {
        const longestKeyword = allKeywords.reduce((a, b) => a.length > b.length ? a : b)
        if (longestKeyword.length >= 3) {
          searchVariants.push({ text: longestKeyword, name: '最长关键词', requireAll: false })
        }
      }
      
      // 变体4: 前N个字符（用于部分匹配）
      if (cleanSearchText.length >= 5) {
        const partial = cleanSearchText.substring(0, Math.min(8, cleanSearchText.length))
        searchVariants.push({ text: partial, name: '前缀匹配', requireAll: false })
      }
    }
    
    console.log('8. 搜索变体:', searchVariants.map(v => `${v.name}: "${v.text}" (requireAll: ${v.requireAll})`).join(', '))
    
    // 临时修改：强制使用AI定位（用于测试）
    // TODO: 测试完成后改回 if (hasTechName)
    console.log('🔧 临时修改：强制使用AI定位进行测试')
    if (true) {  // 原来是: if (hasTechName)
      console.log('⚠️ 跳过简单搜索，直接使用AI智能定位')
      console.log('🤖 启动AI智能定位...')
      tryAILocate(searchText, fullDocText, fullPath)
      return
    }
    
    // 下面的代码暂时不会执行（因为上面强制return了）
    /*
    // 如果包含技术名称，直接跳过简单搜索，使用AI智能定位
    if (hasTechName) {
      console.log('⚠️ 包含技术名称，跳过简单搜索，直接使用AI智能定位')
      console.log('🤖 启动AI智能定位...')
      tryAILocate(searchText, fullDocText, fullPath)
      return
    }
    */
    
    // 遍历文档查找匹配的文本
    doc.descendants((node, pos) => {
      nodeCount++
      if (found) return false // 已找到，停止遍历
      
      if (node.isText) {
        textNodeCount++
        const text = node.text.toLowerCase()
        const textNoSpaces = text.replace(/[\s\u3000、，。！？；：""''（）【】《》]/g, '')
        
        // 尝试所有搜索变体
        for (const variant of searchVariants) {
          let matchIndex = -1
          let matchLength = 0
          
          // 先尝试直接匹配
          matchIndex = text.indexOf(variant.text)
          if (matchIndex !== -1) {
            matchLength = variant.text.length
          } else if (variant.name === '无空格标点' || variant.name === '最长关键词') {
            // 对于无空格变体，也在无空格的文本中查找
            const noSpaceIndex = textNoSpaces.indexOf(variant.text)
            if (noSpaceIndex !== -1) {
              // 找到了，但需要映射回原始文本的位置
              // 简化处理：使用原始文本中第一次出现的位置
              let charCount = 0
              for (let i = 0; i < text.length; i++) {
                if (!/[\s\u3000、，。！？；：""''（）【】《》]/.test(text[i])) {
                  if (charCount === noSpaceIndex) {
                    matchIndex = i
                    // 计算实际长度（包含可能的空格和标点）
                    let actualLength = 0
                    let noSpaceCount = 0
                    for (let j = i; j < text.length && noSpaceCount < variant.text.length; j++) {
                      actualLength++
                      if (!/[\s\u3000、，。！？；：""''（）【】《》]/.test(text[j])) {
                        noSpaceCount++
                      }
                    }
                    matchLength = actualLength
                    break
                  }
                  charCount++
                }
              }
            }
          }
          
          if (matchIndex !== -1) {
            foundPos = pos + matchIndex
            foundLength = matchLength
            found = true
            console.log('✅ 找到匹配!')
            console.log('  - 匹配策略:', variant.name)
            console.log('  - 搜索文本:', variant.text)
            console.log('  - 匹配文本:', node.text.substring(matchIndex, matchIndex + matchLength))
            console.log('  - 位置:', foundPos)
            console.log('  - 长度:', foundLength)
            console.log('  - 节点文本:', node.text.substring(0, 50) + '...')
            return false // 停止遍历
          }
        }
      }
    })
    
    console.log('9. 遍历完成')
    console.log('  - 总节点数:', nodeCount)
    console.log('  - 文本节点数:', textNodeCount)
    console.log('  - 是否找到:', found)
    
    if (found && foundPos !== null) {
      console.log('10. 开始选中文本')
      
      // 选中找到的文本
      editor.value
        .chain()
        .focus()
        .setTextSelection({
          from: foundPos,
          to: foundPos + foundLength
        })
        .run()
      
      console.log('11. 文本已选中')
      
      // 滚动到可见区域
      nextTick(() => {
        const editorElement = document.querySelector('.ProseMirror')
        if (editorElement) {
          const selection = window.getSelection()
          if (selection && selection.rangeCount > 0) {
            const range = selection.getRangeAt(0)
            const rect = range.getBoundingClientRect()
            
            // 计算滚动位置，使选中的文本居中显示
            const editorRect = editorElement.getBoundingClientRect()
            const scrollTop = editorElement.scrollTop + rect.top - editorRect.top - (editorRect.height / 2) + (rect.height / 2)
            
            console.log('12. 开始滚动')
            console.log('  - 滚动位置:', scrollTop)
            
            editorElement.scrollTo({
              top: scrollTop,
              behavior: 'smooth'
            })
            
            console.log('13. 滚动完成')
          }
        }
      })
      
      toast.success(`已定位到: ${searchText}`)
      console.log('=== handleLocateInDoc 成功结束 ===')
    } else {
      console.warn('❌ 未找到匹配的文本')
      console.warn('  - 搜索文本:', searchText)
      console.warn('  - 清理后:', cleanSearchText)
      console.warn('  - 文档长度:', fullDocText.length)
      console.warn('  - 建议: 尝试AI智能定位')
      
      // 尝试AI智能定位
      console.log('🤖 启动AI智能定位...')
      tryAILocate(searchText, fullDocText, fullPath)
    }
  } catch (error) {
    console.error('❌ 定位失败:', error)
    console.error('  - 错误堆栈:', error.stack)
    toast.error('定位失败: ' + error.message)
    console.log('=== handleLocateInDoc 异常结束 ===')
  }
}

// 认证成功处理（已移除，现在在 ProjectsView 中处理）

// 选择项目
const handleSelectProject = async (project) => {
  currentProject.value = project
  currentProjectId.value = project.id
  currentView.value = 'editor'
  
  // 初始化工作区服务（使用项目ID）
  workspaceService.value = new WorkspaceService(project.id)
  workspaceDocuments.value = workspaceService.value.getAllDocuments()
  
  // 如果没有文档，自动创建一个默认文档
  if (workspaceDocuments.value.length === 0) {
    const defaultDoc = workspaceService.value.createDocument('我的第一个文档')
    workspaceDocuments.value = workspaceService.value.getAllDocuments()
    activeDocumentId.value = defaultDoc.id
    editor.value?.commands.setContent(defaultDoc.content)
    // 加载新文档的历史记录（应该为空）
    await loadChatHistory(defaultDoc.id)
    toast.info('已为您创建第一个文档')
  } else {
    // 如果有文档，加载第一个
    const firstDoc = workspaceDocuments.value[0]
    activeDocumentId.value = firstDoc.id
    editor.value?.commands.setContent(firstDoc.content)
    // 加载第一个文档的历史记录
    await loadChatHistory(firstDoc.id)
  }
  
  // 连接 WebSocket（暂时禁用，等待后端 WebSocket 服务实现）
  // TODO: 启用 WebSocket 连接用于实时 AI 对话
  // wsService.connect('ws://localhost:5000/ws')
  
  // 获取项目素材
  await fetchMaterials()
  
  // 恢复焦点
  restoreEditorFocus('end')
}

// 返回项目列表
const handleBackToProjects = () => {
  // 保存当前工作区文档
  if (activeDocumentId.value && workspaceService.value && editor.value) {
    const currentContent = editor.value.getJSON()
    if (currentContent) {
      workspaceService.value.saveDocument(activeDocumentId.value, currentContent)
    }
  }
  
  currentView.value = 'projects'
  currentProject.value = null
  currentProjectId.value = null
  materials.value = []
  chatMessages.value = []
  
  // 清理工作区服务
  workspaceService.value = null
  workspaceDocuments.value = []
  activeDocumentId.value = null
  
  // 清空编辑器
  editor.value?.commands.setContent('')
  
  // 重置样式为默认值，避免污染下一个打开的项目
  docStyles.value = [...defaultStyles]
  updateEditorStyles()
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

// ============ 工作区文档管理 ============

// 全局焦点恢复函数
const restoreEditorFocus = (position = 'end') => {
  nextTick(() => {
    // 强制窗口焦点
    window.focus()
    
    // 多次尝试设置焦点
    const focusAttempts = [0, 50, 150, 300, 500]
    let focusAchieved = false
    
    focusAttempts.forEach(delay => {
      setTimeout(() => {
        if (!focusAchieved && editor.value) {
          const editorElement = document.querySelector('.ProseMirror')
          if (editorElement) {
            // 强制窗口焦点
            window.focus()
            
            // 设置tabindex
            editorElement.setAttribute('tabindex', '0')
            
            // 直接聚焦DOM元素
            editorElement.focus()
            
            // 调用TipTap的focus命令
            editor.value.commands.focus(position)
            
            // 检查是否成功
            setTimeout(() => {
              if (document.activeElement === editorElement) {
                focusAchieved = true
              }
            }, 50)
          }
        }
      }, delay)
    })
    
    // 禁用提示覆盖层功能，因为它会干扰右键菜单
    // 如果500ms后仍未获得焦点，显示点击提示覆盖层
    // setTimeout(() => {
    //   const editorElement = document.querySelector('.ProseMirror')
    //   if (editorElement && document.activeElement !== editorElement && !focusAchieved) {
    //     showClickPrompt.value = true
    //   }
    // }, 600)
  })
}

// 点击提示覆盖层
const showClickPrompt = ref(false)

const handleEditorClick = () => {
  showClickPrompt.value = false
  const editorElement = document.querySelector('.ProseMirror')
  if (editorElement) {
    window.focus()
    editorElement.focus()
    editor.value?.commands.focus('end')
  }
}

// 处理右键菜单
const handleContextMenu = (event) => {
  // 记录事件信息
  console.log('Vue层右键菜单事件:', event)
  console.log('  - defaultPrevented:', event.defaultPrevented)
  console.log('  - cancelable:', event.cancelable)
  console.log('  - isTrusted:', event.isTrusted)
  
  // 如果默认行为被阻止，尝试恢复
  if (event.defaultPrevented) {
    console.warn('⚠️ 默认行为被阻止了！')
    
    // 停止事件传播
    event.stopImmediatePropagation()
    
    // 创建并触发新事件
    const newEvent = new MouseEvent('contextmenu', {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: event.clientX,
      clientY: event.clientY,
      screenX: event.screenX,
      screenY: event.screenY,
      button: 2,
      buttons: 2
    })
    
    setTimeout(() => {
      event.target.dispatchEvent(newEvent)
      console.log('✓ 已重新触发右键事件')
    }, 0)
  } else {
    console.log('✓ 默认行为未被阻止，菜单应该显示')
  }
  
  // 不调用preventDefault，让默认行为发生
}

// 自定义右键菜单
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })

const showCustomContextMenu = (event) => {
  event.preventDefault()
  contextMenuPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
  contextMenuVisible.value = true
}

const hideContextMenu = () => {
  contextMenuVisible.value = false
}

const handleContextMenuAction = async (action) => {
  hideContextMenu()
  
  if (!editor.value) return
  
  try {
    switch (action) {
      case 'cut':
        if (hasSelection.value) {
          const selectedText = editor.value.state.doc.textBetween(
            editor.value.state.selection.from,
            editor.value.state.selection.to
          )
          await navigator.clipboard.writeText(selectedText)
          editor.value.commands.deleteSelection()
          toast.success('已剪切')
        }
        break
        
      case 'copy':
        if (hasSelection.value) {
          const selectedText = editor.value.state.doc.textBetween(
            editor.value.state.selection.from,
            editor.value.state.selection.to
          )
          await navigator.clipboard.writeText(selectedText)
          toast.success('已复制')
        }
        break
        
      case 'paste':
        try {
          const text = await navigator.clipboard.readText()
          editor.value.commands.insertContent(text)
          toast.success('已粘贴')
        } catch (err) {
          toast.error('粘贴失败，请使用 Ctrl+V')
        }
        break
        
      case 'selectAll':
        editor.value.commands.selectAll()
        toast.success('已全选')
        break
    }
  } catch (error) {
    console.error('操作失败:', error)
    toast.error('操作失败: ' + error.message)
  }
}

// 监听键盘事件，按任意键关闭提示
const handleKeyPress = (e) => {
  if (showClickPrompt.value) {
    showClickPrompt.value = false
    const editorElement = document.querySelector('.ProseMirror')
    if (editorElement) {
      window.focus()
      editorElement.focus()
      editor.value?.commands.focus('end')
    }
  }
}

const handleSelectDocument = async (doc) => {
  console.log('=== 切换文档 ===')
  console.log('目标文档:', doc)
  console.log('当前活动文档ID:', activeDocumentId.value)
  
  // 保存当前文档
  if (activeDocumentId.value && workspaceService.value) {
    const currentContent = editor.value?.getJSON()
    console.log('保存当前文档内容:', currentContent)
    if (currentContent) {
      const saved = workspaceService.value.saveDocument(activeDocumentId.value, currentContent)
      console.log('保存结果:', saved)
    }
  }

  // 切换到新文档
  activeDocumentId.value = doc.id
  console.log('设置新文档内容:', doc.content)
  editor.value?.commands.setContent(doc.content)
  
  // 加载该文档的历史记录
  await loadChatHistory(doc.id)
  
  // 验证内容是否正确设置
  setTimeout(() => {
    const actualContent = editor.value?.getJSON()
    console.log('实际编辑器内容:', actualContent)
  }, 100)
  
  // 恢复焦点
  restoreEditorFocus('end')
  
  toast.success(`已切换到: ${doc.name}`)
  console.log('=== 切换完成 ===')
}

const handleCreateDocument = () => {
  if (!workspaceService.value) return

  const newDoc = workspaceService.value.createDocument('未命名文档')
  workspaceDocuments.value = workspaceService.value.getAllDocuments()
  activeDocumentId.value = newDoc.id
  
  // 设置内容
  editor.value?.commands.setContent(newDoc.content)
  
  // 恢复焦点
  restoreEditorFocus('start')
  
  toast.success('已创建新文档')
}

const handleRenameDocument = (docId, newName) => {
  if (!workspaceService.value) return

  try {
    workspaceService.value.renameDocument(docId, newName)
    workspaceDocuments.value = workspaceService.value.getAllDocuments()
    toast.success('重命名成功')
  } catch (error) {
    toast.error(error.message)
  }
}

const handleDeleteDocument = (docId) => {
  if (!workspaceService.value) return

  // 如果只剩一个文档，不允许删除
  if (workspaceDocuments.value.length === 1) {
    toast.warning('至少需要保留一个文档')
    return
  }

  workspaceService.value.deleteDocument(docId)
  workspaceDocuments.value = workspaceService.value.getAllDocuments()

  // 如果删除的是当前文档，切换到第一个文档
  if (activeDocumentId.value === docId) {
    const firstDoc = workspaceDocuments.value[0]
    activeDocumentId.value = firstDoc.id
    editor.value?.commands.setContent(firstDoc.content)
    
    // 立即强制激活窗口和编辑器
    // 使用 setTimeout 0 确保在 confirm 对话框关闭后执行
    setTimeout(() => {
      // 强制激活窗口
      window.focus()
      
      // 触发一个点击事件来激活窗口
      const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
      })
      document.body.dispatchEvent(clickEvent)
      
      // 恢复焦点
      restoreEditorFocus('end')
    }, 0)
  }

  toast.success('文档已删除')
}

// ============================================

// 组件挂载
onMounted(async () => {
  // 确保窗口获得焦点
  window.focus()
  
  // 等待编辑器完全初始化
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 强制启用编辑器的右键菜单 - 使用纯DOM方式
  nextTick(() => {
    const editorElement = document.querySelector('.ProseMirror')
    if (editorElement) {
      console.log('✓ 找到编辑器元素，准备启用右键菜单')
      
      // 方案：完全不添加任何监听器，让浏览器自然处理
      // 移除contenteditable可能导致的问题
      editorElement.setAttribute('oncontextmenu', 'return true;')
      
      console.log('✓ 已设置oncontextmenu属性')
      console.log('✓ 编辑器应该可以显示右键菜单了')
    } else {
      // 这是正常的，在项目列表页面时编辑器还没有加载
      console.log('ℹ️ 编辑器元素未加载（可能在项目列表页面）')
    }
  })
  
  // 注意：不再克隆元素，因为这会破坏TipTap的功能
  // 也不再添加任何contextmenu监听器
  
  // 添加窗口焦点监听器
  // 当窗口重新获得焦点时，自动恢复编辑器焦点
  const handleWindowFocus = () => {
    // 延迟一下，确保窗口完全激活
    setTimeout(() => {
      if (activeDocumentId.value && editor.value) {
        const editorElement = document.querySelector('.ProseMirror')
        if (editorElement && document.activeElement !== editorElement) {
          editorElement.focus()
          editor.value.commands.focus('end')
        }
      }
    }, 100)
  }
  
  window.addEventListener('focus', handleWindowFocus)
  
  // 添加键盘监听器
  window.addEventListener('keydown', handleKeyPress)
  
  // 点击外部关闭自定义右键菜单
  window.addEventListener('click', hideContextMenu)
  window.addEventListener('contextmenu', (e) => {
    // 如果不是在编辑器上右键，隐藏自定义菜单
    const editor = document.querySelector('.ProseMirror')
    if (editor && !editor.contains(e.target)) {
      hideContextMenu()
    }
  })
  
  // 等待编辑器完全初始化
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 注意：工作区服务现在在 handleSelectProject 中初始化
  // 这样每个项目都有独立的文档存储空间
  
  // 加载系统字体
  if (window.electronAPI && window.electronAPI.getSystemFonts) {
     try {
         const rawFonts = await window.electronAPI.getSystemFonts()
         // 简单的滤镜和映射
         const fontNameMap = {
            'Microsoft YaHei': '微软雅黑',
            'SimSun': '宋体',
            'NSimSun': '新宋体',
            'SimHei': '黑体',
            'KaiTi': '楷体',
            'FangSong': '仿宋',
            'DengXian': '等线',
            'YouYuan': '幼圆',
            'STXihei': '华文细黑',
            'STKaiti': '华文楷体',
            'STSong': '华文宋体',
            'STZhongsong': '华文中宋',
            'STFangsong': '华文仿宋'
         }
         systemFonts.value = rawFonts
             .filter(f => !f.startsWith('@'))
             .filter(f => !['Webdings', 'Wingdings', 'Marlett', 'Symbol'].includes(f))
             .map(f => {
                 const clean = f.replace(/^['"]|['"]$/g, '')
                 return {
                     label: fontNameMap[clean] || clean,
                     value: `"${clean}"`,
                     originalName: clean
                 }
             })
             .sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'))
     } catch (e) {
         console.warn('Load fonts failed', e)
     }
  } else {
     // fallback
     systemFonts.value = [
       { label: '微软雅黑', value: '"Microsoft YaHei"', originalName: 'Microsoft YaHei' },
       { label: '宋体', value: 'SimSun', originalName: 'SimSun' },
       { label: '黑体', value: 'SimHei', originalName: 'SimHei' },
       { label: '楷体', value: 'KaiTi', originalName: 'KaiTi' },
       { label: 'Arial', value: 'Arial', originalName: 'Arial' },
       { label: 'Times New Roman', value: '"Times New Roman"', originalName: 'Times New Roman' }
     ]
  }

  authStore.restoreUser()
  
  // 初始化编辑器样式
  updateEditorStyles()
  
  // 总是显示项目列表（包含登录注册）
  currentView.value = 'projects'
  
  // 检查后端连接状态
  checkBackendConnection()

  // 恢复用户设置
  const savedSettings = localStorage.getItem('user_settings')
  if (savedSettings) {
    try {
      userSettings.value = { ...userSettings.value, ...JSON.parse(savedSettings) }
    } catch (e) {}
  }
  
  // 启动自动快照
  startAutoSnapshot()
  
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
  
  window.addEventListener('mousemove', handleGlobalMouseMove)
  window.addEventListener('mouseup', handleGlobalMouseUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', handleGlobalMouseMove)
  window.removeEventListener('mouseup', handleGlobalMouseUp)
  window.removeEventListener('keydown', handleKeyPress)
  window.removeEventListener('click', hideContextMenu)
  window.removeEventListener('contextmenu', hideContextMenu)
  
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

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.3) translateY(-50px);
  }
  50% {
    transform: scale(1.05) translateY(0);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

.animate-bounce-in {
  animation: bounce-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
</style>
