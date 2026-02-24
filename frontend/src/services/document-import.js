/**
 * 文档导入服务
 * 支持Word、PDF、Markdown等格式的导入
 */

import api from './api'

/**
 * 解析上传的文档
 * @param {File} file - 文档文件
 * @returns {Promise} 解析结果
 */
export async function parseDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/document/parse', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

/**
 * 获取支持的文件格式
 * @returns {Promise} 支持的格式列表
 */
export async function getSupportedFormats() {
  const response = await api.get('/document/supported-formats')
  return response.data
}

/**
 * 检查文件格式是否支持
 * @param {string} filename - 文件名
 * @returns {boolean} 是否支持
 */
export function isSupportedFormat(filename) {
  const supportedFormats = ['.docx', '.doc', '.pdf', '.md', '.markdown', '.txt', '.text']
  const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase()
  return supportedFormats.includes(ext)
}

/**
 * 将HTML内容转换为TipTap JSON格式
 * @param {string} html - HTML内容
 * @returns {object} TipTap JSON格式
 */
export function htmlToTipTapJSON(html) {
  // 创建临时DOM元素
  const temp = document.createElement('div')
  temp.innerHTML = html

  const content = []

  // 遍历子元素
  temp.childNodes.forEach(node => {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const element = node

      // 处理标题
      if (element.tagName.match(/^H[1-6]$/)) {
        const level = parseInt(element.tagName.substring(1))
        content.push({
          type: 'heading',
          attrs: { level },
          content: [{ type: 'text', text: element.textContent }]
        })
      }
      // 处理段落
      else if (element.tagName === 'P') {
        const text = element.textContent.trim()
        if (text) {
          content.push({
            type: 'paragraph',
            content: [{ type: 'text', text }]
          })
        }
      }
      // 处理表格
      else if (element.tagName === 'TABLE') {
        // 简化处理：将表格转换为段落
        const tableText = element.textContent.trim()
        if (tableText) {
          content.push({
            type: 'paragraph',
            content: [{ type: 'text', text: `[表格]\n${tableText}` }]
          })
        }
      }
      // 处理换行
      else if (element.tagName === 'BR') {
        // 跳过，由段落处理
      }
      // 其他元素
      else {
        const text = element.textContent.trim()
        if (text) {
          content.push({
            type: 'paragraph',
            content: [{ type: 'text', text }]
          })
        }
      }
    }
    // 处理文本节点
    else if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent.trim()
      if (text) {
        content.push({
          type: 'paragraph',
          content: [{ type: 'text', text }]
        })
      }
    }
  })

  // 如果没有内容，添加一个空段落
  if (content.length === 0) {
    content.push({
      type: 'paragraph',
      content: []
    })
  }

  return {
    type: 'doc',
    content
  }
}

/**
 * 将纯文本转换为TipTap JSON格式
 * @param {string} text - 纯文本
 * @returns {object} TipTap JSON格式
 */
export function textToTipTapJSON(text) {
  const paragraphs = text.split('\n').filter(p => p.trim())

  if (paragraphs.length === 0) {
    return {
      type: 'doc',
      content: [{ type: 'paragraph', content: [] }]
    }
  }

  const content = paragraphs.map(p => ({
    type: 'paragraph',
    content: [{ type: 'text', text: p }]
  }))

  return {
    type: 'doc',
    content
  }
}

/**
 * 导入文档到编辑器
 * @param {File} file - 文档文件
 * @param {Function} onProgress - 进度回调
 * @returns {Promise} 导入结果
 */
export async function importDocument(file, onProgress) {
  try {
    // 检查文件格式
    if (!isSupportedFormat(file.name)) {
      throw new Error(`不支持的文件格式: ${file.name}`)
    }

    // 上传并解析
    if (onProgress) onProgress(30, '正在上传文件...')
    
    const result = await parseDocument(file)

    if (result.code !== 200) {
      throw new Error(result.message || '解析失败')
    }

    if (onProgress) onProgress(60, '正在转换格式...')

    const data = result.data

    // 转换为TipTap格式
    let tipTapContent
    if (data.html && data.html.trim()) {
      tipTapContent = htmlToTipTapJSON(data.html)
    } else if (data.content && data.content.trim()) {
      tipTapContent = textToTipTapJSON(data.content)
    } else {
      throw new Error('文档内容为空')
    }

    if (onProgress) onProgress(100, '导入完成')

    return {
      success: true,
      content: tipTapContent,
      metadata: data.metadata,
      filename: data.filename
    }

  } catch (error) {
    console.error('导入文档失败:', error)
    return {
      success: false,
      error: error.message || '导入失败'
    }
  }
}
