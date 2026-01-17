import api from './api'

// 获取所有文件夹
export const getFolders = async () => {
  const response = await api.get('/folders')
  return response.data.folders
}

// 创建文件夹
export const createFolder = async (name, color = 'blue', icon = 'folder') => {
  const response = await api.post('/folders', { name, color, icon })
  return response.data
}

// 更新文件夹
export const updateFolder = async (folderId, data) => {
  const response = await api.put(`/folders/${folderId}`, data)
  return response.data
}

// 删除文件夹
export const deleteFolder = async (folderId) => {
  const response = await api.delete(`/folders/${folderId}`)
  return response.data
}

// 将项目添加到文件夹
export const addProjectToFolder = async (folderId, projectId) => {
  const response = await api.post(`/folders/${folderId}/projects/${projectId}`)
  return response.data
}

// 将项目从文件夹移出
export const removeProjectFromFolder = async (projectId) => {
  const response = await api.post(`/folders/projects/${projectId}/remove`)
  return response.data
}
