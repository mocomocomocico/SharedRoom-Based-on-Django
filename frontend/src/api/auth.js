// 账号与用户管理接口：登录、注册、个人资料、管理端用户 CRUD。
import http from './http'

export const authApi = {
  login(data) {
    return http.post('/auth/login/', data)
  },
  register(data) {
    return http.post('/auth/register/', data)
  },
  profile() {
    return http.get('/auth/profile/')
  },
  updateProfile(data) {
    return http.patch('/auth/profile/', data)
  },
  changePassword(data) {
    return http.post('/auth/profile/change-password/', data)
  },
  myViolations() {
    return http.get('/auth/violations/me/')
  },
  adminViolations(params) {
    return http.get('/auth/admin/violations/', { params })
  },
  createViolation(data) {
    return http.post('/auth/admin/violations/', data)
  },
  adminUsers(params) {
    return http.get('/auth/admin/users/', { params })
  },
  adminUserDetail(id) {
    return http.get(`/auth/admin/users/${id}/`)
  },
  updateAdminUser(id, data) {
    return http.patch(`/auth/admin/users/${id}/`, data)
  },
  resetAdminUserPassword(id) {
    return http.post(`/auth/admin/users/${id}/`, { action: 'reset_password' })
  },
  deleteAdminUser(id) {
    return http.delete(`/auth/admin/users/${id}/`)
  }
}
