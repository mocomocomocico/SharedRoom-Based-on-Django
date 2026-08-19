// 学习资料接口：上传、共享、下载、管理端资料审核/删除。
import http from './http'

export const materialApi = {
  list(params = {}) {
    return http.get('/materials/', { params })
  },
  upload(formData) {
    return http.post('/materials/', formData)
  },
  update(id, data) {
    return http.patch(`/materials/${id}/`, data)
  },
  download(id) {
    return http.get(`/materials/${id}/download/`, { responseType: 'blob' })
  },
  delete(id) {
    return http.delete(`/materials/${id}/`)
  },
}
