<!--
  管理端 · 资料管理：
  - 查看用户上传资料；
  - 按共享状态和关键词筛选；
  - 删除违规或无效资料。
-->
<template>
  <div class="page-stack admin-materials-page">
    <section class="card hero admin-hero admin-hero-compact">
      <div class="hero-head hero-head-compact">
        <div>
          <div class="badge ok">管理端 · 资料管理</div>
          <h2>统一管理所有用户上传的学习资料</h2>
          <p>管理员可以查看全部资料、按关键字筛选、修改资料可见性，或直接删除违规内容。</p>
        </div>
        <div class="toolbar">
          <button class="btn btn-secondary btn-sm" @click="resetPage(); loadMaterials()">刷新</button>
        </div>
      </div>
      <div class="metric-row metric-row-4 admin-materials-metrics admin-materials-metrics-tight">
        <div class="metric">
          <strong>{{ stats.total }}</strong>
          <span>资料总数</span>
        </div>
        <div class="metric">
          <strong>{{ stats.shared }}</strong>
          <span>共享资料</span>
        </div>
        <div class="metric">
          <strong>{{ stats.private }}</strong>
          <span>私人资料</span>
        </div>
        <div class="metric">
          <strong>{{ stats.users }}</strong>
          <span>上传用户</span>
        </div>
      </div>
    </section>

    <section class="card list-card admin-materials-card">
      <div class="section-title">
        <div>
          <h3>全部资料列表</h3>
          <p>共 {{ materials.length }} 条记录，当前第 {{ currentPage }} / {{ totalPages }} 页，筛选、表格和操作按钮保持与其他管理页一致。</p>
        </div>
      </div>

      <div class="toolbar admin-toolbar admin-materials-toolbar admin-materials-toolbar-lined">
        <div class="field">
          <label>搜索关键字</label>
          <input class="input" v-model="keyword" placeholder="标题 / 说明 / 用户名 / 昵称" @keyup.enter="resetPage(); loadMaterials()" />
        </div>
        <div class="field">
          <label>资料类型</label>
          <select class="input" v-model="visibilityFilter" @change="resetPage(); loadMaterials()">
            <option value="all">全部</option>
            <option value="shared">共享资料</option>
            <option value="private">私人资料</option>
          </select>
        </div>
        <div class="field admin-materials-actions">
          <label>&nbsp;</label>
          <button class="btn btn-primary" @click="resetPage(); loadMaterials()">查询</button>
        </div>
      </div>

      <div v-if="loading" class="notice">正在加载资料...</div>
      <div v-else-if="!materials.length" class="notice">暂无符合条件的资料。</div>
      <div v-else class="table-wrap admin-materials-table-wrap">
        <table class="table admin-table admin-materials-table admin-materials-table-refined">
          <colgroup>
            <col class="col-title" />
            <col class="col-owner" />
            <col class="col-type" />
            <col class="col-size" />
            <col class="col-time" />
            <col class="col-action" />
          </colgroup>
          <thead>
            <tr>
              <th>标题</th>
              <th>上传者</th>
              <th>类型</th>
              <th>大小</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedMaterials" :key="item.id">
              <td class="material-title-cell">
                <div class="material-table-title single-line-cell" :title="item.title || item.file_name">{{ item.title || item.file_name }}</div>
                <div class="small-muted text-ellipsis" :title="item.description || '暂无说明'">{{ item.description || '暂无说明' }}</div>
              </td>
              <td>
                <div class="single-line-cell" :title="item.owner_name">{{ item.owner_name }}</div>
                <div class="small-muted text-ellipsis" :title="item.file_name">{{ item.file_name }}</div>
              </td>
              <td>
                <span class="badge" :class="item.is_shared ? 'ok' : 'neutral'">{{ item.visibility_label }}</span>
              </td>
              <td class="single-line-cell">{{ item.file_size_label }}</td>
              <td class="single-line-cell" :title="item.created_at">{{ item.created_at }}</td>
              <td>
                <div class="reservation-actions admin-materials-actions-inline">
                  <button class="btn btn-secondary btn-sm" @click="downloadMaterial(item)">查看</button>
                  <button class="btn btn-ghost btn-sm" @click="toggleVisibility(item)">{{ item.is_shared ? '设为私人' : '设为共享' }}</button>
                  <button class="btn btn-danger btn-sm" @click="removeMaterial(item)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar
        v-if="materials.length"
        v-model="currentPage"
        :total="materials.length"
        :page-size="pageSize"
      />

      <div v-if="message" class="notice success">{{ message }}</div>
      <div v-if="error" class="notice error">{{ error }}</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { materialApi } from '../api/materials'

const materials = ref([])
const loading = ref(false)
const keyword = ref('')
const visibilityFilter = ref('all')
const message = ref('')
const error = ref('')
const currentPage = ref(1)
const pageSize = 8

const totalPages = computed(() => Math.max(1, Math.ceil(materials.value.length / pageSize)))
const paginatedMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return materials.value.slice(start, start + pageSize)
})

const stats = computed(() => ({
  total: materials.value.length,
  shared: materials.value.filter((item) => item.is_shared).length,
  private: materials.value.filter((item) => !item.is_shared).length,
  users: new Set(materials.value.map((item) => item.owner_name)).size,
}))

function resetPage() {
  currentPage.value = 1
}

async function loadMaterials() {
  loading.value = true
  message.value = ''
  error.value = ''
  try {
    const params = {
      scope: 'all',
      q: keyword.value.trim() || undefined,
    }
    const res = await materialApi.list(params)
    const all = Array.isArray(res.data) ? res.data : []
    materials.value = visibilityFilter.value === 'shared'
      ? all.filter((item) => item.is_shared)
      : visibilityFilter.value === 'private'
        ? all.filter((item) => !item.is_shared)
        : all
  } catch (e) {
    error.value = e.response?.data?.detail || '加载资料失败'
  } finally {
    loading.value = false
  }
}

async function downloadMaterial(item) {
  message.value = ''
  error.value = ''
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
    error.value = e.response?.data?.detail || '资料下载失败'
  }
}

async function toggleVisibility(item) {
  message.value = ''
  error.value = ''
  try {
    const res = await materialApi.update(item.id, {
      title: item.title,
      description: item.description,
      is_shared: !item.is_shared,
    })
    message.value = res.data.detail || '资料状态已更新'
    await loadMaterials()
  } catch (e) {
    error.value = e.response?.data?.detail || '更新失败'
  }
}

async function removeMaterial(item) {
  if (!window.confirm(`确认删除资料《${item.title || item.file_name}》吗？`)) return
  message.value = ''
  error.value = ''
  try {
    const res = await materialApi.delete(item.id)
    message.value = res.data.detail || '资料已删除'
    await loadMaterials()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除失败'
  }
}

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

onMounted(loadMaterials)
</script>
