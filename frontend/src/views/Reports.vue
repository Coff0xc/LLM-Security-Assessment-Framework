<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { ElMessage } from 'element-plus'

const reports = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const detailVisible = ref(false)
const compareVisible = ref(false)
const selectedReport = ref<any>(null)
const compareReports = ref<any[]>([])

onMounted(fetchReports)

async function fetchReports() {
  loading.value = true
  try {
    const { data } = await api.get('/reports', { params: { q: searchQuery.value, page: currentPage.value, size: pageSize.value } })
    reports.value = data.reports || data || []
  } catch { /* empty */ } finally {
    loading.value = false
  }
}

function viewDetail(row: any) {
  selectedReport.value = row
  detailVisible.value = true
}

function handleCompare() {
  if (compareReports.value.length !== 2) return ElMessage.warning('请选择两份报告')
  compareVisible.value = true
}

function handleSelectionChange(rows: any[]) {
  compareReports.value = rows.slice(0, 2)
}

async function exportReport(id: string, format: string) {
  try {
    const res = await api.get(`/reports/${id}/export`, { params: { format }, responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${id}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}
</script>

<template>
  <div class="reports-page">
    <div class="toolbar">
      <el-input v-model="searchQuery" placeholder="搜索报告..." style="width: 300px" @keyup.enter="fetchReports" clearable>
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button @click="handleCompare" :disabled="compareReports.length !== 2">
        <el-icon><Switch /></el-icon>对比报告
      </el-button>
    </div>

    <el-table :data="reports" stripe v-loading="loading" @selection-change="handleSelectionChange" style="margin-top: 16px">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="报告ID" width="200" />
      <el-table-column prop="method" label="攻击方法" width="120" />
      <el-table-column prop="model" label="目标模型" width="160" />
      <el-table-column prop="asr" label="ASR" width="80">
        <template #default="{ row }">{{ (row.asr * 100).toFixed(1) }}%</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" sortable />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="viewDetail(row)">详情</el-button>
          <el-button text size="small" @click="exportReport(row.id, 'pdf')">PDF</el-button>
          <el-button text size="small" @click="exportReport(row.id, 'csv')">CSV</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="reports.length"
      layout="prev, pager, next"
      style="margin-top: 16px; justify-content: center"
      @current-change="fetchReports"
    />

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="报告详情" width="700px">
      <template v-if="selectedReport">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="报告ID">{{ selectedReport.id }}</el-descriptions-item>
          <el-descriptions-item label="攻击方法">{{ selectedReport.method }}</el-descriptions-item>
          <el-descriptions-item label="目标模型">{{ selectedReport.model }}</el-descriptions-item>
          <el-descriptions-item label="ASR">{{ ((selectedReport.asr || 0) * 100).toFixed(1) }}%</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ selectedReport.created_at }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedReport.summary" style="margin-top: 16px">
          <h4>摘要</h4>
          <p style="color: var(--text-secondary); font-size: 13px; white-space: pre-wrap;">{{ selectedReport.summary }}</p>
        </div>
      </template>
    </el-dialog>

    <!-- Compare Dialog -->
    <el-dialog v-model="compareVisible" title="报告对比" width="900px">
      <div v-if="compareReports.length === 2" style="display: flex; gap: 16px">
        <div v-for="r in compareReports" :key="r.id" style="flex: 1">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="ID">{{ r.id }}</el-descriptions-item>
            <el-descriptions-item label="方法">{{ r.method }}</el-descriptions-item>
            <el-descriptions-item label="模型">{{ r.model }}</el-descriptions-item>
            <el-descriptions-item label="ASR">{{ ((r.asr || 0) * 100).toFixed(1) }}%</el-descriptions-item>
            <el-descriptions-item label="时间">{{ r.created_at }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 12px; }
</style>
