import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'vue-vendor',
              test: /node_modules[\\/](vue|vue-router|pinia)[\\/]/,
              priority: 30,
            },
            {
              name: 'element-plus',
              test: /node_modules[\\/](@element-plus|element-plus)[\\/]/,
              priority: 20,
            },
            {
              name: 'vue-echarts',
              test: /node_modules[\\/]vue-echarts[\\/]/,
              priority: 25,
            },
            {
              name: 'zrender',
              test: /node_modules[\\/]zrender[\\/]/,
              priority: 24,
            },
            {
              name: 'echarts',
              test: /node_modules[\\/]echarts[\\/]/,
              priority: 20,
            },
            {
              name: 'vendor',
              test: /node_modules[\\/]/,
              priority: 1,
            },
          ],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
    },
  },
})
