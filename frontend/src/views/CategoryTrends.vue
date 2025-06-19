<template>
  <div class="category-trends">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>分类趋势分析</span>
          <el-button type="primary" @click="fetchData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </template>

      <el-table :data="trends" v-loading="loading">
        <el-table-column label="分类" prop="category_name" width="150" />
        <el-table-column label="平台" prop="platform_name" width="120" />
        <el-table-column label="商品数量" prop="product_count" width="120" />
        <el-table-column label="总销量" prop="total_sales" width="120" />
        <el-table-column label="平均价格" width="120">
          <template #default="{ row }">
            ${{ row.avg_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="平均评分" width="120">
          <template #default="{ row }">
            <el-rate :value="row.avg_rating" disabled show-score />
          </template>
        </el-table-column>
        <el-table-column label="热度评分" width="150">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.heat_score, 100)" />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiService } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const trends = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const data = await apiService.getCategoryTrends('1day')
    trends.value = data
  } catch (error) {
    ElMessage.error('获取分类趋势失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const getGrowthClass = (growth) => {
  if (growth > 0) return 'growth-positive'
  if (growth < 0) return 'growth-negative'
  return 'growth-neutral'
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