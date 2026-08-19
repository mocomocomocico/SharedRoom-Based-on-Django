<!--
  通用分页条：所有列表/平面图分页统一使用这个组件，避免每个页面重复维护上一页/下一页逻辑。
-->
<template>
  <div v-if="total > 0" class="pagination-bar">
    <div class="pagination-summary">
      第 {{ safePage }} / {{ totalPages }} 页 · 显示 {{ startIndex }}-{{ endIndex }} 条，共 {{ total }} 条
    </div>
    <div class="pagination-actions">
      <button class="btn btn-secondary btn-sm" type="button" :disabled="safePage <= 1" @click="changePage(1)">首页</button>
      <button class="btn btn-secondary btn-sm" type="button" :disabled="safePage <= 1" @click="changePage(safePage - 1)">上一页</button>
      <button class="btn btn-secondary btn-sm" type="button" :disabled="safePage >= totalPages" @click="changePage(safePage + 1)">下一页</button>
      <button class="btn btn-secondary btn-sm" type="button" :disabled="safePage >= totalPages" @click="changePage(totalPages)">末页</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 1 },
  total: { type: Number, default: 0 },
  pageSize: { type: Number, default: 10 },
})

const emit = defineEmits(['update:modelValue'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / Math.max(1, props.pageSize))))
const safePage = computed(() => Math.min(Math.max(1, props.modelValue || 1), totalPages.value))
const startIndex = computed(() => (props.total ? (safePage.value - 1) * props.pageSize + 1 : 0))
const endIndex = computed(() => Math.min(safePage.value * props.pageSize, props.total))

function changePage(page) {
  const next = Math.min(Math.max(1, page), totalPages.value)
  if (next !== props.modelValue) emit('update:modelValue', next)
}
</script>
