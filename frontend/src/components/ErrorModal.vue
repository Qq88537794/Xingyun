<template>
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" @click="close">
      <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div v-if="show" class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6" @click.stop>
          <div class="text-center">
            <!-- 图标 -->
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" :class="iconBgClass">
              <component :is="iconComponent" :size="32" :class="iconClass" />
            </div>
            
            <!-- 标题 -->
            <h3 class="text-lg font-bold text-gray-900 mb-2">{{ title }}</h3>
            
            <!-- 消息 -->
            <p class="text-gray-600 mb-6 whitespace-pre-line">{{ message }}</p>
            
            <!-- 按钮 -->
            <button
              @click="close"
              class="w-full px-4 py-3 rounded-lg font-medium transition-colors"
              :class="buttonClass"
            >
              {{ buttonText }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { AlertTriangle, AlertCircle, CheckCircle, Info } from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'error', // 'error', 'warning', 'success', 'info'
    validator: (value) => ['error', 'warning', 'success', 'info'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    required: true
  },
  buttonText: {
    type: String,
    default: '确定'
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const iconComponent = computed(() => {
  switch (props.type) {
    case 'error':
      return AlertCircle
    case 'warning':
      return AlertTriangle
    case 'success':
      return CheckCircle
    case 'info':
      return Info
    default:
      return AlertCircle
  }
})

const iconBgClass = computed(() => {
  switch (props.type) {
    case 'error':
      return 'bg-red-100'
    case 'warning':
      return 'bg-yellow-100'
    case 'success':
      return 'bg-green-100'
    case 'info':
      return 'bg-blue-100'
    default:
      return 'bg-red-100'
  }
})

const iconClass = computed(() => {
  switch (props.type) {
    case 'error':
      return 'text-red-600'
    case 'warning':
      return 'text-yellow-600'
    case 'success':
      return 'text-green-600'
    case 'info':
      return 'text-blue-600'
    default:
      return 'text-red-600'
  }
})

const buttonClass = computed(() => {
  switch (props.type) {
    case 'error':
      return 'bg-red-600 text-white hover:bg-red-700'
    case 'warning':
      return 'bg-yellow-600 text-white hover:bg-yellow-700'
    case 'success':
      return 'bg-green-600 text-white hover:bg-green-700'
    case 'info':
      return 'bg-blue-600 text-white hover:bg-blue-700'
    default:
      return 'bg-red-600 text-white hover:bg-red-700'
  }
})
</script>
