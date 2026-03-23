import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '仪表盘', icon: 'Monitor' } },
    { path: '/attack', name: 'AttackTest', component: () => import('../views/AttackTest.vue'), meta: { title: '攻击测试', icon: 'Aim' } },
    { path: '/webscan', name: 'WebScan', component: () => import('../views/WebScan.vue'), meta: { title: '网站扫描', icon: 'Search' } },
    { path: '/reports', name: 'Reports', component: () => import('../views/Reports.vue'), meta: { title: '报告中心', icon: 'Document' } },
    { path: '/models', name: 'Models', component: () => import('../views/Models.vue'), meta: { title: '模型管理', icon: 'Connection' } },
    { path: '/datasets', name: 'Datasets', component: () => import('../views/Datasets.vue'), meta: { title: '数据集', icon: 'Files' } },
    { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { title: '系统设置', icon: 'Setting' } },
  ],
})

export default router
