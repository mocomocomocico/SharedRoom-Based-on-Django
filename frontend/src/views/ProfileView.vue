<!--
  个人中心：整合账号资料、信用记录、近期预约和资料上传概览。
-->
<template>
  <div class="page-stack profile-page">
    <section class="card hero profile-hero">
      <div class="hero-head hero-head-rich">
        <div>
          <h2>{{ form.nickname || form.account || '我的账号' }}</h2>
          <p>把账号资料、密码安全、预约状态、学习统计、资料概览和违规记录整合到一个页面里，减少来回跳转。</p>
        </div>
        <div class="profile-hero-side">
          <div class="profile-avatar">{{ avatarText }}</div>
          <div class="today-box">
            <span>账号状态</span>
            <strong>{{ profileLoaded ? '正常使用中' : '加载中' }}</strong>
          </div>
        </div>
      </div>

      <div class="metric-row metric-row-4">
        <div class="metric metric-rich"><strong>{{ profile.credit_score ?? 100 }}</strong><span>信用分</span><small>{{ profile.violation_count ?? 0 }} 次违规</small></div>
        <div class="metric metric-rich"><strong>{{ activeReservations.length }}</strong><span>当前预约</span><small>{{ nextReservationText }}</small></div>
        <div class="metric metric-rich"><strong>{{ stats.materialCount }}</strong><span>我的资料</span><small>{{ stats.sharedCount }} 份已共享</small></div>
        <div class="metric metric-rich"><strong>{{ formatMinutes(stats.monthMinutes) }}</strong><span>本月学习</span><small>{{ stats.streakDays }} 天连续打卡</small></div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-grid-home-plus profile-grid-main">
      <div class="side-stack">
        <div class="card light profile-form-card">
          <div class="section-title">
            <div>
              <h3>基础资料</h3>
              <p>修改后会同步到系统中，并立即刷新顶部展示信息</p>
            </div>
            <button class="btn btn-secondary btn-sm" @click="loadAll">刷新数据</button>
          </div>

          <form class="form-stack" @submit.prevent="saveProfile">
            <div class="field">
              <label>账号</label>
              <input class="input" :value="form.account" disabled />
            </div>
            <div class="field">
              <label>昵称</label>
              <input class="input" v-model="form.nickname" placeholder="请输入昵称" />
            </div>
            <div class="field">
              <label>邮箱</label>
              <input class="input" v-model="form.email" type="email" placeholder="请输入邮箱" />
            </div>
            <div class="field">
              <label>手机号</label>
              <input class="input" v-model="form.phone" placeholder="请输入手机号" />
            </div>

            <button class="btn btn-primary" type="submit" :disabled="loadingProfile">
              {{ loadingProfile ? '保存中...' : '保存资料' }}
            </button>
          </form>

          <div v-if="profileMessage" class="notice success">{{ profileMessage }}</div>
          <div v-if="profileError" class="notice error">{{ profileError }}</div>
        </div>

        <div class="card light">
          <div class="section-title">
            <div>
              <h3>密码与安全</h3>
              <p>建议定期更新密码，保障账号安全</p>
            </div>
          </div>

          <form class="form-stack" @submit.prevent="savePassword">
            <div class="field">
              <label>旧密码</label>
              <input class="input" v-model="passwordForm.old_password" type="password" />
            </div>
            <div class="field">
              <label>新密码</label>
              <input class="input" v-model="passwordForm.new_password" type="password" />
            </div>
            <div class="field">
              <label>确认新密码</label>
              <input class="input" v-model="passwordForm.confirm_password" type="password" />
            </div>

            <button class="btn btn-secondary" type="submit" :disabled="loadingPassword">
              {{ loadingPassword ? '修改中...' : '修改密码' }}
            </button>
          </form>

          <div class="status-list compact-status-list">
            <div class="status-line"><span>最近登录</span><strong>{{ formatDateTime(profile.last_login) }}</strong></div>
            <div class="status-line"><span>注册时间</span><strong>{{ formatDate(profile.date_joined) }}</strong></div>
            <div class="status-line"><span>当前角色</span><strong>{{ profile.role === 'admin' ? '管理员' : '普通用户' }}</strong></div>
          </div>

          <div v-if="passwordMessage" class="notice success">{{ passwordMessage }}</div>
          <div v-if="passwordError" class="notice error">{{ passwordError }}</div>
        </div>
      </div>

      <div class="side-stack">
        <div class="card">
          <div class="section-title">
            <div>
              <h3>我的预约概览</h3>
              <p>当前预约较多时可分页查看，页面保持紧凑规整</p>
            </div>
            <div class="section-actions">
              <span v-if="activeReservations.length" class="badge neutral">共 {{ activeReservations.length }} 条</span>
              <RouterLink class="btn btn-secondary btn-sm" to="/reserve">去预约</RouterLink>
            </div>
          </div>
          <div v-if="activeReservations.length" class="reservation-list compact-list profile-reservation-list">
            <div class="reservation-item" v-for="item in paginatedActiveReservations" :key="item.id">
              <div>
                <div class="reservation-title">{{ item.seat_code }} · {{ item.reservation_date }}</div>
                <div class="reservation-meta">{{ item.start_time }} - {{ item.end_time }} · {{ item.status_label }}</div>
                <div class="reservation-meta">签到截止：{{ item.checkin_deadline }}</div>
              </div>
              <span class="badge" :class="badgeClass(item.status)">{{ item.status_label }}</span>
            </div>
          </div>
          <PaginationBar
            v-if="activeReservations.length"
            v-model="activeReservationPage"
            :total="activeReservations.length"
            :page-size="activeReservationPageSize"
          />
          <div v-else class="notice">当前没有进行中的预约，可以前往预约页挑选座位。</div>
        </div>

        <div class="card">
          <div class="section-title">
            <div>
              <h3>个人学习概览</h3>
              <p>在个人中心也能快速看到本周与本月投入</p>
            </div>
          </div>
          <div class="status-list">
            <div class="status-line"><span>今日学习时长</span><strong>{{ formatMinutes(summary.study_minutes_today) }}</strong></div>
            <div class="status-line"><span>本月学习时长</span><strong>{{ formatMinutes(stats.monthMinutes) }}</strong></div>
            <div class="status-line"><span>本月活跃天数</span><strong>{{ stats.activeDays }}</strong></div>
            <div class="status-line"><span>连续打卡天数</span><strong>{{ stats.streakDays }}</strong></div>
          </div>
        </div>
        <div class="card">
          <div class="section-title">
            <div>
              <h3>我的资料概览</h3>
              <p>把上传、管理和历史查看整合成统一的资料摘要</p>
            </div>
          </div>
          <div class="status-list">
            <div class="status-line"><span>资料总数</span><strong>{{ stats.materialCount }} 份</strong></div>
            <div class="status-line"><span>共享资料</span><strong>{{ stats.sharedCount }} 份已公开</strong></div>
            <div class="status-line"><span>最近动作</span><strong>{{ recentMaterials.length ? '有新资料可继续维护' : '还没有上传记录' }}</strong></div>
          </div>
          <div class="panel-action-row">
            <RouterLink class="btn btn-secondary" to="/materials/upload">上传资料</RouterLink>
            <RouterLink class="btn btn-secondary" to="/materials/mine">管理资料</RouterLink>
            <RouterLink class="btn btn-primary" to="/history">查看历史</RouterLink>
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-analytics-grid dashboard-grid-home-plus profile-bottom-grid">
      <div class="card profile-violation-card">
        <div class="section-title profile-card-title">
          <div>
            <h3>违规记录</h3>
            <p>把信用分变化放到个人中心，避免黑箱扣分</p>
          </div>
          <span class="badge" :class="violationSummary.records.length ? 'warn' : 'ok'">
            {{ violationSummary.records.length ? `${violationSummary.records.length} 条` : '信用良好' }}
          </span>
        </div>

        <div class="profile-credit-strip">
          <div>
            <span>当前信用分</span>
            <strong>{{ violationSummary.credit_score ?? profile.credit_score ?? 100 }}</strong>
          </div>
          <div>
            <span>累计违规</span>
            <strong>{{ violationSummary.violation_count ?? profile.violation_count ?? 0 }} 次</strong>
          </div>
        </div>

        <div v-if="violationSummary.records.length" class="violation-list compact-list profile-violation-list">
          <div class="violation-item" v-for="item in violationSummary.records.slice(0, 3)" :key="item.id">
            <div>
              <div class="reservation-title">{{ item.violation_type_label }}</div>
              <div class="reservation-meta">{{ item.reason }}</div>
              <div class="reservation-meta">{{ item.created_by_name }} · {{ formatDateTime(item.created_at) }}</div>
            </div>
            <span class="badge off">{{ item.score_delta }}</span>
          </div>
        </div>
        <div v-else class="profile-empty-state">
          <div class="profile-empty-icon">✓</div>
          <div>
            <strong>当前没有违规记录</strong>
            <p>保持得很好，继续按时签到和离座即可。</p>
          </div>
        </div>
      </div>

      <div class="card profile-material-card">
        <div class="section-title profile-card-title">
          <div>
            <h3>最近上传资料</h3>
            <p>快速确认自己最近维护过的学习资料</p>
          </div>
          <RouterLink class="btn btn-secondary btn-sm" to="/materials/mine">全部资料</RouterLink>
        </div>
        <div v-if="recentMaterials.length" class="profile-material-list">
          <div class="profile-material-item" v-for="item in recentMaterials.slice(0, 4)" :key="item.id">
            <div class="profile-material-main">
              <div class="reservation-title">{{ item.title || item.file_name }}</div>
              <div class="reservation-meta text-ellipsis">{{ item.file_name }}</div>
              <div class="reservation-meta">{{ formatDateTime(item.created_at) }}</div>
            </div>
            <span class="badge" :class="item.is_shared ? 'ok' : 'neutral'">{{ item.visibility_label }}</span>
          </div>
        </div>
        <div v-else class="profile-empty-state">
          <div class="profile-empty-icon">📄</div>
          <div>
            <strong>还没有上传资料</strong>
            <p>可以先去资料中心上传笔记或复习计划。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PaginationBar from '../components/PaginationBar.vue'
import { authApi } from '../api/auth'
import { reservationApi } from '../api/reservations'
import { materialApi } from '../api/materials'
import { setAuthUser } from '../store/auth'
import { formatMinutes, getStatusBadgeClass as badgeClass } from '../utils/uiFormat'

const loadingProfile = ref(false)
const loadingPassword = ref(false)
const profileLoaded = ref(false)
const profileMessage = ref('')
const profileError = ref('')
const passwordMessage = ref('')
const passwordError = ref('')

const profile = ref({})
const summary = ref({ study_minutes_today: 0 })
const analytics = ref({ monthly_report: {} })
const activeReservations = ref([])
const activeReservationPage = ref(1)
const activeReservationPageSize = 4
const violationSummary = ref({ credit_score: 100, violation_count: 0, records: [] })
const recentMaterials = ref([])

const form = reactive({
  account: '',
  nickname: '',
  email: '',
  phone: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const avatarText = computed(() => (form.nickname || form.account || 'U').slice(0, 1).toUpperCase())
const stats = computed(() => ({
  materialCount: recentMaterials.value.length,
  sharedCount: recentMaterials.value.filter(item => item.is_shared).length,
  monthMinutes: Number(analytics.value.monthly_report?.total_minutes || 0),
  activeDays: Number(analytics.value.monthly_report?.active_days || 0),
  streakDays: Number(analytics.value.monthly_report?.current_streak_days || 0),
}))
const nextReservationText = computed(() => {
  const item = activeReservations.value[0]
  return item ? `${item.reservation_date} ${item.start_time}` : '暂无进行中预约'
})
// 个人中心预约概览使用客户端分页，避免记录较多时拉长右侧卡片。
const paginatedActiveReservations = computed(() => {
  const start = (activeReservationPage.value - 1) * activeReservationPageSize
  return activeReservations.value.slice(start, start + activeReservationPageSize)
})


function formatDateTime(value) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 16)
}

function formatDate(value) {
  if (!value) return '-'
  return String(value).slice(0, 10)
}


async function loadProfile() {
  profileError.value = ''
  profileMessage.value = ''
  try {
    const res = await authApi.profile()
    profile.value = res.data || {}
    Object.assign(form, {
      account: res.data.username || '',
      nickname: res.data.nickname || '',
      email: res.data.email || '',
      phone: res.data.phone || ''
    })
    profileLoaded.value = true
  } catch (e) {
    profileError.value = e.response?.data?.detail || '加载个人信息失败'
  }
}

async function loadSummary() {
  const [summaryRes, analyticsRes] = await Promise.all([reservationApi.summary(), reservationApi.analytics()])
  summary.value = summaryRes.data || { study_minutes_today: 0 }
  analytics.value = analyticsRes.data || { monthly_report: {} }
}

async function loadReservations() {
  const [bookedRes, checkedRes] = await Promise.all([
    reservationApi.mine({ status: 'booked' }),
    reservationApi.mine({ status: 'checked_in' }),
  ])
  activeReservations.value = [...(bookedRes.data || []), ...(checkedRes.data || [])]
    .sort((a, b) => `${a.reservation_date} ${a.start_time}`.localeCompare(`${b.reservation_date} ${b.start_time}`))
  // 数据刷新后自动校正页码，避免删除/状态变化后停留在空页。
  const totalPages = Math.max(1, Math.ceil(activeReservations.value.length / activeReservationPageSize))
  if (activeReservationPage.value > totalPages) activeReservationPage.value = totalPages
}

async function loadViolations() {
  const res = await authApi.myViolations()
  violationSummary.value = { credit_score: 100, violation_count: 0, records: [], ...(res.data || {}) }
}

async function loadMaterials() {
  const res = await materialApi.list({ scope: 'mine' })
  recentMaterials.value = (Array.isArray(res.data) ? res.data : []).slice(0, 5)
}

async function loadAll() {
  try {
    await Promise.all([loadProfile(), loadSummary(), loadReservations(), loadViolations(), loadMaterials()])
  } catch {
    // specific error is already surfaced in sub loaders when applicable
  }
}

async function saveProfile() {
  loadingProfile.value = true
  profileError.value = ''
  profileMessage.value = ''
  try {
    const res = await authApi.updateProfile({
      nickname: form.nickname,
      email: form.email,
      phone: form.phone
    })
    setAuthUser(res.data.user)
    window.dispatchEvent(new Event('user-updated'))
    profile.value = res.data.user || profile.value
    profileMessage.value = res.data.detail || '个人信息已更新'
  } catch (e) {
    profileError.value = e.response?.data?.detail || '保存失败'
  } finally {
    loadingProfile.value = false
  }
}

async function savePassword() {
  loadingPassword.value = true
  passwordError.value = ''
  passwordMessage.value = ''
  try {
    const res = await authApi.changePassword({ ...passwordForm })
    passwordMessage.value = res.data.detail || '密码修改成功'
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (e) {
    const data = e.response?.data
    passwordError.value = data?.detail || data?.confirm_password || '修改密码失败'
  } finally {
    loadingPassword.value = false
  }
}

onMounted(loadAll)
</script>


<style scoped>

.profile-bottom-grid {
  align-items: start;
}

.profile-card-title {
  align-items: flex-start;
}

.profile-violation-card,
.profile-material-card {
  display: grid;
  gap: 14px;
}

.profile-credit-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-credit-strip > div {
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(224,242,254,.92), rgba(204,251,241,.80));
  border: 1px solid rgba(14,165,233,.22);
}

.profile-credit-strip span {
  display: block;
  color: #475569;
  font-size: 12px;
  margin-bottom: 4px;
}

.profile-credit-strip strong {
  font-size: 22px;
}

.profile-violation-list {
  gap: 10px;
}

.profile-empty-state {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255,255,255,.88);
  border: 1px solid rgba(15,23,42,.10);
}

.profile-empty-state strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.profile-empty-state p {
  margin: 0;
  color: #475569;
  line-height: 1.55;
  font-size: 13px;
}

.profile-empty-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  background: #dcfce7;
  color: #166534;
  font-weight: 900;
}

.profile-material-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-material-item {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255,255,255,.88);
  border: 1px solid rgba(15,23,42,.10);
}

.profile-material-main {
  min-width: 0;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.profile-reservation-list {
  min-height: 312px;
}

.profile-reservation-list .reservation-item {
  align-items: flex-start;
}

@media (max-width: 860px) {
  .profile-material-list,
  .profile-credit-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .profile-card-title {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile-material-item,
  .profile-empty-state {
    flex-direction: column;
  }

  .section-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .profile-reservation-list {
    min-height: auto;
  }
}
</style>
