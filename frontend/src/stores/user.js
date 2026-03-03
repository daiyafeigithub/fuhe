import { defineStore } from 'pinia'
import { login as loginApi } from '@/api'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.userInfo.userName || '',
    userRole: (state) => state.userInfo.roleName || ''
  },

  actions: {
    async login(userAccount, userPwd) {
      try {
        const res = await loginApi({ userAccount, userPwd })
        if (res.code === '0000') {
          this.token = res.data.token
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
    }
  }
})
