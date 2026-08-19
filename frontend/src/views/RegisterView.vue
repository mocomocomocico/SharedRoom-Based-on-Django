<template>
  <div class="auth-shell auth-shell-simple auth-register-shell auth-shell-refined">
    <section class="auth-panel auth-panel-register card auth-panel-refined auth-panel-simple">
      <div class="auth-panel-head auth-panel-head-simple">
        <div class="badge neutral auth-kicker">用户注册</div>
        <h2>创建新账号</h2>
        <p>填写基础信息后即可完成注册，成功后会自动进入用户首页。</p>
      </div>

      <form class="auth-form auth-form-rich auth-form-polished" @submit.prevent="submit">
        <div class="auth-form-grid auth-form-grid-simple">
          <div class="field auth-field">
            <label>账号</label>
            <input class="input auth-input" v-model.trim="form.username" placeholder="请输入登录账号" autocomplete="username" required />
          </div>
          <div class="field auth-field">
            <label>昵称</label>
            <input class="input auth-input" v-model.trim="form.nickname" placeholder="请输入昵称" />
          </div>
          <div class="field auth-field">
            <label>邮箱</label>
            <input class="input auth-input" v-model.trim="form.email" type="email" placeholder="请输入邮箱" autocomplete="email" />
          </div>
          <div class="field auth-field">
            <label>手机号</label>
            <input class="input auth-input" v-model.trim="form.phone" placeholder="请输入手机号" autocomplete="tel" />
          </div>
        </div>

        <div class="field auth-field">
          <label>密码</label>
          <input class="input auth-input" v-model="form.password" type="password" placeholder="至少 6 位密码" autocomplete="new-password" required />
        </div>

        <div class="auth-inline-tip auth-inline-tip-simple">
          <span>注册成功后会弹出提示，并在 2 秒后自动进入用户首页。</span>
        </div>

        <button class="btn btn-primary auth-submit-btn" type="submit" :disabled="loading || successVisible">
          {{ loading ? '注册中...' : '注册并进入系统' }}
        </button>
        <RouterLink to="/login" class="btn btn-secondary auth-link-btn">已有账号，返回登录</RouterLink>
      </form>

      <div v-if="error" class="notice error">{{ error }}</div>
    </section>

    <NoticePopup
      v-model="successVisible"
      title="注册成功"
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
const successMessage = ref('注册成功，正在为你进入用户首页...')
let successTimer = null

const form = reactive({
  username: '',
  email: '',
  nickname: '',
  phone: '',
  password: ''
})

function scheduleRedirect(user) {
  successVisible.value = true

  if (successTimer) window.clearTimeout(successTimer)
  successTimer = window.setTimeout(() => {
    successVisible.value = false
    setAuthUser(user)
    window.dispatchEvent(new Event('user-updated'))
    router.push('/dashboard')
  }, 2000)
}

async function submit() {
  if (loading.value || successVisible.value) return

  loading.value = true
  error.value = ''
  try {
    const res = await authApi.register(form)
    const nextUser = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user', JSON.stringify(nextUser))
    scheduleRedirect(nextUser)
  } catch (e) {
    loading.value = false
    const data = e.response?.data
    error.value = data?.detail || Object.values(data || {}).flat().join('，') || '注册失败'
  }
}

onBeforeUnmount(() => {
  if (successTimer) window.clearTimeout(successTimer)
})
</script>
