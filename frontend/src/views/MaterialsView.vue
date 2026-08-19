<template>
  <div class="page-stack materials-page">
    <section class="card hero materials-hero materials-hero-plus">
      <div class="hero-head hero-head-rich">
        <div>
          <h2>资料浏览、上传与管理整合入口</h2>
        </div>
        <div class="today-box">
          <span>我的资料</span>
          <strong>{{ myMaterials.length }}</strong>
        </div>
      </div>

      <div class="metric-row metric-row-4">
        <div class="metric metric-rich"><strong>{{ sharedMaterials.length }}</strong><span>共享资料</span><small>公开可浏览</small></div>
        <div class="metric metric-rich"><strong>{{ myMaterials.length }}</strong><span>我的资料</span><small>{{ mySharedCount }} 份已共享</small></div>
        <div class="metric metric-rich"><strong>{{ formatFileSize(sharedTotalSize) }}</strong><span>共享总大小</span><small>方便预估资料规模</small></div>
        <div class="metric metric-rich"><strong>{{ formatFileSize(myTotalSize) }}</strong><span>个人资料总大小</span><small>最近上传 {{ recentMine[0]?.created_at || '暂无' }}</small></div>
      </div>
    </section>

    <section class="material-nav-grid material-nav-grid-plus">
      <RouterLink class="card material-nav-card" to="/materials/shared">
        <div class="badge ok">页面 1</div>
        <h3>共享资料</h3>
        <p>浏览其他同学公开分享的文件、笔记和复习资料。</p>
        <div class="material-nav-meta">
          <span>{{ sharedMaterials.length }} 份资料</span>
          <span>进入查看</span>
        </div>
      </RouterLink>

      <RouterLink class="card material-nav-card" to="/materials/upload">
        <div class="badge warn">页面 2</div>
        <h3>上传资料</h3>
        <p>单独进入上传页面，填写标题、说明，并设置私人或共享。</p>
        <div class="material-nav-meta">
          <span>支持 25MB 内文件</span>
          <span>立即上传</span>
        </div>
      </RouterLink>

      <RouterLink class="card material-nav-card" to="/materials/mine">
        <div class="badge neutral">页面 3</div>
        <h3>我的资料</h3>
        <p>集中管理自己上传的全部资料，支持切换可见性和删除。</p>
        <div class="material-nav-meta">
          <span>{{ myMaterials.length }} 份资料</span>
          <span>进入管理</span>
        </div>
      </RouterLink>
    </section>

    <section class="dashboard-grid dashboard-grid-home-plus">
      <div class="card">
        <div class="section-title">
          <div>
            <h3>最近共享资料</h3>
            <p>在进入列表页前先快速看一下最新内容</p>
          </div>
          <RouterLink class="btn btn-secondary btn-sm" to="/materials/shared">查看全部</RouterLink>
        </div>
        <div v-if="recentShared.length" class="reservation-list compact-list">
          <div v-for="item in recentShared" :key="item.id" class="reservation-item">
            <div>
              <div class="reservation-title">{{ item.title || item.file_name }}</div>
              <div class="reservation-meta">{{ item.owner_name }} · {{ item.file_size_label }}</div>
              <div class="reservation-meta">{{ item.description || '暂无说明' }}</div>
            </div>
            <span class="badge ok">共享</span>
          </div>
        </div>
        <div v-else class="notice">当前还没有共享资料。</div>
      </div>

      <div class="card">
        <div class="section-title">
          <div>
            <h3>我的最近上传</h3>
            <p>方便快速继续管理自己的资料</p>
          </div>
          <RouterLink class="btn btn-secondary btn-sm" to="/materials/mine">进入管理</RouterLink>
        </div>
        <div v-if="recentMine.length" class="reservation-list compact-list">
          <div v-for="item in recentMine" :key="item.id" class="reservation-item">
            <div>
              <div class="reservation-title">{{ item.title || item.file_name }}</div>
              <div class="reservation-meta">{{ item.file_name }}</div>
              <div class="reservation-meta">{{ item.created_at }}</div>
            </div>
            <span class="badge" :class="item.is_shared ? 'ok' : 'neutral'">{{ item.visibility_label }}</span>
          </div>
        </div>
        <div v-else class="notice">你还没有上传资料，可以先上传第一份学习文件。</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { materialApi } from '../api/materials'

const sharedMaterials = ref([])
const myMaterials = ref([])

const sharedTotalSize = computed(() => sharedMaterials.value.reduce((sum, item) => sum + Number(item.file_size || 0), 0))
const myTotalSize = computed(() => myMaterials.value.reduce((sum, item) => sum + Number(item.file_size || 0), 0))
const mySharedCount = computed(() => myMaterials.value.filter(item => item.is_shared).length)
const recentShared = computed(() => sharedMaterials.value.slice(0, 4))
const recentMine = computed(() => myMaterials.value.slice(0, 4))

function formatFileSize(size) {
  const total = Number(size || 0)
  if (!total) return '0 B'
  if (total < 1024) return `${total} B`
  if (total < 1024 * 1024) return `${(total / 1024).toFixed(1)} KB`
  return `${(total / (1024 * 1024)).toFixed(1)} MB`
}

async function loadSummary() {
  try {
    const [sharedRes, mineRes] = await Promise.all([
      materialApi.list({ scope: 'shared' }),
      materialApi.list({ scope: 'mine' }),
    ])
    sharedMaterials.value = Array.isArray(sharedRes.data) ? sharedRes.data : []
    myMaterials.value = Array.isArray(mineRes.data) ? mineRes.data : []
  } catch {
    sharedMaterials.value = []
    myMaterials.value = []
  }
}

onMounted(loadSummary)
</script>
