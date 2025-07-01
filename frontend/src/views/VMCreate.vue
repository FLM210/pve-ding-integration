<template>
  <div class="vm-create-container">
    <h1>创建虚拟机</h1>
    <form @submit.prevent="createVM">
      <div class="form-group">
        <label for="vm-name">虚拟机名称</label>
        <input type="text" id="vm-name" v-model="vmName" required>
      </div>
      <div class="form-group">
        <label for="cpu-cores">CPU核心数</label>
        <input type="number" id="cpu-cores" v-model="cpuCores" min="1" max="16" required>
      </div>
      <div class="form-group">
        <label for="memory-size">内存大小 (GB)</label>
        <input type="number" id="memory-size" v-model="memorySize" min="1" max="128" required>
      </div>
      <div class="form-group">
        <label for="disk-size">磁盘大小 (GB)</label>
        <input type="number" id="disk-size" v-model="diskSize" min="10" max="1024" required>
      </div>
      <button type="submit" class="btn-primary">创建虚拟机</button>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      vmName: '',
      cpuCores: 2,
      memorySize: 4,
      diskSize: 20
    };
  },
  methods: {
    async createVM() {
      try {
        const response = await axios.post('/api/vm/create', {
          name: this.vmName,
          cpu: this.cpuCores,
          memory: this.memorySize,
          disk: this.diskSize
        });
        if (response.data.success) {
          this.$router.push('/history');
          this.$notify({
            title: '成功',
            message: '虚拟机创建请求已提交',
            type: 'success'
          });
        }
      } catch (error) {
        console.error('创建虚拟机失败:', error);
        this.$notify({
          title: '错误',
          message: '虚拟机创建失败: ' + error.message,
          type: 'error'
        });
      }
    }
  }
};
</script>

<style scoped>
.vm-create-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-primary {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #359469;
}
</style>