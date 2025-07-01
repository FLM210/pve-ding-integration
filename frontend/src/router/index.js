import { createRouter, createWebHistory } from 'vue-router'
import GpuDashboard from '../views/GpuDashboard.vue'
import VMCreate from '../views/VMCreate.vue'
import VmHistory from '../views/History.vue'
import SystemSettings from '../views/Settings.vue'

const routes = [
  { path: '/', name: 'GpuDashboard', component: GpuDashboard },
  { path: '/create', name: 'VMCreate', component: VMCreate },
  { path: '/history', name: 'VmHistory', component: VmHistory },
  { path: '/settings', name: 'SystemSettings', component: SystemSettings }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router