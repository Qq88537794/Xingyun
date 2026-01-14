import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

/**
 * 资源管理 API 服务
 */

/**
 * 获取项目的资源列表
 * @param {number} projectId - 项目 ID
 * @returns {Promise<Array>} 资源列表
 */
export const getResources = async (projectId) => {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_BASE_URL}/projects/${projectId}/resources`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    })
    return response.data.resources || []
}

/**
 * 上传资源文件
 * @param {number} projectId - 项目 ID
 * @param {File} file - 文件对象
 * @returns {Promise<Object>} 上传结果
 */
export const uploadResource = async (projectId, file) => {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/resources`,
        formData,
        {
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'multipart/form-data'
            }
        }
    )
    return response.data
}

/**
 * 通过文件路径上传资源（Electron 环境）
 * @param {number} projectId - 项目 ID
 * @param {string} filePath - 文件路径
 * @param {ArrayBuffer} fileContent - 文件内容
 * @param {string} fileName - 文件名
 * @returns {Promise<Object>} 上传结果
 */
export const uploadResourceFromPath = async (projectId, filePath, fileContent, fileName) => {
    const token = localStorage.getItem('token')

    // 创建 Blob 并转为 File
    const blob = new Blob([fileContent])
    const file = new File([blob], fileName)

    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/resources`,
        formData,
        {
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'multipart/form-data'
            }
        }
    )
    return response.data
}

/**
 * 删除资源
 * @param {number} projectId - 项目 ID
 * @param {number} resourceId - 资源 ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteResource = async (projectId, resourceId) => {
    const token = localStorage.getItem('token')
    const response = await axios.delete(
        `${API_BASE_URL}/projects/${projectId}/resources/${resourceId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    )
    return response.data
}
