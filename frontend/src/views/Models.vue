<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useModelsStore, type ModelInfo } from '../stores/models'
import { ElMessage } from 'element-plus'

const store = useModelsStore()
const expandedModel = ref<string | null>(null)
const configForm = ref<Record<string, any>>({})
const testing = ref<string | null>(null)

const defaultModels: ModelInfo[] = [
  { id: 'openai', name: 'OpenAI GPT', provider: 'openai', status: 'unconfigured' },
  { id: 'anthropic', name: 'Anthropic Claude', provider: 'anthropic', status: 'unconfigured' },
  { id: 'google', name: 'Google Gemini', provider: 'google', status: 'unconfigured' },
  { id: 'mistral', name: 'Mistral AI', provider: 'mistral', status: 'unconfigured' },
  { id: 'cohere', name: 'Cohere', provider: 'cohere', status: 'unconfigured' },
  { id: 'zhipu', name: '智谱 GLM', provider: 'zhipu', status: 'unconfigured' },
  { id: 'baidu', name: '百度文心', provider: 'baidu', status: 'unconfigured' },
  { id: 'dashscope', name: '阿里通义', provider: 'dashscope', status: 'unconfigured' },
  { id: 'minimax', name: 'MiniMax', provider: 'minimax', status: 'unconfigured' },
  { id: 'moonshot', name: 'Moonshot', provider: 'moonshot', status: 'unconfigured' },
  { id: 'deepseek', name: 'DeepSeek', provider: 'deepseek', status: 'unconfigured' },
  { id: 'yi', name: '零一万物', provider: 'yi', status: 'unconfigured' },
  { id: 'stepfun', name: '阶跃星辰', provider: 'stepfun', status: 'unconfigured' },
  { id: 'sensetime', name: '商汤日日新', provider: 'sensetime', status: 'unconfigured' },
  { id: 'ollama', name: 'Ollama (本地)', provider: 'ollama', status: 'unconfigured' },
  { id: 'vllm', name: 'vLLM (本地)', provider: 'vllm', status: 'unconfigured' },
  { id: 'lmstudio', name: 'LM Studio', provider: 'lmstudio', status: 'unconfigured' },
  { id: 'huggingface', name: 'HuggingFace', provider: 'huggingface', status: 'unconfigured' },
]

onMounted(async () => {
  try {
    await store.fetchModels()
  } catch {
    store.models = defaultModels
  }
  if (!store.models.length) store.models = defaultModels
})

function toggleExpand(id: string) {
  if (expandedModel.value === id) {
    expandedModel.value = null
  } else {
    expandedModel.value = id
    const m = store.models.find(x => x.id === id)
    configForm.value = { api_key: '', base_url: '', ...m?.config }
  }
}

async function testConn(id: string) {
  testing.value = id
  try {
    await store.testConnection(id)
    ElMessage.success('连接成功')
  } catch {
    ElMessage.error('连接失败')
  } finally {
    testing.value = null
  }
}

async function saveConfig(id: string) {
  try {
    await store.updateConfig(id, configForm.value)
    ElMessage.success('配置已保存')
    expandedModel.value = null
    await store.fetchModels()
  } catch {
    ElMessage.error('保存失败')
  }
}

function statusTag(s: string) {
  if (s === 'connected') return { type: 'success' as const, text: '已连接' }
  if (s === 'error') return { type: 'danger' as const, text: '错误' }
  return { type: 'info' as const, text: '未配置' }
}
</script>

<template>
  <div class="models-page">
    <div class="model-grid">
      <div v-for="m in store.models" :key="m.id" class="model-card" :class="{ expanded: expandedModel === m.id }">
        <div class="card-header" @click="toggleExpand(m.id)">
          <div class="model-info">
            <div class="model-name">{{ m.name }}</div>
            <div class="model-provider">{{ m.provider }}</div>
          </div>
          <el-tag :type="statusTag(m.status).type" size="small" effect="dark">
            {{ statusTag(m.status).text }}
          </el-tag>
        </div>
        <div v-if="expandedModel === m.id" class="card-config">
          <el-form label-position="top" size="small">
            <el-form-item label="API Key">
              <el-input v-model="configForm.api_key" type="password" show-password placeholder="输入 API Key" />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="configForm.base_url" placeholder="自定义 API 地址 (可选)" />
            </el-form-item>
            <div class="config-actions">
              <el-button size="small" @click="testConn(m.id)" :loading="testing === m.id">测试连接</el-button>
              <el-button size="small" type="primary" @click="saveConfig(m.id)">保存配置</el-button>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.model-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.model-card:hover { border-color: var(--color-primary); }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  cursor: pointer;
}
.model-name { font-weight: 600; font-size: 14px; }
.model-provider { color: var(--text-secondary); font-size: 12px; margin-top: 2px; }
.card-config {
  padding: 0 16px 16px;
  border-top: 1px solid var(--border-color);
}
.config-actions { display: flex; gap: 8px; justify-content: flex-end; }
</style>
