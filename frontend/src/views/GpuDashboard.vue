<template>
  <div class="dashboard-container">
    <div class="header">
      <h1>GPU资源实时监控</h1>
      <div class="refresh-btn" @click="fetchGPUStatus">🔄 手动刷新</div>
    </div>
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>数据加载中...</p>
    </div>
    <div v-else class="content">
      <div class="stats-card">
        <h3>总GPU数量</h3>
        <p class="value">{{ gpuStatus.total }}</p>
      </div>
      <div class="stats-card">
        <h3>已使用GPU数量</h3>
        <p class="value">{{ gpuStatus.used }}</p>
      </div>
      <div class="stats-card">
        <h3>实时使用率</h3>
        <p class="value">{{ (gpuStatus.used / gpuStatus.total * 100).toFixed(2) }}%</p>
      </div>
      <div class="chart-container">
        <div ref="chartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const gpuStatus = ref({ total: 0, used: 0 })
const loading = ref(true)
const chartRef = ref(null)
let chartInstance = null

const fetchGPUStatus = async () => {
  try {
    loading.value = true
    const response = await axios.get('/gpu/status')
    let total = 0
    let used = 0
    
    // 处理后端返回的GPU状态数据
    Object.values(response.data).forEach(nodeData => {
      if (nodeData.success) {
        used += nodeData.data
        total += 4 // 假设每个节点有4个GPU
      }
    })
    
    gpuStatus.value = { total, used }
    updateChart()
  } catch (error) {
    console.error('获取GPU状态失败:', error)
  } finally {
    loading.value = false
  }
}

const updateChart = () => {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()
  
  chartInstance = echarts.init(chartRef.value)
  const option = {
    title: { text: 'GPU使用情况', left: 'center' },
    tooltip: {},
    legend: { top: 'bottom' },
    series: [{
      name: 'GPU',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: '20', fontWeight: 'bold' } },
      labelLine: { show: false },
      data: [
        { value: gpuStatus.value.used, name: '已使用' },
        { value: gpuStatus.value.total - gpuStatus.value.used, name: '空闲' }
      ]
    }]
  }
  chartInstance.setOption(option)
}

onMounted(() => {
  fetchGPUStatus()
  const timer = setInterval(fetchGPUStatus, 30000)
  onUnmounted(() => clearInterval(timer))
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px;
  font-family: 'Segoe UI', sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.refresh-btn {
  cursor: pointer;
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border-radius: 6px;
  transition: background 0.3s;
}

.refresh-btn:hover {
  background: #3a8ee6;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.content {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stats-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  text-align: center;
}

.stats-card h3 {
  color: #666;
  font-weight: 500;
  margin-bottom: 10px;
}

.stats-card .value {
  font-size: 2.5em;
  font-weight: bold;
  color: #2c3e50;
}

.chart-container {
  grid-column: 1 / -1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 20px;
  min-height: 400px;
}
</style>