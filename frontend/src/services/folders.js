import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

// 获取认证 token
const getAuthHeader = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 获取所有文件夹
export const getFolders = async () => {
  const response = await axios.get(`${API_BASE_URL}/folders`, {
    headers: getAuthHeader()
  })
  return response.data.folders
}

// 创建文件夹
export const createFolder = async (name, color = 'blue', icon = 'folder') => {
  const response = await axios.post(
    `${API_BASE_URL}/folders`,
    { name, color, icon },
    { headers: getAuthHeader() }
  )
  return response.data
}

// 更新文件夹
export const updateFolder = async (folderId, data) => {
  const response = await axios.put(
    `${API_BASE_URL}/folders/${folderId}`,
    data,
    { headers: getAuthHeader() }
  )
  return response.data
}

// 删除文件夹
export const deleteFolder = async (folderId) => {
  const response = await axios.delete(
    `${API_BASE_URL}/folders/${folderId}`,
    { headers: getAuthHeader() }
  )
  return response.data
}

// 将项目添加到文件夹
export const addProjectToFolder = async (folderId, projectId) => {
  const response = await axios.post(
    `${API_BASE_URL}/folders/${folderId}/projects/${projectId}`,
    {},
    { headers: getAuthHeader() }
  )
  return response.data
}

// 将项目从文件夹移出
export const removeProjectFromFolder = async (projectId) => {
  const response = await axios.post(
    `${API_BASE_URL}/folders/projects/${projectId}/remove`,
    {},
    { headers: getAuthHeader() }
  )
  return response.data
}
