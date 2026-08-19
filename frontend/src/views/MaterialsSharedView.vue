<template>
  <div class="page-stack materials-page">
    <section class="card hero materials-hero">
      <div class="hero-head hero-head-rich">
        <div>
          <div class="badge ok">学习资料 · 页面 1</div>
          <h2>共享资料</h2>
          <p>集中查看公开共享的学习资料，并在进入详细查看前先通过搜索快速缩小范围。</p>
        </div>
        <div class="today-box">
          <span>共享资料数</span>
          <strong>{{ filteredMaterials.length }}</strong>
        </div>
      </div>

      <div class="material-subnav">
        <RouterLink class="btn btn-secondary btn-sm" to="/materials">返回资料中心</RouterLink>
        <RouterLink class="btn btn-ghost btn-sm" to="/materials/upload">上传资料</RouterLink>
        <RouterLink class="btn btn-ghost btn-sm" to="/materials/mine">我的资料</RouterLink>
      </div>
    </section>

    <section class="card material-panel">
      <div class="section-title">
        <div>
          <h3>共享资料列表</h3>
          <p>支持按标题、说明、上传者搜索</p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="loadMaterials">刷新</button>
      </div>

      <div class="toolbar admin-toolbar history-toolbar-grid">
        <div class="field" style="grid-column: span 2;">
          <label>搜索资料</label>
          <input class="input" v-model="keyword" placeholder="标题 / 文件名 / 上传者 / 说明" />
        </div>
        <div class="field">
          <label>&nbsp;</label>
          <button class="btn btn-primary" @click="keyword = ''">清空筛选</button>
        </div>
      </div>

      <div v-if="loading" class="notice">正在加载共享资料...</div>
      <div v-else-if="!filteredMaterials.length" class="notice">当前没有符合条件的共享资料。</div>
      <div v-else class="material-list material-list-compact">
        <div v-for="item in filteredMaterials" :key="item.id" class="material-item material-item-compact">
          <div class="material-main">
            <div class="material-title-row">
              <strong>{{ item.title || item.file_name }}</strong>
              <span class="badge ok">{{ item.visibility_label }}</span>
              <span class="badge neutral">{{ item.file_size_label }}</span>
            </div>
            <p>{{ item.description || '暂无说明' }}</p>
            <div class="material-meta">
              <span>上传者：{{ item.owner_name }}</span>
              <span>{{ item.file_name }}</span>
              <span>{{ item.created_at }}</span>
            </div>
          </div>
          <div class="reservation-actions">
            <button class="btn btn-secondary btn-sm" @click="downloadMaterial(item)">查看</button>
          </div>
        </div>
      </div>
    </section>

    <NoticePopup
      v-model="popup.visible"
      :title="popup.title"
      :message="popup.message"
      :type="popup.type"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { materialApi } from '../api/materials'
import NoticePopup from '../components/NoticePopup.vue'

const popup = reactive({ visible: false, type: 'success', title: '提示', message: '' })
const materials = ref([])
const loading = ref(false)
const keyword = ref('')

const filteredMaterials = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return materials.value
  return materials.value.filter((item) => [item.title, item.description, item.owner_name, item.file_name]
    .filter(Boolean)
    .some((part) => String(part).toLowerCase().includes(q)))
})

async function loadMaterials() {
  loading.value = true
  try {
    const res = await materialApi.list({ scope: 'shared' })
    materials.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    popup.type = 'error'
    popup.title = '加载失败'
    popup.message = e.response?.data?.detail || '加载共享资料失败'
    popup.visible = true
  } finally {
    loading.value = false
  }
}

async function downloadMaterial(item) {
  try {
    const res = await materialApi.download(item.id)
    const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.file_name || item.title || '学习资料'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    popup.type = 'error'
    popup.title = '下载失败'
    popup.message = e.response?.data?.detail || '资料下载失败'
    popup.visible = true
  }
}

onMounted(loadMaterials)
</script>
