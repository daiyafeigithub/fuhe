import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { transformRequest, transformResponse } from '@/utils/apiMapper'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/zyfh/api/v1'

const instance = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = token.startsWith('Bearer ') ? token : `Bearer ${token}`
    }

    if (config.params) {
      config.params = transformRequest(config.params)
    }

    if (config.data && typeof config.data === 'object') {
      config.data = transformRequest(config.data)
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    return transformResponse(response.data)
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      const data = transformResponse(error.response.data || {})
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('无权限访问')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status === 500) {
        ElMessage.error('服务器错误')
      } else {
        ElMessage.error(data.msg || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export const api = instance

export const login = (data) => api.post('/system/token/get', {
  user_account: data.userAccount,
  user_pwd: data.userPwd
})
export const getUserList = (params) => api.get('/sys/user/list', { params })
export const saveUser = (data) => api.post('/sys/user/save', data)
export const deleteUser = (params) => api.delete('/sys/user/delete', { params })
export const getRoleList = () => api.get('/sys/role/list')
export const saveRole = (data) => api.post('/sys/role/save', data)
export const deleteRole = (params) => api.delete('/sys/role/delete', { params })

export const generateQRCode = (data) => api.post('/qrcode/generate/single', {
  enterprise_code: data.enterpriseCode,
  cj_id: data.cjId,
  spec: data.spec,
  batch_no: data.batchNo,
  num: data.num,
  weight: data.weight
})
export const generateBatchQRCode = (data) => api.post('/qrcode/generate/batch', data)
export const verifyQRCode = (data) => api.post('/qrcode/verify', data)
export const getQRCodeHistory = (params) => api.get('/qrcode/record/query', { params })

export const initCheck = (data) => api.post('/check/init', data)
export const scanCheck = (data) => api.post('/check/scan', data)
export const saveProgress = (data) => api.post('/check/progress/save', data)
export const submitCheck = (data) => api.post('/check/submit', data)

export const getDashboardOverview = () => api.get('/dashboard/overview')

export const handleError = (data) => api.put('/alert/error/handle', data)
export const getErrorList = (params) => api.get('/alert/error/stat/query', { params })

export const saveBasket = (data) => api.post('/basket/save', data)
export const saveBasketRelation = (data) => api.post('/basket/relation/save', data)
export const confirmBasket = (data) => api.post('/basket/check/confirm', data)
export const getBasketList = (params) => api.get('/basket/list', { params })
export const getBasketRelations = (params) => api.get('/basket/relation/query', { params })
export const disableBasket = (data) => api.put('/basket/disable', data)

export const getTraceRecords = (params) => api.get('/trace/record/query', { params })
export const getTraceVideo = (params) => api.get('/trace/video/query', { params })
export const generateReport = (data) => api.post('/trace/report/generate', data)

export const getWorkloadStat = (params) => api.get('/stat/workload/query', { params })
export const generateStatReport = (data) => api.post('/stat/report/generate', data)

export const getCurrentUserProfile = () => api.get('/sys/user/profile/get')
export const updateCurrentUserProfile = (data) => api.put('/sys/user/profile/update', data)
export const updateCurrentUserPassword = (data) => api.put('/sys/user/password/update', data)

export default api
