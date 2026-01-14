<template>
  <div class="fixed top-4 right-4 z-[100] space-y-2">
    <TransitionGroup
      enter-active-class="transition ease-out duration-300"
      enter-from-class="transform translate-x-full opacity-0"
      enter-to-class="transform translate-x-0 opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="transform translate-x-0 opacity-100"
      leave-to-class="transform translate-x-full opacity-0"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="[
          'flex items-center px-4 py-3 rounded-lg shadow-lg min-w-[280px] max-w-[400px]',
          toastStyles[toast.type]
        ]"
      >
        <component :is="toastIcons[toast.type]" :size="18" class="flex-shrink-0 mr-3" />
        <span class="text-sm flex-1">{{ toast.message }}</span>
        <button @click="remove(toast.id)" class="ml-3 opacity-70 hover:opacity-100">
          <X :size="16" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { toasts, remove } = useToast()

const toastStyles = {
  success: 'bg-green-50 text-green-800 border border-green-200',
  error: 'bg-red-50 text-red-800 border border-red-200',
  warning: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
  info: 'bg-blue-50 text-blue-800 border border-blue-200'
}

const toastIcons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info
}
</script>
