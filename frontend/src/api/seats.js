// 座位接口：座位列表、管理端座位维护、固定时间段维护。

import http from './http'

export const seatApi = {
  list(params) {
    return http.get('/seats/availability/', { params })
  },
  create(data) {
    return http.post('/seats/', data)
  },
  patch(id, data) {
    return http.patch(`/seats/${id}/`, data)
  },
  deleteSeat(id) {
    return http.delete(`/seats/${id}/`)
  },
  remainingSlots(id, params) {
    return http.get(`/seats/${id}/remaining-slots/`, { params })
  }
}
