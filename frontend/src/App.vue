<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="sidebar">
      <div class="logo">
        <h2>电商数据分析</h2>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        
        <el-menu-item index="/trending">
          <el-icon><TrendCharts /></el-icon>
          <span>热门商品</span>
        </el-menu-item>
        
        <el-menu-item index="/categories">
          <el-icon><Grid /></el-icon>
          <span>分类趋势</span>
        </el-menu-item>
        
        <el-menu-item index="/price-analysis">
          <el-icon><LineChart /></el-icon>
          <span>价格分析</span>
        </el-menu-item>
        
        <el-menu-item index="/recommendations">
          <el-icon><Star /></el-icon>
          <span>选品推荐</span>
        </el-menu-item>
        
        <el-menu-item index="/tasks">
          <el-icon><Setting /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-content">
          <h3>{{ $route.meta.title || '电商热销数据分析系统' }}</h3>
          <div class="header-actions">
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主要内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const refreshData = () => {
  // 触发当前页面的数据刷新
  router.go(0)
  ElMessage.success('数据刷新中...')
}

onMounted(() => {
  console.log('电商数据分析系统已启动')
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow: hidden;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #434a50;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.sidebar-menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-content h3 {
  margin: 0;
  color: #303133;
}

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
}
</style>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.el-card {
  margin-bottom: 20px;
}

.el-table {
  margin-top: 20px;
}
</style>