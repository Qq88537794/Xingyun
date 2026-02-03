import api from './api'

/**
 * 文档导出服务
 * 纯前端实现 Markdown 导出
 * Word/PDF/LaTeX 需要后端支持（已预留接口）
 */

export class ExportService {
  /**
   * TipTap JSON 转 Markdown（纯前端）
   */
  static toMarkdown(json) {
    if (!json || !json.content) return ''
    return this.processNodes(json.content)
  }

  /**
   * 导出为 PDF
   */
  static async exportToPdf(htmlContent, title = 'document') {
    if (window.electronAPI) {
      // Electron 环境：使用 Native PrintToPDF
      return await window.electronAPI.exportPdf(htmlContent)
    } else {
      // 浏览器环境：使用 iframe 打印
      const iframe = document.createElement('iframe')
      iframe.style.position = 'fixed'
      iframe.style.right = '0'
      iframe.style.bottom = '0'
      iframe.style.width = '0'
      iframe.style.height = '0'
      iframe.style.border = '0'
      
      document.body.appendChild(iframe)
      
      const doc = iframe.contentWindow.document
      doc.open()
      doc.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>${title}</title>
            <style>
              body { 
                font-family: 'Microsoft YaHei', sans-serif; 
                padding: 5px; 
                max-width: 800px; 
                margin: 0 auto; 
                line-height: 1.6;
              }
              h1, h2, h3, h4 { color: #111827; margin-top: 1em; margin-bottom: 0.5em; }
              p { margin-bottom: 1em; color: #374151; }
              img { max-width: 100%; height: auto; }
              table { border-collapse: collapse; width: 100%; margin: 1em 0; }
              th, td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
              th { background-color: #f3f4f6; }
              blockquote { border-left: 4px solid #e5e7eb; padding-left: 1em; color: #6b7280; font-style: italic; }
            </style>
          </head>
          <body>
            ${htmlContent}
          </body>
        </html>
      `)
      doc.close()

      // 等待图片加载完成
      setTimeout(() => {
        iframe.contentWindow.focus()
        iframe.contentWindow.print()
        // 打印对话框关闭后移除 iframe (注意：用户取消也会触发)
        // 无法精确监听打印完成，延迟移除
        setTimeout(() => {
          document.body.removeChild(iframe)
        }, 1000)
      }, 500)
      
      return { success: true }
    }
  }

  static processNodes(nodes, listLevel = 0) {
    if (!nodes) return ''
    return nodes.map(node => this.processNode(node, listLevel)).join('')
  }

  static processNode(node, listLevel = 0) {
    switch (node.type) {
      case 'heading':
        const level = node.attrs?.level || 1
        const prefix = '#'.repeat(level)
        return `${prefix} ${this.processInline(node.content)}\n\n`

      case 'paragraph':
        const text = this.processInline(node.content)
        return text ? `${text}\n\n` : '\n'

      case 'bulletList':
        return this.processList(node.content, false, listLevel) + '\n'

      case 'orderedList':
        return this.processList(node.content, true, listLevel) + '\n'

      case 'listItem':
        return this.processNodes(node.content, listLevel)

      case 'blockquote':
        const quoteContent = this.processNodes(node.content)
        return quoteContent.split('\n').map(line => line ? `> ${line}` : '>').join('\n') + '\n'

      case 'codeBlock':
        const lang = node.attrs?.language || ''
        const code = this.processInline(node.content)
        return `\`\`\`${lang}\n${code}\n\`\`\`\n\n`

      case 'horizontalRule':
        return '---\n\n'

      case 'image':
        const src = node.attrs?.src || ''
        const alt = node.attrs?.alt || ''
        return `![${alt}](${src})\n\n`

      case 'table':
        return this.processTable(node) + '\n'

      default:
        if (node.content) {
          return this.processNodes(node.content, listLevel)
        }
        return ''
    }
  }

  static processList(items, ordered, level) {
    const indent = '  '.repeat(level)
    return items.map((item, index) => {
      const prefix = ordered ? `${index + 1}.` : '-'
      const content = this.processNodes(item.content, level + 1).trim()
      return `${indent}${prefix} ${content}`
    }).join('\n')
  }

  static processInline(nodes) {
    if (!nodes) return ''
    return nodes.map(node => {
      let text = node.text || ''
      
      if (node.marks) {
        node.marks.forEach(mark => {
          switch (mark.type) {
            case 'bold':
              text = `**${text}**`
              break
            case 'italic':
              text = `*${text}*`
              break
            case 'underline':
              text = `<u>${text}</u>`
              break
            case 'code':
              text = `\`${text}\``
              break
            case 'link':
              text = `[${text}](${mark.attrs?.href || ''})`
              break
          }
        })
      }
      
      return text
    }).join('')
  }

  static processTable(tableNode) {
    if (!tableNode.content) return ''
    
    const rows = tableNode.content
    let markdown = ''
    
    rows.forEach((row, rowIndex) => {
      const cells = row.content || []
      const cellContents = cells.map(cell => {
        return this.processInline(cell.content?.[0]?.content || []).trim()
      })
      
      markdown += '| ' + cellContents.join(' | ') + ' |\n'
      
      // 添加表头分隔符
      if (rowIndex === 0) {
        markdown += '| ' + cellContents.map(() => '---').join(' | ') + ' |\n'
      }
    })
    
    return markdown
  }

  /**
   * 下载 Markdown 文件
   */
  static downloadMarkdown(json, filename = 'document.md') {
    const markdown = this.toMarkdown(json)
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    return true
  }

  /**
   * 导出为 Word（调用后端）
   */
  static async toWord(json, filename = 'document.docx') {
    try {
      const response = await api.post('/export/docx', {
        content: json,
        title: filename.replace('.docx', '')
      }, {
        responseType: 'blob'
      })

      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = window.URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      return true
    } catch (error) {
           console.error('Export docx error', error);
      throw new Error('Word 导出失败: ' + (error.response?.data?.error || error.message))
    }
  }


  static downloadWord(fileBlob, filename = 'document.docx') {
  }

  /**
   * 导出为 PDF（需要后端）
   * @placeholder 预留接口
   */
  static async toPDF(json, wsService) {
    // TODO: 后端实现
    throw new Error('PDF 导出需要后端支持')
  }

  /**
   * 导出为 LaTeX（需要后端）
   * @placeholder 预留接口
   */
  static async toLaTeX(json, wsService) {
    // TODO: 后端实现
    throw new Error('LaTeX 导出需要后端支持')
  }
}
