import api from './api'

export const uploadImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 返回完整的URL
    // 假设后端返回的是相对路径，我们需要拼接 baseURL 的基础地址（去掉 /api）
    // 但后端返回的 url 已经是 /editor_images/xxx.png 这样的 path
    // 我们的 baseURL 是 http://localhost:5000/api
    // 所以我们需要 http://localhost:5000 + /editor_images/xxx.png
    
    // 简单的处理方式：后端直接返回相对路径，前端拼
    const baseUrl = api.defaults.baseURL.replace(/\/api$/, '')
    return `${baseUrl}${response.data.url}`
  } catch (error) {
    console.error('Image upload failed:', error)
    throw error
  }
}
