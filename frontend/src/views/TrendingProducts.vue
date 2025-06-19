<template>
  <div class="trending-products">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>热门商品分析</span>
          <div class="header-controls">
            <el-select v-model="timePeriod" @change="fetchData" style="margin-right: 10px;">
              <el-option label="15分钟" value="15min" />
              <el-option label="1小时" value="1hour" />
              <el-option label="1天" value="1day" />
              <el-option label="1周" value="1week" />
              <el-option label="1月" value="1month" />
            </el-select>
            <el-button type="primary" @click="fetchData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="products" v-loading="loading" style="width: 100%">
        <el-table-column label="排名" width="80">
          <template #default="{ $index }">
            <el-tag :type="getRankType($index)">{{ $index + 1 }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="商品信息" min-width="350">
          <template #default="{ row }">
            <div class="product-info">
              <img :src="row.image_url" :alt="row.title" class="product-image" />
              <div class="product-details">
                <div class="product-title">{{ row.title }}</div>
                <div class="product-meta">
                  <el-tag size="small">{{ row.platform_name }}</el-tag>
                  <el-tag size="small" type="info">{{ row.category_name }}</el-tag>
                </div>
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

        <el-table-column label="评分" width="120">
          <template #default="{ row }">
            <el-rate :value="row.avg_rating" disabled show-score />
          </template>
        </el-table-column>

        <el-table-column label="热度评分" width="150">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.min(row.trending_score, 100)" 
              :color="getScoreColor(row.trending_score)"
              :show-text="true"
            />
          </template>
        </el-table-column>

        <el-table-column label="增长率" width="120">
          <template #default="{ row }">
            <span :class="getGrowthClass(row.growth_rate)">
              {{ row.growth_rate > 0 ? '+' : '' }}{{ row.growth_rate.toFixed(1) }}%
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="text" @click="viewProduct(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiService } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const products = ref([])
const timePeriod = ref('1day')

const fetchData = async () => {
  loading.value = true
  try {
    const data = await apiService.getTrendingProducts(timePeriod.value, 100)
    products.value = data
  } catch (error) {
    ElMessage.error('获取热门商品失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

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

const viewProduct = (product) => {
  if (product.product_url) {
    window.open(product.product_url, '_blank')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}

.product-info {
  display: flex;
  align-items: center;
}

.product-image {
  width: 60px;
  height: 60px;
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
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.product-meta {
  display: flex;
  gap: 8px;
}

.price-info {
  text-align: right;
}

.current-price {
  font-weight: bold;
  color: #F56C6C;
  font-size: 16px;
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
</style>