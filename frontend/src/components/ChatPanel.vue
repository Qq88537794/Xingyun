<template>
  <div class="chat-panel h-full flex flex-col">
    <!-- Header (Optional if using Tabs in App.vue, but nice to keep context info) -->
    <!-- 
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-800">AI 助手</h2>
      <p class="text-xs text-gray-500 mt-1">与 AI 对话，优化您的文档</p>
    </div>
    -->
    
    <!-- 快捷指令 -->
    <div class="px-3 py-2 border-b border-gray-200 bg-gray-50">
      <p class="text-xs text-gray-500 mb-2">快捷指令</p>
      <div class="flex flex-wrap gap-1">
        <button 
          v-for="cmd in quickCommands" 
          :key="cmd.id"
          @click="sendQuickCommand(cmd.prompt)"
          class="px-2 py-1 text-xs bg-white border border-gray-200 text-gray-600 rounded hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-colors"
        >
          {{ cmd.label }}
        </button>
      </div>
    </div>
    
    <!-- 消息列表 -->
    <div ref="messageContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div v-if="messages.length === 0" class="text-center text-gray-400 mt-8">
        <MessageSquare :size="48" class="mx-auto mb-2 opacity-50" />
        <p class="text-sm">开始与 AI 对话</p>
        <p class="text-xs mt-2">点击上方快捷指令或输入问题</p>
      </div>
      
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        :class="['message', message.role === 'user' ? 'message-user' : 'message-assistant']"
      >
        <!-- 加载状态消息 -->
        <div v-if="message.isLoading" class="flex items-center space-x-2">
          <Loader2 :size="16" class="animate-spin text-purple-500" />
          <span class="text-sm text-gray-500">AI 正在思考...</span>
        </div>
        
        <!-- 普通消息 -->
        <template v-else>
          <div class="message-header">
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                message.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
              ]">
                <User v-if="message.role === 'user'" :size="14" />
                <Bot v-else :size="14" />
              </div>
              <span class="text-xs font-medium">
                {{ message.role === 'user' ? '你' : 'AI 助手' }}
              </span>
            </div>
            <span class="text-xs text-gray-400">
              {{ formatTime(message.timestamp) }}
            </span>
          </div>
          <div class="message-content" v-html="renderMessage(message.content)"></div>
          
          <!-- AI 消息操作按钮 -->
          <div v-if="message.role === 'assistant' && !message.isLoading" class="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-100">
            <button 
              @click="handleInsertToDoc(message.content)"
              class="text-xs text-gray-500 hover:text-blue-600 flex items-center space-x-1"
              title="插入到当前文档"
            >
              <FileInput :size="12" />
              <span>插入文档</span>
            </button>
            <button 
              @click="handleSaveAsNewDoc(message.content)"
              class="text-xs text-gray-500 hover:text-green-600 flex items-center space-x-1"
              title="另存为新文档"
            >
              <FilePlus :size="12" />
              <span>另存为新文档</span>
            </button>
            <button 
              @click="handleCopy(message.content)"
              class="text-xs text-gray-500 hover:text-gray-600 flex items-center space-x-1"
              title="复制到剪贴板"
            >
              <Copy :size="12" />
              <span>复制</span>
            </button>
          </div>
        </template>
      </div>
      
      <!-- 加载中状态 -->
      <div v-if="isLoading" class="message message-assistant">
        <div class="flex items-center space-x-2">
          <Loader2 :size="16" class="animate-spin text-purple-500" />
          <span class="text-sm text-gray-500">AI 正在思考...</span>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="p-4 border-t border-gray-200">
      <!-- 上下文管理器 -->
      <ContextManager
        :contexts="contexts"
        @remove="removeContext"
        @clear="clearContexts"
      />
      
      <div class="flex space-x-2">
        <textarea 
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="() => {}"
          placeholder="输入消息... (Shift+Enter 换行)"
          rows="1"
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none"
          :class="{ 'ring-2 ring-yellow-400': !isConnected }"
        ></textarea>
        <button 
          @click="sendMessage"
          :disabled="!inputMessage.trim()"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send :size="16" />
        </button>
      </div>
      
      <!-- 连接状态提示 -->
      <div v-if="!isConnected" class="mt-2 text-xs text-yellow-600 flex items-center">
        <AlertCircle :size="12" class="mr-1" />
        未连接到后端，消息将在本地模拟响应
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { MessageSquare, Send, User, Bot, Loader2, FileInput, Copy, FileText, AlertCircle, FilePlus } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import ContextManager from './ContextManager.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isConnected: {
    type: Boolean,
    default: false
  },
  contexts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['send-message', 'insert-to-doc', 'save-as-new-doc', 'remove-context', 'clear-contexts', 'locate-in-doc'])

const toast = useToast()
const inputMessage = ref('')
const isLoading = ref(false)
const messageContainer = ref(null)

// 快捷指令
const quickCommands = [
  { id: 1, label: '生成大纲', prompt: '根据当前文档内容生成详细大纲' },
  { id: 2, label: '润色文字', prompt: '优化当前选中内容的表达，使其更加流畅专业' },
  { id: 3, label: '扩展内容', prompt: '扩展当前选中的内容，增加更多细节' },
  { id: 4, label: '生成摘要', prompt: '生成当前文档的摘要' },
  { id: 5, label: '检查语法', prompt: '检查文档中的语法和拼写错误' },
  { id: 6, label: '翻译英文', prompt: '将选中内容翻译成英文' }
]

// 处理大纲项点击 - 使用事件委托
const handleOutlineClick = (event) => {
  console.log('=== handleOutlineClick 触发 ===')
  console.log('event.target:', event.target)
  console.log('event.target.className:', event.target.className)
  
  const target = event.target.closest('.outline-item, .outline-subitem')
  console.log('找到的目标元素:', target)
  
  if (target) {
    const searchText = target.getAttribute('data-search-text')
    const fullPath = target.getAttribute('data-full-path')
    
    console.log('data-search-text:', searchText)
    console.log('data-full-path:', fullPath)
    
    if (searchText) {
      console.log('准备定位文本:', searchText)
      console.log('完整路径:', fullPath)
      
      // 发送定位请求，包含完整路径信息
      emit('locate-in-doc', {
        searchText: searchText,
        fullPath: fullPath || searchText  // 如果没有完整路径，使用searchText
      })
      toast.info(`正在定位: ${searchText}`)
      
      console.log('已发送 locate-in-doc 事件')
    } else {
      console.warn('未找到 data-search-text 属性')
    }
  } else {
    console.log('未找到 .outline-item 或 .outline-subitem 元素')
  }
  
  console.log('=== handleOutlineClick 结束 ===')
}

// 在组件挂载时绑定事件监听器
onMounted(() => {
  console.log('ChatPanel 组件已挂载，绑定大纲点击事件')
  if (messageContainer.value) {
    messageContainer.value.addEventListener('click', handleOutlineClick)
    console.log('✅ 大纲点击事件已绑定到 messageContainer')
  }
})

// 在组件卸载时移除事件监听器
onUnmounted(() => {
  console.log('ChatPanel 组件卸载，移除大纲点击事件')
  if (messageContainer.value) {
    messageContainer.value.removeEventListener('click', handleOutlineClick)
  }
})

// 监听消息变化，自动滚动到底部
watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
})

// 监听消息变化，重新绑定大纲点击事件
watch(() => props.messages, () => {
  nextTick(() => {
    if (messageContainer.value) {
      // 重新绑定事件（确保新消息的大纲项可以点击）
      messageContainer.value.removeEventListener('click', handleOutlineClick)
      messageContainer.value.addEventListener('click', handleOutlineClick)
      console.log('✅ 大纲点击事件已重新绑定（消息更新）')
    }
  })
}, { deep: true })

const sendMessage = () => {
  if (inputMessage.value.trim()) {
    emit('send-message', inputMessage.value)
    inputMessage.value = ''
    
    // 模拟加载状态
    if (!props.isConnected) {
      isLoading.value = true
      setTimeout(() => {
        isLoading.value = false
      }, 1500)
    }
  }
}

const sendQuickCommand = (prompt) => {
  emit('send-message', prompt)
  
  if (!props.isConnected) {
    isLoading.value = true
    setTimeout(() => {
      isLoading.value = false
    }, 1500)
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 增强的 Markdown 渲染 - 支持交互式大纲
const renderMessage = (content) => {
  // 处理各种空值情况
  if (content === null || content === undefined) {
    console.warn('renderMessage收到null/undefined内容')
    return '<span class="text-gray-400 italic">（空内容）</span>'
  }
  
  // 转换为字符串
  const text = String(content)
  
  // 如果是空字符串
  if (text.trim() === '') {
    console.warn('renderMessage收到空字符串')
    return '<span class="text-gray-400 italic">（空内容）</span>'
  }
  
  // 转义HTML特殊字符，防止XSS
  const escapeHtml = (str) => {
    const div = document.createElement('div')
    div.textContent = str
    return div.innerHTML
  }
  
  // 检测是否是大纲格式（包含编号的列表）
  // 支持格式：1. 标题、1.1 标题、3.标题（无空格）、- 标题、• 标题
  // 允许行首有空格（缩进）
  const isOutline = /^\s*(\d+(?:\.\d+)*\.?[\s\u3000]*\S|[-•][\s\u3000]+\S)/m.test(text)
  
  console.log('renderMessage 调试:', {
    textLength: text.length,
    textPreview: text.substring(0, 100),
    isOutline: isOutline,
    hasNewlines: text.includes('\n')
  })
  
  if (isOutline) {
    console.log('✅ 检测到大纲格式，开始渲染...')
    
    const outlineItems = []
    
    // 处理大纲格式，使其可点击
    // 注意：在原始文本上进行匹配，然后转义
    const html = text.split('\n').map((line, lineIndex) => {
      // 匹配大纲项：1. 标题、1.1 标题、1.1.1 标题、- 标题、• 标题
      // 支持中文空格和普通空格，允许行首有缩进
      // 修复：数字后的空格改为可选，支持 "3.标题" 和 "3. 标题" 两种格式
      const outlineMatch = line.match(/^(\s*)(\d+(?:\.\d+)*\.?[\s\u3000]*|[-•][\s\u3000]+)(.+)$/)
      if (outlineMatch) {
        const [, indent, prefix, fullTitle] = outlineMatch
        
        // 清理标题（移除可能的标记）
        let title = fullTitle.trim()
        
        // 移除可能残留的 @@SOURCE 标记
        title = title.replace(/\s*@@SOURCE:"[^"]*"@@/g, '')
        
        // 移除可能的 (原文: ...) 标记
        title = title.replace(/\s*\(原文[:：]\s*["""'][^"""']*["""']\s*\)/g, '')
        
        // 构建完整的大纲路径（包含编号和标题）
        // 例如："8.1 NAS的典型应用场景" 而不是只有 "NAS的典型应用场景"
        const fullOutlinePath = `${prefix.trim()} ${title}`
        
        // 记录大纲项用于调试
        outlineItems.push({
          line: lineIndex + 1,
          indent: indent.length,
          prefix: prefix.trim(),
          title: title,
          fullPath: fullOutlinePath
        })
        
        // 根据缩进决定是主项还是子项
        const isSubItem = indent.length >= 2
        const className = isSubItem ? 'outline-subitem' : 'outline-item'
        
        // 保存完整路径用于AI定位
        // data-search-text 保存标题（用于简单搜索）
        // data-full-path 保存完整路径（用于AI智能定位）
        return `<div class="${className}" data-search-text="${escapeHtml(title)}" data-full-path="${escapeHtml(fullOutlinePath)}">
          <span class="outline-prefix">${escapeHtml(prefix)}</span>
          <span class="outline-title">${escapeHtml(title)}</span>
        </div>`
      }
      
      // 普通文本行
      return line ? `<div class="outline-text">${escapeHtml(line)}</div>` : '<br>'
    }).join('\n')
    
    console.log(`✅ 大纲HTML已生成，共 ${outlineItems.length} 个大纲项`)
    console.log('大纲项列表:', outlineItems)
    console.log('HTML预览:', html.substring(0, 300))
    
    return html
  } else {
    // 处理普通Markdown格式
    // 先转义，再处理Markdown
    let html = escapeHtml(text)
    html = html
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
      .replace(/\n/g, '<br>')
    
    return html
  }
}

const handleInsertToDoc = (content) => {
  emit('insert-to-doc', content)
  toast.success('已插入到文档')
}

const handleSaveAsNewDoc = (content) => {
  emit('save-as-new-doc', content)
  toast.success('已创建新文档')
}

const handleCopy = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    toast.success('已复制到剪贴板')
  } catch (err) {
    toast.error('复制失败')
  }
}

const removeContext = (index) => {
  emit('remove-context', index)
}

const clearContexts = () => {
  emit('clear-contexts')
}
</script>

<style scoped>
.message {
  @apply rounded-lg p-3;
}

.message-user {
  @apply bg-blue-50 ml-4;
}

.message-assistant {
  @apply bg-gray-50 mr-4;
}

.message-header {
  @apply flex items-center justify-between mb-2;
}

.message-content {
  @apply text-sm text-gray-800 leading-relaxed;
}
</style>

<style>
/* 交互式大纲样式 - 使用全局样式确保可以应用到动态生成的HTML */
.message-content .outline-item,
.message-content .outline-subitem {
  padding: 0.25rem 0.5rem;
  margin: 0.25rem 0;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.message-content .outline-item:hover,
.message-content .outline-subitem:hover {
  background-color: #eff6ff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.message-content .outline-item {
  font-weight: 500;
}

.message-content .outline-subitem {
  margin-left: 1rem;
  font-size: 0.875rem;
}

.message-content .outline-prefix {
  color: #6b7280;
  margin-right: 0.5rem;
  font-family: monospace;
}

.message-content .outline-title {
  color: #374151;
}

.message-content .outline-item:hover .outline-title,
.message-content .outline-subitem:hover .outline-title {
  color: #2563eb;
}

.message-content .outline-item:active,
.message-content .outline-subitem:active {
  background-color: #dbeafe;
}

.message-content .outline-text {
  color: #4b5563;
  font-size: 0.875rem;
  padding: 0.125rem 0;
}
</style>
