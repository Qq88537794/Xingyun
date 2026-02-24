<template>
  <div class="ai-history-panel">
    <!-- 头部 -->
    <div class="history-header">
      <h3>AI对话历史</h3>
      <div class="header-actions">
        <select v-model="filterType" @change="loadHistory" class="filter-select">
          <option value="">全部类型</option>
          <option value="chat">聊天</option>
          <option value="outline">生成大纲</option>
          <option value="expand">扩展内容</option>
          <option value="locate">智能定位</option>
          <option value="edit">编辑文档</option>
        </select>
        <select v-model="filterDays" @change="loadHistory" class="filter-select">
          <option value="1">最近1天</option>
          <option value="3">最近3天</option>
          <option value="7">最近7天</option>
        </select>
        <button @click="loadHistory" class="refresh-btn" :disabled="loading">
          <span v-if="!loading">🔄 刷新</span>
          <span v-else>加载中...</span>
        </button>
      </div>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list" v-if="!loading && historyRecords.length > 0">
      <div 
        v-for="record in historyRecords" 
        :key="record.id"
        class="history-item"
        :class="`type-${record.request_type}`"
      >
        <div class="item-header">
          <span class="item-type">{{ getTypeLabel(record.request_type) }}</span>
          <span class="item-time">{{ formatTime(record.created_at) }}</span>
        </div>
        
        <div class="item-content">
          <div class="user-message" v-if="record.user_message">
            <strong>用户:</strong> {{ record.user_message }}
          </div>
          <div class="ai-response">
            <strong>AI:</strong> {{ truncateText(record.ai_response, 200) }}
          </div>
        </div>
        
        <div class="item-footer">
          <span v-if="record.tokens_used > 0" class="tokens">
            🪙 {{ record.tokens_used }} tokens
          </span>
          <span v-if="record.session_id" class="session">
            💬 会话: {{ record.session_id.substring(0, 8) }}
          </span>
          <button @click="viewDetail(record)" class="view-btn">查看详情</button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && historyRecords.length === 0" class="empty-state">
      <p>📝 暂无历史记录</p>
      <p class="empty-hint">开始使用AI功能后，历史记录会自动保存在这里</p>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading-state">
      <p>⏳ 加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="loadHistory" class="retry-btn">重试</button>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="selectedRecord" class="detail-modal" @click.self="closeDetail">
      <div class="detail-content">
        <div class="detail-header">
          <h4>{{ getTypeLabel(selectedRecord.request_type) }} - 详情</h4>
          <button @click="closeDetail" class="close-btn">✕</button>
        </div>
        
        <div class="detail-body">
          <div class="detail-section">
            <label>时间:</label>
            <p>{{ formatFullTime(selectedRecord.created_at) }}</p>
          </div>
          
          <div class="detail-section" v-if="selectedRecord.user_message">
            <label>用户消息:</label>
            <p class="message-text">{{ selectedRecord.user_message }}</p>
          </div>
          
          <div class="detail-section">
            <label>AI响应:</label>
            <p class="message-text">{{ selectedRecord.ai_response }}</p>
          </div>
          
          <div class="detail-section" v-if="selectedRecord.tokens_used > 0">
            <label>Token使用:</label>
            <p>{{ selectedRecord.tokens_used }} tokens</p>
          </div>
          
          <div class="detail-section" v-if="selectedRecord.session_id">
            <label>会话ID:</label>
            <p>{{ selectedRecord.session_id }}</p>
          </div>
        </div>
        
        <div class="detail-footer">
          <button @click="closeDetail" class="close-detail-btn">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

export default {
  name: 'AIHistoryPanel',
  
  data() {
    return {
      historyRecords: [],
      loading: false,
      error: null,
      filterType: '',
      filterDays: '3',
      selectedRecord: null
    }
  },
  
  mounted() {
    this.loadHistory()
  },
  
  methods: {
    async loadHistory() {
      this.loading = true
      this.error = null
      
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          this.error = '请先登录'
          return
        }
        
        const params = {
          days: this.filterDays,
          limit: 100
        }
        
        if (this.filterType) {
          params.request_type = this.filterType
        }
        
        const response = await axios.get(`${API_BASE_URL}/api/ai/history`, {
          params,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (response.data.code === 200) {
          this.historyRecords = response.data.data.records
        } else {
          this.error = response.data.message || '加载失败'
        }
      } catch (err) {
        console.error('加载历史记录失败:', err)
        this.error = err.response?.data?.message || '加载失败，请重试'
      } finally {
        this.loading = false
      }
    },
    
    getTypeLabel(type) {
      const labels = {
        'chat': '💬 聊天',
        'outline': '📋 生成大纲',
        'expand': '📝 扩展内容',
        'locate': '🎯 智能定位',
        'edit': '✏️ 编辑文档'
      }
      return labels[type] || type
    },
    
    formatTime(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 小于1分钟
      if (diff < 60000) {
        return '刚刚'
      }
      // 小于1小时
      if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`
      }
      // 小于1天
      if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`
      }
      // 大于1天
      return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatFullTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    
    truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
    
    viewDetail(record) {
      this.selectedRecord = record
    },
    
    closeDetail() {
      this.selectedRecord = null
    }
  }
}
</script>

<style scoped>
.ai-history-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.history-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.refresh-btn {
  padding: 6px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-btn:hover:not(:disabled) {
  background: #2563eb;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.history-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.history-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item.type-chat {
  border-left: 3px solid #3b82f6;
}

.history-item.type-outline {
  border-left: 3px solid #10b981;
}

.history-item.type-expand {
  border-left: 3px solid #f59e0b;
}

.history-item.type-locate {
  border-left: 3px solid #8b5cf6;
}

.history-item.type-edit {
  border-left: 3px solid #ef4444;
}

.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.item-type {
  font-weight: 600;
  font-size: 14px;
}

.item-time {
  font-size: 12px;
  color: #6b7280;
}

.item-content {
  margin-bottom: 8px;
}

.user-message,
.ai-response {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.user-message {
  color: #374151;
}

.ai-response {
  color: #6b7280;
}

.item-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
  color: #9ca3af;
}

.tokens,
.session {
  display: flex;
  align-items: center;
  gap: 4px;
}

.view-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: #e5e7eb;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.view-btn:hover {
  background: #d1d5db;
}

.empty-state,
.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #6b7280;
}

.empty-hint {
  font-size: 14px;
  margin-top: 8px;
}

.retry-btn {
  margin-top: 12px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* 详情弹窗 */
.detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.detail-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.detail-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header h4 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f3f4f6;
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section label {
  display: block;
  font-weight: 600;
  margin-bottom: 4px;
  color: #374151;
}

.detail-section p {
  margin: 0;
  color: #6b7280;
  line-height: 1.6;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.close-detail-btn {
  padding: 8px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.close-detail-btn:hover {
  background: #2563eb;
}
</style>
