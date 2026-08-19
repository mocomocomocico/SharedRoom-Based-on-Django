<!--
  管理端 · 座位管理：维护座位区域、编号、容量、状态和说明。
-->
<template>
  <div class="page-stack admin-seat-page">
    <section class="card hero admin-hero admin-hero-compact">
      <div class="hero-head hero-head-compact">
        <div>
          <div class="badge ok">管理端 · 座位管理</div>
          <h2>维护平面图坐标与座位属性</h2>
        </div>
        <div class="toolbar">
          <button class="btn btn-primary btn-sm" type="button" @click="openCreateModal">添加座位</button>
          <button class="btn btn-secondary btn-sm" @click="loadAll">刷新</button>
        </div>
      </div>
    </section>

    <section class="card list-card">
      <div class="section-title">
        <div>
          <h3>座位列表</h3>
          <p>共 {{ seats.length }} 个座位，当前第 {{ currentPage }} / {{ totalPages }} 页</p>
        </div>
      </div>

      <div class="admin-seat-list">
        <div class="admin-seat-row admin-seat-headrow admin-seat-row-wide admin-seat-row-editable">
          <span>编号</span><span>区域</span><span>坐标</span><span>标签</span><span>状态</span><span>操作</span>
        </div>
        <div class="admin-seat-row admin-seat-row-wide admin-seat-row-editable" v-for="seat in paginatedSeats" :key="seat.id">
          <span class="seat-code-cell">{{ seat.seat_code }}</span>
          <span>{{ seat.area || '-' }}</span>
          <span>{{ seat.map_row }} - {{ seat.map_col }}</span>
          <span>
            <div class="tag-row">
              <span class="seat-tag">{{ seat.seat_type_label }}</span>
              <span class="seat-tag" v-if="seat.has_power">插座</span>
              <span class="seat-tag" v-if="seat.near_window">靠窗</span>
            </div>
          </span>
          <span><span class="badge" :class="seat.is_active ? 'ok' : 'off'">{{ seat.is_active ? '可用' : '不可用' }}</span></span>
          <span class="action-inline action-inline-compact">
            <button class="btn btn-ghost btn-sm" @click="startEdit(seat)">编辑</button>
            <button class="btn btn-secondary btn-sm" @click="toggleSeat(seat)">{{ seat.is_active ? '停用' : '启用' }}</button>
            <button class="btn btn-danger btn-sm" @click="deleteSeat(seat)">删除</button>
          </span>
        </div>
      </div>

      <div v-if="!paginatedSeats.length" class="notice">当前没有座位数据。</div>

      <div class="panel-action-row admin-pagination-row">
        <button class="btn btn-secondary btn-sm" type="button" :disabled="currentPage <= 1" @click="goPrevPage">上一页</button>
        <span class="pagination-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
        <button class="btn btn-secondary btn-sm" type="button" :disabled="currentPage >= totalPages" @click="goNextPage">下一页</button>
      </div>
    </section>

    <div v-if="pageMessage" class="notice success">{{ pageMessage }}</div>
    <div v-if="pageError" class="notice error">{{ pageError }}</div>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="seatModalOpen" class="modal-backdrop modal-backdrop-centered" @click.self="closeSeatModal">
          <div class="modal-card seat-modal admin-form-modal">
            <div class="section-title">
              <div>
                <h3>{{ editingSeatId ? '编辑座位' : '新增座位' }}</h3>
                <p>{{ editingSeatId ? '修改后会同步更新平面图显示' : '创建后会立即显示在预约平面图中' }}</p>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="closeSeatModal">关闭</button>
            </div>

            <form class="form-stack" @submit.prevent="submitSeatForm">
              <div class="field">
                <label>座位编号</label>
                <input class="input" v-model="seatForm.seat_code" placeholder="A-01" required />
              </div>
              <div class="field">
                <label>区域</label>
                <input class="input" v-model="seatForm.area" placeholder="靠窗区 / 安静区" />
              </div>
              <div class="form-grid two-cols">
                <div class="field">
                  <label>平面图行</label>
                  <input class="input" type="number" min="1" v-model="seatForm.map_row" />
                </div>
                <div class="field">
                  <label>平面图列</label>
                  <input class="input" type="number" min="1" v-model="seatForm.map_col" />
                </div>
              </div>
              <div class="field">
                <label>座位类型</label>
                <select class="input" v-model="seatForm.seat_type">
                  <option value="normal">普通位</option>
                  <option value="quiet">安静位</option>
                  <option value="window">靠窗位</option>
                  <option value="power">插座位</option>
                </select>
              </div>
              <div class="field">
                <label>备注</label>
                <input class="input" v-model="seatForm.note" placeholder="台灯位 / 独立隔板" />
              </div>
              <label class="check-line"><input type="checkbox" v-model="seatForm.has_power" />带插座</label>
              <label class="check-line"><input type="checkbox" v-model="seatForm.near_window" />靠窗</label>
              <label class="check-line"><input type="checkbox" v-model="seatForm.is_active" />当前可用</label>
              <div class="modal-actions">
                <button class="btn btn-secondary" type="button" @click="closeSeatModal">取消</button>
                <button class="btn btn-primary" type="submit">{{ editingSeatId ? '保存修改' : '创建座位' }}</button>
              </div>
            </form>

            <div v-if="seatMessage" class="notice success">{{ seatMessage }}</div>
            <div v-if="seatError" class="notice error">{{ seatError }}</div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { seatApi } from '../api/seats'

const seats = ref([])
const pageMessage = ref('')
const pageError = ref('')
const seatMessage = ref('')
const seatError = ref('')
const editingSeatId = ref(null)
const seatModalOpen = ref(false)
const currentPage = ref(1)
const pageSize = 8

const defaultSeatForm = () => ({
  seat_code: '',
  area: '',
  note: '',
  is_active: true,
  map_row: 1,
  map_col: 1,
  seat_type: 'normal',
  has_power: false,
  near_window: false,
})

const seatForm = reactive(defaultSeatForm())

const totalPages = computed(() => Math.max(1, Math.ceil(seats.value.length / pageSize)))
const paginatedSeats = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return seats.value.slice(start, start + pageSize)
})

function resetSeatForm() {
  Object.assign(seatForm, defaultSeatForm())
}

function normalizePayload() {
  return {
    ...seatForm,
    map_row: Number(seatForm.map_row) || 1,
    map_col: Number(seatForm.map_col) || 1,
  }
}

function closeSeatModal() {
  seatModalOpen.value = false
  editingSeatId.value = null
  resetSeatForm()
  seatMessage.value = ''
  seatError.value = ''
}

function openCreateModal() {
  closeSeatModal()
  seatModalOpen.value = true
}

function startEdit(seat) {
  editingSeatId.value = seat.id
  Object.assign(seatForm, {
    seat_code: seat.seat_code || '',
    area: seat.area || '',
    note: seat.note || '',
    is_active: !!seat.is_active,
    map_row: seat.map_row || 1,
    map_col: seat.map_col || 1,
    seat_type: seat.seat_type || 'normal',
    has_power: !!seat.has_power,
    near_window: !!seat.near_window,
  })
  seatMessage.value = ''
  seatError.value = ''
  seatModalOpen.value = true
}

function goPrevPage() {
  if (currentPage.value > 1) currentPage.value -= 1
}

function goNextPage() {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

async function loadAll() {
  pageError.value = ''
  try {
    const res = await seatApi.list({})
    seats.value = Array.isArray(res.data) ? res.data : []
    if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  } catch (e) {
    pageError.value = e.response?.data?.detail || '加载失败'
  }
}

async function submitSeatForm() {
  seatMessage.value = ''
  seatError.value = ''
  pageMessage.value = ''
  pageError.value = ''
  try {
    const payload = normalizePayload()
    if (editingSeatId.value) {
      const res = await seatApi.patch(editingSeatId.value, payload)
      seatMessage.value = `座位 ${res.data.seat_code} 修改成功`
    } else {
      const res = await seatApi.create(payload)
      seatMessage.value = `座位 ${res.data.seat_code} 创建成功`
    }
    pageMessage.value = seatMessage.value
    await loadAll()
    closeSeatModal()
  } catch (e) {
    seatError.value = e.response?.data?.detail || '保存座位失败'
  }
}

async function toggleSeat(seat) {
  pageMessage.value = ''
  pageError.value = ''
  try {
    await seatApi.patch(seat.id, { is_active: !seat.is_active })
    pageMessage.value = `座位 ${seat.seat_code} 已更新`
    await loadAll()
  } catch (e) {
    pageError.value = e.response?.data?.detail || '更新座位失败'
  }
}

async function deleteSeat(seat) {
  if (!window.confirm(`确认删除座位 ${seat.seat_code} 吗？`)) return
  pageMessage.value = ''
  pageError.value = ''
  try {
    await seatApi.deleteSeat(seat.id)
    pageMessage.value = `座位 ${seat.seat_code} 已删除`
    if (editingSeatId.value === seat.id) closeSeatModal()
    await loadAll()
  } catch (e) {
    pageError.value = e.response?.data?.detail || '删除座位失败'
  }
}

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

onMounted(loadAll)
</script>
