// 打卡接口：每日打卡、打卡状态和打卡历史。

import http from './http'

export const checkinApi = {
  calendar(params) {
    return http.get('/checkins/calendar/', { params })
  },
  today() {
    return http.post('/checkins/today/')
  },
}
