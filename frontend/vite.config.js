import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 开发时代理 API 请求，避免跨域
      '/api': {
        target: 'http://agent-core:8000',
        changeOrigin: true,
      }
    }
  }
})