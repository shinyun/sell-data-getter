import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// API方法
export const apiService = {
  // 获取热门商品
  getTrendingProducts(timePeriod = '1day', limit = 50) {
    return api.get('/trending-products', {
      params: { time_period: timePeriod, limit }
    })
  },

  // 获取分类趋势
  getCategoryTrends(timePeriod = '1day') {
    return api.get('/category-trends', {
      params: { time_period: timePeriod }
    })
  },

  // 获取价格趋势
  getPriceTrends(productId, days = 30) {
    return api.get(`/price-trends/${productId}`, {
      params: { days }
    })
  },

  // 获取商品推荐
  getRecommendations(params = {}) {
    return api.get('/recommendations', { params })
  },

  // 获取市场洞察
  getMarketInsights(timePeriod = '1week') {
    return api.get('/market-insights', {
      params: { time_period: timePeriod }
    })
  },

  // 获取平台列表
  getPlatforms() {
    return api.get('/platforms')
  },

  // 获取分类列表
  getCategories() {
    return api.get('/categories')
  },

  // 获取商品列表
  getProducts(params = {}) {
    return api.get('/products', { params })
  },

  // 获取任务列表
  getJobs() {
    return api.get('/jobs')
  },

  // 立即执行任务
  runJobNow(jobId) {
    return api.post(`/jobs/${jobId}/run`)
  },

  // 暂停任务
  pauseJob(jobId) {
    return api.post(`/jobs/${jobId}/pause`)
  },

  // 恢复任务
  resumeJob(jobId) {
    return api.post(`/jobs/${jobId}/resume`)
  },

  // 获取统计概览
  getStatsOverview() {
    return api.get('/stats/overview')
  },

  // 健康检查
  healthCheck() {
    return api.get('/health')
  }
}

export default api