import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDocumentStore = defineStore('document', () => {
  // 文档JSON模型 - 唯一真实数据源
  const documentModel = ref({
    type: 'doc',
    content: []
  })
  
  // 文档元数据
  const metadata = ref({
    title: '未命名文档',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    author: '',
    version: 1
  })
  
  // 历史记录
  const history = ref([])
  const historyIndex = ref(-1)
  
  // 更新文档
  const updateDocument = (json) => {
    documentModel.value = json
    metadata.value.updatedAt = new Date().toISOString()
    
    // 添加到历史记录
    addToHistory(json)
  }
  
  // 清空文档
  const clearDocument = () => {
    documentModel.value = {
      type: 'doc',
      content: []
    }
    metadata.value = {
      title: '未命名文档',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: '',
      version: 1
    }
    history.value = []
    historyIndex.value = -1
  }
  
  // 添加到历史记录
  const addToHistory = (json) => {
    // 限制历史记录数量
    if (history.value.length >= 50) {
      history.value.shift()
    }
    
    history.value.push({
      content: JSON.parse(JSON.stringify(json)),
      timestamp: new Date().toISOString()
    })
    historyIndex.value = history.value.length - 1
  }
  
  // 撤销
  const undo = () => {
    if (historyIndex.value > 0) {
      historyIndex.value--
      return history.value[historyIndex.value].content
    }
    return null
  }
  
  // 重做
  const redo = () => {
    if (historyIndex.value < history.value.length - 1) {
      historyIndex.value++
      return history.value[historyIndex.value].content
    }
    return null
  }
  
  return {
    documentModel,
    metadata,
    history,
    historyIndex,
    updateDocument,
    clearDocument,
    undo,
    redo
  }
})
