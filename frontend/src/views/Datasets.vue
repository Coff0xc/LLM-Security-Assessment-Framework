<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { ElMessage } from 'element-plus'

const datasets = ref<any[]>([])
const loading = ref(false)
const previewVisible = ref(false)
const previewData = ref<any[]>([])
const previewTitle = ref('')

onMounted(fetchDatasets)

async function fetchDatasets() {
  loading.value = true
  try {
    const { data } = await api.get('/datasets')
    datasets.value = data.datasets || data || []
  } catch { /* empty */ } finally {
    loading.value = false
  }
}

async function previewDataset(ds: any) {
  previewTitle.value = ds.name
  try {
    const { data } = await api.get(`/datasets/${ds.id}/preview`)
    previewData.value = data.samples || data || []
    previewVisible.value = true
  } catch {
    ElMessage.error('预览失败')
  }
}

async function handleUpload(options: any) {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    await api.post('/datasets/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('上传成功')
    await fetchDatasets()
  } catch {
    ElMessage.error('上传失败')
  }
}
</script>

<template>
  <div class="datasets-page">
    <div class="toolbar">
      <el-upload :http-request="handleUpload" :show-file-list="false" accept=".json,.csv,.jsonl">
        <el-button type="primary"><el-icon><Upload /></el-icon>上传数据集</el-button>
      </el-upload>
    </div>

    <el-table :data="datasets" stripe v-loading="loading" style="margin-top: 16px">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="samples_count" label="样本数" width="100" />
      <el-table-column prop="category" label="类别" width="140" />
      <el-table-column prop="source" label="来源" width="140" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="previewDataset(row)">预览</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="previewVisible" :title="`数据集预览: ${previewTitle}`" width="700px">
      <el-table :data="previewData" max-height="400">
        <el-table-column prop="prompt" label="提示词" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="120" />
        <el-table-column prop="label" label="标签" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 12px; }
</style>
