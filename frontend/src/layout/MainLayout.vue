<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="aside">
      <div class="logo" :class="{ collapsed: isCollapsed }">
        <div class="logo-mark">
          <HerbLeafIcon :size="20" />
        </div>
        <div v-if="!isCollapsed" class="logo-text">
          <h3>饮片复核系统</h3>
          <p>Traditional Chinese Medicine</p>
        </div>
      </div>
      <el-menu
        class="side-menu"
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><ModuleHerbIcon variant="dashboard" :size="16" /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('qrcodeGenerate')" index="/qrcode/generate">
          <el-icon><ModuleHerbIcon variant="qrcode" :size="16" /></el-icon>
          <span>二维码生成</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('qrcodeManage')" index="/qrcode/manage">
          <el-icon><ModuleHerbIcon variant="qrcode" :size="16" /></el-icon>
          <span>二维码管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('check')" index="/check">
          <el-icon><ModuleHerbIcon variant="check" :size="16" /></el-icon>
          <span>扫码复核</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('alert')" index="/alert">
          <el-icon><ModuleHerbIcon variant="alert" :size="16" /></el-icon>
          <span>错误提醒</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('basket')" index="/basket">
          <el-icon><ModuleHerbIcon variant="basket" :size="16" /></el-icon>
          <span>分筐管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('trace')" index="/trace">
          <el-icon><ModuleHerbIcon variant="trace" :size="16" /></el-icon>
          <span>溯源管理</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><ModuleHerbIcon variant="statistics" :size="16" /></el-icon>
          <span>工作量统计</span>
        </el-menu-item>
        <el-menu-item v-if="canAccessMenu('system')" index="/system">
          <el-icon><ModuleHerbIcon variant="system" :size="16" /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text @click="toggleSidebar">
            <el-icon size="20"><Fold /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute">{{ currentRoute.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import HerbLeafIcon from '@/components/icons/HerbLeafIcon.vue'
import ModuleHerbIcon from '@/components/icons/ModuleHerbIcon.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)
const userName = computed(() => userStore.userName || '用户')
const isCollapsed = ref(false)

const canAccessMenu = (menuKey) => userStore.canAccessMenu(menuKey)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
    return
  }
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      userStore.logout()
      router.push('/login')
    } catch {
      // 用户取消
    }
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background: transparent;
}

.aside {
  background: linear-gradient(180deg, #f9f7f2 0%, #f4f1e8 100%);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 72px;
  display: flex;
  flex-direction: row;
  gap: 10px;
  align-items: center;
  justify-content: flex-start;
  padding: 0 14px;
  border-bottom: 1px solid var(--el-border-color-light);
  background:
    linear-gradient(90deg, rgba(120, 146, 98, 0.08) 0%, transparent 70%),
    #f8f5ee;
}

.logo.collapsed {
  justify-content: center;
  padding: 0;
}

.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary-dark-2);
  background: rgba(120, 146, 98, 0.12);
  border: 1px solid rgba(120, 146, 98, 0.24);
}

.logo-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo h3 {
  color: var(--el-text-color-primary);
  margin: 0;
  font-size: 19px;
  font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
  letter-spacing: 1px;
}

.logo p {
  margin-top: 1px;
  font-size: 11px;
  color: #7a8473;
  letter-spacing: 0.4px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: rgba(251, 250, 247, 0.92);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;
  box-shadow: 0 4px 12px rgba(62, 74, 50, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid transparent;
}

.user-info:hover {
  background: rgba(120, 146, 98, 0.08);
  border-color: rgba(120, 146, 98, 0.2);
}

.main-content {
  background-color: transparent;
  padding: 18px;
  overflow-y: auto;
}

:deep(.side-menu.el-menu) {
  border-right: none;
  background: transparent;
  padding-top: 8px;
}

:deep(.side-menu .el-menu-item) {
  height: 46px;
  margin: 4px 10px;
  border-radius: 4px;
  color: #4e5649;
}

:deep(.side-menu .el-menu-item:hover) {
  background: rgba(120, 146, 98, 0.1);
  color: var(--el-color-primary-dark-2);
}

:deep(.side-menu .el-menu-item.is-active) {
  position: relative;
  background: rgba(120, 146, 98, 0.12);
  color: var(--el-color-primary-dark-2);
  font-weight: 600;
}

:deep(.side-menu .el-menu-item.is-active::before) {
  content: "";
  position: absolute;
  left: -10px;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: var(--el-color-primary);
}

:deep(.el-breadcrumb__inner a),
:deep(.el-breadcrumb__inner) {
  color: #5d6658;
}
</style>
