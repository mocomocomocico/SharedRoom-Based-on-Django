<!--
  管理端 · 预约管理：
  - 负责预约记录查询、状态筛选、分页展示和取消预约；
  - 当前页面已删除签到/签退列，仅保留管理端需要的预约状态；
  - 尺寸样式统一由 src/style.css 中 admin-reservation 相关规则控制。
-->
<template>
  <div class="page-stack admin-reservation-page">
    <section class="card hero admin-hero admin-hero-compact">
      <div class="hero-head hero-head-compact">
        <div>
          <div class="badge ok">管理端 · 预约管理</div>
          <h2>集中查看自由时间段预约记录</h2>
        </div>
        <div class="toolbar">
          <button class="btn btn-secondary btn-sm" @click="loadData">刷新</button>
        </div>
      </div>
    </section>

    <section class="card list-card admin-reservation-list-card">
      <div class="section-title">
        <div>
          <h3>预约记录列表</h3>
          <p>共 {{ reservations.length }} 条记录，当前第 {{ currentPage }} / {{ totalPages }} 页，长内容自动省略但不换行。</p>
        </div>
      </div>

      <div class="toolbar admin-reservation-toolbar-compact admin-reservation-toolbar-lined">
        <div class="field">
          <label>日期</label>
          <input class="input" type="date" v-model="filters.date" @change="resetPage(); loadData()" />
        </div>
        <div class="field">
          <label>状态</label>
          <select class="input" v-model="filters.status" @change="resetPage(); loadData()">
            <option value="">全部</option>
            <option value="booked">已预约</option>
            <option value="checked_in">使用中</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
            <option value="expired">已过期</option>
          </select>
        </div>
        <div class="field grow">
          <label>用户账号 / 昵称 / ID</label>
          <input class="input" v-model="filters.user" placeholder="输入账号或昵称" @keyup.enter="resetPage(); loadData()" />
        </div>
        <div class="admin-reservation-toolbar-action">
          <button class="btn btn-primary" @click="resetPage(); loadData()">查询</button>
        </div>
      </div>

      <div class="metric-row metric-row-4 admin-reservation-metrics admin-reservation-metrics-tight">
        <div class="metric metric-compact">
          <strong>{{ reservations.length }}</strong>
          <span>当前记录数</span>
        </div>
        <div class="metric metric-compact">
          <strong>{{ bookedCount }}</strong>
          <span>待使用</span>
        </div>
        <div class="metric metric-compact">
          <strong>{{ checkedInCount }}</strong>
          <span>使用中</span>
        </div>
        <div class="metric metric-compact">
          <strong>{{ completedCount }}</strong>
          <span>已完成</span>
        </div>
      </div>

      <div class="table-wrap admin-reservation-table-wrap">
        <table class="table admin-table admin-reservation-table admin-reservation-table-compact admin-reservation-table-refined">
          <colgroup>
            <col class="col-user" />
            <col class="col-seat" />
            <col class="col-date" />
            <col class="col-time" />
            <col class="col-status" />
            <col class="col-release" />
            <col class="col-action" />
          </colgroup>
          <thead>
            <tr>
              <th>用户</th>
              <th>座位</th>
              <th>日期</th>
              <th>时间</th>
              <th>状态</th>
              <th>预计释放</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedReservations" :key="item.id">
              <td class="single-line-cell" :title="item.user_display_name || item.user_username">{{ item.user_display_name || item.user_username }}</td>
              <td class="single-line-cell" :title="`${item.seat_code}（${item.seat_area || '-'}）`">{{ item.seat_code }}（{{ item.seat_area || '-' }}）</td>
              <td class="single-line-cell" :title="item.reservation_date">{{ item.reservation_date }}</td>
              <td class="single-line-cell" :title="`${item.start_time} - ${item.end_time}`">{{ item.start_time }} - {{ item.end_time }}</td>
              <td class="single-line-cell"><span class="badge" :class="badgeClass(item.status)">{{ displayStatus(item) }}</span></td>
              <td class="single-line-cell" :title="item.expected_release_time || '-'">{{ item.expected_release_time || '-' }}</td>
              <td class="single-line-cell">
                <button v-if="item.status === 'booked'" class="btn btn-danger btn-sm" @click="cancelReservation(item.id)">取消</button>
                <span v-else>-</span>
              </td>
            </tr>
            <tr v-if="!paginatedReservations.length">
              <td colspan="7">
                <div class="notice admin-empty-inline">当前筛选条件下没有预约记录。</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        v-if="reservations.length"
        v-model="currentPage"
        :total="reservations.length"
        :page-size="pageSize"
      />

      <div v-if="message" class="notice success">{{ message }}</div>
      <div v-if="error" class="notice error">{{ error }}</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { reservationApi } from '../api/reservations'
import { getStatusBadgeClass as badgeClass } from '../utils/uiFormat'

const reservations = ref([])
const error = ref('')
const message = ref('')
const filters = reactive({ date: '', status: '', user: '' })
const currentPage = ref(1)
// 预约管理分页：只在前端切片显示，后端仍按筛选条件返回完整列表。
const pageSize = 10


function displayStatus(item) {
  if (item.status === 'booked') return '待使用'
  if (item.status === 'checked_in') return '使用中'
  if (item.status === 'completed') return '已完成'
  return item.status_label || '-'
}


const bookedCount = computed(() => reservations.value.filter(item => item.status === 'booked').length)
const checkedInCount = computed(() => reservations.value.filter(item => item.status === 'checked_in').length)
const completedCount = computed(() => reservations.value.filter(item => item.status === 'completed').length)
const totalPages = computed(() => Math.max(1, Math.ceil(reservations.value.length / pageSize)))
// 当前页要渲染的数据，模板中的 v-for 只遍历这部分。
const paginatedReservations = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return reservations.value.slice(start, start + pageSize)
})
function resetPage() {
  currentPage.value = 1
}


// 根据日期、状态、用户关键词加载预约列表。
async function loadData() {
  error.value = ''
  try {
    const params = {}
    if (filters.date) params.date = filters.date
    if (filters.status) params.status = filters.status
    if (filters.user) params.user = filters.user
    const res = await reservationApi.admin(params)
    reservations.value = Array.isArray(res.data) ? res.data : []
    if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

// 管理端取消预约后重新加载列表，并保留/修正当前页。
async function cancelReservation(id) {
  message.value = ''
  error.value = ''
  try {
    const res = await reservationApi.cancel(id)
    message.value = res.data.detail || '取消成功'
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '取消失败'
  }
}

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

onMounted(loadData)
</script>
