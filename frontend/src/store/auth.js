// 登录状态管理：保存当前用户、token、本地缓存和退出登录逻辑。
import { reactive } from 'vue'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

function readStoredMode() {
  const mode = localStorage.getItem('ui_mode')
  return mode === 'admin' || mode === 'user' ? mode : null
}

function isAdminUser(user) {
  return !!(user?.is_staff || user?.is_superuser)
}

export const authState = reactive({
  user: readStoredUser(),
  mode: readStoredMode() || (isAdminUser(readStoredUser()) ? 'admin' : 'user'),
})

export function setAuthUser(user) {
  authState.user = user
  const mode = isAdminUser(user) ? 'admin' : 'user'
  authState.mode = mode
  if (user) {
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('ui_mode', mode)
  } else {
    localStorage.removeItem('user')
  }
}

export function setUiMode(mode) {
  const nextMode = mode === 'admin' ? 'admin' : 'user'
  authState.mode = nextMode
  localStorage.setItem('ui_mode', nextMode)
}

export function refreshAuthUserFromStorage() {
  authState.user = readStoredUser()
  const storedMode = readStoredMode()
  if (storedMode) {
    authState.mode = storedMode
  } else {
    authState.mode = isAdminUser(authState.user) ? 'admin' : 'user'
  }
  localStorage.setItem('ui_mode', authState.mode)
  return authState.user
}

export function clearAuthUser() {
  authState.user = null
  authState.mode = 'user'
  localStorage.removeItem('user')
  localStorage.removeItem('ui_mode')
}
