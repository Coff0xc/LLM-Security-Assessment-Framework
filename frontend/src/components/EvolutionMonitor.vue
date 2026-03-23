<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { getSocket } from '../api/client'
import type { EChartsOption } from 'echarts'

const props = defineProps<{ taskId?: string }>()

const fitnessData = ref<number[]>([])
const logs = ref<string[]>([])
const progress = ref(0)
const currentPrompt = ref('')
const generations = ref<number[]>([])

const chartOption = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  grid: { top: 30, right: 20, bottom: 30, left: 50 },
  xAxis: { type: 'category', data: generations.value.map(String), axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e' } },
  yAxis: { type: 'value', axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } },
  series: [{
    type: 'line',
    data: fitnessData.value,
    smooth: true,
    lineStyle: { color: '#58a6ff', width: 2 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(88,166,255,0.3)' }, { offset: 1, color: 'rgba(88,166,255,0)' }] } },
    itemStyle: { color: '#58a6ff' },
  }],
  tooltip: { trigger: 'axis', backgroundColor: '#1c2128', borderColor: '#30363d', textStyle: { color: '#e6edf3' } },
}))

onMounted(() => {
  const socket = getSocket()
  socket.on('attack_progress', (data: any) => {
    if (props.taskId && data.task_id !== props.taskId) return
    progress.value = data.progress || 0
    if (data.fitness !== undefined) {
      fitnessData.value.push(data.fitness)
      generations.value.push(generations.value.length + 1)
    }
    if (data.current_prompt) currentPrompt.value = data.current_prompt
    if (data.log) logs.value.push(data.log)
  })
})

onUnmounted(() => {
  getSocket().off('attack_progress')
})

function reset() {
  fitnessData.value = []
  generations.value = []
  logs.value = []
  progress.value = 0
  currentPrompt.value = ''
}

defineExpose({ reset })
</script>

<template>
  <div class="evo-monitor">
    <div class="monitor-section">
      <div class="section-title">进度</div>
      <el-progress :percentage="progress" :stroke-width="10" :color="'#58a6ff'" />
    </div>
    <div class="monitor-section">
      <div class="section-title">适应度趋势</div>
      <v-chart :option="chartOption" style="height: 200px" autoresize />
    </div>
    <div class="monitor-section" v-if="currentPrompt">
      <div class="section-title">当前候选提示词</div>
      <div class="prompt-preview">{{ currentPrompt }}</div>
    </div>
    <div class="monitor-section">
      <div class="section-title">日志</div>
      <div class="log-panel">
        <div v-for="(log, i) in logs.slice(-50)" :key="i" class="log-line">{{ log }}</div>
        <div v-if="!logs.length" class="log-empty">等待任务开始...</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evo-monitor { display: flex; flex-direction: column; gap: 16px; }
.monitor-section { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; }
.section-title { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; font-weight: 600; }
.prompt-preview {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
  font-size: 13px;
  max-height: 120px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-panel {
  background: var(--bg-primary);
  border-radius: 6px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Consolas', monospace;
  font-size: 12px;
}
.log-line { color: var(--text-secondary); line-height: 1.6; }
.log-empty { color: var(--text-secondary); text-align: center; padding: 20px; }
</style>
