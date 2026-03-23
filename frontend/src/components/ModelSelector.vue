<script setup lang="ts">
import { computed } from 'vue'
import { useModelsStore } from '../stores/models'

const props = defineProps<{
  modelValue?: string
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
}>()

const store = useModelsStore()

const grouped = computed(() => {
  const intl: any[] = []
  const cn: any[] = []
  const local: any[] = []
  for (const m of store.models) {
    if (['ollama', 'vllm', 'lmstudio'].includes(m.provider)) local.push(m)
    else if (['zhipu', 'baidu', 'dashscope', 'minimax', 'moonshot', 'deepseek', 'yi', 'stepfun', 'sensetime'].includes(m.provider)) cn.push(m)
    else intl.push(m)
  }
  return { intl, cn, local }
})
</script>

<template>
  <el-select
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    placeholder="选择目标模型"
    filterable
    style="width: 100%"
  >
    <el-option-group label="国际模型">
      <el-option v-for="m in grouped.intl" :key="m.id" :label="m.name" :value="m.id">
        <span>{{ m.name }}</span>
        <el-tag v-if="m.status === 'connected'" type="success" size="small" style="margin-left:8px">已连接</el-tag>
      </el-option>
    </el-option-group>
    <el-option-group label="国产模型">
      <el-option v-for="m in grouped.cn" :key="m.id" :label="m.name" :value="m.id">
        <span>{{ m.name }}</span>
        <el-tag v-if="m.status === 'connected'" type="success" size="small" style="margin-left:8px">已连接</el-tag>
      </el-option>
    </el-option-group>
    <el-option-group label="本地模型">
      <el-option v-for="m in grouped.local" :key="m.id" :label="m.name" :value="m.id">
        <span>{{ m.name }}</span>
        <el-tag v-if="m.status === 'connected'" type="success" size="small" style="margin-left:8px">已连接</el-tag>
      </el-option>
    </el-option-group>
  </el-select>
</template>
