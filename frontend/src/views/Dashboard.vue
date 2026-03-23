<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import api from '../api/client'
import type { EChartsOption } from 'echarts'

const stats = ref({ total: 0, success: 0, failed: 0, running: 0 })
const recentTasks = ref<any[]>([])

const asrTrendOption = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  grid: { top: 30, right: 20, bottom: 30, left: 50 },
  xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'], axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e' } },
  yAxis: { type: 'value', max: 100, axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#21262d' } } },
  series: [{
    type: 'line', smooth: true, data: [65, 72, 68, 80, 75, 82, 78],
    lineStyle: { color: '#58a6ff', width: 2 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(88,166,255,0.25)' }, { offset: 1, color: 'rgba(88,166,255,0)' }] } },
    itemStyle: { color: '#58a6ff' },
  }],
  tooltip: { trigger: 'axis', backgroundColor: '#1c2128', borderColor: '#30363d', textStyle: { color: '#e6edf3' } },
}))

const methodDistOption = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  series: [{
    type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'],
    data: [
      { value: 35, name: 'FORGEDAN', itemStyle: { color: '#58a6ff' } },
      { value: 20, name: 'AutoDAN', itemStyle: { color: '#a371f7' } },
      { value: 15, name: 'PAIR', itemStyle: { color: '#3fb950' } },
      { value: 12, name: 'GCG', itemStyle: { color: '#d29922' } },
      { value: 10, name: 'Crescendo', itemStyle: { color: '#f0883e' } },
      { value: 8, name: 'TAP', itemStyle: { color: '#f85149' } },
    ],
    label: { color: '#8b949e', fontSize: 12 },
  }],
  tooltip: { backgroundColor: '#1c2128', borderColor: '#30363d', textStyle: { color: '#e6edf3' } },
}))

const statCards = computed(() => [
  { label: '总测试数', value: stats.value.total, color: '#58a6ff', icon: 'DataAnalysis' },
  { label: '成功', value: stats.value.success, color: '#3fb950', icon: 'SuccessFilled' },
  { label: '失败', value: stats.value.failed, color: '#f85149', icon: 'CircleCloseFilled' },
  { label: '进行中', value: stats.value.running, color: '#d29922', icon: 'Loading' },
])

onMounted(async () => {
  try {
    const { data } = await api.get('/dashboard/stats')
    stats.value = data
  } catch { /* use defaults */ }
  try {
    const { data } = await api.get('/attacks/history')
    recentTasks.value = (data.tasks || data || []).slice(0, 10)
  } catch { /* use defaults */ }
})

function statusType(s: string) {
  return s === 'success' ? 'success' : s === 'failed' ? 'danger' : s === 'running' ? 'warning' : 'info'
}
function statusLabel(s: string) {
  return s === 'success' ? '成功' : s === 'failed' ? '失败' : s === 'running' ? '运行中' : '等待中'
}
</script>

<template>
  <div class="dashboard">
    <div class="stats-row">
      <div v-for="card in statCards" :key="card.label" class="stat-card">
        <div class="stat-icon" :style="{ color: card.color }">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div class="value" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="label">{{ card.label }}</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="card-title">ASR 趋势</div>
        <v-chart :option="asrTrendOption" style="height: 280px" autoresize />
      </div>
      <div class="chart-card">
        <div class="card-title">攻击方法分布</div>
        <v-chart :option="methodDistOption" style="height: 280px" autoresize />
      </div>
    </div>

    <div class="table-card">
      <div class="card-title">最近任务</div>
      <el-table :data="recentTasks" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="200" />
        <el-table-column prop="method" label="攻击方法" width="140" />
        <el-table-column prop="model" label="目标模型" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 20px; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stat-card { display: flex; flex-direction: column; align-items: center; text-align: center; }
.stat-icon { margin-bottom: 8px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-card, .table-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
}
.card-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; }

@media (max-width: 900px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}
</style>
