<template>
  <Teleport to="body">
    <Transition name="menu-fade">
      <div v-if="modelValue" class="popup-backdrop" @click.self="close">
        <div class="popup-card" :class="`popup-${type}`" role="dialog" aria-modal="true" :aria-label="title">
          <div class="popup-head">
            <div>
              <div class="popup-title">{{ title }}</div>
              <p class="popup-message">{{ message }}</p>
            </div>
            <button class="popup-close" type="button" @click="close">×</button>
          </div>
          <div class="popup-actions">
            <button class="btn btn-primary btn-sm" type="button" @click="close">知道了</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '提示' },
  message: { type: String, default: '' },
  type: { type: String, default: 'info' },
})

const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}
</script>
