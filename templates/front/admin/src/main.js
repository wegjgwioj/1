import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, {
  ElLoading,
  ElMessage,
  ElMessageBox,
  ElNotification,
} from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

import router from './router'
import App from './App.vue'

import 'element-plus/dist/index.css'
import 'animate.css'
import '@/style/index.scss'
import 'quill/dist/quill.snow.css'

import '@/utils/YyLocalSotrage'
import registerGlobalData from '@/utils/global'

window.ElLoading = ElLoading
window.ElMessage = ElMessage
window.ElMessageBox = ElMessageBox
window.ElNotification = ElNotification
window.echarts = echarts

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

registerGlobalData(app)

app.mount('#app')

export default app
