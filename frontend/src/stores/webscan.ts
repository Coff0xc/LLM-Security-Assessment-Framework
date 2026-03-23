import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export interface ScanResult {
  id: string
  url: string
  type: 'crawl' | 'security' | 'llm_test'
  status: 'running' | 'completed' | 'failed'
  results?: any
  created_at: string
}

export const useWebScanStore = defineStore('webscan', () => {
  const currentScan = ref<ScanResult | null>(null)
  const scanHistory = ref<ScanResult[]>([])
  const loading = ref(false)

  async function startCrawl(url: string, depth: number) {
    loading.value = true
    try {
      const { data } = await api.post('/webscan/crawl', { url, depth })
      currentScan.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function startSecurityScan(url: string, checks: string[]) {
    loading.value = true
    try {
      const { data } = await api.post('/webscan/security', { url, checks })
      currentScan.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function startLLMTest(url: string, model: string) {
    loading.value = true
    try {
      const { data } = await api.post('/webscan/llm-test', { url, model })
      currentScan.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return { currentScan, scanHistory, loading, startCrawl, startSecurityScan, startLLMTest }
})
