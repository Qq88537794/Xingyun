import { ref } from 'vue'

class WebSocketService {
  constructor() {
    this.ws = null
    this.connected = ref(false)
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
  }
  
  connect(url) {
    try {
      this.ws = new WebSocket(url)
      
      this.ws.onopen = () => {
        console.log('WebSocket连接成功')
        this.connected.value = true
        this.reconnectAttempts = 0
        this.emit('connect')
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.emit('message', data)
        } catch (error) {
          console.error('解析消息失败:', error)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        this.emit('error', error)
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket连接关闭')
        this.connected.value = false
        this.emit('disconnect')
        
        // 尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          setTimeout(() => {
            this.connect(url)
          }, this.reconnectDelay)
        }
      }
    } catch (error) {
      console.error('WebSocket连接失败:', error)
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
  
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }
  
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }
  
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        callback(data)
      })
    }
  }
  
  isConnected() {
    return this.connected.value
  }
}

// 单例模式
let wsServiceInstance = null

export const useWebSocketService = () => {
  if (!wsServiceInstance) {
    wsServiceInstance = new WebSocketService()
  }
  return wsServiceInstance
}
