const { contextBridge, ipcRenderer } = require('electron')

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 文件对话框
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),

  // 文件操作
  readFile: (filePath) => ipcRenderer.invoke('file:read', filePath),
  readFileAsBuffer: (filePath) => ipcRenderer.invoke('file:readBuffer', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('file:write', filePath, content),

  // 应用路径
  getAppPath: (name) => ipcRenderer.invoke('app:getPath', name),

  // 系统信息
  getSystemFonts: () => ipcRenderer.invoke('system:getFonts'),

  // 平台信息
  platform: process.platform
})
