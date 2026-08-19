<template>
  <div class="auth-shell auth-shell-simple auth-login-shell auth-shell-refined">
    <section class="auth-panel auth-panel-login card auth-panel-refined auth-panel-simple">
      <div class="auth-panel-head auth-panel-head-simple">
        <div class="badge neutral auth-kicker">账号登录</div>
        <h2>欢迎登录</h2>
        <p>请输入账号和密码，登录后将根据角色自动进入对应首页。</p>
      </div>

      <form class="auth-form auth-form-rich auth-form-polished" @submit.prevent="submit">
        <div class="field auth-field">
          <label>账号</label>
          <input class="input auth-input" v-model.trim="form.account" autocomplete="username" placeholder="请输入账号 / 用户名" required />
        </div>
        <div class="field auth-field">
          <label>密码</label>
          <input class="input auth-input" v-model="form.password" type="password" autocomplete="current-password" placeholder="请输入密码" required />
        </div>

        <div class="auth-inline-tip auth-inline-tip-simple">
          <span>普通用户进入用户首页，管理员进入管理首页。</span>
        </div>

        <button class="btn btn-primary auth-submit-btn" type="submit" :disabled="loading || successVisible">
          {{ loading ? '登录中...' : '登录并进入系统' }}
        </button>
        <RouterLink to="/register" class="btn btn-secondary auth-link-btn">还没有账号，立即注册</RouterLink>
      </form>

      <div v-if="error" class="notice error">{{ error }}</div>
    </section>

    <NoticePopup
      v-model="successVisible"
      title="登录成功"
      :message="successMessage"
      type="success"
    />
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { authApi } from '../api/auth'
import NoticePopup from '../components/NoticePopup.vue'
import { setAuthUser } from '../store/auth'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const successVisible = ref(false)
const successMessage = ref('登录成功，正在为你进入系统首页...')
let successTimer = null

const form = reactive({
  account: '',
  password: ''
})

function scheduleRedirect(user) {
  const isAdmin = !!(user?.is_staff || user?.is_superuser)
  successMessage.value = isAdmin
    ? '登录成功，正在为你进入管理首页...'
    : '登录成功，正在为你进入用户首页...'
  successVisible.value = true

  if (successTimer) window.clearTimeout(successTimer)
  successTimer = window.setTimeout(() => {
    successVisible.value = false
    setAuthUser(user)
    window.dispatchEvent(new Event('user-updated'))
    router.push(isAdmin ? '/admin/home' : '/dashboard')
  }, 2000)
}

async function submit() {
  if (loading.value || successVisible.value) return

  loading.value = true
  error.value = ''
  try {
    const res = await authApi.login({
      username: form.account,
      password: form.password
    })

    const nextUser = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user', JSON.stringify(nextUser))
    scheduleRedirect(nextUser)
  } catch (e) {
    loading.value = false
    error.value = e.response?.data?.detail || '登录失败'
  }
}

onBeforeUnmount(() => {
  if (successTimer) window.clearTimeout(successTimer)
})
</script>
