import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export interface AttackTask {
  id: string
  method: string
  target: string
  model: string
  status: 'pending' | 'running' | 'success' | 'failed'
  progress: number
  result?: any
  created_at: string
}

export const useAttackStore = defineStore('attack', () => {
  const currentTask = ref<AttackTask | null>(null)
  const history = ref<AttackTask[]>([])
  const methods = ref<any[]>([])
  const loading = ref(false)

  async function fetchMethods() {
    const { data } = await api.get('/attacks/methods')
    methods.value = data.methods || data
  }

  async function fetchHistory() {
    const { data } = await api.get('/attacks/history')
    history.value = data.tasks || data
  }

  async function runAttack(params: Record<string, any>) {
    loading.value = true
    try {
      const { data } = await api.post('/attacks/run', params)
      currentTask.value = data.task || data
      return data
    } finally {
      loading.value = false
    }
  }

  return { currentTask, history, methods, loading, fetchMethods, fetchHistory, runAttack }
})
