<template>
  <div v-if="contexts.length > 0" class="context-manager">
    <div class="context-header">
      <div class="flex items-center space-x-2">
        <FileText :size="14" class="text-blue-600" />
        <span class="text-xs font-medium text-gray-700">上下文 ({{ contexts.length }})</span>
      </div>
      <button
        @click="clearAll"
        class="text-xs text-gray-500 hover:text-red-600 transition-colors"
        title="清空所有上下文"
      >
        <X :size="14" />
      </button>
    </div>
    
    <div class="context-list">
      <div
        v-for="(context, index) in contexts"
        :key="context.id"
        class="context-item"
      >
        <div class="context-content">
          <div class="context-text">{{ truncateText(context.text, 60) }}</div>
          <div class="context-meta">
            <span class="text-xs text-gray-400">{{ context.text.length }} 字符</span>
            <span class="text-xs text-gray-400">{{ formatTime(context.timestamp) }}</span>
          </div>
        </div>
        <button
          @click="removeContext(index)"
          class="context-remove"
          title="移除此上下文"
        >
          <X :size="12" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileText, X } from 'lucide-vue-next'

const props = defineProps({
  contexts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['remove', 'clear'])

const truncateText = (text, maxLength) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const removeContext = (index) => {
  emit('remove', index)
}

const clearAll = () => {
  emit('clear')
}
</script>

<style scoped>
.context-manager {
  @apply mb-3 border border-blue-200 rounded-lg bg-blue-50 overflow-hidden;
}

.context-header {
  @apply flex items-center justify-between px-3 py-2 bg-blue-100 border-b border-blue-200;
}

.context-list {
  @apply max-h-32 overflow-y-auto;
}

.context-item {
  @apply flex items-start justify-between px-3 py-2 border-b border-blue-100 last:border-b-0 hover:bg-blue-100 transition-colors;
}

.context-content {
  @apply flex-1 min-w-0;
}

.context-text {
  @apply text-xs text-gray-700 leading-relaxed break-words;
}

.context-meta {
  @apply flex items-center space-x-2 mt-1;
}

.context-remove {
  @apply ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0;
}
</style>
