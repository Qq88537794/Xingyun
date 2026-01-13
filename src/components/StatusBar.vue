<template>
  <div class="status-bar bg-gray-100 border-t border-gray-200 px-4 py-1 flex items-center justify-between text-xs text-gray-600">
    <div class="flex items-center space-x-4">
      <span>字数: {{ wordCount }}</span>
      <span v-if="lastSaved" class="text-gray-500">
        上次保存: {{ formatTime(lastSaved) }}
      </span>
      <span class="flex items-center space-x-1">
        <span 
          :class="[
            'w-2 h-2 rounded-full',
            connectionStatus === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
          ]"
        ></span>
        <span>{{ connectionStatus === 'connected' ? '已连接' : '离线模式' }}</span>
      </span>
    </div>
    
    <div class="flex items-center space-x-3">
      <span class="text-gray-400">Ctrl+S 保存 | Ctrl+Z 撤销</span>
      <span>行云文档 v1.0.0</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  wordCount: {
    type: Number,
    default: 0
  },
  connectionStatus: {
    type: String,
    default: 'disconnected'
  },
  lastSaved: {
    type: String,
    default: null
  }
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>
