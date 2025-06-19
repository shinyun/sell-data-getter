<template>
  <div class="task-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button type="primary" @click="fetchJobs" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="jobs" v-loading="loading">
        <el-table-column label="任务ID" prop="id" width="200" />
        <el-table-column label="任务名称" prop="name" min-width="200" />
        <el-table-column label="下次执行时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.next_run_time) }}
          </template>
        </el-table-column>
        <el-table-column label="触发器" prop="trigger" min-width="200" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="runJob(row.id)">
              立即执行
            </el-button>
            <el-button type="warning" size="small" @click="pauseJob(row.id)">
              暂停
            </el-button>
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
import dayjs from 'dayjs'

const loading = ref(false)
const jobs = ref([])

const fetchJobs = async () => {
  loading.value = true
  try {
    const data = await apiService.getJobs()
    jobs.value = data
  } catch (error) {
    ElMessage.error('获取任务列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const runJob = async (jobId) => {
  try {
    await apiService.runJobNow(jobId)
    ElMessage.success('任务已开始执行')
  } catch (error) {
    ElMessage.error('执行任务失败: ' + error.message)
  }
}

const pauseJob = async (jobId) => {
  try {
    await apiService.pauseJob(jobId)
    ElMessage.success('任务已暂停')
    fetchJobs()
  } catch (error) {
    ElMessage.error('暂停任务失败: ' + error.message)
  }
}

const formatTime = (time) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '未设置'
}

onMounted(() => {
  fetchJobs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>