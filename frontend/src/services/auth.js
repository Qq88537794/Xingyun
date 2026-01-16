import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

/**
 * 用户认证 API 服务
 */

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<Object>} 登录结果 { user, token }
 */
export const login = async (username, password) => {
    const response = await axios.post(
        `${API_BASE_URL}/auth/login`,
        { username, password },
        {
            headers: {
                'Content-Type': 'application/json'
            }
        }
    )
    return response.data
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} email - 邮箱
 * @param {string} password - 密码
 * @returns {Promise<Object>} 注册结果 { user, token }
 */
export const register = async (username, email, password) => {
    const response = await axios.post(
        `${API_BASE_URL}/auth/register`,
        { username, email, password },
        {
            headers: {
                'Content-Type': 'application/json'
            }
        }
    )
    return response.data
}

/**
 * 获取当前用户信息
 * @returns {Promise<Object>} 用户信息
 */
export const getCurrentUser = async () => {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    })
    return response.data.user
}

/**
 * 更新用户资料
 * @param {Object} data - 更新数据 { username?, email?, current_password?, new_password? }
 * @returns {Promise<Object>} 更新结果 { user }
 */
export const updateUserProfile = async (data) => {
    const token = localStorage.getItem('token')
    const response = await axios.put(
        `${API_BASE_URL}/auth/profile`,
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
