<template>
  <div class="page-stack materials-page">
    <section class="card hero materials-hero">
      <div class="hero-head hero-head-rich">
        <div>
          <div class="badge warn">学习资料 · 页面 2</div>
          <h2>上传资料</h2>
          <p>上传页除了保留独立流程，也加入了上传提示和最近上传预览，让页面更完整。</p>
        </div>
        <div class="today-box">
          <span>上传状态</span>
          <strong>{{ materialUploading ? '进行中' : '待上传' }}</strong>
        </div>
      </div>

      <div class="material-subnav">
        <RouterLink class="btn btn-secondary btn-sm" to="/materials">返回资料中心</RouterLink>
        <RouterLink class="btn btn-ghost btn-sm" to="/materials/shared">共享资料</RouterLink>
        <RouterLink class="btn btn-ghost btn-sm" to="/materials/mine">我的资料</RouterLink>
      </div>
    </section>

    <section class="dashboard-grid dashboard-grid-home-plus">
      <div class="card material-panel upload-panel single-panel-width">
        <div class="section-title">
          <div>
            <h3>上传新资料</h3>
            <p>填写资料信息后即可提交</p>
          </div>
        </div>

        <form class="form-stack material-upload-form" @submit.prevent="uploadMaterial">
          <div class="field">
            <label>资料标题</label>
            <input class="input" v-model="materialForm.title" placeholder="例如：线性代数整理" />
          </div>

          <div class="field">
            <label>资料说明</label>
            <textarea class="textarea" v-model="materialForm.description" placeholder="可选，简单介绍这份资料"></textarea>
          </div>

          <div class="field">
            <label>选择文件</label>
            <input ref="fileInputRef" class="input" type="file" @change="handleFileChange" />
          </div>

          <div class="field">
            <label>资料类型</label>
            <select class="input" v-model="materialForm.visibility">
              <option value="private">私人资料（仅自己可见）</option>
              <option value="shared">共享资料（其他人可见）</option>
            </select>
          </div>

          <div class="material-upload-meta">
            <span>{{ materialForm.file ? materialForm.file.name : '尚未选择文件' }}</span>
            <span>单文件最大 25MB</span>
          </div>

          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="resetMaterialForm">重置</button>
            <button class="btn btn-primary" type="submit" :disabled="materialUploading || !materialForm.file">
              {{ materialUploading ? '上传中...' : '上传资料' }}
            </button>
          </div>
        </form>
      </div>

      <div class="side-stack">
        <div class="card">
          <div class="section-title">
            <div>
              <h3>上传建议</h3>
              <p>让资料更容易被自己和别人再次找到</p>
            </div>
          </div>
          <div class="status-list">
            <div class="status-line"><span>标题建议</span><strong>写清课程名 + 内容</strong></div>
            <div class="status-line"><span>说明建议</span><strong>写清适用章节</strong></div>
            <div class="status-line"><span>共享资料</span><strong>适合笔记、总结、讲义</strong></div>
            <div class="status-line"><span>私人资料</span><strong>适合草稿、阶段整理</strong></div>
          </div>
        </div>

        <div class="card">
          <div class="section-title">
            <div>
              <h3>最近上传</h3>
              <p>上传完成后可在这里确认结果</p>
            </div>
          </div>
          <div v-if="recentMaterials.length" class="reservation-list compact-list">
            <div class="reservation-item" v-for="item in recentMaterials" :key="item.id">
              <div>
                <div class="reservation-title">{{ item.title || item.file_name }}</div>
                <div class="reservation-meta">{{ item.file_name }}</div>
                <div class="reservation-meta">{{ item.created_at }}</div>
              </div>
              <span class="badge" :class="item.is_shared ? 'ok' : 'neutral'">{{ item.visibility_label }}</span>
            </div>
          </div>
          <div v-else class="notice">你还没有上传过资料。</div>
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
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { materialApi } from '../api/materials'
import NoticePopup from '../components/NoticePopup.vue'

const popup = reactive({ visible: false, type: 'success', title: '提示', message: '' })
const materialUploading = ref(false)
const fileInputRef = ref(null)
const recentMaterials = ref([])
const materialForm = reactive({ title: '', description: '', file: null, visibility: 'private' })

function handleFileChange(event) {
  const file = event.target.files?.[0] || null
  materialForm.file = file
}

function resetMaterialForm() {
  materialForm.title = ''
  materialForm.description = ''
  materialForm.file = null
  materialForm.visibility = 'private'
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function loadRecentMaterials() {
  const res = await materialApi.list({ scope: 'mine' })
  recentMaterials.value = (Array.isArray(res.data) ? res.data : []).slice(0, 4)
}

async function uploadMaterial() {
  if (!materialForm.file) return
  materialUploading.value = true
  try {
    const formData = new FormData()
    formData.append('title', materialForm.title)
    formData.append('description', materialForm.description)
    formData.append('file', materialForm.file)
    formData.append('is_shared', materialForm.visibility === 'shared' ? 'true' : 'false')
    const res = await materialApi.upload(formData)
    popup.type = 'success'
    popup.title = '上传成功'
    popup.message = res.data.detail || '学习资料上传成功'
    popup.visible = true
    resetMaterialForm()
    await loadRecentMaterials()
  } catch (e) {
    popup.type = 'error'
    popup.title = '上传失败'
    popup.message = e.response?.data?.detail || '学习资料上传失败'
    popup.visible = true
  } finally {
    materialUploading.value = false
  }
}

onMounted(async () => {
  try {
    await loadRecentMaterials()
  } catch {
    recentMaterials.value = []
  }
})
</script>
