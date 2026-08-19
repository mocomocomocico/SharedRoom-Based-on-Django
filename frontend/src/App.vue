<!--
  根布局组件：
  1. 未登录时只显示登录/注册页面；
  2. 已登录普通用户显示顶部导航；
  3. 已登录管理员显示左侧管理导航；
  4. 统一处理头像菜单、退出登录和管理端/用户端模式切换。
-->
<template>
  <div class="app-shell">
    <template v-if="user.user">
      <div class="workspace-shell container" :class="currentMode === 'admin' ? 'workspace-shell-admin' : 'workspace-shell-user'">
        <template v-if="currentMode === 'admin'">
          <aside class="workspace-sidebar card">
            <RouterLink class="brand-block brand-block-side" :to="homeRoute">
              <div class="brand-mark">📘</div>
              <div>
                <h1>共享自习室系统</h1>
                <p>{{ pageInfo.subtitle }}</p>
              </div>
            </RouterLink>

            <div class="sidebar-section">
              <div class="sidebar-title">管理导航</div>
              <nav class="workspace-nav">
                <RouterLink
                  v-for="item in navItems"
                  :key="item.to"
                  :to="item.to"
                  class="workspace-nav-link"
                >
                  <span class="workspace-nav-icon">{{ item.icon }}</span>
                  <div>
                    <strong>{{ item.label }}</strong>
                    <small>{{ item.desc }}</small>
                  </div>
                </RouterLink>
              </nav>
            </div>

            <div class="sidebar-panel">
              <div class="sidebar-title">当前模式</div>
              <div class="sidebar-mode-card">
                <strong>管理端工作台</strong>
                <p>集中处理座位、预约、用户和资料运营。</p>
                <button class="btn btn-secondary" type="button" @click="handleModeSwitch">
                  {{ modeSwitchLabel }}
                </button>
              </div>
            </div>
          </aside>

          <div class="workspace-content">
            <div class="workspace-userbar">
              <div ref="avatarWrapRef" class="workspace-topbar-profile avatar-menu-wrap workspace-userbar-inner">
                <button
                  class="topbar-user-btn"
                  type="button"
                  :aria-expanded="avatarMenuOpen ? 'true' : 'false'"
                  aria-haspopup="menu"
                  @click="toggleAvatarMenu"
                >
                  <span class="avatar-btn avatar-btn-inline">{{ avatarText }}</span>
                  <span class="topbar-user-copy">
                    <strong>{{ displayName }}</strong>
                    <small>{{ roleLabel }}</small>
                  </span>
                </button>

                <Transition name="menu-fade">
                  <div v-show="avatarMenuOpen" class="avatar-menu topbar-avatar-menu" role="menu">
                    <div class="avatar-menu-top">
                      <strong>{{ displayName }}</strong>
                      <span>@{{ user.user?.username }} · {{ roleLabel }}</span>
                    </div>
                    <div class="avatar-menu-summary">
                      <div>
                        <strong>{{ user.user?.credit_score ?? 100 }}</strong>
                        <span>信用分</span>
                      </div>
                      <div>
                        <strong>{{ user.user?.violation_count ?? 0 }}</strong>
                        <span>违规次数</span>
                      </div>
                    </div>
                    <RouterLink to="/profile" role="menuitem" @click="closeAvatarMenu">个人中心</RouterLink>
                    <RouterLink :to="homeRoute" role="menuitem" @click="closeAvatarMenu">管理首页</RouterLink>
                    <button type="button" role="menuitem" @click="logout">退出登录</button>
                  </div>
                </Transition>
              </div>
            </div>

            <main class="workspace-main">
              <RouterView />
            </main>
          </div>
        </template>

        <template v-else>
          <div class="workspace-user-layout">
            <header class="card workspace-user-topnav workspace-user-topnav-compact">
              <div class="workspace-user-topnav-main">
                <div class="workspace-user-topnav-left">
                  <RouterLink class="brand-block brand-block-top" :to="homeRoute">
                    <div class="brand-mark">📘</div>
                    <div>
                      <h1>共享自习室系统</h1>
                      <p>{{ pageInfo.subtitle }}</p>
                    </div>
                  </RouterLink>

                  <div class="workspace-user-topnav-copy compact-copy">
                    <div class="badge ok">{{ pageInfo.title }}</div>
                    <p>{{ pageInfo.desc }}</p>
                  </div>
                </div>

                <div class="workspace-user-topnav-actions workspace-user-topnav-actions-compact">
                  <RouterLink
                    v-if="showUserReturnHome"
                    to="/dashboard"
                    class="btn btn-secondary btn-sm user-return-home-btn"
                    @click="closeAvatarMenu"
                  >
                    ← 返回首页
                  </RouterLink>

                  <button class="btn btn-secondary btn-sm mode-switch-btn" type="button" @click="handleModeSwitch">
                    {{ modeSwitchLabel }}
                  </button>

                  <div ref="avatarWrapRef" class="workspace-topbar-profile avatar-menu-wrap workspace-user-avatar-anchor">
                    <button
                      class="topbar-user-btn topbar-user-btn-compact"
                      type="button"
                      :aria-expanded="avatarMenuOpen ? 'true' : 'false'"
                      aria-haspopup="menu"
                      @click="toggleAvatarMenu"
                    >
                      <span class="avatar-btn avatar-btn-inline">{{ avatarText }}</span>
                      <span class="topbar-user-copy">
                        <strong>{{ displayName }}</strong>
                        <small>{{ roleLabel }}</small>
                      </span>
                    </button>

                    <Transition name="menu-fade">
                      <div v-show="avatarMenuOpen" class="avatar-menu topbar-avatar-menu" role="menu">
                        <div class="avatar-menu-top">
                          <strong>{{ displayName }}</strong>
                          <span>@{{ user.user?.username }} · {{ roleLabel }}</span>
                        </div>
                        <div class="avatar-menu-summary">
                          <div>
                            <strong>{{ user.user?.credit_score ?? 100 }}</strong>
                            <span>信用分</span>
                          </div>
                          <div>
                            <strong>{{ user.user?.violation_count ?? 0 }}</strong>
                            <span>违规次数</span>
                          </div>
                        </div>
                        <RouterLink to="/profile" role="menuitem" @click="closeAvatarMenu">个人中心</RouterLink>
                        <RouterLink :to="homeRoute" role="menuitem" @click="closeAvatarMenu">用户首页</RouterLink>
                        <button type="button" role="menuitem" @click="logout">退出登录</button>
                      </div>
                    </Transition>
                  </div>
                </div>
              </div>

              <nav v-if="showUserHomeNav" class="workspace-nav workspace-nav-top workspace-nav-top-compact">
                <RouterLink
                  v-for="item in navItems"
                  :key="item.to"
                  :to="item.to"
                  class="workspace-nav-link workspace-nav-pill workspace-nav-pill-compact"
                >
                  <span class="workspace-nav-icon">{{ item.icon }}</span>
                  <div>
                    <strong>{{ item.label }}</strong>
                    <small>{{ item.desc }}</small>
                  </div>
                </RouterLink>
              </nav>
            </header>

            <main class="workspace-main workspace-main-user-compact">
              <RouterView />
            </main>
          </div>
        </template>
      </div>
    </template>

    <main v-else class="container main-layout guest-layout">
      <RouterView v-if="!route.meta.requiresAuth" />
    </main>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="adminVerifyOpen" class="modal-backdrop" @click.self="closeAdminVerify">
          <div class="modal-card seat-modal auth-modal-card">
            <div class="section-title">
              <div>
                <h3>管理端重新验证</h3>
                <p>输入管理员账号和密码后即可进入管理端</p>
              </div>
              <button class="btn btn-ghost btn-sm" type="button" @click="closeAdminVerify">关闭</button>
            </div>

            <form class="auth-form auth-verify-form" @submit.prevent="verifyAdminAccess">
              <div class="field">
                <label>管理员账号</label>
                <input class="input" v-model="adminVerifyForm.account" autocomplete="username" required />
              </div>
              <div class="field">
                <label>管理员密码</label>
                <input class="input" v-model="adminVerifyForm.password" type="password" autocomplete="current-password" required />
              </div>
              <div class="modal-actions">
                <button class="btn btn-secondary" type="button" @click="closeAdminVerify">取消</button>
                <button class="btn btn-primary" type="submit" :disabled="adminVerifyLoading">
                  {{ adminVerifyLoading ? '验证中...' : '进入管理端' }}
                </button>
              </div>
            </form>
            <div v-if="adminVerifyError" class="notice error">{{ adminVerifyError }}</div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { authApi } from './api/auth'
import { authState, clearAuthUser, refreshAuthUserFromStorage, setAuthUser, setUiMode } from './store/auth'

const router = useRouter()
const route = useRoute()
const user = authState
const avatarWrapRef = ref(null)
const avatarMenuOpen = ref(false)
const adminVerifyOpen = ref(false)
const adminVerifyLoading = ref(false)
const adminVerifyError = ref('')
const adminVerifyForm = reactive({ account: '', password: '' })

const isAdmin = computed(() => !!user.user?.is_staff || !!user.user?.is_superuser)
const currentMode = computed(() => (isAdmin.value ? (user.mode || 'admin') : 'user'))
const homeRoute = computed(() => (currentMode.value === 'admin' ? '/admin/home' : '/dashboard'))
const displayName = computed(() => user.user?.nickname || user.user?.username || '用户')
const roleLabel = computed(() => {
  if (isAdmin.value && currentMode.value === 'admin') return '管理员 · 管理模式'
  if (isAdmin.value) return '管理员 · 用户模式'
  return '普通用户'
})
const avatarText = computed(() => {
  const text = (user.user?.nickname || user.user?.username || 'U').trim()
  return text.slice(0, 1).toUpperCase()
})
const modeSwitchLabel = computed(() => {
  if (!isAdmin.value) return '进入管理端'
  return currentMode.value === 'admin' ? '切换到用户端' : '切换到管理端'
})

const userNavItems = [
  { to: '/dashboard', label: '首页', desc: '学习总览与关键数据', icon: '🏠' },
  { to: '/reserve', label: '预约座位', desc: '平面图选座与签到签退', icon: '🪑' },
  { to: '/materials', label: '学习资料', desc: '共享、上传、我的资料', icon: '📚' },
  { to: '/history', label: '预约历史', desc: '记录与趋势分析', icon: '🕘' },
  { to: '/profile', label: '个人中心', desc: '账号设置与个人数据', icon: '👤' },
]

const adminNavItems = [
  { to: '/admin/home', label: '管理首页', desc: '运营看板与趋势', icon: '📊' },
  { to: '/admin/seats', label: '座位管理', desc: '平面图与座位属性', icon: '🗺️' },
  { to: '/admin/reservations', label: '预约管理', desc: '预约状态与查询', icon: '📅' },
  { to: '/admin/users', label: '用户管理', desc: '信用分与违规处理', icon: '🧑‍💼' },
  { to: '/admin/materials', label: '资料管理', desc: '审核与资料维护', icon: '🗂️' },
]

const navItems = computed(() => (currentMode.value === 'admin' ? adminNavItems : userNavItems))
const showUserHomeNav = computed(() => currentMode.value === 'user' && route.path === '/dashboard')
const showUserReturnHome = computed(() => currentMode.value === 'user' && route.path !== '/dashboard')

const pageMetaMap = [
  { match: '/dashboard', title: '用户首页', subtitle: '用户端首页 · 预约与打卡', desc: '在这里查看学习统计、签到情况、资料概览和近期学习趋势。' },
  { match: '/reserve', title: '预约座位', subtitle: '用户端导航 · 预约座位', desc: '支持平面图选座、剩余时段查看，以及签到签退的完整预约流程。' },
  { match: '/materials/shared', title: '共享资料', subtitle: '学习资料 · 共享区', desc: '浏览他人共享资料，按关键字快速找到可用的笔记、讲义和复习文件。' },
  { match: '/materials/upload', title: '上传资料', subtitle: '学习资料 · 上传区', desc: '上传新文件，并在私人资料与共享资料之间灵活切换。' },
  { match: '/materials/mine', title: '我的资料', subtitle: '学习资料 · 管理区', desc: '管理自己上传的资料，切换可见性并删除不需要的内容。' },
  { match: '/materials', title: '学习资料中心', subtitle: '学习资料 · 三页整合入口', desc: '从一个总览页进入共享、上传和我的资料，并查看资料规模和最近更新。' },
  { match: '/history', title: '预约历史', subtitle: '预约记录 · 数据可视化与明细', desc: '在历史预约页按日期和状态筛选记录，并通过图表快速查看预约趋势。' },
  { match: '/profile', title: '个人中心', subtitle: '账号资料与个人数据', desc: '集中维护个人资料、密码、安全状态，并查看学习与资料概览。' },
  { match: '/admin/home', title: '管理端首页', subtitle: '管理端首页 · 统览与维护', desc: '集中查看系统运营指标、学习趋势、热门座位和核心风险提示。' },
  { match: '/admin/seats', title: '座位管理', subtitle: '管理端 · 座位与平面图', desc: '维护座位编号、平面图坐标、区域、插座和靠窗等属性。' },
  { match: '/admin/reservations', title: '预约管理', subtitle: '管理端 · 预约与状态', desc: '按日期、用户与状态筛选预约，快速排查当前运行中的记录。' },
  { match: '/admin/users', title: '用户管理', subtitle: '管理端 · 用户与信用分', desc: '处理用户资料、角色、信用分与违规记录，支持快速查询和管理。' },
  { match: '/admin/materials', title: '资料管理', subtitle: '管理端 · 资料维护', desc: '统一查看系统中的全部学习资料，进行可见性管理和内容清理。' },
]

const pageInfo = computed(() => pageMetaMap.find((item) => route.path.startsWith(item.match)) || {
  title: currentMode.value === 'admin' ? '管理工作台' : '学习工作台',
  subtitle: currentMode.value === 'admin' ? '管理端首页 · 统览与维护' : '用户端首页 · 预约与打卡',
  desc: currentMode.value === 'admin' ? '当前位于管理工作区。' : '当前位于用户工作区。',
})

async function loadProfile() {
  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    const res = await authApi.profile()
    setAuthUser(res.data)
  } catch {
    localStorage.clear()
    clearAuthUser()
    router.push('/login')
  }
}

function syncUserFromStorage() {
  refreshAuthUserFromStorage()
}

function closeAvatarMenu() {
  avatarMenuOpen.value = false
}

function toggleAvatarMenu() {
  avatarMenuOpen.value = !avatarMenuOpen.value
}

function handleDocumentClick(event) {
  if (!avatarMenuOpen.value) return
  const el = avatarWrapRef.value
  if (el && !el.contains(event.target)) {
    closeAvatarMenu()
  }
}

async function logout() {
  closeAvatarMenu()
  localStorage.clear()
  window.dispatchEvent(new Event('user-updated'))
  await router.replace('/login')
  clearAuthUser()
}

function handleStorageEvent() {
  syncUserFromStorage()
}

function handleUserUpdated() {
  syncUserFromStorage()
}

function closeAdminVerify() {
  adminVerifyOpen.value = false
  adminVerifyError.value = ''
  adminVerifyForm.account = ''
  adminVerifyForm.password = ''
}

function handleModeSwitch() {
  if (!isAdmin.value) {
    adminVerifyOpen.value = true
    return
  }

  if (currentMode.value === 'admin') {
    setUiMode('user')
    router.push('/dashboard')
    return
  }

  setUiMode('admin')
  router.push('/admin/home')
}

async function verifyAdminAccess() {
  adminVerifyLoading.value = true
  adminVerifyError.value = ''
  try {
    const res = await authApi.login({
      username: adminVerifyForm.account,
      password: adminVerifyForm.password,
    })
    const nextUser = res.data?.user
    if (!(nextUser?.is_staff || nextUser?.is_superuser)) {
      adminVerifyError.value = '该账号不是管理员账号'
      return
    }
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user', JSON.stringify(nextUser))
    setAuthUser(nextUser)
    setUiMode('admin')
    closeAdminVerify()
    window.dispatchEvent(new Event('user-updated'))
    await router.push('/admin/home')
  } catch (e) {
    adminVerifyError.value = e.response?.data?.detail || '管理员验证失败'
  } finally {
    adminVerifyLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
  document.addEventListener('click', handleDocumentClick)
  window.addEventListener('storage', handleStorageEvent)
  window.addEventListener('user-updated', handleUserUpdated)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
  window.removeEventListener('storage', handleStorageEvent)
  window.removeEventListener('user-updated', handleUserUpdated)
})
</script>
