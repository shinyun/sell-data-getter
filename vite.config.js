import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: 'frontend',
  build: {
    outDir: '../static',
    emptyOutDir: true
  },
  server: {
    host: '0.0.0.0',
    port: 12001,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:12000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'frontend/src')
    }
  }
})