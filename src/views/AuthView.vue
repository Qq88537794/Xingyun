<template>
  <div>
    <LoginView 
      v-if="currentView === 'login'"
      @switch-to-register="currentView = 'register'"
      @login-success="handleAuthSuccess"
    />
    <RegisterView 
      v-else
      @switch-to-login="currentView = 'login'"
      @register-success="handleAuthSuccess"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LoginView from './LoginView.vue'
import RegisterView from './RegisterView.vue'

const emit = defineEmits(['auth-success'])

const currentView = ref('login')

const handleAuthSuccess = () => {
  emit('auth-success')
}
</script>
