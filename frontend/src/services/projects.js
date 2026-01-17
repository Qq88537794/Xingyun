import api from './api'

/**
 * 项目管理 API 服务
 */

/**
 * 获取当前用户的项目列表
 * @returns {Promise<Array>} 项目列表
 */
export const getProjects = async () => {
  const response = await api.get('/projects')
  return response.data.projects || []
}

/**
 * 获取单个项目详情
 * @param {number} projectId - 项目 ID
 * @param {boolean} includeResources - 是否包含资源
 * @returns {Promise<Object>} 项目详情
 */
export const getProject = async (projectId, includeResources = false) => {
  const response = await api.get(
    `/projects/${projectId}?include_resources=${includeResources}`
  )
  return response.data.project
}

/**
 * 创建新项目
 * @param {string} name - 项目名称
 * @param {string} description - 项目描述（可选）
 * @returns {Promise<Object>} 创建结果
 */
export const createProject = async (name, description = '') => {
  const response = await api.post('/projects', { name, description })
  return response.data
}

/**
 * 更新项目
 * @param {number} projectId - 项目 ID
 * @param {Object} data - 更新数据 { name?, description?, status? }
 * @returns {Promise<Object>} 更新结果
 */
export const updateProject = async (projectId, data) => {
  const response = await api.put(`/projects/${projectId}`, data)
  return response.data
}

/**
 * 删除项目（软删除）
 * @param {number} projectId - 项目 ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteProject = async (projectId) => {
  const response = await api.delete(`/projects/${projectId}`)
  return response.data
}
