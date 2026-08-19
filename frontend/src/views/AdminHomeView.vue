<!--
  管理端首页：汇总预约、座位、用户、资料和违规等运营数据。
-->
<template>
  <div class="admin-home-layout">
    <section class="card hero admin-hero admin-hero-plus">
      <div class="hero-head hero-head-rich">
        <div>
          <div class="badge warn">管理端首页</div>
          <h2>统览座位、预约、信用分与学习趋势</h2>
        </div>
        <div class="hero-side-stack">
          <div class="today-box big">
            <span>今日预约</span>
            <strong>{{ summary.reservation_today ?? 0 }}</strong>
          </div>
          <div class="today-box">
            <span>今日打卡</span>
            <strong>{{ summary.checkin_today ?? 0 }}</strong>
          </div>
        </div>
      </div>
      <div class="metric-row metric-row-4">
        <div class="metric metric-rich"><strong>{{ summary.seat_total ?? 0 }}</strong><span>座位总数</span><small>{{ summary.seat_active ?? 0 }} 个可用</small></div>
        <div class="metric metric-rich"><strong>{{ summary.reservation_active ?? 0 }}</strong><span>进行中预约</span><small>当前仍需关注</small></div>
        <div class="metric metric-rich"><strong>{{ analytics.system_report?.violation_month ?? 0 }}</strong><span>本月违规次数</span><small>本周 {{ analytics.system_report?.violation_week ?? 0 }} 次</small></div>
        <div class="metric metric-rich"><strong>{{ formatMinutes(summary.study_minutes_today) }}</strong><span>全站今日学习</span><small>来自有效签到后的统计</small></div>
      </div>
    </section>

    <section class="admin-grid admin-grid-plus">
      <div class="card">
        <div class="section-title">
          <div>
            <h3>运营焦点</h3>
          </div>
        </div>
        <div class="status-list status-list-contrast">
          <div class="status-line"><span>座位维护</span><strong>{{ summary.seat_active ?? 0 }} / {{ summary.seat_total ?? 0 }} 个座位可用</strong></div>
          <div class="status-line"><span>预约处理</span><strong>{{ summary.reservation_active ?? 0 }} 条进行中预约</strong></div>
          <div class="status-line"><span>用户风险</span><strong>{{ analytics.system_report?.violation_week ?? 0 }} 条本周违规</strong></div>
          <div class="status-line"><span>资料规模</span><strong>{{ summary.material_total ?? 0 }} 份资料在库</strong></div>
        </div>
        <div class="panel-action-row">
          <RouterLink class="btn btn-secondary" to="/admin/seats">维护座位</RouterLink>
          <RouterLink class="btn btn-secondary" to="/admin/reservations">处理预约</RouterLink>
          <RouterLink class="btn btn-primary" to="/admin/users">查看用户</RouterLink>
        </div>
      </div>

      <div class="card">
        <div class="section-title">
          <div>
            <h3>系统运行状态</h3>
          </div>
          <button class="btn btn-secondary btn-sm" @click="reloadAll">刷新</button>
        </div>
        <div class="status-list">
          <div class="status-line"><span>今日预约</span><strong>{{ summary.reservation_today ?? 0 }}</strong></div>
          <div class="status-line"><span>今日打卡</span><strong>{{ summary.checkin_today ?? 0 }}</strong></div>
          <div class="status-line"><span>本日学习时长</span><strong>{{ formatMinutes(summary.study_minutes_today) }}</strong></div>
          <div class="status-line"><span>本周违规</span><strong>{{ analytics.system_report?.violation_week ?? 0 }}</strong></div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid dashboard-analytics-grid dashboard-analytics-grid-wide">
      <div class="card">
        <div class="section-title">
          <div>
            <h3>近 7 天全站学习时长</h3>
            <p>按所有用户的有效学习时长统计</p>
          </div>
        </div>
        <div class="bar-chart">
          <div v-for="item in analytics.weekly_chart" :key="item.date" class="bar-item">
            <div class="bar-value">{{ item.minutes }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="barStyle(item.minutes, weeklyMax)"></div>
            </div>
            <div class="bar-label">{{ item.label }}</div>
          </div>
        </div>
      </div>

      <div class="side-stack">
        <div class="card">
          <div class="section-title">
            <div>
              <h3>热门座位 TOP 5</h3>
              <p>按本月累计使用分钟数排序</p>
            </div>
          </div>
          <div class="violation-list compact-list" v-if="analytics.system_report?.top_seats?.length">
            <div class="violation-item" v-for="item in analytics.system_report.top_seats" :key="item.seat_code">
              <div>
                <div class="reservation-title">{{ item.seat_code }}</div>
                <div class="reservation-meta">本月累计使用 {{ formatMinutes(item.minutes) }}</div>
              </div>
              <span class="badge ok">TOP</span>
            </div>
          </div>
          <div v-else class="notice">暂无足够数据生成热门座位排行。</div>
        </div>

        <div class="card">
          <div class="section-title">
            <div>
              <h3>运营提示</h3>
            </div>
          </div>
          <div class="status-list">
            <div class="status-line"><span>座位启用率</span><strong>{{ summary.seat_total ? Math.round((summary.seat_active || 0) / summary.seat_total * 100) : 0 }}%</strong></div>
            <div class="status-line"><span>预约活跃度</span><strong>{{ summary.reservation_active ? '当前繁忙' : '当前平稳' }}</strong></div>
            <div class="status-line"><span>违规风险</span><strong>{{ (analytics.system_report?.violation_week || 0) > 0 ? '需持续关注' : '本周较平稳' }}</strong></div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { reservationApi } from '../api/reservations'
import { formatMinutes, getBarHeightStyle as barStyle } from '../utils/uiFormat'

const summary = ref({})
const analytics = ref({ weekly_chart: [], system_report: {} })
const weeklyMax = computed(() => Math.max(60, ...((analytics.value.weekly_chart || []).map(item => item.minutes || 0))))


async function loadSummary() {
  const res = await reservationApi.summary()
  summary.value = res.data || {}
}

async function loadAnalytics() {
  const res = await reservationApi.analytics()
  analytics.value = res.data || { weekly_chart: [], system_report: {} }
}

async function reloadAll() {
  await Promise.all([loadSummary(), loadAnalytics()])
}

onMounted(reloadAll)
</script>
