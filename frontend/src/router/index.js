import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', menuKey: 'dashboard' }
      },
      {
        path: 'qrcode',
        redirect: '/qrcode/generate'
      },
      {
        path: 'qrcode/generate',
        name: 'QRCodeGenerate',
        component: () => import('@/views/QRCode.vue'),
        meta: { title: '二维码生成', menuKey: 'qrcodeGenerate', qrcodeMode: 'generate' }
      },
      {
        path: 'qrcode/manage',
        name: 'QRCodeManage',
        component: () => import('@/views/QRCode.vue'),
        meta: { title: '二维码管理', menuKey: 'qrcodeManage', qrcodeMode: 'manage' }
      },
      {
        path: 'check',
        name: 'Check',
        component: () => import('@/views/Check.vue'),
        meta: { title: '扫码复核', menuKey: 'check' }
      },
      {
        path: 'alert',
        name: 'Alert',
        component: () => import('@/views/Alert.vue'),
        meta: { title: '错误提醒', menuKey: 'alert' }
      },
      {
        path: 'basket',
        name: 'Basket',
        component: () => import('@/views/Basket.vue'),
        meta: { title: '分筐管理', menuKey: 'basket' }
      },
      {
        path: 'trace',
        name: 'Trace',
        component: () => import('@/views/Trace.vue'),
        meta: { title: '溯源管理', menuKey: 'trace' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '工作量统计', menuKey: 'statistics' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('@/views/System.vue'),
        meta: { title: '系统管理', menuKey: 'system' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/dashboard')
  } else if (to.meta?.menuKey && !userStore.canAccessMenu(to.meta.menuKey)) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
