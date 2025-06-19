<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon size="40" color="#409EFF"><Goods /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ overview.total_products || 0 }}</div>
              <div class="stats-label">总商品数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon size="40" color="#67C23A"><Platform /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ overview.total_platforms || 0 }}</div>
              <div class="stats-label">监控平台</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon size="40" color="#E6A23C"><Grid /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ overview.total_categories || 0 }}</div>
              <div class="stats-label">商品分类</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon size="40" color="#F56C6C"><TrendCharts /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ trendingProducts.length || 0 }}</div>
              <div class="stats-label">热门商品</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card title="平台商品分布">
          <template #header>
            <span>平台商品分布</span>
          </template>
          <div ref="platformChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card title="分类热度排行">
          <template #header>
            <span>分类热度排行</span>
          </template>
          <div ref="categoryChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 热门商品表格 -->
    <el-card title="热门商品 TOP 10">
      <template #header>
        <div class="card-header">
          <span>热门商品 TOP 10</span>
          <el-button type="text" @click="$router.push('/trending')">查看更多</el-button>
        </div>
      </template>
      
      <el-table :data="trendingProducts.slice(0, 10)" v-loading="loading">
        <el-table-column label="排名" width="80">
          <template #default="{ $index }">
            <el-tag :type="getRankType($index)">{{ $index + 1 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="商品" min-width="300">
          <template #default="{ row }">
            <div class="product-info">
              <img :src="row.image_url" :alt="row.title" class="product-image" />
              <div class="product-details">
                <div class="product-title">{{ row.title }}</div>
                <div class="product-platform">{{ row.platform_name }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="价格" width="120">
          <template #default="{ row }">
            <div class="price-info">
              <div class="current-price">${{ row.current_price }}</div>
              <div v-if="row.original_price && row.original_price > row.current_price" 
                   class="original-price">${{ row.original_price }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="销量" prop="total_sales" width="100" />
        
        <el-table-column label="评分" width="100">
          <template #default="{ row }">
            <el-rate :value="row.avg_rating" disabled show-score />
          </template>
        </el-table-column>
        
        <el-table-column label="热度评分" width="120">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.trending_score, 100)" :color="getScoreColor(row.trending_score)" />
          </template>
        </el-table-column>
        
        <el-table-column label="增长率" width="120">
          <template #default="{ row }">
            <span :class="getGrowthClass(row.growth_rate)">
              {{ row.growth_rate > 0 ? '+' : '' }}{{ row.growth_rate.toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 最近更新商品 -->
    <el-card title="最近更新商品">
      <template #header>
        <span>最近更新商品</span>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="product in overview.recent_products"
          :key="product.id"
          :timestamp="formatTime(product.last_updated)"
        >
          <div class="timeline-item">
            <strong>{{ product.title }}</strong>
            <span class="price">${{ product.current_price }}</span>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { apiService } from '@/api'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

// 响应式数据
const loading = ref(false)
const overview = ref({})
const trendingProducts = ref([])
const marketInsights = ref({})

// 图表引用
const platformChart = ref(null)
const categoryChart = ref(null)

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // 并行获取数据
    const [overviewData, trendingData, insightsData] = await Promise.all([
      apiService.getStatsOverview(),
      apiService.getTrendingProducts('1day', 10),
      apiService.getMarketInsights('1week')
    ])
    
    overview.value = overviewData
    trendingProducts.value = trendingData
    marketInsights.value = insightsData
    
    // 渲染图表
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 渲染图表
const renderCharts = () => {
  renderPlatformChart()
  renderCategoryChart()
}

// 渲染平台分布图表
const renderPlatformChart = () => {
  if (!platformChart.value || !marketInsights.value.platform_ranking) return
  
  const chart = echarts.init(platformChart.value)
  const data = marketInsights.value.platform_ranking.map(item => ({
    name: item.platform_name,
    value: item.product_count
  }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '商品数量',
        type: 'pie',
        radius: '50%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 渲染分类热度图表
const renderCategoryChart = () => {
  if (!categoryChart.value || !marketInsights.value.category_ranking) return
  
  const chart = echarts.init(categoryChart.value)
  const data = marketInsights.value.category_ranking.slice(0, 8)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.category_name)
    },
    series: [
      {
        name: '商品数量',
        type: 'bar',
        data: data.map(item => item.product_count),
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 工具函数
const getRankType = (index) => {
  if (index === 0) return 'danger'
  if (index === 1) return 'warning'
  if (index === 2) return 'success'
  return 'info'
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getGrowthClass = (growth) => {
  if (growth > 0) return 'growth-positive'
  if (growth < 0) return 'growth-negative'
  return 'growth-neutral'
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}

// 生命周期
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  height: 120px;
}

.stats-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stats-icon {
  margin-right: 20px;
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-info {
  display: flex;
  align-items: center;
}

.product-image {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
  margin-right: 12px;
}

.product-details {
  flex: 1;
}

.product-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.product-platform {
  font-size: 12px;
  color: #909399;
}

.price-info {
  text-align: right;
}

.current-price {
  font-weight: bold;
  color: #F56C6C;
}

.original-price {
  font-size: 12px;
  color: #909399;
  text-decoration: line-through;
}

.growth-positive {
  color: #67C23A;
  font-weight: bold;
}

.growth-negative {
  color: #F56C6C;
  font-weight: bold;
}

.growth-neutral {
  color: #909399;
}

.timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-item .price {
  color: #F56C6C;
  font-weight: bold;
}
</style>