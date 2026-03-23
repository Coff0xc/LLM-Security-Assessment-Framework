<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { ElMessage } from 'element-plus'

const form = ref({
  api_key: '',
  default_model: '',
  max_concurrent: 5,
  timeout: 300,
  cors_origins: '*',
  auth_enabled: true,
  log_level: 'INFO',
  report_format: 'json',
})

const loading = ref(false)

onMounted(async () => {
  try {
    const { data } = await api.get('/settings')
    Object.assign(form.value, data)
  } catch { /* use defaults */ }
})

async function saveSettings() {
  loading.value = true
  try {
    await api.put('/settings', form.value)
    ElMessage.success('设置已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-card">
      <h3 style="margin-bottom: 20px">系统配置</h3>
      <el-form :model="form" label-position="top" style="max-width: 600px">
        <el-form-item label="全局 API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="用于保护API接口" />
        </el-form-item>
        <el-form-item label="默认模型">
          <el-input v-model="form.default_model" placeholder="默认测试模型ID" />
        </el-form-item>
        <el-form-item label="最大并发任务">
          <el-input-number v-model="form.max_concurrent" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="任务超时(秒)">
          <el-input-number v-model="form.timeout" :min="60" :max="3600" :step="60" />
        </el-form-item>
        <el-form-item label="CORS 允许来源">
          <el-input v-model="form.cors_origins" placeholder="*" />
        </el-form-item>
        <el-form-item label="启用认证">
          <el-switch v-model="form.auth_enabled" />
        </el-form-item>
        <el-form-item label="日志级别">
          <el-select v-model="form.log_level" style="width: 200px">
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告格式">
          <el-select v-model="form.report_format" style="width: 200px">
            <el-option label="JSON" value="json" />
            <el-option label="PDF" value="pdf" />
            <el-option label="CSV" value="csv" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="loading">保存设置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 24px;
}
</style>
