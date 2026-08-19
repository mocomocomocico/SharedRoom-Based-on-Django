// 路由配置：定义用户端/管理端页面，并在进入页面前校验登录状态和管理员权限。
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminHomeView from '../views/AdminHomeView.vue'
import ProfileView from '../views/ProfileView.vue'
import AdminSeatView from '../views/AdminSeatView.vue'
import AdminReservationView from '../views/AdminReservationView.vue'
import AdminUserView from '../views/AdminUserView.vue'
import AdminMaterialsView from '../views/AdminMaterialsView.vue'
import HistoryView from '../views/HistoryView.vue'
import ReservationView from '../views/ReservationView.vue'
import MaterialsView from '../views/MaterialsView.vue'
import MaterialsSharedView from '../views/MaterialsSharedView.vue'
import MaterialsUploadView from '../views/MaterialsUploadView.vue'
import MaterialsMineView from '../views/MaterialsMineView.vue'

// 从 localStorage 读取登录用户，路由守卫依赖它判断角色。
function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

function getStoredMode() {
  const mode = localStorage.getItem('ui_mode')
  return mode === 'admin' || mode === 'user' ? mode : null
}

function isAdminUser(user) {
  return !!(user?.is_staff || user?.is_superuser)
}

function getActiveMode() {
  const user = getStoredUser()
  if (!isAdminUser(user)) return 'user'
  return getStoredMode() || 'admin'
}

function getLandingRoute() {
  return getActiveMode() === 'admin' ? '/admin/home' : '/dashboard'
}

const routes = [
  { path: '/', redirect: () => getLandingRoute() },
  { path: '/login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', component: RegisterView, meta: { guestOnly: true } },
  { path: '/dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/admin/home', component: AdminHomeView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/profile', component: ProfileView, meta: { requiresAuth: true } },
  { path: '/history', component: HistoryView, meta: { requiresAuth: true } },
  { path: '/reserve', component: ReservationView, meta: { requiresAuth: true } },
  { path: '/materials', component: MaterialsView, meta: { requiresAuth: true } },
  { path: '/materials/shared', component: MaterialsSharedView, meta: { requiresAuth: true } },
  { path: '/materials/upload', component: MaterialsUploadView, meta: { requiresAuth: true } },
  { path: '/materials/mine', component: MaterialsMineView, meta: { requiresAuth: true } },
  { path: '/admin/materials', component: AdminMaterialsView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/seats', component: AdminSeatView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/reservations', component: AdminReservationView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', component: AdminUserView, meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局路由守卫：未登录跳登录页，非管理员禁止进入管理端。
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  const user = getStoredUser()
  const isAdmin = isAdminUser(user)
  const activeMode = getActiveMode()

  if (to.meta.requiresAuth && !token) {
    return '/login'
  }

  if (to.meta.requiresAdmin && !(isAdmin && activeMode === 'admin')) {
    return '/dashboard'
  }

  if (to.meta.guestOnly && token) {
    return getLandingRoute()
  }

  if (token && isAdmin && activeMode === 'admin' && ['/dashboard', '/reserve', '/history'].includes(to.path)) {
    return '/admin/home'
  }

  if (token && isAdmin && activeMode === 'admin' && to.path === '/materials') {
    return '/admin/materials'
  }

  if (token && isAdmin && activeMode === 'user' && ['/admin/home', '/admin/seats', '/admin/reservations', '/admin/users', '/admin/materials'].includes(to.path)) {
    return '/dashboard'
  }
})

export default router
