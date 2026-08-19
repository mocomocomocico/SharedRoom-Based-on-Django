<!--
  用户选座页：固定平面图 + 座位弹窗预约。
  筛选、可预约时段和我的预约弹窗都在本页面统一管理。
-->
<template>
  <div class="page-stack reservation-page">
    <section class="card hero reservation-hero reservation-hero-plus">
      <div class="hero-head hero-head-rich">
        <div>
          <h2>固定平面图视图，点击座位即可弹窗预约</h2>
          <p>当前页面仅保留座位平面图，点击任意座位会直接弹出预约窗口；窗口内可选择开始时间和结束时间完成预约。</p>
        </div>
        <div class="hero-side-stack reservation-hero-actions">
          <div class="today-box big">
            <span>预约日期</span>
            <strong>{{ selectedDate }}</strong>
          </div>
          <div class="today-box">
            <span>推荐座位</span>
            <strong>{{ recommendedSeat ? recommendedSeat.seat_code : '暂无' }}</strong>
          </div>
          <button class="btn btn-secondary" type="button" @click="openMyReservationsModal">
            我的预约（{{ activeReservations.length }}）
          </button>
        </div>
      </div>

      <div class="metric-row metric-row-4">
        <div class="metric metric-rich">
          <strong>{{ filteredSeats.length }}</strong>
          <span>当前可浏览座位</span>
          <small>共 {{ seats.length }} 个座位</small>
        </div>
        <div class="metric metric-rich">
          <strong>{{ availableSeatCount }}</strong>
          <span>当前可预约座位</span>
          <small>已过滤不可预约与满座状态</small>
        </div>
        <div class="metric metric-rich metric-button-card">
          <button class="metric-inline-button" type="button" @click="openMyReservationsModal">
            <strong>{{ activeReservations.length }}</strong>
            <span>我的当前预约</span>
            <small>{{ activeReservations[0]?.seat_code || '点击查看详情' }}</small>
          </button>
        </div>
        <div class="metric metric-rich">
          <strong>{{ summary.credit_score ?? 100 }}</strong>
          <span>当前信用分</span>
          <small>{{ summary.violation_count ?? 0 }} 次违规</small>
        </div>
      </div>
    </section>

    <section v-if="lowCreditBlocked" class="notice error reservation-credit-limit">
      当前信用分为 {{ summary.credit_score ?? 0 }} 分，低于 60 分，暂时无法预约座位。你仍然可以点击座位查看时段，但无法提交预约。
    </section>

    <section class="card seat-panel seat-panel-wide">
      <div class="section-title">
        <div>
          <h3>座位平面图</h3>
          <p>平面图尺寸已固定；当前第 {{ seatPage }} / {{ seatTotalPages }} 页，点击座位后会直接弹出预约窗口</p>
        </div>
        <div class="toolbar toolbar-tight reservation-toolbar-top">
          <div class="field compact-field">
            <label>预约日期</label>
            <input class="input" type="date" v-model="selectedDate" />
          </div>
          <button class="btn btn-secondary btn-sm" type="button" @click="openMyReservationsModal">我的预约</button>
          <button class="btn btn-secondary btn-sm" type="button" @click="reloadAll">刷新</button>
        </div>
      </div>

      <div class="toolbar admin-toolbar reservation-filter-grid">
        <div class="field">
          <label>关键字</label>
          <input class="input" v-model="filters.keyword" placeholder="座位编号 / 区域 / 备注" />
        </div>
        <div class="field">
          <label>座位类型</label>
          <select class="input" v-model="filters.seatType">
            <option value="">全部</option>
            <option value="normal">普通位</option>
            <option value="quiet">安静位</option>
            <option value="window">靠窗位</option>
            <option value="power">插座位</option>
          </select>
        </div>
        <div class="field">
          <label>可预约状态</label>
          <select class="input" v-model="filters.availability">
            <option value="all">全部</option>
            <option value="available">仅看可预约</option>
            <option value="full">仅看已满</option>
          </select>
        </div>
      </div>

      <div class="filter-check-row">
        <label class="check-line"><input type="checkbox" v-model="filters.hasPower" />仅看插座位</label>
        <label class="check-line"><input type="checkbox" v-model="filters.nearWindow" />仅看靠窗位</label>
        <button class="btn btn-ghost btn-sm" type="button" @click="resetFilters">清空筛选</button>
      </div>

      <div class="seat-legend">
        <span><i class="legend-dot available"></i>可预约</span>
        <span><i class="legend-dot full"></i>已约满</span>
        <span><i class="legend-dot inactive"></i>不可用</span>
      </div>

      <div v-if="loading" class="notice">正在加载座位数据...</div>
      <div v-else-if="!filteredSeats.length" class="notice">当前没有符合筛选条件的座位。</div>

      <div v-else class="seat-map-fixed">
        <div class="seat-map-shell">
          <div class="map-axis-header" :style="gridColumnStyle">
            <span></span>
            <span v-for="col in maxCols" :key="`col-${col}`">{{ col }}</span>
          </div>
          <div class="seat-map-grid" :style="gridStyle">
            <template v-for="row in seatMapRows" :key="`row-${row.row}`">
              <div class="map-row-label">{{ row.row }}</div>
              <button
                v-for="(cell, cellIndex) in row.cells"
                :key="cell ? `seat-${cell.id}` : `empty-${row.row}-${cellIndex}`"
                class="seat-map-cell"
                :class="seatMapClass(cell)"
                :disabled="!cell"
                type="button"
                @click="cell && openSeatModal(cell)"
              >
                <template v-if="cell">
                  <strong>{{ cell.seat_code }}</strong>
                  <span>{{ cell.area || '未分区' }}</span>
                  <small>{{ cell.remaining_minutes || 0 }} 分钟</small>
                </template>
              </button>
            </template>
          </div>
        </div>
      </div>

      <PaginationBar
        v-if="filteredSeats.length"
        v-model="seatPage"
        :total="filteredSeats.length"
        :page-size="seatPageSize"
      />
    </section>

    <NoticePopup v-model="popup.visible" :title="popup.title" :message="popup.message" :type="popup.type" />

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="modalOpen" class="modal-backdrop modal-backdrop-centered" @click.self="closeModal">
          <div class="modal-card seat-modal seat-booking-modal">
            <div class="section-title">
              <div>
                <h3>预约座位</h3>
                <p>选择开始时间和结束时间，系统会自动校验是否可预约</p>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="closeModal">关闭</button>
            </div>

            <div v-if="selectedSeatLoading" class="notice">正在加载剩余时间段...</div>
            <div v-else-if="selectedSeatDetail" class="seat-detail-box">
              <div class="seat-head">
                <div>
                  <div class="seat-code">{{ selectedSeatDetail.seat.seat_code }}</div>
                  <div class="seat-meta">{{ selectedSeatDetail.seat.area || '未设置区域' }} · {{ selectedSeatDetail.seat.seat_type_label }}</div>
                </div>
                <span class="badge" :class="selectedSeatDetail.is_full ? 'off' : 'ok'">
                  {{ selectedSeatDetail.is_full ? '已预满' : `${selectedSeatDetail.remaining_minutes} 分钟可预约` }}
                </span>
              </div>

              <div class="tag-row">
                <span class="seat-tag" v-if="selectedSeatDetail.seat.has_power">插座位</span>
                <span class="seat-tag" v-if="selectedSeatDetail.seat.near_window">靠窗位</span>
                <span class="seat-tag">坐标 {{ selectedSeatDetail.seat.map_row }} - {{ selectedSeatDetail.seat.map_col }}</span>
              </div>

              <div v-if="lowCreditBlocked" class="notice error">
                当前信用分为 {{ summary.credit_score ?? 0 }} 分，低于 60 分，暂时无法提交预约。
              </div>

              <div class="slot-summary">
                <div class="slot-summary-head">
                  <strong>当前剩余可预约时间</strong>
                  <span>点击即可自动带入开始时间与结束时间</span>
                </div>
                <div class="range-chip-list">
                  <button
                    v-for="range in selectedSeatDetail.remaining_ranges"
                    :key="range.label"
                    class="range-chip"
                    type="button"
                    @click="applyRange(range)"
                  >
                    {{ range.label }} · {{ range.duration_minutes }} 分钟
                  </button>
                </div>
                <div v-if="!selectedSeatDetail.remaining_ranges.length" class="notice">这个日期已经没有可预约时间段了。</div>
              </div>

              <div v-if="selectedSeatDetail.occupied_reservations?.length" class="slot-summary">
                <div class="slot-summary-head">
                  <strong>当前占用情况</strong>
                  <span>可看到预约人和预计释放时间</span>
                </div>
                <div class="occupied-list">
                  <div v-for="item in selectedSeatDetail.occupied_reservations" :key="item.id" class="occupied-item">
                    <div>
                      <div class="reservation-title">{{ item.user_display_name || item.user_username }}</div>
                      <div class="reservation-meta">{{ item.start_time }} - {{ item.end_time }} · {{ item.duration_minutes }} 分钟 · {{ item.status_label }}</div>
                    </div>
                    <span class="badge" :class="statusBadge(item.status)">{{ item.status_label }}</span>
                  </div>
                </div>
              </div>

              <div class="booking-form booking-form-modal">
                <div class="field">
                  <label>开始时间</label>
                  <input class="input" type="time" step="900" v-model="bookingForm.start_time" />
                </div>
                <div class="field">
                  <label>结束时间</label>
                  <input class="input" type="time" step="900" v-model="bookingForm.end_time" />
                </div>
                <div class="field">
                  <label>预约时长</label>
                  <input class="input" :value="bookingDurationLabel || '-'" readonly />
                </div>
                <div v-if="bookingDisabledReason" class="notice error">{{ bookingDisabledReason }}</div>
                <div class="field">
                  <label>备注</label>
                  <input class="input" v-model="bookingForm.note" placeholder="可选备注" />
                </div>
                <div class="modal-actions">
                  <button class="btn btn-secondary" type="button" @click="clearForm">重置</button>
                  <button class="btn btn-primary" type="button" :disabled="bookingDisabled" @click="bookSelectedSeat">
                    {{ bookingSeatId === selectedSeatId ? '预约中...' : '确认预约' }}
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="notice">请选择一个座位。</div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="myReservationsOpen" class="modal-backdrop modal-backdrop-centered" @click.self="closeMyReservationsModal">
          <div class="modal-card seat-modal reservations-modal-card">
            <div class="section-title">
              <div>
                <h3>我的预约</h3>
                <p>集中查看当前预约，并直接执行签到、签退和取消操作</p>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="closeMyReservationsModal">关闭</button>
            </div>

            <div v-if="activeReservations.length" class="reservation-list reservation-list-large">
              <div class="reservation-item reservation-item-wide reservation-item-modal" v-for="item in paginatedActiveReservations" :key="item.id">
                <div class="reservation-main-copy">
                  <div class="reservation-title">{{ item.seat_code }} · {{ item.reservation_date }}</div>
                  <div class="reservation-meta">{{ item.start_time }} - {{ item.end_time }} · {{ item.duration_minutes }} 分钟 · {{ item.status_label }}</div>
                  <div class="reservation-meta">签到截止：{{ item.checkin_deadline }}</div>
                </div>
                <div class="reservation-actions reservation-actions-row">
                  <span class="badge" :class="statusBadge(item.status)">{{ item.status_label }}</span>
                  <button v-if="item.status === 'booked'" class="btn btn-success btn-sm" @click="checkIn(item.id)">签到</button>
                  <button v-if="item.status === 'checked_in'" class="btn btn-warning btn-sm" @click="checkOut(item.id)">签退</button>
                  <button v-if="item.status === 'booked'" class="btn btn-danger btn-sm" @click="cancelReservation(item.id)">取消</button>
                </div>
              </div>
            </div>
            <PaginationBar
              v-if="activeReservations.length"
              v-model="myReservationsPage"
              :total="activeReservations.length"
              :page-size="myReservationsPageSize"
            />
            <div v-else class="notice">当前没有预约记录。</div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { seatApi } from '../api/seats'
import { reservationApi } from '../api/reservations'
import NoticePopup from '../components/NoticePopup.vue'
import PaginationBar from '../components/PaginationBar.vue'
import { getStatusBadgeClass as statusBadge, todayString } from '../utils/uiFormat'

const seats = ref([])
const activeReservations = ref([])
const loading = ref(false)
const bookingSeatId = ref(null)
const selectedDate = ref(todayString())
const selectedSeatId = ref(null)
const selectedSeatDetail = ref(null)
const selectedSeatLoading = ref(false)
const modalOpen = ref(false)
const myReservationsOpen = ref(false)
const seatPage = ref(1)
const seatPageSize = 36
const myReservationsPage = ref(1)
const myReservationsPageSize = 4
const summary = ref({ study_minutes_today: 0, checkin_done_today: false, credit_score: 100, violation_count: 0 })
const popup = reactive({ visible: false, type: 'success', title: '提示', message: '' })
const errorMessage = (error, fallback = '操作失败') => {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length) return data.non_field_errors[0]
  const firstKey = Object.keys(data)[0]
  const value = firstKey ? data[firstKey] : null
  if (Array.isArray(value) && value.length) return value[0]
  if (typeof value === 'string') return value
  return fallback
}
const filters = reactive({ keyword: '', seatType: '', availability: 'all', hasPower: false, nearWindow: false })
let refreshTimer = null

const bookingForm = reactive({
  start_time: '',
  end_time: '',
  note: ''
})


function seatMapClass(seat) {
  if (!seat) return 'empty'
  return {
    available: seat.is_active && !seat.is_full,
    full: seat.is_active && seat.is_full,
    inactive: !seat.is_active,
    selected: selectedSeatId.value === seat.id,
  }
}

function clearForm() {
  bookingForm.start_time = ''
  bookingForm.end_time = ''
  bookingForm.note = ''
}

function closeModal() {
  modalOpen.value = false
  clearForm()
}

function openMyReservationsModal() {
  myReservationsPage.value = 1
  myReservationsOpen.value = true
}

function closeMyReservationsModal() {
  myReservationsOpen.value = false
}

function showPopup(type, title, message) {
  popup.type = type
  popup.title = title
  popup.message = message
  popup.visible = true
}

function parseTimeToMinutes(value) {
  if (!value || typeof value !== 'string' || !value.includes(':')) return null
  const [h, m] = value.split(':').map(Number)
  if (Number.isNaN(h) || Number.isNaN(m)) return null
  return h * 60 + m
}

function formatMinutesToTime(totalMinutes) {
  const safe = ((totalMinutes % 1440) + 1440) % 1440
  const hours = Math.floor(safe / 60)
  const minutes = safe % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

const filteredSeats = computed(() => {
  const q = filters.keyword.trim().toLowerCase()
  return seats.value.filter((seat) => {
    if (q && ![seat.seat_code, seat.area, seat.note, seat.seat_type_label].filter(Boolean).some(part => String(part).toLowerCase().includes(q))) return false
    if (filters.seatType && seat.seat_type !== filters.seatType) return false
    if (filters.availability === 'available' && (seat.is_full || !seat.is_active)) return false
    if (filters.availability === 'full' && !seat.is_full) return false
    if (filters.hasPower && !seat.has_power) return false
    if (filters.nearWindow && !seat.near_window) return false
    return true
  })
})
const recommendedSeat = computed(() => filteredSeats.value.find(seat => seat.is_active && !seat.is_full && seat.has_power) || filteredSeats.value.find(seat => seat.is_active && !seat.is_full) || null)
const availableSeatCount = computed(() => filteredSeats.value.filter(seat => seat.is_active && !seat.is_full).length)
const seatTotalPages = computed(() => Math.max(1, Math.ceil(filteredSeats.value.length / seatPageSize)))
const paginatedSeats = computed(() => {
  const sorted = [...filteredSeats.value].sort((a, b) => {
    const rowGap = (Number(a.map_row) || 0) - (Number(b.map_row) || 0)
    return rowGap || ((Number(a.map_col) || 0) - (Number(b.map_col) || 0))
  })
  const start = (seatPage.value - 1) * seatPageSize
  return sorted.slice(start, start + seatPageSize)
})
const paginatedActiveReservations = computed(() => {
  const start = (myReservationsPage.value - 1) * myReservationsPageSize
  return activeReservations.value.slice(start, start + myReservationsPageSize)
})
const lowCreditBlocked = computed(() => Number(summary.value?.credit_score ?? 100) < 60)
// 根据后端返回的 map_row/map_col 动态生成平面图，座位扩到 72 个后无需再改前端布局。
const maxCols = computed(() => Math.max(1, ...filteredSeats.value.map(item => Number(item.map_col) || 1)))
const visibleRows = computed(() => {
  const rows = [...new Set(paginatedSeats.value.map(item => Number(item.map_row) || 1))].sort((a, b) => a - b)
  return rows.length ? rows : [1]
})
const gridStyle = computed(() => ({ gridTemplateColumns: `44px repeat(${maxCols.value}, 118px)` }))
const gridColumnStyle = computed(() => ({ gridTemplateColumns: `44px repeat(${maxCols.value}, 118px)` }))
const seatMapRows = computed(() => {
  const seatMap = new Map(paginatedSeats.value.map(item => [`${item.map_row}-${item.map_col}`, item]))
  const rows = []
  for (const row of visibleRows.value) {
    const cells = []
    for (let col = 1; col <= maxCols.value; col += 1) {
      cells.push(seatMap.get(`${row}-${col}`) || null)
    }
    rows.push({ row, cells })
  }
  return rows
})

// 找到用户选择的开始时间所在的剩余可预约区间，用于限制结束时间。
function getSelectedRange() {
  if (!selectedSeatDetail.value || !bookingForm.start_time) return null
  const startMinutes = parseTimeToMinutes(bookingForm.start_time)
  if (startMinutes == null) return null
  return (selectedSeatDetail.value.remaining_ranges || []).find((range) => {
    const rangeStart = parseTimeToMinutes(range.start_time)
    const rangeEnd = parseTimeToMinutes(range.end_time)
    return rangeStart != null && rangeEnd != null && startMinutes >= rangeStart && startMinutes < rangeEnd
  }) || null
}

const selectedRange = computed(getSelectedRange)
const selectedRangeMaxMinutes = computed(() => {
  const range = selectedRange.value
  if (!range) return null
  const rangeStart = parseTimeToMinutes(range.start_time)
  const rangeEnd = parseTimeToMinutes(range.end_time)
  if (rangeStart == null || rangeEnd == null) return null
  return Math.max(0, rangeEnd - Math.max(rangeStart, parseTimeToMinutes(bookingForm.start_time) || rangeStart))
})
const bookingDurationMinutes = computed(() => {
  const startMinutes = parseTimeToMinutes(bookingForm.start_time)
  const endMinutes = parseTimeToMinutes(bookingForm.end_time)
  if (startMinutes == null || endMinutes == null) return 0
  return endMinutes - startMinutes
})
const bookingDurationLabel = computed(() => {
  const minutes = bookingDurationMinutes.value
  if (minutes <= 0) return ''
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h} 小时 ${m} 分钟` : `${m} 分钟`
})
// 表单校验集中放在 computed 中，按钮禁用和提示文案都复用同一套规则。
const bookingFormValid = computed(() => {
  if (!selectedSeatDetail.value) return false
  if (!selectedSeatDetail.value.seat?.is_active) return false
  if (selectedSeatDetail.value.is_full) return false
  const startMinutes = parseTimeToMinutes(bookingForm.start_time)
  const endMinutes = parseTimeToMinutes(bookingForm.end_time)
  const maxMinutes = selectedRangeMaxMinutes.value
  if (startMinutes == null || endMinutes == null || maxMinutes == null) return false
  if (endMinutes <= startMinutes) return false
  if (bookingDurationMinutes.value < 30) return false
  if (bookingDurationMinutes.value > maxMinutes) return false
  return true
})
const bookingHint = computed(() => {
  if (!selectedSeatDetail.value) return '请选择一个座位。'
  if (!selectedSeatDetail.value.seat?.is_active) return '该座位当前不可用。'
  if (selectedSeatDetail.value.is_full) return '剩余可预约时间不足 30 分钟，当前座位已预满。'
  if (!bookingForm.start_time) return '请选择开始时间。'
  if (!bookingForm.end_time) return '请选择结束时间。'
  if (bookingDurationMinutes.value < 30) return '单次预约时长不能少于 30 分钟。'
  if (bookingDurationMinutes.value <= 0) return '结束时间必须晚于开始时间。'
  if (selectedRangeMaxMinutes.value != null && bookingDurationMinutes.value > selectedRangeMaxMinutes.value) return '结束时间不能超过当前可预约区间。'
  return '请在可预约时间范围内选择开始和结束时间。'
})
const bookingDisabledReason = computed(() => {
  if (lowCreditBlocked.value) return `当前信用分为 ${summary.value?.credit_score ?? 0} 分，低于 60 分，暂时无法提交预约。`
  if (!bookingFormValid.value) return bookingHint.value
  return ''
})
const bookingDisabled = computed(() => bookingSeatId.value === selectedSeatId.value || !!bookingDisabledReason.value)

function resetFilters() {
  seatPage.value = 1
  filters.keyword = ''
  filters.seatType = ''
  filters.availability = 'all'
  filters.hasPower = false
  filters.nearWindow = false
}

async function loadSummary() {
  const res = await reservationApi.summary()
  summary.value = res.data || {}
}

async function loadSeats() {
  const res = await seatApi.list({ date: selectedDate.value })
  seats.value = Array.isArray(res.data) ? res.data : []
}

async function loadMyReservations() {
  const bookedRes = await reservationApi.mine({ status: 'booked' })
  const checkedInRes = await reservationApi.mine({ status: 'checked_in' })
  const merged = [...(bookedRes.data || []), ...(checkedInRes.data || [])]
  activeReservations.value = merged.sort((a, b) => `${a.reservation_date} ${a.start_time}`.localeCompare(`${b.reservation_date} ${b.start_time}`))
}

async function loadSelectedSeatDetail() {
  if (!selectedSeatId.value) {
    selectedSeatDetail.value = null
    return
  }
  selectedSeatLoading.value = true
  try {
    const res = await seatApi.remainingSlots(selectedSeatId.value, { date: selectedDate.value })
    selectedSeatDetail.value = res.data
  } catch (e) {
    showPopup('error', '加载失败', errorMessage(e, '加载座位剩余时段失败'))
  } finally {
    selectedSeatLoading.value = false
  }
}

async function refreshSeatState() {
  await Promise.all([loadSeats(), selectedSeatId.value ? loadSelectedSeatDetail() : Promise.resolve()])
}

async function reloadAll() {
  loading.value = true
  try {
    await Promise.all([loadSummary(), loadSeats(), loadMyReservations()])
    if (selectedSeatId.value) await loadSelectedSeatDetail()
  } catch (e) {
    showPopup('error', '加载失败', errorMessage(e, '加载失败'))
  } finally {
    loading.value = false
  }
}

async function openSeatModal(seat) {
  if (!seat) return
  selectedSeatId.value = seat.id
  clearForm()
  if (seat.next_available_range) {
    bookingForm.start_time = seat.next_available_range.start_time
    bookingForm.end_time = seat.next_available_range.end_time
  }
  modalOpen.value = true
  await loadSelectedSeatDetail()
}

function applyRange(range) {
  bookingForm.start_time = range.start_time
  bookingForm.end_time = range.end_time
}

async function bookSelectedSeat() {
  if (!selectedSeatId.value || bookingDisabled.value) return
  bookingSeatId.value = selectedSeatId.value
  try {
    const res = await reservationApi.book({
      seat_id: selectedSeatId.value,
      reservation_date: selectedDate.value,
      start_time: bookingForm.start_time,
      end_time: bookingForm.end_time,
      duration_minutes: bookingDurationMinutes.value,
      note: bookingForm.note,
    })
    showPopup('success', '预约成功', res.data.detail || '预约成功')
    await reloadAll()
    closeModal()
    myReservationsOpen.value = true
    window.dispatchEvent(new Event('user-updated'))
  } catch (e) {
    showPopup('error', '预约失败', errorMessage(e, '预约失败'))
  } finally {
    bookingSeatId.value = null
  }
}

async function cancelReservation(id) {
  try {
    const res = await reservationApi.cancel(id)
    showPopup('success', '取消成功', res.data.detail || '取消成功')
    await reloadAll()
  } catch (e) {
    showPopup('error', '取消失败', errorMessage(e, '取消失败'))
  }
}

async function checkIn(id) {
  try {
    const res = await reservationApi.checkIn(id)
    showPopup('success', '签到成功', res.data.detail || '签到成功')
    await reloadAll()
  } catch (e) {
    showPopup('error', '签到失败', errorMessage(e, '签到失败'))
  }
}

async function checkOut(id) {
  try {
    const res = await reservationApi.checkOut(id)
    showPopup('success', '签退成功', res.data.detail || '签退成功')
    await reloadAll()
  } catch (e) {
    showPopup('error', '签退失败', errorMessage(e, '签退失败'))
  }
}

watch(() => ({ ...filters }), () => {
  seatPage.value = 1
}, { deep: true })

watch(filteredSeats, () => {
  if (seatPage.value > seatTotalPages.value) seatPage.value = seatTotalPages.value
})

watch(activeReservations, () => {
  const totalPages = Math.max(1, Math.ceil(activeReservations.value.length / myReservationsPageSize))
  if (myReservationsPage.value > totalPages) myReservationsPage.value = totalPages
})

watch(selectedDate, async () => {
  seatPage.value = 1
  await refreshSeatState()
  await loadMyReservations()
})

watch(() => bookingForm.start_time, () => {
  const maxDuration = selectedRangeMaxMinutes.value
  if (maxDuration != null && maxDuration > 0) {
    const startMinutes = parseTimeToMinutes(bookingForm.start_time)
    if (startMinutes != null) {
      if (!bookingForm.end_time || parseTimeToMinutes(bookingForm.end_time) <= startMinutes || bookingDurationMinutes.value > maxDuration) {
        bookingForm.end_time = formatMinutesToTime(startMinutes + Math.min(60, maxDuration))
      }
    }
  }
})

watch(() => selectedSeatDetail.value, () => {
  const maxDuration = selectedRangeMaxMinutes.value
  if (maxDuration != null && maxDuration > 0) {
    const startMinutes = parseTimeToMinutes(bookingForm.start_time)
    if (startMinutes != null && (!bookingForm.end_time || bookingDurationMinutes.value > maxDuration)) {
      bookingForm.end_time = formatMinutesToTime(startMinutes + Math.min(60, maxDuration))
    }
  }
})

watch(filteredSeats, (list) => {
  if (!selectedSeatId.value) return
  const exists = list.find((item) => item.id === selectedSeatId.value)
  if (!exists) {
    selectedSeatId.value = null
    selectedSeatDetail.value = null
    modalOpen.value = false
  }
})

onMounted(async () => {
  await reloadAll()
  refreshTimer = window.setInterval(async () => {
    try {
      await Promise.all([loadSummary(), loadSeats(), loadMyReservations()])
      if (selectedSeatId.value) await loadSelectedSeatDetail()
    } catch {
      // ignore timer refresh errors
    }
  }, 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>
