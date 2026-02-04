const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const fontList = require('font-list')

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'default',
    frame: true,
    backgroundColor: '#ffffff'
  })

  // 开发环境加载Vite服务器，生产环境加载打包后的文件
  const isDev = !app.isPackaged

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    // mainWindow.webContents.openDevTools() // 开发模式下自动打开开发者工具（已禁用）
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// IPC处理器 - 文件操作
ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Documents', extensions: ['docx', 'pdf', 'txt', 'md', 'html'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths
  }
  return null
})

ipcMain.handle('dialog:saveFile', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: options.defaultPath || 'document',
    filters: options.filters || [
      { name: 'Word Document', extensions: ['docx'] },
      { name: 'PDF', extensions: ['pdf'] },
      { name: 'Markdown', extensions: ['md'] },
      { name: 'LaTeX', extensions: ['tex'] }
    ]
  })

  if (!result.canceled) {
    return result.filePath
  }
  return null
})

ipcMain.handle('file:read', async (event, filePath) => {
  try {
    const data = fs.readFileSync(filePath, 'utf-8')
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('file:readBuffer', async (event, filePath) => {
  try {
    const buffer = fs.readFileSync(filePath)
    return buffer
  } catch (error) {
    throw new Error(error.message)
  }
})

ipcMain.handle('file:write', async (event, filePath, content) => {
  try {
    fs.writeFileSync(filePath, content, 'utf-8')
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

// PDF 导出
ipcMain.handle('system:exportPdf', async (event, htmlContent) => {
  let printWindow = new BrowserWindow({ 
    show: false, 
    webPreferences: { 
      nodeIntegration: true 
    } 
  })

  const completeHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { 
            font-family: 'Microsoft YaHei', sans-serif; 
            padding: 40px; 
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
          code { background-color: #f3f4f6; padding: 0.2em 0.4em; border-radius: 4px; font-family: monospace; }
          pre { background-color: #1f2937; color: #f9fafb; padding: 1em; border-radius: 6px; overflow-x: auto; }
          pre code { background-color: transparent; padding: 0; }
          ul, ol { padding-left: 1.5em; margin-bottom: 1em; }
        </style>
      </head>
      <body>
        ${htmlContent}
      </body>
    </html>
  `
  
  try {
    const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(completeHtml)}`
    await printWindow.loadURL(dataUrl)
    
    const { filePath } = await dialog.showSaveDialog(mainWindow, {
      defaultPath: 'document.pdf',
      filters: [{ name: 'PDF Document', extensions: ['pdf'] }]
    })

    if (filePath) {
      const pdfData = await printWindow.webContents.printToPDF({
        printBackground: true,
        pageSize: 'A4',
        margins: { top: 0.3, bottom: 0.3, left: 0.3, right: 0.3 } // inches
      })
      fs.writeFileSync(filePath, pdfData)
      printWindow.close()
      return { success: true, filePath }
    } else {
      printWindow.close()
      return { canceled: true }
    }
  } catch (error) {
    if(!printWindow.isDestroyed()) printWindow.close()
    return { success: false, error: error.message }
  }
})

// IPC处理器 - 应用信息
ipcMain.handle('app:getPath', async (event, name) => {
  return app.getPath(name)
})

// IPC处理器 - 系统字体
ipcMain.handle('system:getFonts', async () => {
  try {
    const fonts = await fontList.getFonts({ disableQuoting: true })
    // fontList 有时候返回的是带引号的，有时候是不带的，这里先尽量去引号
    return fonts.map(f => f.replace(/^"|"$/g, ''))
  } catch (error) {
    console.error('Get fonts error:', error)
    return []
  }
})
