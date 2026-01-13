<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">版本快照</h2>
          <p class="text-xs text-gray-500 mt-1">自动保存的文档历史版本</p>
        </div>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <X :size="20" class="text-gray-500" />
        </button>
      </div>
      
      <!-- 快照列表 -->
      <div class="flex-1 overflow-y-auto p-4">
        <div v-if="snapshots.length === 0" class="text-center text-gray-400 py-12">
          <History :size="48" class="mx-auto mb-3 opacity-50" />
          <p>暂无版本快照</p>
          <p class="text-xs mt-2">编辑文档时会自动保存快照</p>
        </div>
        
        <div v-else class="space-y-2">
          <div 
            v-for="(snapshot, index) in snapshots" 
            :key="index"
            class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer group"
            @click="handlePreview(snapshot)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-sm font-medium">
                  {{ snapshots.length - index }}
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-800">
                    {{ snapshot.label || '自动保存' }}
                  </p>
                  <p class="text-xs text-gray-500">
                    {{ formatTime(snapshot.timestamp) }}
                  </p>
                </div>
              </div>
              <div class="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  @click.stop="handleRestore(snapshot)"
                  class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  恢复
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部 -->
      <div class="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <button 
          @click="handleSaveSnapshot"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 text-sm"
        >
          <Save :size="16" />
          <span>手动保存快照</span>
        </button>
        <button 
          @click="handleClearAll"
          class="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm"
        >
          清空全部
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { X, History, Save } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  snapshots: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'restore', 'save-snapshot', 'clear-all'])

const toast = useToast()

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const handlePreview = (snapshot) => {
  // 可以扩展为预览功能
  toast.info('点击"恢复"按钮可恢复到此版本')
}

const handleRestore = (snapshot) => {
  if (confirm('确定要恢复到此版本吗？当前内容将被替换。')) {
    emit('restore', snapshot)
    toast.success('已恢复到选中版本')
  }
}

const handleSaveSnapshot = () => {
  const label = prompt('为此快照添加备注（可选）:')
  emit('save-snapshot', label || '')
  toast.success('快照已保存')
}

const handleClearAll = () => {
  if (confirm('确定要清空所有快照吗？此操作不可恢复。')) {
    emit('clear-all')
    toast.success('已清空所有快照')
  }
}
</script>
