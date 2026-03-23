import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export interface ModelInfo {
  id: string
  name: string
  provider: string
  status: 'connected' | 'unconfigured' | 'error'
  config?: Record<string, any>
}

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelInfo[]>([])
  const loading = ref(false)

  async function fetchModels() {
    loading.value = true
    try {
      const { data } = await api.get('/models')
      models.value = data.models || data
    } finally {
      loading.value = false
    }
  }

  async function testConnection(modelId: string) {
    const { data } = await api.post(`/models/${modelId}/test`)
    return data
  }

  async function updateConfig(modelId: string, config: Record<string, any>) {
    const { data } = await api.put(`/models/${modelId}/config`, config)
    return data
  }

  return { models, loading, fetchModels, testConnection, updateConfig }
})
