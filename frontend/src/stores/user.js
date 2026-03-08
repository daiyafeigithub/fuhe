import { defineStore } from 'pinia'
import { login as loginApi } from '@/api'
import { ElMessage } from 'element-plus'

const REVIEW_MODULE_KEYS = ['check', 'alert', 'basket', 'trace']

const buildMenuPermissionMap = (roleName = '') => {
  const normalizedRole = String(roleName || '').trim()
  const isAdminRole = ['超级管理员', '系统管理员'].includes(normalizedRole)

  const permission = {
    dashboard: true,
    qrcodeGenerate: true,
    qrcodeManage: true,
    check: false,
    alert: false,
    basket: false,
    trace: false,
    statistics: true,
    profile: true,
    system: true
  }

  if (isAdminRole) {
    REVIEW_MODULE_KEYS.forEach((key) => {
      permission[key] = true
    })
  }

  return permission
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.userInfo.userName || '',
    userRole: (state) => state.userInfo.roleName || '',
    menuPermissions: (state) => buildMenuPermissionMap(state.userInfo.roleName),
    canAccessMenu: (state) => {
      const permissionMap = buildMenuPermissionMap(state.userInfo.roleName)
      return (menuKey) => {
        if (!menuKey) return true
        return permissionMap[menuKey] !== false
      }
    }
  },

  actions: {
    async login(userAccount, userPwd) {
      try {
        const res = await loginApi({ userAccount, userPwd })
        if (res.code === '0000') {
          const rawToken = res.data.token || ''
          this.token = rawToken.replace(/^Bearer\s+/i, '')
          this.userInfo = res.data.userInfo
          localStorage.setItem('token', this.token)
          localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
          return true
        } else {
          ElMessage.error(res.msg || '登录失败')
          return false
        }
      } catch (error) {
        ElMessage.error('登录失败：' + error.message)
        return false
      }
    },

    logout() {
      this.token = ''
      this.userInfo = {}
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    },

    setUserInfo(userInfo) {
      this.userInfo = userInfo || {}
      localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
    }
  }
})
