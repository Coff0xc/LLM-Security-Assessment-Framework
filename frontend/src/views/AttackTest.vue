<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAttackStore } from '../stores/attack'
import { useModelsStore } from '../stores/models'
import ModelSelector from '../components/ModelSelector.vue'
import EvolutionMonitor from '../components/EvolutionMonitor.vue'
import { ElMessage } from 'element-plus'

const attackStore = useAttackStore()
const modelsStore = useModelsStore()
const monitorRef = ref<InstanceType<typeof EvolutionMonitor>>()

const activeTab = ref('forgedan')
const selectedModel = ref('')
const targetPrompt = ref('')
const selectedTemplate = ref('')
const running = ref(false)

const methodTabs = [
  { name: 'forgedan', label: 'FORGEDAN' },
  { name: 'autodan', label: 'AutoDAN' },
  { name: 'pair', label: 'PAIR' },
  { name: 'gcg', label: 'GCG' },
  { name: 'crescendo', label: 'Crescendo' },
  { name: 'tap', label: 'TAP' },
]

// Dynamic params per method
const methodParams = ref<Record<string, any>>({})
const methodSchemas = ref<Record<string, any[]>>({})

onMounted(async () => {
  await modelsStore.fetchModels()
  try {
    await attackStore.fetchMethods()
    for (const m of attackStore.methods) {
      methodSchemas.value[m.name] = m.parameters || []
    }
  } catch { /* fallback defaults */ }
})

const currentSchema = computed(() => methodSchemas.value[activeTab.value] || [])

function getParamValue(paramName: string) {
  if (!methodParams.value[activeTab.value]) methodParams.value[activeTab.value] = {}
  return methodParams.value[activeTab.value][paramName]
}
function setParamValue(paramName: string, val: any) {
  if (!methodParams.value[activeTab.value]) methodParams.value[activeTab.value] = {}
  methodParams.value[activeTab.value][paramName] = val
}

async function startAttack() {
  if (!selectedModel.value) return ElMessage.warning('请选择目标模型')
  if (!targetPrompt.value) return ElMessage.warning('请输入目标提示词')
  running.value = true
  monitorRef.value?.reset()
  try {
    await attackStore.runAttack({
      method: activeTab.value,
      model: selectedModel.value,
      target: targetPrompt.value,
      template: selectedTemplate.value,
      parameters: methodParams.value[activeTab.value] || {},
    })
    ElMessage.success('攻击任务已启动')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '启动失败')
    running.value = false
  }
}
</script>

<template>
  <div class="attack-page">
    <div class="attack-left">
      <el-tabs v-model="activeTab" type="border-card" class="method-tabs">
        <el-tab-pane v-for="m in methodTabs" :key="m.name" :name="m.name" :label="m.label">
          <div class="config-form">
            <!-- Target -->
            <el-form label-position="top">
              <el-form-item label="目标提示词">
                <el-input v-model="targetPrompt" type="textarea" :rows="3" placeholder="输入要测试的目标行为描述..." />
              </el-form-item>

              <el-form-item label="目标模型">
                <ModelSelector v-model="selectedModel" />
              </el-form-item>

              <el-form-item label="模板选择">
                <el-select v-model="selectedTemplate" placeholder="选择提示词模板" style="width:100%" clearable>
                  <el-option label="默认模板" value="default" />
                  <el-option label="角色扮演" value="roleplay" />
                  <el-option label="编码绕过" value="encoding" />
                  <el-option label="多轮对话" value="multiturn" />
                </el-select>
              </el-form-item>

              <!-- Dynamic params -->
              <template v-for="param in currentSchema" :key="param.name">
                <el-form-item :label="param.label || param.name">
                  <el-input-number
                    v-if="param.type === 'number' || param.type === 'integer'"
                    :model-value="getParamValue(param.name) ?? param.default"
                    @update:model-value="setParamValue(param.name, $event)"
                    :min="param.min" :max="param.max" :step="param.step || 1"
                    style="width: 100%"
                  />
                  <el-switch
                    v-else-if="param.type === 'boolean'"
                    :model-value="getParamValue(param.name) ?? param.default"
                    @update:model-value="setParamValue(param.name, $event)"
                  />
                  <el-select
                    v-else-if="param.type === 'select'"
                    :model-value="getParamValue(param.name) ?? param.default"
                    @update:model-value="setParamValue(param.name, $event)"
                    style="width: 100%"
                  >
                    <el-option v-for="opt in param.options" :key="opt" :label="opt" :value="opt" />
                  </el-select>
                  <el-input
                    v-else
                    :model-value="getParamValue(param.name) ?? param.default ?? ''"
                    @update:model-value="setParamValue(param.name, $event)"
                    :placeholder="param.description"
                  />
                </el-form-item>
              </template>

              <el-form-item>
                <el-button type="primary" size="large" @click="startAttack" :loading="running" style="width: 100%">
                  <el-icon><Aim /></el-icon>
                  启动攻击测试
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="attack-right">
      <div class="panel-title">实时监控</div>
      <EvolutionMonitor ref="monitorRef" :task-id="attackStore.currentTask?.id" />
    </div>
  </div>
</template>

<style scoped>
.attack-page { display: flex; gap: 20px; height: calc(100vh - 120px); }
.attack-left { flex: 1; overflow-y: auto; }
.attack-right { width: 400px; overflow-y: auto; flex-shrink: 0; }
.panel-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.config-form { padding: 8px 0; }
.method-tabs {
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}

@media (max-width: 1100px) {
  .attack-page { flex-direction: column; height: auto; }
  .attack-right { width: 100%; }
}
</style>
