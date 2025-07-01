<template>
  <div class="settings-container">
    <h1>系统设置</h1>
    <div class="settings-section">
      <h2>钉钉集成设置</h2>
      <div class="form-group">
        <label for="dingtalk-app-key">钉钉应用AppKey</label>
        <input type="text" id="dingtalk-app-key" v-model="dingtalkAppKey" placeholder="输入钉钉应用AppKey">
      </div>
      <div class="form-group">
        <label for="dingtalk-app-secret">钉钉应用AppSecret</label>
        <input type="password" id="dingtalk-app-secret" v-model="dingtalkAppSecret" placeholder="输入钉钉应用AppSecret">
      </div>
      <button @click="saveSettings" class="btn-primary">保存设置</button>
    </div>

    <div class="settings-section">
      <h2>PVE连接设置</h2>
      <div class="form-group">
        <label for="pve-host">PVE主机地址</label>
        <input type="text" id="pve-host" v-model="pveHost" placeholder="例如: https://pve.example.com:8006">
      </div>
      <div class="form-group">
        <label for="pve-username">PVE用户名</label>
        <input type="text" id="pve-username" v-model="pveUsername" placeholder="PVE登录用户名">
      </div>
      <div class="form-group">
        <label for="pve-password">PVE密码</label>
        <input type="password" id="pve-password" v-model="pvePassword" placeholder="PVE登录密码">
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'SystemSettings',
  data() {
    return {
      dingtalkAppKey: '',
      dingtalkAppSecret: '',
      pveHost: '',
      pveUsername: '',
      pvePassword: ''
    };
  },
  mounted() {
    // 加载保存的设置
    this.loadSettings();
  },
  methods: {
    async loadSettings() {
      try {
        const response = await axios.get('/api/settings');
        this.dingtalkAppKey = response.data.dingtalk_app_key || '';
        this.dingtalkAppSecret = response.data.dingtalk_app_secret || '';
        this.pveHost = response.data.pve_host || '';
        this.pveUsername = response.data.pve_username || '';
        this.pvePassword = response.data.pve_password || '';
      } catch (error) {
        console.error('加载设置失败:', error);
      }
    },
    async saveSettings() {
      try {
        await axios.post('/api/settings', {
          dingtalk_app_key: this.dingtalkAppKey,
          dingtalk_app_secret: this.dingtalkAppSecret,
          pve_host: this.pveHost,
          pve_username: this.pveUsername,
          pve_password: this.pvePassword
        });
        this.$notify({
          title: '成功',
          message: '设置已保存',
          type: 'success'
        });
      } catch (error) {
        console.error('保存设置失败:', error);
        this.$notify({
          title: '错误',
          message: '保存设置失败: ' + error.message,
          type: 'error'
        });
      }
    }
  }
};
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-section {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
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