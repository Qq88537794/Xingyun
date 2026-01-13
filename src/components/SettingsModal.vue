<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">设置</h2>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <X :size="20" class="text-gray-500" />
        </button>
      </div>
      
      <!-- 内容 -->
      <div class="p-6 space-y-6">
        <!-- 快照设置 -->
        <div>
          <h3 class="text-sm font-medium text-gray-900 mb-4 flex items-center">
            <History :size="16" class="mr-2" />
            版本快照
          </h3>
          
          <!-- 开启/关闭自动快照 -->
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="text-sm text-gray-700">自动保存快照</p>
              <p class="text-xs text-gray-500">定时自动保存文档版本</p>
            </div>
            <button 
              @click="localSettings.autoSnapshot = !localSettings.autoSnapshot"
              :class="[
                'relative w-12 h-6 rounded-full transition-colors',
                localSettings.autoSnapshot ? 'bg-blue-600' : 'bg-gray-300'
              ]"
            >
              <span 
                :class="[
                  'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform shadow',
                  localSettings.autoSnapshot ? 'left-7' : 'left-1'
                ]"
              ></span>
            </button>
          </div>
          
          <!-- 快照间隔 -->
          <div v-if="localSettings.autoSnapshot" class="mb-4">
            <label class="block text-sm text-gray-700 mb-2">
              保存间隔
            </label>
            <div class="flex items-center space-x-3">
              <input 
                v-model.number="localSettings.snapshotInterval"
                type="range"
                min="1"
                max="30"
                class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <span class="text-sm text-gray-600 w-20 text-right">
                {{ localSettings.snapshotInterval }} 分钟
              </span>
            </div>
            <div class="flex justify-between text-xs text-gray-400 mt-1">
              <span>1分钟</span>
              <span>30分钟</span>
            </div>
          </div>
          
          <!-- 最大快照数量 -->
          <div>
            <label class="block text-sm text-gray-700 mb-2">
              最大保存数量
            </label>
            <select 
              v-model.number="localSettings.maxSnapshots"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
            >
              <option :value="10">10 个</option>
              <option :value="20">20 个</option>
              <option :value="30">30 个</option>
              <option :value="50">50 个</option>
            </select>
          </div>
        </div>
        
        <!-- 分割线 -->
        <div class="border-t border-gray-200"></div>
        
        <!-- 编辑器设置 -->
        <div>
          <h3 class="text-sm font-medium text-gray-900 mb-4 flex items-center">
            <FileText :size="16" class="mr-2" />
            编辑器
          </h3>
          
          <!-- 自动保存到本地 -->
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-700">自动保存到本地</p>
              <p class="text-xs text-gray-500">关闭页面前自动保存内容</p>
            </div>
            <button 
              @click="localSettings.autoSaveLocal = !localSettings.autoSaveLocal"
              :class="[
                'relative w-12 h-6 rounded-full transition-colors',
                localSettings.autoSaveLocal ? 'bg-blue-600' : 'bg-gray-300'
              ]"
            >
              <span 
                :class="[
                  'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform shadow',
                  localSettings.autoSaveLocal ? 'left-7' : 'left-1'
                ]"
              ></span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 底部 -->
      <div class="flex items-center justify-end space-x-3 p-4 border-t border-gray-200 bg-gray-50">
        <button 
          @click="handleReset"
          class="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors text-sm"
        >
          恢复默认
        </button>
        <button 
          @click="handleSave"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          保存设置
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { X, History, FileText } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  settings: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'save'])

const toast = useToast()

// 默认设置
const defaultSettings = {
  autoSnapshot: true,
  snapshotInterval: 5,
  maxSnapshots: 30,
  autoSaveLocal: true
}

// 本地编辑的设置副本
const localSettings = ref({ ...defaultSettings })

onMounted(() => {
  // 从 props 初始化
  localSettings.value = { ...defaultSettings, ...props.settings }
})

const handleSave = () => {
  emit('save', { ...localSettings.value })
  toast.success('设置已保存')
  emit('close')
}

const handleReset = () => {
  localSettings.value = { ...defaultSettings }
  toast.info('已恢复默认设置')
}
</script>
