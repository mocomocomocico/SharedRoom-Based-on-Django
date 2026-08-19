<template>
  <div class="grid" style="gap: 18px;">
    <section class="card hero">
      <div class="badge ok">每日打卡</div>
      <h2>用日历查看每日打卡状态</h2>
      <p>绿色代表已打卡，灰色代表未打卡。你也可以直接完成今天的打卡。</p>

      <div class="metric-row">
        <div class="metric">
          <strong>{{ calendarData.checked_count || 0 }}</strong>
          <span>本月已打卡</span>
        </div>
        <div class="metric">
          <strong>{{ totalDays }}</strong>
          <span>当月总天数</span>
        </div>
        <div class="metric">
          <strong>{{ monthLabel }}</strong>
          <span>当前月份</span>
        </div>
      </div>
    </section>

    <section class="card light">
      <div class="section-title">
        <div>
          <h3>打卡日历</h3>
          <p>点击上方按钮可切换月份，也可以直接完成今日打卡</p>
        </div>
        <div class="toolbar" style="gap: 8px;">
          <button class="btn btn-secondary btn-sm" type="button" @click="prevMonth">上个月</button>
          <button class="btn btn-secondary btn-sm" type="button" @click="goToday">本月</button>
          <button class="btn btn-secondary btn-sm" type="button" @click="nextMonth">下个月</button>
          <button class="btn btn-primary btn-sm" type="button" @click="checkInToday" :disabled="checkingIn">
            {{ checkingIn ? '打卡中...' : '今日打卡' }}
          </button>
        </div>
      </div>

      <div class="calendar-shell" v-if="calendarData.weeks.length">
        <div class="calendar-weekdays">
          <div v-for="day in weekdayLabels" :key="day">{{ day }}</div>
        </div>

        <div class="calendar-grid">
          <div
            v-for="cell in flattenedDays"
            :key="cell.date"
            class="calendar-cell"
            :class="cellClass(cell)"
          >
            <div class="calendar-day-top">
              <strong>{{ cell.day }}</strong>
              <span v-if="cell.is_today" class="calendar-today-tag">今天</span>
            </div>
            <div class="calendar-state">{{ cell.checked ? '已打卡' : '未打卡' }}</div>
          </div>
        </div>
      </div>

      <div v-else class="notice">正在加载日历...</div>
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
import { checkinApi } from '../api/checkins'
import NoticePopup from '../components/NoticePopup.vue'

const popup = reactive({ visible: false, type: 'success', title: '提示', message: '' })
const checkingIn = ref(false)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const calendarData = ref({ weeks: [], checked_count: 0, month_days: 0, month_label: '' })

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']
const flattenedDays = computed(() => calendarData.value.weeks.flat())
const monthLabel = computed(() => calendarData.value.month_label || `${currentYear.value}年${currentMonth.value}月`)
const totalDays = computed(() => calendarData.value.month_days || 0)

function cellClass(cell) {
  return {
    checked: !!cell.checked,
    unchecked: !cell.checked,
    outside: !cell.in_month,
    today: !!cell.is_today,
  }
}

async function loadCalendar() {
  try {
    const res = await checkinApi.calendar({ year: currentYear.value, month: currentMonth.value })
    calendarData.value = res.data || { weeks: [] }
  } catch (e) {
    popup.type = 'error'
    popup.title = '加载失败'
    popup.message = e.response?.data?.detail || '加载打卡日历失败'
    popup.visible = true
  }
}

function prevMonth() {
  const date = new Date(currentYear.value, currentMonth.value - 2, 1)
  currentYear.value = date.getFullYear()
  currentMonth.value = date.getMonth() + 1
  loadCalendar()
}

function nextMonth() {
  const date = new Date(currentYear.value, currentMonth.value, 1)
  currentYear.value = date.getFullYear()
  currentMonth.value = date.getMonth() + 1
  loadCalendar()
}

function goToday() {
  const now = new Date()
  currentYear.value = now.getFullYear()
  currentMonth.value = now.getMonth() + 1
  loadCalendar()
}

async function checkInToday() {
  checkingIn.value = true
  try {
    const res = await checkinApi.today()
    popup.type = 'success'
    popup.title = '打卡成功'
    popup.message = res.data.detail || '今日打卡成功'
    popup.visible = true
    await loadCalendar()
  } catch (e) {
    popup.type = 'error'
    popup.title = '打卡失败'
    popup.message = e.response?.data?.detail || '打卡失败'
    popup.visible = true
  } finally {
    checkingIn.value = false
  }
}

onMounted(loadCalendar)
</script>
