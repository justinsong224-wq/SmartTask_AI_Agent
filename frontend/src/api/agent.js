/**
 * Agent API 封装
 * 统一管理所有与后端的通信
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,  // Agent 执行可能较慢，设置2分钟超时
})

export const agentApi = {
  // ── Agent 执行 ──────────────────────────────────
  runTask(task, sessionId = 'default') {
    return http.post('/api/agent/run', {
      task,
      session_id: sessionId,
    })
  },

  // ── 长期记忆 ────────────────────────────────────
  getLongTermMemory(limit = 20, offset = 0) {
    return http.get('/api/memory/long-term', { params: { limit, offset } })
  },

  clearLongTermMemory() {
    return http.delete('/api/memory/long-term')
  },

  getMemoryStats() {
    return http.get('/api/memory/long-term/stats')
  },

  // ── 短期记忆 ────────────────────────────────────
  getShortTermMemory(sessionId) {
    return http.get(`/api/memory/short-term/${sessionId}`)
  },

  clearShortTermMemory(sessionId) {
    return http.delete(`/api/memory/short-term/${sessionId}`)
  },

  // ── 健康检查 ────────────────────────────────────
  healthCheck() {
    return http.get('/health')
  },
}