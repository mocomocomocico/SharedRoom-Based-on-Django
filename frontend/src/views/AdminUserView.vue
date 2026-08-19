<!--
  管理端 · 用户管理：
  - 查询用户列表；
  - 编辑用户基础信息、角色、启用状态和信用分；
  - 登记人工违规并展示最近违规记录。
-->
<template>
  <div class="page-stack admin-user-page">
    <section class="card hero admin-hero admin-hero-compact">
      <div class="hero-head hero-head-compact">
        <div>
          <div class="badge ok">管理端 · 用户管理</div>
          <h2>统一维护系统用户账号与信用分状态</h2>
        </div>
        <button class="btn btn-secondary btn-sm" @click="loadUsers">刷新</button>
      </div>
    </section>

    <section class="card admin-user-list-card">
      <div class="section-title">
        <div>
          <h3>用户列表</h3>
          <p>点击“编辑”弹出窗口，对用户信息、信用分和违规进行集中处理</p>
        </div>
      </div>

      <div class="toolbar admin-user-toolbar">
        <div class="field grow">
          <label>搜索账号</label>
          <input class="input" v-model="keyword" placeholder="账号 / 昵称 / 邮箱 / 手机号" @keyup.enter="loadUsers" />
        </div>
        <button class="btn btn-primary" @click="loadUsers">查询</button>
      </div>

      <div class="table-wrap">
        <table class="table admin-table admin-user-table">
          <thead>
            <tr>
              <th>账号</th>
              <th>昵称</th>
              <th>邮箱 / 手机</th>
              <th>信用分</th>
              <th>违规</th>
              <th>角色</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in users" :key="item.id">
              <td class="single-line-cell">{{ item.username }}</td>
              <td class="single-line-cell">{{ item.nickname || '-' }}</td>
              <td class="single-line-cell">{{ item.email || item.phone || '-' }}</td>
              <td class="single-line-cell">{{ item.credit_score ?? 100 }}</td>
              <td class="single-line-cell">{{ item.violation_count ?? 0 }}</td>
              <td class="single-line-cell">{{ item.role === 'admin' ? '管理员' : '普通用户' }}</td>
              <td class="single-line-cell"><span class="badge" :class="item.is_active ? 'ok' : 'off'">{{ item.is_active ? '启用' : '禁用' }}</span></td>
              <td class="single-line-cell">
                <div class="action-inline action-inline-compact">
                  <button class="btn btn-ghost btn-sm" @click="selectUser(item)">编辑</button>
                  <button class="btn btn-danger btn-sm" @click="removeUser(item)" :disabled="item.id === currentUserId">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="message" class="notice success">{{ message }}</div>
      <div v-if="error" class="notice error">{{ error }}</div>
    </section>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="userModalOpen" class="modal-backdrop modal-backdrop-centered" @click.self="closeUserModal">
          <div class="modal-card seat-modal admin-form-modal admin-user-modal-card">
            <div class="section-title">
              <div>
                <h3>编辑用户</h3>
                <p>修改账号资料、角色、状态，并可登记违规</p>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="closeUserModal">关闭</button>
            </div>

            <template v-if="selected">
              <form class="form-stack" @submit.prevent="saveUser">
                <div class="field">
                  <label>账号</label>
                  <input class="input" :value="selected.username" disabled />
                </div>
                <div class="status-list compact-status-list user-modal-stats">
                  <div class="status-line"><span>当前信用分</span><strong>{{ selected.credit_score ?? 100 }}</strong></div>
                  <div class="status-line"><span>累计违规</span><strong>{{ selected.violation_count ?? 0 }}</strong></div>
                </div>
                <div class="form-grid two-cols">
                  <div class="field">
                    <label>昵称</label>
                    <input class="input" v-model="editForm.nickname" />
                  </div>
                  <div class="field">
                    <label>邮箱</label>
                    <input class="input" v-model="editForm.email" type="email" />
                  </div>
                </div>
                <div class="form-grid two-cols">
                  <div class="field">
                    <label>手机号</label>
                    <input class="input" v-model="editForm.phone" />
                  </div>
                  <div class="field">
                    <label>角色</label>
                    <select class="input" v-model="editForm.role">
                      <option value="user">普通用户</option>
                      <option value="admin">管理员</option>
                    </select>
                  </div>
                </div>
                <div class="form-grid two-cols">
                  <div class="field">
                    <label>信用分</label>
                    <input class="input" type="number" min="0" max="100" v-model="editForm.credit_score" />
                  </div>
                  <div class="field">
                    <label>账号状态</label>
                    <select class="input" v-model="editForm.is_active">
                      <option :value="true">启用</option>
                      <option :value="false">禁用</option>
                    </select>
                  </div>
                </div>

                <div class="modal-actions modal-actions-spread">
                  <div class="action-inline action-inline-compact">
                    <button class="btn btn-secondary" type="button" @click="resetEdit">重置</button>
                    <button class="btn btn-danger" type="button" :disabled="saving" @click="resetPassword">重置密码</button>
                  </div>
                  <button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存修改' }}</button>
                </div>
              </form>

              <div class="divider-line"></div>

              <div class="section-title">
                <div>
                  <h3>手动登记违规</h3>
                  <p>适用于人工核实后的占座、扰乱秩序等情况</p>
                </div>
              </div>
              <form class="form-grid two-cols admin-violation-form" @submit.prevent="submitViolation">
                <div class="field">
                  <label>违规类型</label>
                  <select class="input" v-model="violationForm.violation_type">
                    <option value="manual">管理员记录</option>
                    <option value="other">其他违规</option>
                  </select>
                </div>
                <div class="field">
                  <label>扣减分值</label>
                  <input class="input" type="number" v-model="violationForm.score_delta" />
                </div>
                <div class="field admin-violation-reason">
                  <label>违规说明</label>
                  <input class="input" v-model="violationForm.reason" placeholder="例如：多次占座离场未签退" required />
                </div>
                <div class="field admin-violation-submit">
                  <label>&nbsp;</label>
                  <button class="btn btn-warning" type="submit" :disabled="savingViolation">{{ savingViolation ? '提交中...' : '登记违规' }}</button>
                </div>
              </form>

              <div class="divider-line"></div>

              <div class="section-title">
                <div>
                  <h3>最近违规记录</h3>
                  <p>展示该用户最近的几条记录</p>
                </div>
              </div>
              <div v-if="selectedViolations.length" class="violation-list compact-list">
                <div class="violation-item" v-for="item in selectedViolations" :key="item.id">
                  <div>
                    <div class="reservation-title">{{ item.violation_type_label }}</div>
                    <div class="reservation-meta">{{ item.reason }}</div>
                    <div class="reservation-meta">{{ item.created_by_name }} · {{ formatDateTime(item.created_at) }}</div>
                  </div>
                  <span class="badge off">{{ item.score_delta }}</span>
                </div>
              </div>
              <div v-else class="notice">该用户暂时没有违规记录。</div>
            </template>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { authApi } from '../api/auth'

const users = ref([])
const selected = ref(null)
const selectedViolations = ref([])
const userModalOpen = ref(false)
const message = ref('')
const error = ref('')
const saving = ref(false)
const savingViolation = ref(false)
const keyword = ref('')
const currentUserId = JSON.parse(localStorage.getItem('user') || 'null')?.id

const editForm = reactive({
  nickname: '',
  email: '',
  phone: '',
  role: 'user',
  is_active: true,
  credit_score: 100
})

const violationForm = reactive({
  violation_type: 'manual',
  score_delta: -10,
  reason: ''
})

function fillForm(user) {
  editForm.nickname = user.nickname || ''
  editForm.email = user.email || ''
  editForm.phone = user.phone || ''
  editForm.role = user.role || 'user'
  editForm.is_active = !!user.is_active
  editForm.credit_score = Number(user.credit_score ?? 100)
}

function resetViolationForm() {
  violationForm.violation_type = 'manual'
  violationForm.score_delta = -10
  violationForm.reason = ''
}

function formatDateTime(value) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 16)
}

function closeUserModal() {
  userModalOpen.value = false
  selected.value = null
  selectedViolations.value = []
  resetViolationForm()
}

async function loadUsers() {
  error.value = ''
  message.value = ''
  try {
    const res = await authApi.adminUsers({ q: keyword.value.trim() || undefined })
    users.value = res.data
    if (selected.value) {
      const latest = users.value.find((item) => item.id === selected.value.id)
      if (latest) {
        selected.value = latest
        fillForm(latest)
      }
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '加载用户列表失败'
  }
}

async function loadSelectedViolations() {
  if (!selected.value) return
  try {
    const res = await authApi.adminViolations({ user_id: selected.value.id })
    selectedViolations.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    error.value = e.response?.data?.detail || '加载违规记录失败'
  }
}

async function selectUser(user) {
  selected.value = user
  fillForm(user)
  resetViolationForm()
  message.value = ''
  error.value = ''
  userModalOpen.value = true
  await loadSelectedViolations()
}

function resetEdit() {
  if (selected.value) fillForm(selected.value)
}

async function saveUser() {
  if (!selected.value) return
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const res = await authApi.updateAdminUser(selected.value.id, { ...editForm, credit_score: Number(editForm.credit_score ?? 100) })
    message.value = res.data.detail || '用户已更新'
    await loadUsers()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function submitViolation() {
  if (!selected.value) return
  savingViolation.value = true
  message.value = ''
  error.value = ''
  try {
    const res = await authApi.createViolation({
      user_id: selected.value.id,
      violation_type: violationForm.violation_type,
      score_delta: Number(violationForm.score_delta) || -10,
      reason: violationForm.reason,
    })
    message.value = res.data.detail || '违规记录已添加'
    resetViolationForm()
    await Promise.all([loadUsers(), loadSelectedViolations()])
  } catch (e) {
    error.value = e.response?.data?.detail || '登记违规失败'
  } finally {
    savingViolation.value = false
  }
}

async function resetPassword() {
  if (!selected.value) return
  if (!window.confirm(`确认将账号 ${selected.value.username} 的密码重置为默认密码吗？`)) return
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const res = await authApi.resetAdminUserPassword(selected.value.id)
    message.value = res.data.detail || '密码已重置'
  } catch (e) {
    error.value = e.response?.data?.detail || '重置密码失败'
  } finally {
    saving.value = false
  }
}

async function removeUser(user) {
  if (user.id === currentUserId) {
    error.value = '不能删除当前登录账号'
    return
  }
  if (!window.confirm(`确认删除账号 ${user.username} 吗？`)) return
  message.value = ''
  error.value = ''
  try {
    const res = await authApi.deleteAdminUser(user.id)
    message.value = res.data.detail || '用户已删除'
    if (selected.value?.id === user.id) {
      closeUserModal()
    }
    await loadUsers()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除失败'
  }
}

onMounted(loadUsers)
</script>
