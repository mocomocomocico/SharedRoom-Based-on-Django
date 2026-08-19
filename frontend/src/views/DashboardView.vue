<!--
  用户首页：聚合个人学习时长、预约提醒、打卡日历与学习报表。
  页面只负责展示和交互，通用格式化逻辑统一放在 utils/uiFormat.js。
-->
<template>
  <div class="dashboard-layout">
    <section class="card hero dashboard-hero-xl">
      <div class="hero-head hero-head-rich">
        <div>
          <h2>欢迎回来，{{ userName }}</h2>
          <p>这里把学习、预约、资料和信用分整合成一个总览页，避免在多个页面之间来回切换。</p>
        </div>
        <div class="hero-side-stack">
          <div class="today-box big">
            <span>今日日期</span>
            <strong>{{ summary.today_label || today }}</strong>
          </div>
          <div class="today-box">
            <span>今日状态</span>
            <strong>{{ summary.checkin_done_today ? '已打卡' : '待打卡' }}</strong>
          </div>
        </div>
      </div>

      <div class="metric-row metric-row-4">
        <div class="metric metric-rich">
          <strong>{{ formatMinutes(summary.study_minutes_today) }}</strong>
          <span>本日学习时长</span>
          <small>{{ summary.checkin_done_today ? '已完成今日打卡' : '建议先完成打卡' }}</small>
        </div>
        <div class="metric metric-rich">
          <strong>{{ formatMinutes(summary.study_minutes_month) }}</strong>
          <span>本月学习时长</span>
          <small>{{ analytics.monthly_report?.active_days ?? 0 }} 个有效学习日</small>
        </div>
        <div class="metric metric-rich">
          <strong>{{ summary.credit_score ?? 100 }}</strong>
          <span>当前信用分</span>
          <small>{{ summary.violation_count ?? 0 }} 次违规记录</small>
        </div>
        <div class="metric metric-rich">
          <strong>{{ upcomingReservation ? upcomingReservation.seat_code : '暂无' }}</strong>
          <span>最近预约</span>
          <small>{{ upcomingReservation ? `${upcomingReservation.start_time} - ${upcomingReservation.end_time}` : '去预约一个座位' }}</small>
        </div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-grid-home dashboard-grid-home-plus dashboard-grid-home-single">
      <div class="card mini-calendar-card">
        <div class="section-title">
          <div>
            <h3>每日打卡日历</h3>
            <p>绿色为已打卡，灰色为未打卡，可按月份查看习惯变化</p>
          </div>
          <button class="btn btn-primary btn-sm" @click="checkInToday">{{ summary.checkin_done_today ? '今日已打卡' : '今日打卡' }}</button>
        </div>

        <div class="mini-calendar-head">
          <button class="btn btn-ghost btn-sm" @click="prevMonth">‹</button>
          <strong>{{ calendarMonthLabel }}</strong>
          <button class="btn btn-ghost btn-sm" @click="nextMonth">›</button>
        </div>

        <div class="mini-calendar">
          <div v-for="day in weekdayLabels" :key="day" class="mini-calendar-weekday">{{ day }}</div>
          <div
            v-for="cell in flattenedDays"
            :key="cell.date"
            class="mini-calendar-cell"
            :class="cellClass(cell)"
          >
            {{ cell.day }}
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-analytics-grid dashboard-analytics-grid-wide">
      <div class="card">
        <div class="section-title">
          <div>
            <h3>近 7 天学习时长</h3>
            <p>周报可视化，按天统计签到后的有效学习分钟数</p>
          </div>
          <span class="badge neutral">总计 {{ formatMinutes(analytics.weekly_report?.total_minutes) }}</span>
        </div>
        <div class="bar-chart">
          <div v-for="item in analytics.weekly_chart" :key="item.date" class="bar-item">
            <div class="bar-value">{{ item.minutes }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="barStyle(item.minutes, weeklyMax)"></div>
            </div>
            <div class="bar-label">{{ item.label }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">
          <div>
            <h3>本月学习日报</h3>
            <p>按日期展示本月学习分钟数，柱子越高代表当天学习越久</p>
          </div>
          <div class="month-report-badges">
            <span class="badge neutral">平均 {{ analytics.monthly_report?.average_minutes ?? 0 }} 分钟/天</span>
            <span class="badge ok">活跃 {{ analytics.monthly_report?.active_days ?? 0 }} 天</span>
          </div>
        </div>
        <div class="mini-bar-chart month-report-chart">
          <div
            v-for="item in analytics.monthly_chart"
            :key="item.date"
            class="mini-bar-item month-report-item"
            :class="{ active: Number(item.minutes || 0) > 0 }"
            :title="`${item.label}：${item.minutes} 分钟`"
          >
            <div class="month-bar-value">{{ item.minutes || 0 }}</div>
            <div class="mini-bar-track">
              <div class="mini-bar-fill" :style="barStyle(item.minutes, monthlyMax)"></div>
            </div>
            <span>{{ item.label.replace('日', '') }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-analytics-grid dashboard-grid-home-plus">
      <div class="card">
        <div class="section-title">
          <div>
            <h3>近期预约与待办</h3>
            <p>把最重要的预约提醒放到首页，可翻页查看全部当前预约</p>
          </div>
          <RouterLink class="btn btn-secondary btn-sm" to="/reserve">去选座位</RouterLink>
        </div>
        <div v-if="upcomingReservations.length" class="reservation-list compact-list">
          <div class="reservation-item" v-for="item in paginatedUpcomingReservations" :key="item.id">
            <div>
              <div class="reservation-title">{{ item.seat_code }} · {{ item.reservation_date }}</div>
              <div class="reservation-meta">{{ item.start_time }} - {{ item.end_time }} · {{ item.duration_minutes }} 分钟</div>
              <div class="reservation-meta">签到截止：{{ item.checkin_deadline }}</div>
            </div>
            <div class="reservation-actions">
              <span class="badge" :class="statusBadge(item.status)">{{ item.status_label }}</span>
              <button v-if="item.status === 'booked'" class="btn btn-success btn-sm" @click="checkReservationIn(item.id)">签到</button>
              <button v-if="item.status === 'checked_in'" class="btn btn-warning btn-sm" @click="checkReservationOut(item.id)">签退</button>
            </div>
          </div>
        </div>
        <PaginationBar
          v-if="upcomingReservations.length"
          v-model="upcomingPage"
          :total="upcomingReservations.length"
          :page-size="upcomingPageSize"
        />
        <div v-else class="notice">当前没有待处理预约，去预约页挑个喜欢的位置吧。</div>
      </div>

      <div class="card">
        <div class="section-title">
          <div>
            <h3>学习周报</h3>
            <p>一眼看完本周投入情况</p>
          </div>
        </div>
        <div class="status-list">
          <div class="status-line"><span>周学习总时长</span><strong>{{ formatMinutes(analytics.weekly_report?.total_minutes) }}</strong></div>
          <div class="status-line"><span>周活跃天数</span><strong>{{ analytics.weekly_report?.active_days ?? 0 }}</strong></div>
          <div class="status-line"><span>周平均投入</span><strong>{{ analytics.weekly_report?.average_minutes ?? 0 }} 分钟/天</strong></div>
        </div>
      </div>
    </section>

    <NoticePopup
      v-model="popup.visible"
      :title="popup.title"
      :message="popup.message"
      :type="popup.type"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { reservationApi } from '../api/reservations'
import { checkinApi } from '../api/checkins'
import NoticePopup from '../components/NoticePopup.vue'
import PaginationBar from '../components/PaginationBar.vue'
import { formatMinutes, getBarHeightStyle as barStyle, getStatusBadgeClass as statusBadge, todayString } from '../utils/uiFormat'

const popup = reactive({ visible: false, type: 'success', title: '提示', message: '' })
const today = todayString()
const currentUser = JSON.parse(localStorage.getItem('user') || 'null')
const userName = currentUser?.nickname || currentUser?.username || '同学'
const summary = ref({
  today_label: today,
  study_minutes_today: 0,
  study_minutes_month: 0,
  checkin_done_today: false,
  checkin_count_month: 0,
  credit_score: 100,
  violation_count: 0,
})
const analytics = ref({
  weekly_chart: [],
  monthly_chart: [],
  weekly_report: {},
  monthly_report: {},
})
const upcomingReservations = ref([])
const upcomingPage = ref(1)
const upcomingPageSize = 4
const calendarData = ref({ weeks: [], month_label: '', checked_dates: [] })
const calendarYear = ref(new Date().getFullYear())
const calendarMonth = ref(new Date().getMonth() + 1)

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']
const flattenedDays = computed(() => calendarData.value.weeks.flat())
const calendarMonthLabel = computed(() => calendarData.value.month_label || `${calendarYear.value}年${calendarMonth.value}月`)
const weeklyMax = computed(() => Math.max(60, ...((analytics.value.weekly_chart || []).map(item => item.minutes || 0))))
const monthlyMax = computed(() => Math.max(60, ...((analytics.value.monthly_chart || []).map(item => item.minutes || 0))))
const upcomingReservation = computed(() => upcomingReservations.value[0] || null)
const paginatedUpcomingReservations = computed(() => {
  const start = (upcomingPage.value - 1) * upcomingPageSize
  return upcomingReservations.value.slice(start, start + upcomingPageSize)
})


function cellClass(cell) {
  return {
    checked: !!cell.checked,
    unchecked: !cell.checked,
    today: !!cell.is_today,
    outside: !cell.in_month,
  }
}


function showPopup(type, title, message) {
  popup.type = type
  popup.title = title
  popup.message = message
  popup.visible = true
}

async function loadSummary() {
  const res = await reservationApi.summary()
  summary.value = res.data || {}
}

async function loadAnalytics() {
  const res = await reservationApi.analytics()
  analytics.value = res.data || { weekly_chart: [], monthly_chart: [], weekly_report: {}, monthly_report: {} }
}

async function loadCalendar() {
  const res = await checkinApi.calendar({ year: calendarYear.value, month: calendarMonth.value })
  calendarData.value = res.data || { weeks: [], month_label: '', checked_dates: [] }
}

async function loadReservations() {
  const [bookedRes, checkedRes] = await Promise.all([
    reservationApi.mine({ status: 'booked' }),
    reservationApi.mine({ status: 'checked_in' }),
  ])
  upcomingReservations.value = [...(bookedRes.data || []), ...(checkedRes.data || [])]
    .sort((a, b) => `${a.reservation_date} ${a.start_time}`.localeCompare(`${b.reservation_date} ${b.start_time}`))
  const totalPages = Math.max(1, Math.ceil(upcomingReservations.value.length / upcomingPageSize))
  if (upcomingPage.value > totalPages) upcomingPage.value = totalPages
}

async function checkInToday() {
  try {
    const res = await checkinApi.today()
    showPopup('success', '打卡提醒', res.data.detail || '今日打卡成功')
    await Promise.all([loadSummary(), loadAnalytics(), loadCalendar()])
  } catch (e) {
    showPopup('error', '打卡失败', e.response?.data?.detail || '今日打卡失败')
  }
}

async function checkReservationIn(id) {
  try {
    const res = await reservationApi.checkIn(id)
    showPopup('success', '签到成功', res.data.detail || '签到成功')
    await Promise.all([loadSummary(), loadAnalytics(), loadReservations()])
  } catch (e) {
    showPopup('error', '签到失败', e.response?.data?.detail || '签到失败')
  }
}

async function checkReservationOut(id) {
  try {
    const res = await reservationApi.checkOut(id)
    showPopup('success', '签退成功', res.data.detail || '签退成功')
    await Promise.all([loadSummary(), loadAnalytics(), loadReservations()])
  } catch (e) {
    showPopup('error', '签退失败', e.response?.data?.detail || '签退失败')
  }
}

async function prevMonth() {
  if (calendarMonth.value === 1) {
    calendarMonth.value = 12
    calendarYear.value -= 1
  } else {
    calendarMonth.value -= 1
  }
  await loadCalendar()
}

async function nextMonth() {
  if (calendarMonth.value === 12) {
    calendarMonth.value = 1
    calendarYear.value += 1
  } else {
    calendarMonth.value += 1
  }
  await loadCalendar()
}

onMounted(async () => {
  try {
    await Promise.all([loadSummary(), loadAnalytics(), loadCalendar(), loadReservations()])
  } catch (e) {
    showPopup('error', '加载失败', e.response?.data?.detail || '首页数据加载失败')
  }
})
</script>


<style scoped>
.dashboard-grid-home-single {
  grid-template-columns: 1fr;
}
</style>
