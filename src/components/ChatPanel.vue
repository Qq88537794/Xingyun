<template>
  <div class="chat-panel w-80 bg-white border-l border-gray-200 flex flex-col">
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-800">AI 助手</h2>
      <p class="text-xs text-gray-500 mt-1">与 AI 对话，优化您的文档</p>
    </div>
    
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
        <div v-if="message.role === 'assistant'" class="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-100">
          <button 
            @click="handleInsertToDoc(message.content)"
            class="text-xs text-gray-500 hover:text-blue-600 flex items-center space-x-1"
          >
            <FileInput :size="12" />
            <span>插入文档</span>
          </button>
          <button 
            @click="handleCopy(message.content)"
            class="text-xs text-gray-500 hover:text-blue-600 flex items-center space-x-1"
          >
            <Copy :size="12" />
            <span>复制</span>
          </button>
        </div>
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
      <!-- 上下文提示 -->
      <div v-if="hasSelection" class="mb-2 px-2 py-1 bg-blue-50 rounded text-xs text-blue-600 flex items-center">
        <FileText :size="12" class="mr-1" />
        已选中文本将作为上下文
      </div>
      
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
import { ref, nextTick, watch } from 'vue'
import { MessageSquare, Send, User, Bot, Loader2, FileInput, Copy, FileText, AlertCircle } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isConnected: {
    type: Boolean,
    default: false
  },
  hasSelection: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send-message', 'insert-to-doc'])

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

// 监听消息变化，自动滚动到底部
watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
})

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

// 简单的 Markdown 渲染
const renderMessage = (content) => {
  if (!content) return ''
  
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
    .replace(/\n/g, '<br>')
}

const handleInsertToDoc = (content) => {
  emit('insert-to-doc', content)
  toast.success('已插入到文档')
}

const handleCopy = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    toast.success('已复制到剪贴板')
  } catch (err) {
    toast.error('复制失败')
  }
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
