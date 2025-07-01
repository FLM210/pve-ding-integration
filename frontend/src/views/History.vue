<template>
  <div class="history-container">
    <h1>虚拟机创建历史</h1>
    <div class="history-list">
      <div v-if="history.length === 0" class="empty-state">暂无历史记录</div>
      <div v-else class="history-items">
        <div v-for="item in history" :key="item.id" class="history-item">
          <p><strong>名称:</strong> {{ item.name }}</p>
          <p><strong>创建时间:</strong> {{ item.timestamp }}</p>
          <p><strong>状态:</strong> <span :class="{'status-success': item.status === 'success', 'status-failed': item.status === 'failed'}"></span></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'VmHistory',
  data() {
    return {
      history: []
    };
  },
  mounted() {
    this.fetchHistory();
  },
  methods: {
    async fetchHistory() {
      try {
        const response = await axios.get('/api/vm/history');
        this.history = response.data;
      } catch (error) {
        console.error('获取历史记录失败:', error);
      }
    }
  }
};
</script>

<style scoped>
.history-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.history-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.status-success {
  color: #10b981;
}

.status-failed {
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>