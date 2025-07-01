import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

const app = createApp(App)

// 配置Axios默认基础URL
axios.defaults.baseURL = 'http://localhost:8000'
app.config.globalProperties.$http = axios

app.use(router)
app.mount('#app')