<template>
  <div class="workspace-panel h-full flex flex-col bg-white">
    <!-- Header -->
    <div class="p-3 border-b border-gray-200 bg-gray-50">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-gray-800 flex items-center space-x-2">
          <FolderOpen :size="16" />
          <span>工作区</span>
        </h2>
        <button
          @click="createNewDocument"
          class="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="新建文档"
        >
          <FilePlus :size="16" />
        </button>
      </div>
      <p class="text-xs text-gray-500">管理您的文档</p>
    </div>

    <!-- Document List -->
    <div class="flex-1 overflow-y-auto p-2">
      <div v-if="documents.length === 0" class="text-center text-gray-400 mt-8">
        <FileText :size="32" class="mx-auto mb-2 opacity-50" />
        <p class="text-xs">暂无文档</p>
        <p class="text-xs mt-1">点击上方 + 创建新文档</p>
      </div>

      <div
        v-for="doc in documents"
        :key="doc.id"
        @click="selectDocument(doc)"
        @contextmenu.prevent="showContextMenu($event, doc)"
        class="group relative p-2 mb-1 rounded-lg cursor-pointer transition-all"
        :class="[
          doc.id === activeDocumentId
            ? 'bg-blue-50 border border-blue-200'
            : 'hover:bg-gray-50 border border-transparent'
        ]"
      >
        <div class="flex items-start space-x-2">
          <FileText
            :size="14"
            :class="[
              doc.id === activeDocumentId ? 'text-blue-600' : 'text-gray-400'
            ]"
          />
          <div class="flex-1 min-w-0">
            <!-- 文档名称 -->
            <div v-if="editingDocId !== doc.id" class="flex items-center justify-between">
              <h3
                class="text-sm font-medium truncate"
                :class="[
                  doc.id === activeDocumentId ? 'text-blue-700' : 'text-gray-700'
                ]"
              >
                {{ doc.name }}
              </h3>
              <!-- 操作按钮 -->
              <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  @click.stop="startRename(doc)"
                  class="p-1 text-gray-400 hover:text-blue-600 rounded"
                  title="重命名"
                >
                  <Edit2 :size="12" />
                </button>
                <button
                  @click.stop="deleteDocument(doc)"
                  :disabled="documents.length === 1"
                  :class="[
                    'p-1 rounded',
                    documents.length === 1
                      ? 'text-gray-300 cursor-not-allowed'
                      : 'text-gray-400 hover:text-red-600'
                  ]"
                  :title="documents.length === 1 ? '至少需要保留一个文档' : '删除'"
                >
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>

            <!-- 重命名输入框 -->
            <input
              v-else
              v-model="editingDocName"
              @click.stop
              @keydown.enter="finishRename(doc)"
              @keydown.esc="cancelRename"
              @blur="finishRename(doc)"
              ref="renameInput"
              class="w-full px-1 py-0.5 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />

            <!-- 文档信息 -->
            <div class="flex items-center space-x-2 mt-1 text-xs text-gray-400">
              <span>{{ formatWordCount(doc.wordCount) }}</span>
              <span>•</span>
              <span>{{ formatTime(doc.updatedAt) }}</span>
            </div>
          </div>
        </div>

        <!-- 未保存标记 -->
        <div
          v-if="doc.hasUnsavedChanges"
          class="absolute top-2 right-2 w-2 h-2 bg-orange-400 rounded-full"
          title="有未保存的更改"
        ></div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="p-2 border-t border-gray-200 bg-gray-50">
      <div class="text-xs text-gray-500 text-center">
        共 {{ documents.length }} 个文档
      </div>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenuVisible"
      class="fixed bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 min-w-[160px]"
      :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
      @click.stop
    >
      <button
        @click="handleCopy"
        class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center space-x-2"
      >
        <Copy :size="14" />
        <span>复制</span>
      </button>
      <button
        @click="handleCut"
        class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center space-x-2"
      >
        <Scissors :size="14" />
        <span>剪切</span>
      </button>
      <button
        v-if="clipboardDoc"
        @click="handlePaste"
        class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center space-x-2"
      >
        <Clipboard :size="14" />
        <span>粘贴</span>
      </button>
      <div class="border-t border-gray-200 my-1"></div>
      <button
        @click="handleRename"
        class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center space-x-2"
      >
        <Edit2 :size="14" />
        <span>重命名</span>
      </button>
      <button
        @click="handleDelete"
        :disabled="documents.length === 1"
        :class="[
          'w-full px-3 py-2 text-left text-sm transition-colors flex items-center space-x-2',
          documents.length === 1
            ? 'text-gray-400 cursor-not-allowed'
            : 'hover:bg-red-50 hover:text-red-600'
        ]"
        :title="documents.length === 1 ? '至少需要保留一个文档' : '删除'"
      >
        <Trash2 :size="14" />
        <span>删除</span>
      </button>
    </div>

    <!-- 删除确认对话框 -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100]"
      @click.self="cancelDelete"
    >
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4 animate-scale-in">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">确认删除</h3>
        <p class="text-gray-600 mb-6">
          确定要删除文档 <span class="font-medium text-gray-900">"{{ deleteTarget?.name }}"</span> 吗？
        </p>
        <div class="flex justify-end space-x-3">
          <button
            @click="cancelDelete"
            class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="confirmDelete"
            class="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { FolderOpen, FileText, FilePlus, Edit2, Trash2, Copy, Scissors, Clipboard } from 'lucide-vue-next'

const props = defineProps({
  documents: {
    type: Array,
    default: () => []
  },
  activeDocumentId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['select-document', 'create-document', 'rename-document', 'delete-document'])

const editingDocId = ref(null)
const editingDocName = ref('')
const renameInput = ref(null)

// 删除确认对话框状态
const showDeleteConfirm = ref(false)
const deleteTarget = ref(null)

// 右键菜单状态
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuDoc = ref(null)
const clipboardDoc = ref(null) // 剪贴板中的文档
const clipboardAction = ref('') // 'copy' 或 'cut'

const selectDocument = (doc) => {
  emit('select-document', doc)
}

const createNewDocument = () => {
  emit('create-document')
}

const startRename = (doc) => {
  editingDocId.value = doc.id
  editingDocName.value = doc.name
  nextTick(() => {
    if (renameInput.value) {
      renameInput.value.focus()
      renameInput.value.select()
    }
  })
}

const finishRename = (doc) => {
  if (editingDocName.value.trim() && editingDocName.value !== doc.name) {
    emit('rename-document', doc.id, editingDocName.value.trim())
  }
  editingDocId.value = null
  editingDocName.value = ''
}

const cancelRename = () => {
  editingDocId.value = null
  editingDocName.value = ''
}

const deleteDocument = (doc) => {
  // 如果只剩一个文档，不允许删除
  if (props.documents.length === 1) {
    return
  }
  
  // 显示自定义删除确认对话框
  deleteTarget.value = doc
  showDeleteConfirm.value = true
}

// 确认删除
const confirmDelete = () => {
  if (deleteTarget.value) {
    emit('delete-document', deleteTarget.value.id)
  }
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

// 取消删除
const cancelDelete = () => {
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

// 显示右键菜单
const showContextMenu = (event, doc) => {
  contextMenuDoc.value = doc
  contextMenuPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
  contextMenuVisible.value = true
}

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenuVisible.value = false
  contextMenuDoc.value = null
}

// 复制文档
const handleCopy = () => {
  if (contextMenuDoc.value) {
    clipboardDoc.value = { ...contextMenuDoc.value }
    clipboardAction.value = 'copy'
    console.log('已复制文档:', contextMenuDoc.value.name)
  }
  hideContextMenu()
}

// 剪切文档
const handleCut = () => {
  if (contextMenuDoc.value) {
    clipboardDoc.value = { ...contextMenuDoc.value }
    clipboardAction.value = 'cut'
    console.log('已剪切文档:', contextMenuDoc.value.name)
  }
  hideContextMenu()
}

// 粘贴文档
const handlePaste = () => {
  if (clipboardDoc.value) {
    if (clipboardAction.value === 'copy') {
      // 复制：创建新文档
      const newName = `${clipboardDoc.value.name} (副本)`
      emit('create-document', newName, clipboardDoc.value.content)
      console.log('已粘贴文档:', newName)
    } else if (clipboardAction.value === 'cut') {
      // 剪切：移动文档（这里简化为重命名）
      console.log('剪切操作完成')
      clipboardDoc.value = null
      clipboardAction.value = ''
    }
  }
  hideContextMenu()
}

// 重命名
const handleRename = () => {
  if (contextMenuDoc.value) {
    startRename(contextMenuDoc.value)
  }
  hideContextMenu()
}

// 删除
const handleDelete = () => {
  if (contextMenuDoc.value) {
    // 如果只剩一个文档，不允许删除
    if (props.documents.length === 1) {
      hideContextMenu()
      return
    }
    deleteDocument(contextMenuDoc.value)
  }
  hideContextMenu()
}

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (contextMenuVisible.value) {
    hideContextMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

const formatWordCount = (count) => {
  if (count === 0) return '空文档'
  if (count < 1000) return `${count} 字`
  return `${(count / 1000).toFixed(1)}k 字`
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  // 小于1分钟
  if (diff < 60000) return '刚刚'
  // 小于1小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  // 小于1天
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  // 小于7天
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  // 超过7天显示日期
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.workspace-panel {
  user-select: none;
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scale-in {
  animation: scale-in 0.2s ease-out;
}
</style>
