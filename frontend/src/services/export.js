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
  static async exportToPdf(htmlContent, title = 'document', styles = []) {
    // Generate CSS from styles object
    const customCss = this.generateCssFromStyles(styles)
    
    // Default base styles
    const baseCss = `
      body { 
        font-family: 'Microsoft YaHei', sans-serif; 
        padding: 20px; 
        max-width: 800px; 
        margin: 0 auto; 
        line-height: 1.6;
        color: #333;
      }
      img { max-width: 100%; height: auto; }
      table { border-collapse: collapse; width: 100%; margin: 1em 0; }
      th, td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
      th { background-color: #f3f4f6; }
      blockquote { border-left: 4px solid #e5e7eb; padding-left: 1em; color: #6b7280; font-style: italic; }
      
      /* Inline Code */
      code { background-color: #f3f4f6; color: #e01e5a; padding: 2px 4px; border-radius: 4px; font-family: Consolas, Monaco, 'Andale Mono', monospace; }
      
      /* Code Blocks - Dark Theme */
      pre { background-color: #1e1e1e; color: #f8f8f2; padding: 1em; border-radius: 8px; overflow-x: auto; margin: 1em 0; }
      pre code { background-color: transparent; color: inherit; padding: 0; }
    `

    const finalHtml = `
        <!DOCTYPE html>
        <html>
          <head>
            <title>${title}</title>
            <style>
              ${baseCss}
              /* Custom Project Styles */
              ${customCss}
            </style>
          </head>
          <body>
            ${htmlContent}
          </body>
        </html>
    `

    if (window.electronAPI) {
      // Electron 环境：使用 Native PrintToPDF
      return await window.electronAPI.exportPdf(finalHtml)
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
      doc.write(finalHtml)
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

  static generateCssFromStyles(styles) {
    if (!styles || !Array.isArray(styles)) return ''
    
    return styles.map(item => {
      const { element, style } = item
      if (!element || !style) return ''
      
      // Convert camelCase style keys to kebab-case (e.g., fontSize -> font-size)
      const cssProps = Object.entries(style).map(([key, value]) => {
        const cssKey = key.replace(/([A-Z])/g, '-$1').toLowerCase()
        
        // Handle specific values if needed, mainly units for numbers
        let cssValue = value
        
        // Add px to numeric values for certain properties if they are numbers
        if (typeof value === 'number') {
           if (['fontSize', 'marginTop', 'marginBottom', 'paddingTop', 'paddingBottom', 'lineHeight'].includes(key)) {
               // lineHeight is unitless usually for ratio, but fontSize needs px.
               // Check logic. The json shows fontSize: 32. 
               // lineHeight: 1.2 (unitless).
               // margins: 1 (likely em or rem? or unitless for lineHeight?). 
               // In TipTap editor commonly: 
               // fontSize -> px
               // lineHeight -> unitless
               // margin -> em or rem often. 
               
               // Let's assume usage in editor:
               if (key === 'fontSize') cssValue = `${value}px`
               // if (key.includes('margin')) cssValue = `${value}em` // Assumption based on editor
           }
        }
        
        // Handle specific boolean flags like 'bold', 'italic' if they exist in the style block
        if (key === 'bold') return value ? 'font-weight: bold;' : ''
        if (key === 'italic') return value ? 'font-style: italic;' : ''
        
        // Cleanup null/undefined
        if (value === null || value === undefined) return ''
        
        return `${cssKey}: ${cssValue};`
      }).join(' ')
      
      return `${element} { ${cssProps} }`
    }).join('\n')
  }

  /**
   * 导出为 Word (.docx)
   * 调用后端 API
   */
  static async toWord(json, title = 'document', styles = []) {
    // Debug info
    console.log('ExportService.toWord styles:', styles)
    
    // Ensure we are sending a plain array
    const stylesPlain = Array.isArray(styles) ? JSON.parse(JSON.stringify(styles)) : []
    
    if (stylesPlain.length === 0) {
        console.warn('ExportService: Styles list is empty, export will use default Word styles.')
    }

    try {
      // Fix: Ensure we pass the full TipTap document object (dict), not the content array (list).
      // Backend expects a dict with 'type' and 'content'.
      const contentPayload = (json.type === 'doc') ? json : { type: 'doc', content: json.content || json }

      const response = await api.post('/export/docx', {
        title: title,
        content: contentPayload, 
        styles: stylesPlain // Pass custom styles
      }, {
        responseType: 'blob'
      })
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', title.endsWith('.docx') ? title : `${title}.docx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      return { success: true }
    } catch (error) {
      console.error('Word export failed:', error)
      throw new Error('导出服务连接失败，请确保后端服务正在运行')
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
   * 导出为 PDF（需要后端）
   * @placeholder 预留接口
   */
  static async toPDF(json, wsService) {
    // TODO: 后端实现
    throw new Error('PDF 导出需要后端支持')
  }

  /**
   * 导出为 LaTeX (zip with images)
   */
  static async toLaTeX(json, title = 'document', styles = []) {
    try {
      const contentPayload = (json.type === 'doc') ? json : { type: 'doc', content: json.content || json }
      const stylesPlain = Array.isArray(styles) ? JSON.parse(JSON.stringify(styles)) : []

      const response = await api.post('/export/latex', {
        title: title,
        content: contentPayload,
        styles: stylesPlain
      }, {
        responseType: 'blob'
      })

      const blob = new Blob([response.data], { type: 'application/zip' })
      const url = window.URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `${title}_latex.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      return { success: true }
    } catch (error) {
       console.error('LaTeX export failed:', error)
       throw new Error('LaTeX 导出失败: ' + (error.response?.data?.error || error.message))
    }
  }
}
