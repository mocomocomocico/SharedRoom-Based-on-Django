// 前端通用展示工具：统一日期、时长、徽标和柱状图高度计算，避免多个页面重复实现。

// 生成 <input type="date"> 可直接使用的本地日期字符串，格式为 YYYY-MM-DD。
export function todayString() {
  return new Date().toLocaleDateString('en-CA')
}

// 把分钟数格式化成更适合卡片展示的 h/m 文案。
export function formatMinutes(value) {
  const total = Number(value || 0)
  const h = Math.floor(total / 60)
  const m = total % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

// 预约状态到徽标样式的统一映射；所有页面都使用这套颜色语义。
export function getStatusBadgeClass(status) {
  if (status === 'booked') return 'warn'
  if (status === 'checked_in') return 'ok'
  if (status === 'completed') return 'ok'
  if (status === 'expired') return 'off'
  return 'neutral'
}

// 生成柱状图高度。minPercent 用于保证 0 值或低值也有可见的底部高度。
export function getBarHeightStyle(value, maxValue, minPercent = 8) {
  const safeMax = Math.max(1, Number(maxValue || 1))
  const percent = Math.max(minPercent, Math.round((Number(value || 0) / safeMax) * 100))
  return { height: `${percent}%` }
}
