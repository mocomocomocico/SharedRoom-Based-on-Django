<!--
  预约历史页：负责历史记录筛选、KPI 统计，以及状态分布/日期趋势可视化。
  图表高度和状态徽标走通用工具，保持与首页图表同一套视觉语义。
-->
<template>
  <div class="page-stack history-page history-page-simple history-page-visual">
    <section class="card">
      <div class="section-title">
        <div>
          <h3>历史预约数据可视化</h3>
          <p>基于当前筛选结果自动生成，帮助你快速看清预约总量、状态分布与日期趋势。</p>
        </div>
        <span class="badge neutral">{{ reservations.length }} 条记录</span>
      </div>

      <div v-if="reservations.length" class="history-visual-grid">
        <div class="history-kpi-grid">
          <div class="metric metric-rich history-kpi-card">
            <strong>{{ reservations.length }}</strong>
            <span>预约总数</span>
            <small>当前筛选结果中的全部预约</small>
          </div>
          <div class="metric metric-rich history-kpi-card">
            <strong>{{ totalDurationHours }}</strong>
            <span>累计时长</span>
            <small>按预约分钟数自动折算</small>
          </div>
          <div class="metric metric-rich history-kpi-card">
            <strong>{{ completedCount }}</strong>
            <span>已完成预约</span>
            <small>已签退或已完成的历史记录</small>
          </div>
          <div class="metric metric-rich history-kpi-card">
            <strong>{{ completionRate }}%</strong>
            <span>完成率</span>
            <small>已完成预约 ÷ 全部预约</small>
          </div>
        </div>

        <div class="history-chart-grid history-chart-grid-refined">
          <div class="card light history-chart-card history-status-card history-analysis-card">
            <div class="section-title compact-title">
              <div>
                <h3>状态分布</h3>
                <p>查看不同状态下的预约数量</p>
              </div>
              <span class="badge neutral">{{ statusChart.filter(item => item.count > 0).length }} 类状态</span>
            </div>
            <div class="bar-chart history-bar-chart history-status-bar-chart">
              <div
                v-for="item in statusChart"
                :key="item.key"
                class="bar-item history-status-bar-item"
                :class="{ active: item.count > 0 }"
                :title="`${item.label}：${item.count} 条`"
              >
                <div class="bar-value">{{ item.count }}</div>
                <div class="bar-track">
                  <div class="bar-fill" :style="barStyle(item.count, statusMax)"></div>
                </div>
                <div class="bar-label">{{ item.label }}</div>
              </div>
            </div>
          </div>

          <div class="card light history-chart-card history-trend-card history-analysis-card">
            <div class="section-title compact-title">
              <div>
                <h3>按日期趋势</h3>
                <p>按预约日期统计数量，快速观察近期波动</p>
              </div>
              <span class="badge ok">{{ dateTrend.length }} 天</span>
            </div>
            <div class="bar-chart history-bar-chart history-trend-bar-chart">
              <div
                v-for="item in dateTrend"
                :key="item.date"
                class="bar-item history-trend-bar-item"
                :class="{ active: Number(item.count || 0) > 0 }"
                :title="`${item.date}：${item.count} 条预约，${item.minutes} 分钟`"
              >
                <div class="bar-value">{{ item.count }}</div>
                <div class="bar-track">
                  <div class="bar-fill" :style="barStyle(item.count, trendMax)"></div>
                </div>
                <div class="bar-label">{{ item.label }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="notice">暂无可视化数据，先去完成几次预约后再来看趋势吧。</div>
    </section>

    <section class="card">
      <div class="section-title">
        <div>
          <h3>预约历史记录</h3>
          <p>可按日期和状态筛选，并直接处理待取消预约。</p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="loadReservations">刷新</button>
      </div>

      <div class="toolbar admin-toolbar history-toolbar-grid">
        <div class="field">
          <label>筛选日期</label>
          <input class="input" type="date" v-model="filters.date" @change="loadReservations" />
        </div>
        <div class="field">
          <label>状态</label>
          <select class="input" v-model="filters.status" @change="loadReservations">
            <option value="">全部</option>
            <option value="booked">已预约</option>
            <option value="checked_in">已签到</option>
            <option value="completed">已签退</option>
            <option value="cancelled">已取消</option>
            <option value="expired">已过期</option>
          </select>
        </div>
        <div class="field">
          <label>&nbsp;</label>
          <button class="btn btn-primary" @click="resetFilters">重置筛选</button>
        </div>
      </div>

      <div v-if="reservations.length" class="reservation-list history-list">
        <div class="reservation-item reservation-item-rich" v-for="item in paginatedReservations" :key="item.id">
          <div>
            <div class="reservation-title">{{ item.seat_code }} · {{ item.reservation_date }}</div>
            <div class="reservation-meta">{{ item.start_time }} - {{ item.end_time }} · {{ item.duration_minutes }} 分钟 · {{ item.status_label }}</div>
            <div class="reservation-meta">签到截止：{{ item.checkin_deadline }}</div>
            <div class="reservation-meta" v-if="item.note">预约备注：{{ item.note }}</div>
          </div>
          <div class="reservation-actions reservation-actions-vertical">
            <span class="badge" :class="badgeClass(item.status)">{{ item.status_label }}</span>
            <button v-if="item.status === 'booked'" class="btn btn-danger btn-sm" @click="cancelReservation(item.id)">取消预约</button>
          </div>
        </div>
      </div>
      <PaginationBar
        v-if="reservations.length"
        v-model="currentPage"
        :total="reservations.length"
        :page-size="pageSize"
      />
      <div v-else class="notice">当前没有符合条件的历史记录。</div>
    </section>

    <div v-if="message" class="notice success">{{ message }}</div>
    <div v-if="error" class="notice error">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { reservationApi } from '../api/reservations'
import PaginationBar from '../components/PaginationBar.vue'
import { getBarHeightStyle as baseBarStyle, getStatusBadgeClass as badgeClass } from '../utils/uiFormat'

const reservations = ref([])
const message = ref('')
const error = ref('')
const filters = reactive({ date: '', status: '' })
const currentPage = ref(1)
const pageSize = 6

const statusMeta = [
  { key: 'booked', label: '已预约' },
  { key: 'checked_in', label: '已签到' },
  { key: 'completed', label: '已签退' },
  { key: 'cancelled', label: '已取消' },
  { key: 'expired', label: '已过期' },
]

const totalDurationMinutes = computed(() => reservations.value.reduce((sum, item) => sum + Number(item.duration_minutes || 0), 0))
const totalDurationHours = computed(() => `${(totalDurationMinutes.value / 60).toFixed(1)} 小时`)
const completedCount = computed(() => reservations.value.filter((item) => item.status === 'completed').length)
const completionRate = computed(() => {
  if (!reservations.value.length) return 0
  return Math.round((completedCount.value / reservations.value.length) * 100)
})

// 状态分布只依赖当前筛选结果，切换日期/状态后图表会自动跟随刷新。
const statusChart = computed(() => statusMeta.map((status) => ({
  ...status,
  count: reservations.value.filter((item) => item.status === status.key).length,
})))

const statusMax = computed(() => Math.max(1, ...statusChart.value.map((item) => item.count || 0)))

// 日期趋势聚合为最近 7 个日期桶，避免历史记录变多后柱子过密。
const dateTrend = computed(() => {
  const buckets = new Map()
  reservations.value.forEach((item) => {
    const date = item.reservation_date || '未设置日期'
    const current = buckets.get(date) || { date, count: 0, minutes: 0 }
    current.count += 1
    current.minutes += Number(item.duration_minutes || 0)
    buckets.set(date, current)
  })

  return Array.from(buckets.values())
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-7)
    .map((item) => ({
      ...item,
      label: item.date.includes('-') ? item.date.slice(5).replace('-', '/') : item.date,
    }))
})

const trendMax = computed(() => Math.max(1, ...dateTrend.value.map((item) => item.count || 0)))
const totalPages = computed(() => Math.max(1, Math.ceil(reservations.value.length / pageSize)))
const paginatedReservations = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return reservations.value.slice(start, start + pageSize)
})


// 历史页的 0 值柱子需要更轻盈，因此最小高度略低于首页。
function barStyle(value, max) {
  return baseBarStyle(value, max, 6)
}

function resetFilters() {
  currentPage.value = 1
  filters.date = ''
  filters.status = ''
  loadReservations()
}

async function loadReservations() {
  currentPage.value = 1
  message.value = ''
  error.value = ''
  try {
    const params = {}
    if (filters.date) params.date = filters.date
    if (filters.status) params.status = filters.status
    const res = await reservationApi.mine(params)
    const next = Array.isArray(res.data) ? res.data : []
    reservations.value = next.sort((a, b) => {
      const left = `${b.reservation_date || ''} ${b.start_time || ''}`
      const right = `${a.reservation_date || ''} ${a.start_time || ''}`
      return left.localeCompare(right)
    })
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

async function cancelReservation(id) {
  message.value = ''
  error.value = ''
  try {
    const res = await reservationApi.cancel(id)
    message.value = res.data.detail
    await loadReservations()
  } catch (e) {
    error.value = e.response?.data?.detail || '取消失败'
  }
}

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

onMounted(loadReservations)
</script>
