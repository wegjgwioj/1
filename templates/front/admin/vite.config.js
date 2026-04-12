import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { apiBaseUrl } from './src/utils/base'

function createVendorChunkName(prefix, id, marker) {
  const relativePath = id.split(marker)[1] || ''
  const pathSegments = relativePath.split('/').filter(Boolean)
  const groupSegments =
    pathSegments[0] === 'es' || pathSegments[0] === 'lib'
      ? pathSegments.slice(0, 2)
      : pathSegments.slice(0, 1)
  const safeGroup = (groupSegments.join('-') || 'core').replace(/[^a-zA-Z0-9_-]/g, '-')
  return `${prefix}-${safeGroup}`
}

export default defineConfig({
  plugins: [
    vue(),
  ],

  resolve: {
    //设置路径别名
    alias: {
      "@": resolve(__dirname, "src/")
    },
  },

  server: {

    // 服务器默认端口是8080，前端默认8081，所以需要代理
    port: 8081,
    host: "0.0.0.0",

    // 自动打开浏览器
    open: false, 

    // 设置代理
    proxy: {
      "/diandong5k56la1f": {
        target: apiBaseUrl,
        changeOrigin: true,
      },
    },
  },

  // 打包后的文件引入路径 由/assets，改为./assets
  base: "",
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 1100,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }

          if (
            id.includes('/vue/') ||
            id.includes('/vue-router/') ||
            id.includes('/pinia/')
          ) {
            return 'vendor-vue'
          }

          if (id.includes('/element-plus/')) {
            return createVendorChunkName('vendor-element-plus', id, '/element-plus/')
          }

          if (id.includes('/echarts') || id.includes('echarts-wordcloud')) {
            if (id.includes('/echarts/')) {
              return createVendorChunkName('vendor-echarts', id, '/echarts/')
            }
            return 'vendor-echarts-wordcloud'
          }

          if (id.includes('/xlsx/')) {
            return 'vendor-xlsx'
          }

          if (id.includes('/quill/')) {
            return 'vendor-editor'
          }

          return 'vendor-misc'
        },
      },
    },
  },
})
