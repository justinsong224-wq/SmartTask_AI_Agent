import axios from 'axios'

// 生产环境从环境变量读取后端地址
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
})

export const agentApi = {
  runTask(task, sessionId = 'default') {
    return http.post('/api/agent/run', { task, session_id: sessionId })
  },
  getLongTermMemory(limit = 20, offset = 0) {
    return http.get('/api/memory/long-term', { params: { limit, offset } })
  },
  clearLongTermMemory() {
    return http.delete('/api/memory/long-term')
  },
  getMemoryStats() {
    return http.get('/api/memory/long-term/stats')
  },
  getShortTermMemory(sessionId) {
    return http.get(`/api/memory/short-term/${sessionId}`)
  },
  clearShortTermMemory(sessionId) {
    return http.delete(`/api/memory/short-term/${sessionId}`)
  },
  healthCheck() {
    return http.get('/health')
  },
}