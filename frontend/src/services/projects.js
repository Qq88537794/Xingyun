import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

/**
 * 项目管理 API 服务
 */

/**
 * 获取当前用户的项目列表
 * @returns {Promise<Array>} 项目列表
 */
export const getProjects = async () => {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_BASE_URL}/projects`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    })
    return response.data.projects || []
}

/**
 * 获取单个项目详情
 * @param {number} projectId - 项目 ID
 * @param {boolean} includeResources - 是否包含资源
 * @returns {Promise<Object>} 项目详情
 */
export const getProject = async (projectId, includeResources = false) => {
    const token = localStorage.getItem('token')
    const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}?include_resources=${includeResources}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
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
    const token = localStorage.getItem('token')
    const response = await axios.post(
        `${API_BASE_URL}/projects`,
        { name, description },
        {
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }
    )
    return response.data
}

/**
 * 更新项目
 * @param {number} projectId - 项目 ID
 * @param {Object} data - 更新数据 { name?, description?, status? }
 * @returns {Promise<Object>} 更新结果
 */
export const updateProject = async (projectId, data) => {
    const token = localStorage.getItem('token')
    const response = await axios.put(
        `${API_BASE_URL}/projects/${projectId}`,
        data,
        {
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }
    )
    return response.data
}

/**
 * 删除项目（软删除）
 * @param {number} projectId - 项目 ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteProject = async (projectId) => {
    const token = localStorage.getItem('token')
    const response = await axios.delete(
        `${API_BASE_URL}/projects/${projectId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    )
    return response.data
}
