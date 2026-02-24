<template>
  <div class="ai-chat-panel">
    <!-- 聊天消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', `message-${msg.role}`, { 'message-error': msg.isError }]"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else-if="msg.role === 'assistant'">🤖</span>
          <span v-else>ℹ️</span>
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      
      <!-- 加载中提示 -->
      <div v-if="isLoading" class="message message-assistant">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 知识库来源 -->
    <div v-if="sources.length > 0" class="sources-panel">
      <div class="sources-title">📚 参考来源</div>
      <div class="sources-list">
        <div
          v-for="(source, index) in sources"
          :key="index"
          class="source-item"
        >
          <div class="source-text">{{ source.text }}</div>
          <div class="source-score">相关度: {{ (source.score * 100).toFixed(0) }}%</div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <!-- 控制选项 -->
      <div class="chat-options">
        <label class="option-item">
          <input type="checkbox" v-model="enableAgent" />
          <span>Agent模式</span>
          <span class="option-tip" title="启用后AI可以执行文档操作">ℹ️</span>
        </label>
        
        <label class="option-item" :class="{ disabled: !enableAgent }">
          <input type="checkbox" v-model="autoExecute" :disabled="!enableAgent" />
          <span>自动执行</span>
          <span class="option-tip" title="AI将直接修改文档，无需确认">⚡</span>
        </label>
        
        <label class="option-item">
          <input type="checkbox" v-model="enableRag" />
          <span>知识库检索</span>
        </label>
      </div>
      
      <!-- 警告提示 -->
      <div v-if="autoExecute" class="warning-banner">
        ⚠️ 自动执行模式：AI将直接修改文档。建议先保存重要内容。
      </div>
      
      <!-- 输入框 -->
      <div class="input-wrapper">
        <textarea
          v-model="userInput"
          placeholder="输入您的需求... (Ctrl+Enter 发送)"
          @keydown.ctrl.enter="sendMessage"
          @keydown.meta.enter="sendMessage"
          :disabled="isLoading"
          rows="3"
        />
        <button
          class="send-button"
          @click="sendMessage"
          :disabled="!userInput.trim() || isLoading"
        >
          <span v-if="!isLoading">发送</span>
          <span v-else>处理中...</span>
        </button>
      </div>
      
      <!-- 快捷操作 -->
      <div class="quick-actions">
        <button @click="quickAction('生成大纲')" :disabled="isLoading">
          📝 生成大纲
        </button>
        <button @click="quickAction('扩写内容')" :disabled="isLoading">
          ✍️ 扩写内容
        </button>
        <button @click="quickAction('生成摘要')" :disabled="isLoading">
          📄 生成摘要
        </button>
        <button @click="quickAction('检查语法')" :disabled="isLoading">
          ✅ 检查语法
        </button>
      </div>
    </div>
    
    <!-- 预览对话框 -->
    <PreviewDialog
      v-if="showPreview"
      :title="previewData.title"
      :message="previewData.message"
      :content="previewData.content"
      @confirm="handlePreviewConfirm"
      @cancel="handlePreviewCancel"
    />
  </div>
</template>

<script>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useEditor } from '@/composables/useEditor'
import { chatWithAI, undoLastChange } from '@/services/ai-auto-execute'
import PreviewDialog from './PreviewDialog.vue'

export default {
  name: 'AIChatPanelWithAutoExecute',
  components: {
    PreviewDialog
  },
  props: {
    projectId: {
      type: Number,
      required: true
    },
    documentId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const { showToast } = useToast()
    const { editor } = useEditor()
    
    // 状态
    const messages = ref([])
    const sources = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const sessionId = ref(null)
    
    // 选项
    const enableAgent = ref(true)
    const autoExecute = ref(false)
    const enableRag = ref(true)
    
    // 预览对话框
    const showPreview = ref(false)
    const previewData = ref({
      title: '',
      message: '',
      content: ''
    })
    let previewResolve = null
    
    // 消息容器引用
    const messagesContainer = ref(null)
    
    // 滚动到底部
    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
      })
    }
    
    // 添加消息
    const addMessage = (role, content, isError = false) => {
      messages.value.push({
        role,
        content,
        timestamp: Date.now(),
        isError
      })
      scrollToBottom()
    }
    
    // 格式化时间
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 如果是今天
      if (diff < 86400000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      // 如果是昨天
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (date.getDate() === yesterday.getDate() && 
          date.getMonth() === yesterday.getMonth() &&
          date.getFullYear() === yesterday.getFullYear()) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      // 其他日期（显示月-日 时:分）
      return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    // 显示预览对话框
    const showPreviewDialog = (options) => {
      return new Promise((resolve) => {
        previewData.value = {
          title: options.title,
          message: options.message,
          content: options.content
        }
        showPreview.value = true
        previewResolve = resolve
      })
    }
    
    // 处理预览确认
    const handlePreviewConfirm = () => {
      showPreview.value = false
      if (previewResolve) {
        previewResolve(true)
        if (previewData.value.onConfirm) {
          previewData.value.onConfirm()
        }
      }
    }
    
    // 处理预览取消
    const handlePreviewCancel = () => {
      showPreview.value = false
      if (previewResolve) {
        previewResolve(false)
        if (previewData.value.onCancel) {
          previewData.value.onCancel()
        }
      }
    }
    
    // 发送消息
    const sendMessage = async () => {
      const message = userInput.value.trim()
      if (!message || isLoading.value) return
      
      // 添加用户消息
      addMessage('user', message)
      userInput.value = ''
      isLoading.value = true
      
      try {
        // 调用AI
        const result = await chatWithAI({
          message,
          projectId: props.projectId,
          documentId: props.documentId,
          getDocumentContent: () => editor.value?.getHTML() || '',
          setDocumentContent: (content) => {
            if (editor.value) {
              editor.value.commands.setContent(content)
            }
          },
          showNotification: (options) => {
            showToast(options.message, options.type, options.duration)
          },
          showPreviewDialog: (options) => {
            return showPreviewDialog(options)
          },
          onChatMessage: (msg) => {
            if (msg.role === 'assistant') {
              addMessage('assistant', msg.content, msg.isError)
            }
          },
          onSourcesReceived: (receivedSources) => {
            sources.value = receivedSources
          },
          autoExecute: autoExecute.value,
          enableAgent: enableAgent.value,
          sessionId: sessionId.value
        })
        
        // 保存会话ID
        if (result.sessionId) {
          sessionId.value = result.sessionId
        }
        
        // 显示token使用情况
        if (result.tokensUsed) {
          console.log(`Token使用: ${result.tokensUsed}`)
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        addMessage('system', `错误: ${error.message}`, true)
      } finally {
        isLoading.value = false
      }
    }
    
    // 快捷操作
    const quickAction = (action) => {
      userInput.value = action
      sendMessage()
    }
    
    // 撤销操作
    const handleUndo = () => {
      const lastContent = undoLastChange()
      if (lastContent && editor.value) {
        editor.value.commands.setContent(lastContent)
        showToast('已撤销', 'info')
      } else {
        showToast('没有可撤销的操作', 'warning')
      }
    }
    
    // 加载历史记录
    const loadHistory = async () => {
      console.log('开始加载历史记录...')
      console.log('documentId:', props.documentId)
      
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          console.log('未找到token，跳过加载历史记录')
          return
        }
        
        // 使用 document_id 参数过滤当前文档的历史记录
        const url = `http://localhost:5000/api/ai/history?days=3&limit=50&document_id=${props.documentId}`
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
            
            // 按时间排序（从旧到新）
            const records = data.data.records.reverse()
            
            // 添加历史记录到消息列表
            records.forEach(record => {
              // 添加用户消息
              if (record.user_message) {
                messages.value.push({
                  role: 'user',
                  content: record.user_message,
                  timestamp: new Date(record.created_at).getTime()
                })
              }
              
              // 添加AI响应
              messages.value.push({
                role: 'assistant',
                content: record.ai_response,
                timestamp: new Date(record.created_at).getTime()
              })
            })
            
            console.log(`已加载 ${messages.value.length} 条消息`)
            scrollToBottom()
          } else {
            console.log('没有找到历史记录')
          }
        } else {
          console.error('加载历史记录失败，状态码:', response.status)
        }
      } catch (error) {
        console.error('加载历史记录失败:', error)
      }
    }
    
    // 初始化
    onMounted(async () => {
      console.log('=== AI聊天组件已挂载 ===')
      console.log('projectId:', props.projectId)
      console.log('documentId:', props.documentId)
      
      // 加载历史记录
      await loadHistory()
      
      console.log('=== 组件初始化完成 ===')
    })
    
    return {
      messages,
      sources,
      userInput,
      isLoading,
      enableAgent,
      autoExecute,
      enableRag,
      showPreview,
      previewData,
      messagesContainer,
      sendMessage,
      quickAction,
      handleUndo,
      formatTime,
      handlePreviewConfirm,
      handlePreviewCancel
    }
  }
}
</script>

<style scoped>
.ai-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  background: #fff;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-user .message-content {
  background: #007bff;
  color: #fff;
}

.message-error .message-content {
  background: #ff4444;
  color: #fff;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.message-user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #007bff;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.sources-panel {
  background: #fff;
  border-top: 1px solid #e0e0e0;
  padding: 16px 20px;
}

.sources-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  padding: 8px 12px;
  background: #f9f9f9;
  border-radius: 6px;
  font-size: 14px;
}

.source-text {
  color: #666;
  margin-bottom: 4px;
}

.source-score {
  font-size: 12px;
  color: #999;
}

.chat-input-area {
  background: #fff;
  border-top: 1px solid #e0e0e0;
  padding: 16px 20px;
}

.chat-options {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
  user-select: none;
}

.option-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.option-tip {
  font-size: 12px;
  cursor: help;
}

.warning-banner {
  background: #fff3cd;
  border: 1px solid #ffc107;
  color: #856404;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.input-wrapper textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: #007bff;
}

.send-button {
  padding: 0 24px;
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #0056b3;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-actions button {
  padding: 6px 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-actions button:hover:not(:disabled) {
  background: #e0e0e0;
  border-color: #ccc;
}

.quick-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
