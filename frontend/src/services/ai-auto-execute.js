/**
 * AI自动执行模式服务
 * 提供完整的AI请求和响应处理功能
 */

import { api } from './api'

// 文档历史记录（用于撤销）
const documentHistory = []
const MAX_HISTORY = 20

/**
 * 保存文档到历史记录
 * @param {string} content - 文档内容
 */
export function saveToHistory(content) {
  documentHistory.push({
    content: content,
    timestamp: Date.now()
  })
  
  // 限制历史记录数量
  if (documentHistory.length > MAX_HISTORY) {
    documentHistory.shift()
  }
}

/**
 * 撤销上一次修改
 * @returns {string|null} 上一次的文档内容，如果没有则返回null
 */
export function undoLastChange() {
  if (documentHistory.length === 0) {
    return null
  }
  
  const lastState = documentHistory.pop()
  return lastState.content
}

/**
 * 清空历史记录
 */
export function clearHistory() {
  documentHistory.length = 0
}

/**
 * 判断是否应该自动执行
 * @param {string} userInput - 用户输入
 * @returns {boolean}
 */
export function shouldAutoExecute(userInput) {
  // 明确要求直接修改的关键词
  const autoExecuteKeywords = [
    '直接', '自动', '帮我', '立即',
    '马上', '现在就', '不用确认', '直接应用'
  ]
  
  // 需要谨慎的操作关键词
  const cautiousKeywords = [
    '删除全部', '清空', '重写全部', '完全替换', '删除所有'
  ]
  
  const input = userInput.toLowerCase()
  
  // 如果包含谨慎关键词，不自动执行
  if (cautiousKeywords.some(kw => input.includes(kw))) {
    return false
  }
  
  // 如果包含自动执行关键词，启用自动执行
  if (autoExecuteKeywords.some(kw => input.includes(kw))) {
    return true
  }
  
  // 默认不自动执行（更安全）
  return false
}

/**
 * 检测是否为危险操作
 * @param {string} message - 用户消息
 * @returns {boolean}
 */
export function isDangerousOperation(message) {
  const dangerousPatterns = [
    /删除.*全部/,
    /清空/,
    /重写.*全部/,
    /完全.*替换/,
    /删除.*所有/
  ]
  
  return dangerousPatterns.some(pattern => pattern.test(message))
}

/**
 * 发送AI请求
 * @param {Object} options - 请求选项
 * @param {string} options.message - 用户消息
 * @param {number} options.projectId - 项目ID
 * @param {string} options.documentContent - 当前文档内容
 * @param {string} options.documentId - 文档ID
 * @param {string} [options.selectedText] - 选中的文本
 * @param {Object} [options.selectionRange] - 选中范围
 * @param {boolean} [options.enableAgent=true] - 是否启用Agent模式
 * @param {boolean} [options.autoExecute=false] - 是否自动执行
 * @param {boolean} [options.enableRag=true] - 是否启用RAG
 * @param {string} [options.sessionId] - 会话ID
 * @returns {Promise<Object>} AI响应
 */
export async function sendAIRequest(options) {
  const {
    message,
    projectId,
    documentContent,
    documentId,
    selectedText,
    selectionRange,
    enableAgent = true,
    autoExecute = false,
    enableRag = true,
    sessionId
  } = options
  
  // 验证必需参数
  if (!message || !message.trim()) {
    throw new Error('消息不能为空')
  }
  
  // 构建请求体
  const requestBody = {
    message: message.trim(),
    project_id: projectId,
    document_content: documentContent,
    document_id: documentId,
    enable_agent: enableAgent,
    auto_execute: autoExecute,
    enable_rag: enableRag
  }
  
  // 可选参数
  if (selectedText) {
    requestBody.selected_text = selectedText
  }
  
  if (selectionRange) {
    requestBody.selection_range = selectionRange
  }
  
  if (sessionId) {
    requestBody.session_id = sessionId
  }
  
  // 发送请求
  const response = await api.post('/ai/chat', requestBody)
  
  if (response.code !== 200) {
    throw new Error(response.message || 'AI请求失败')
  }
  
  return response.data
}

/**
 * 处理AI响应
 * @param {Object} data - AI响应数据
 * @param {Function} editorSetContent - 编辑器设置内容的函数
 * @param {Function} showNotification - 显示通知的函数
 * @param {Function} showPreviewDialog - 显示预览对话框的函数
 * @returns {Object} 处理结果
 */
export function handleAIResponse(data, editorSetContent, showNotification, showPreviewDialog) {
  const result = {
    success: false,
    autoExecuted: false,
    message: data.message
  }
  
  try {
    // 1. 检查是否自动执行
    if (data.auto_executed && data.executed_content) {
      // 自动执行模式：直接应用
      editorSetContent(data.executed_content)
      
      showNotification({
        message: `✅ ${data.message}`,
        type: 'success',
        duration: 5000,
        action: {
          text: '撤销',
          onClick: () => {
            const lastContent = undoLastChange()
            if (lastContent) {
              editorSetContent(lastContent)
              showNotification({
                message: '已撤销',
                type: 'info'
              })
            }
          }
        }
      })
      
      result.success = true
      result.autoExecuted = true
      
      console.log('AI自动执行完成:', {
        iterations: data.metadata?.agent_iterations,
        toolCalls: data.metadata?.agent_tool_calls?.length
      })
    }
    // 2. 检查是否需要手动确认
    else if (data.requires_confirmation && data.operations && data.operations.length > 0) {
      const operation = data.operations[0]
      
      // 显示预览对话框
      showPreviewDialog({
        title: '预览AI生成的内容',
        message: data.message,
        content: operation.content,
        operationType: operation.operation_type,
        onConfirm: () => {
          // 用户确认后应用
          saveToHistory(editorSetContent())  // 保存当前内容
          editorSetContent(operation.content)
          
          showNotification({
            message: '已应用修改',
            type: 'success'
          })
          
          result.success = true
        },
        onCancel: () => {
          console.log('用户取消了操作')
        }
      })
      
      result.success = true
    }
    // 3. 仅回复，无操作
    else {
      result.success = true
    }
    
    return result
  } catch (error) {
    console.error('处理AI响应失败:', error)
    showNotification({
      message: `处理失败: ${error.message}`,
      type: 'error'
    })
    
    return result
  }
}

/**
 * 完整的AI聊天流程（推荐使用）
 * @param {Object} options - 选项
 * @param {string} options.message - 用户消息
 * @param {number} options.projectId - 项目ID
 * @param {Function} options.getDocumentContent - 获取文档内容的函数
 * @param {Function} options.setDocumentContent - 设置文档内容的函数
 * @param {string} options.documentId - 文档ID
 * @param {Function} options.showNotification - 显示通知的函数
 * @param {Function} options.showPreviewDialog - 显示预览对话框的函数
 * @param {Function} [options.onChatMessage] - 聊天消息回调
 * @param {Function} [options.onSourcesReceived] - 知识库来源回调
 * @param {boolean} [options.autoExecute] - 是否自动执行（可选，会自动判断）
 * @param {boolean} [options.enableAgent=true] - 是否启用Agent
 * @param {string} [options.sessionId] - 会话ID
 * @returns {Promise<Object>} 处理结果
 */
export async function chatWithAI(options) {
  const {
    message,
    projectId,
    getDocumentContent,
    setDocumentContent,
    documentId,
    showNotification,
    showPreviewDialog,
    onChatMessage,
    onSourcesReceived,
    autoExecute,
    enableAgent = true,
    sessionId
  } = options
  
  try {
    // 1. 获取当前文档内容
    const documentContent = getDocumentContent()
    
    // 2. 保存到历史（用于撤销）
    saveToHistory(documentContent)
    
    // 3. 判断是否自动执行（如果未指定）
    const shouldAuto = autoExecute !== undefined 
      ? autoExecute 
      : shouldAutoExecute(message)
    
    // 4. 危险操作二次确认
    let finalAutoExecute = shouldAuto
    if (shouldAuto && isDangerousOperation(message)) {
      const confirmed = confirm(
        '此操作将对文档进行重大修改，是否继续自动执行？\n' +
        '点击"取消"将切换为预览模式。'
      )
      
      if (!confirmed) {
        finalAutoExecute = false
      }
    }
    
    // 5. 发送AI请求
    const data = await sendAIRequest({
      message,
      projectId,
      documentContent,
      documentId,
      enableAgent,
      autoExecute: finalAutoExecute,
      sessionId
    })
    
    // 6. 显示AI回复消息
    if (onChatMessage) {
      onChatMessage({
        role: 'assistant',
        content: data.message,
        timestamp: Date.now()
      })
    }
    
    // 7. 处理文档操作
    const result = handleAIResponse(
      data,
      setDocumentContent,
      showNotification,
      showPreviewDialog
    )
    
    // 8. 显示知识库来源
    if (data.sources && data.sources.length > 0 && onSourcesReceived) {
      onSourcesReceived(data.sources)
    }
    
    return {
      ...result,
      sessionId: data.session_id,
      tokensUsed: data.tokens_used,
      sources: data.sources
    }
    
  } catch (error) {
    console.error('AI聊天失败:', error)
    
    showNotification({
      message: `请求失败: ${error.message}`,
      type: 'error'
    })
    
    if (onChatMessage) {
      onChatMessage({
        role: 'system',
        content: `错误: ${error.message}`,
        timestamp: Date.now(),
        isError: true
      })
    }
    
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 获取聊天历史
 * @param {string} sessionId - 会话ID
 * @param {number} [limit=50] - 限制数量
 * @returns {Promise<Object>} 聊天历史
 */
export async function getChatHistory(sessionId, limit = 50) {
  const response = await api.get('/ai/chat/history', {
    params: { session_id: sessionId, limit }
  })
  
  if (response.code !== 200) {
    throw new Error(response.message || '获取历史失败')
  }
  
  return response.data
}

/**
 * 删除聊天会话
 * @param {string} sessionId - 会话ID
 * @returns {Promise<void>}
 */
export async function deleteChatSession(sessionId) {
  const response = await api.delete(`/ai/chat/sessions/${sessionId}`)
  
  if (response.code !== 200) {
    throw new Error(response.message || '删除会话失败')
  }
}

export default {
  sendAIRequest,
  handleAIResponse,
  chatWithAI,
  getChatHistory,
  deleteChatSession,
  saveToHistory,
  undoLastChange,
  clearHistory,
  shouldAutoExecute,
  isDangerousOperation
}
