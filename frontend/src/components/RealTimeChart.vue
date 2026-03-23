<script setup lang="ts">
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'

defineProps<{
  title?: string
  option: EChartsOption
  height?: string
}>()
</script>

<template>
  <div :style="{ height: height || '300px', width: '100%' }">
    <v-chart ref="chartRef" :option="option" autoresize />
  </div>
</template>
