<script setup lang="ts">
import { ref } from 'vue'
import { useWebScanStore } from '../stores/webscan'
import ModelSelector from '../components/ModelSelector.vue'
import { ElMessage } from 'element-plus'

const webScanStore = useWebScanStore()
// modelsStore loaded by ModelSelector internally

const activeTab = ref('crawl')

// Crawl
const crawlUrl = ref('')
const crawlDepth = ref(2)
const crawlResults = ref<any[]>([])

// Security
const secUrl = ref('')
const secChecks = ref<string[]>(['xss', 'sqli', 'csrf', 'headers', 'ssl'])
const secResults = ref<any[]>([])

// LLM Test
const llmUrl = ref('')
const llmModel = ref('')
const llmResults = ref<any[]>([])

const checkOptions = [
  { label: 'XSS 检测', value: 'xss' },
  { label: 'SQL 注入', value: 'sqli' },
  { label: 'CSRF 检测', value: 'csrf' },
  { label: 'HTTP 头部安全', value: 'headers' },
  { label: 'SSL/TLS 配置', value: 'ssl' },
  { label: '信息泄露', value: 'info_leak' },
  { label: '目录遍历', value: 'directory' },
  { label: '认证缺陷', value: 'auth' },
]

async function startCrawl() {
  if (!crawlUrl.value) return ElMessage.warning('请输入URL')
  try {
    const data = await webScanStore.startCrawl(crawlUrl.value, crawlDepth.value)
    crawlResults.value = data.pages || []
    ElMessage.success('爬取完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '爬取失败')
  }
}

async function startSecScan() {
  if (!secUrl.value) return ElMessage.warning('请输入URL')
  if (!secChecks.value.length) return ElMessage.warning('请选择检查项')
  try {
    const data = await webScanStore.startSecurityScan(secUrl.value, secChecks.value)
    secResults.value = data.vulnerabilities || []
    ElMessage.success('扫描完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '扫描失败')
  }
}

async function startLLMTest() {
  if (!llmUrl.value) return ElMessage.warning('请输入URL')
  if (!llmModel.value) return ElMessage.warning('请选择模型')
  try {
    const data = await webScanStore.startLLMTest(llmUrl.value, llmModel.value)
    llmResults.value = data.results || []
    ElMessage.success('测试完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '测试失败')
  }
}

function severityClass(s: string) {
  return `severity-${s?.toLowerCase() || 'info'}`
}
</script>

<template>
  <div class="webscan-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- Crawl -->
      <el-tab-pane name="crawl" label="URL爬取">
        <el-form label-position="top">
          <el-form-item label="目标 URL">
            <el-input v-model="crawlUrl" placeholder="https://example.com" />
          </el-form-item>
          <el-form-item label="爬取深度">
            <el-input-number v-model="crawlDepth" :min="1" :max="5" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="startCrawl" :loading="webScanStore.loading">
              <el-icon><Search /></el-icon>开始爬取
            </el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="crawlResults.length" :data="crawlResults" stripe>
          <el-table-column prop="url" label="页面URL" />
          <el-table-column prop="status" label="状态码" width="100" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="content_type" label="类型" width="140" />
        </el-table>
      </el-tab-pane>

      <!-- Security -->
      <el-tab-pane name="security" label="安全扫描">
        <el-form label-position="top">
          <el-form-item label="目标 URL">
            <el-input v-model="secUrl" placeholder="https://example.com" />
          </el-form-item>
          <el-form-item label="检查项">
            <el-checkbox-group v-model="secChecks">
              <el-checkbox v-for="c in checkOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-checkbox-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="startSecScan" :loading="webScanStore.loading">
              <el-icon><Search /></el-icon>开始扫描
            </el-button>
          </el-form-item>
        </el-form>
        <div v-if="secResults.length" class="vuln-list">
          <div v-for="(v, i) in secResults" :key="i" class="vuln-card">
            <div class="vuln-header">
              <span :class="severityClass(v.severity)">{{ v.severity }}</span>
              <span class="vuln-type">{{ v.type }}</span>
            </div>
            <div class="vuln-title">{{ v.title }}</div>
            <div class="vuln-desc">{{ v.description }}</div>
            <div v-if="v.url" class="vuln-url">{{ v.url }}</div>
          </div>
        </div>
      </el-tab-pane>

      <!-- LLM Test -->
      <el-tab-pane name="llm_test" label="LLM交互测试">
        <el-form label-position="top">
          <el-form-item label="目标 URL">
            <el-input v-model="llmUrl" placeholder="含LLM交互的Web应用URL" />
          </el-form-item>
          <el-form-item label="测试模型">
            <ModelSelector v-model="llmModel" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="startLLMTest" :loading="webScanStore.loading">
              <el-icon><Aim /></el-icon>开始测试
            </el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="llmResults.length" :data="llmResults" stripe>
          <el-table-column prop="test_name" label="测试项" />
          <el-table-column prop="result" label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="row.result === 'pass' ? 'success' : 'danger'" size="small">
                {{ row.result === 'pass' ? '通过' : '风险' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.webscan-page :deep(.el-tabs) {
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}
.vuln-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.vuln-card {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
}
.vuln-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.vuln-type { font-weight: 600; font-size: 13px; }
.vuln-title { font-weight: 600; margin-bottom: 4px; }
.vuln-desc { color: var(--text-secondary); font-size: 13px; }
.vuln-url { color: var(--color-primary); font-size: 12px; margin-top: 6px; }
</style>
