<script setup lang="ts">
const props = defineProps<{
  methods: Array<{ name: string; label: string; description?: string }>
  modelValue?: string
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
}>()

const icons: Record<string, string> = {
  forgedan: '&#9876;',
  autodan: '&#9881;',
  pair: '&#9878;',
  gcg: '&#9889;',
  crescendo: '&#127926;',
  tap: '&#127795;',
}
</script>

<template>
  <div class="method-grid">
    <div
      v-for="m in methods"
      :key="m.name"
      class="method-card"
      :class="{ active: modelValue === m.name }"
      @click="emit('update:modelValue', m.name)"
    >
      <span class="method-icon" v-html="icons[m.name.toLowerCase()] || '&#9733;'"></span>
      <div class="method-info">
        <div class="method-name">{{ m.label || m.name }}</div>
        <div class="method-desc">{{ m.description || '' }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.method-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.method-card {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.15s;
}
.method-card:hover { border-color: var(--color-primary); }
.method-card.active {
  border-color: var(--color-primary);
  background: rgba(88,166,255,0.08);
}
.method-icon { font-size: 24px; }
.method-name { font-weight: 600; font-size: 14px; }
.method-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
</style>
