<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const menuItems = [
  { path: '/', icon: 'Monitor', label: '仪表盘' },
  { path: '/attack', icon: 'Aim', label: '攻击测试' },
  { path: '/webscan', icon: 'Search', label: '网站扫描' },
  { path: '/reports', icon: 'Document', label: '报告中心' },
  { path: '/models', icon: 'Connection', label: '模型管理' },
  { path: '/datasets', icon: 'Files', label: '数据集' },
  { path: '/settings', icon: 'Setting', label: '系统设置' },
]

const currentPath = computed(() => route.path)
</script>

<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed }">
      <div class="sidebar-header">
        <div class="logo" v-show="!collapsed">
          <span class="logo-icon">&#9876;</span>
          <span class="logo-text">FORGEDAN</span>
        </div>
        <el-button
          text
          @click="collapsed = !collapsed"
          class="collapse-btn"
        >
          <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
        </el-button>
      </div>
      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
          @click="router.push(item.path)"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span v-show="!collapsed" class="nav-label">{{ item.label }}</span>
        </div>
      </nav>
      <div class="sidebar-footer" v-show="!collapsed">
        <span class="version">v1.0.0</span>
      </div>
    </aside>

    <!-- Main -->
    <div class="main-area">
      <header class="top-bar">
        <div class="page-title">{{ route.meta.title || 'FORGEDAN' }}</div>
        <div class="top-actions">
          <el-tag type="success" size="small" effect="dark">系统正常</el-tag>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  flex-shrink: 0;
}
.sidebar.collapsed { width: 60px; }

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-icon { font-size: 22px; color: var(--color-primary); }
.logo-text {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--color-primary), #a371f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
}

.collapse-btn { color: var(--text-secondary) !important; }

.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.15s;
  margin-bottom: 2px;
}
.nav-item:hover {
  background: var(--bg-input);
  color: var(--text-primary);
}
.nav-item.active {
  background: rgba(88,166,255,0.12);
  color: var(--color-primary);
}
.nav-label { font-size: 14px; white-space: nowrap; }

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
}
.version { color: var(--text-secondary); font-size: 12px; }

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: 48px;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}
.page-title { font-size: 15px; font-weight: 600; }

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
