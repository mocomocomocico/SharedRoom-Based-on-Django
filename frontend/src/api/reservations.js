// 预约接口：用户预约/取消/历史，以及管理端预约列表与统计。
import http from './http'

export const reservationApi = {
  book(data) {
    return http.post('/reservations/book/', data)
  },
  cancel(reservation_id) {
    return http.post('/reservations/cancel/', { reservation_id })
  },
  checkIn(reservation_id) {
    return http.post('/reservations/checkin/', { reservation_id })
  },
  checkOut(reservation_id) {
    return http.post('/reservations/checkout/', { reservation_id })
  },
  mine(params) {
    return http.get('/reservations/my/', { params })
  },
  admin(params) {
    return http.get('/reservations/admin/', { params })
  },
  summary() {
    return http.get('/dashboard/summary/')
  },
  analytics() {
    return http.get('/dashboard/analytics/')
  }
}
