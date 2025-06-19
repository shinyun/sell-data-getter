import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import TrendingProducts from './views/TrendingProducts.vue'
import CategoryTrends from './views/CategoryTrends.vue'
import PriceAnalysis from './views/PriceAnalysis.vue'
import Recommendations from './views/Recommendations.vue'
import TaskManager from './views/TaskManager.vue'

// 路由配置
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, name: 'Dashboard', meta: { title: '仪表板' } },
  { path: '/trending', component: TrendingProducts, name: 'TrendingProducts', meta: { title: '热门商品' } },
  { path: '/categories', component: CategoryTrends, name: 'CategoryTrends', meta: { title: '分类趋势' } },
  { path: '/price-analysis', component: PriceAnalysis, name: 'PriceAnalysis', meta: { title: '价格分析' } },
  { path: '/recommendations', component: Recommendations, name: 'Recommendations', meta: { title: '选品推荐' } },
  { path: '/tasks', component: TaskManager, name: 'TaskManager', meta: { title: '任务管理' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 创建应用
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')