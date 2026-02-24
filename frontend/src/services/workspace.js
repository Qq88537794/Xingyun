/**
 * 工作区文档管理服务
 * 管理多个文档的创建、保存、加载、删除等操作
 */

export class WorkspaceService {
  constructor(projectId) {
    this.projectId = projectId
    this.storageKey = `workspace_docs_${projectId}`
  }

  /**
   * 获取所有文档
   */
  getAllDocuments() {
    try {
      const data = localStorage.getItem(this.storageKey)
      if (!data) return []
      
      const docs = JSON.parse(data)
      // 按更新时间倒序排列
      return docs.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    } catch (e) {
      console.error('获取文档列表失败:', e)
      return []
    }
  }

  /**
   * 获取单个文档
   */
  getDocument(docId) {
    const docs = this.getAllDocuments()
    return docs.find(doc => doc.id === docId)
  }

  /**
   * 创建新文档
   */
  createDocument(name = '未命名文档') {
    const docs = this.getAllDocuments()
    
    // 生成唯一ID
    const id = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // 如果名称重复，自动添加编号
    let finalName = name
    let counter = 1
    while (docs.some(doc => doc.name === finalName)) {
      finalName = `${name} (${counter})`
      counter++
    }
    
    const newDoc = {
      id,
      name: finalName,
      content: {
        type: 'doc',
        content: []
      }, // TipTap JSON格式
      wordCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      hasUnsavedChanges: false
    }
    
    docs.push(newDoc)
    this._saveDocuments(docs)
    
    return newDoc
  }

  /**
   * 保存文档内容
   */
  saveDocument(docId, content) {
    const docs = this.getAllDocuments()
    const doc = docs.find(d => d.id === docId)
    
    if (!doc) {
      console.error('文档不存在:', docId)
      return false
    }
    
    // 计算字数
    const wordCount = this._calculateWordCount(content)
    
    doc.content = content
    doc.wordCount = wordCount
    doc.updatedAt = new Date().toISOString()
    doc.hasUnsavedChanges = false
    
    this._saveDocuments(docs)
    return true
  }

  /**
   * 标记文档有未保存的更改
   */
  markAsUnsaved(docId) {
    const docs = this.getAllDocuments()
    const doc = docs.find(d => d.id === docId)
    
    if (doc) {
      doc.hasUnsavedChanges = true
      this._saveDocuments(docs)
    }
  }

  /**
   * 重命名文档
   */
  renameDocument(docId, newName) {
    const docs = this.getAllDocuments()
    const doc = docs.find(d => d.id === docId)
    
    if (!doc) return false
    
    // 检查名称是否重复
    if (docs.some(d => d.id !== docId && d.name === newName)) {
      throw new Error('文档名称已存在')
    }
    
    doc.name = newName
    doc.updatedAt = new Date().toISOString()
    
    this._saveDocuments(docs)
    return true
  }

  /**
   * 删除文档
   */
  deleteDocument(docId) {
    const docs = this.getAllDocuments()
    const filteredDocs = docs.filter(d => d.id !== docId)
    
    if (filteredDocs.length === docs.length) {
      return false // 文档不存在
    }
    
    this._saveDocuments(filteredDocs)
    return true
  }

  /**
   * 从AI回复创建新文档
   */
  createDocumentFromAIReply(content, baseName = 'AI生成') {
    // 提取内容的前20个字符作为文档名
    const textContent = this._extractTextFromContent(content)
    const shortName = textContent.substring(0, 20).trim() || baseName
    
    const doc = this.createDocument(shortName)
    
    // 将文本内容转换为TipTap格式
    const tipTapContent = this._textToTipTapContent(content)
    this.saveDocument(doc.id, tipTapContent)
    
    return doc
  }

  /**
   * 保存文档列表到localStorage
   */
  _saveDocuments(docs) {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(docs))
    } catch (e) {
      console.error('保存文档列表失败:', e)
      // 如果存储空间不足，尝试清理旧文档
      if (e.name === 'QuotaExceededError') {
        this._cleanupOldDocuments(docs)
      }
    }
  }

  /**
   * 清理旧文档（保留最近的20个）
   */
  _cleanupOldDocuments(docs) {
    const sortedDocs = docs.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    const recentDocs = sortedDocs.slice(0, 20)
    
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(recentDocs))
      console.warn('已清理旧文档，保留最近的20个')
    } catch (e) {
      console.error('清理后仍然保存失败:', e)
    }
  }

  /**
   * 计算文档字数
   */
  _calculateWordCount(content) {
    if (!content || !content.content) return 0
    
    let text = ''
    const extractText = (node) => {
      if (node.type === 'text') {
        text += node.text || ''
      }
      if (node.content && Array.isArray(node.content)) {
        node.content.forEach(extractText)
      }
    }
    
    extractText(content)
    return text.length
  }

  /**
   * 从内容中提取纯文本
   */
  _extractTextFromContent(content) {
    if (typeof content === 'string') {
      // 移除Markdown标记
      return content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/`(.*?)`/g, '$1')
        .replace(/\n/g, ' ')
        .trim()
    }
    
    if (content && content.content) {
      return this._calculateWordCount(content).toString()
    }
    
    return ''
  }

  /**
   * 将文本转换为TipTap内容格式
   */
  _textToTipTapContent(text) {
    if (typeof text !== 'string') {
      return text // 已经是TipTap格式
    }
    
    // 将文本按段落分割
    const paragraphs = text.split('\n').filter(p => p.trim())
    
    return {
      type: 'doc',
      content: paragraphs.map(p => ({
        type: 'paragraph',
        content: [
          {
            type: 'text',
            text: p
          }
        ]
      }))
    }
  }

  /**
   * 导出文档为JSON
   */
  exportDocument(docId) {
    const doc = this.getDocument(docId)
    if (!doc) return null
    
    return {
      version: '1.0',
      name: doc.name,
      content: doc.content,
      createdAt: doc.createdAt,
      updatedAt: doc.updatedAt,
      wordCount: doc.wordCount
    }
  }

  /**
   * 导入文档
   */
  importDocument(data) {
    if (!data || !data.content) {
      throw new Error('无效的文档数据')
    }
    
    const doc = this.createDocument(data.name || '导入的文档')
    this.saveDocument(doc.id, data.content)
    
    return doc
  }

  /**
   * 清空所有文档
   */
  clearAll() {
    localStorage.removeItem(this.storageKey)
  }
}

/**
 * 创建工作区服务实例
 */
export function createWorkspaceService(projectId) {
  return new WorkspaceService(projectId)
}
