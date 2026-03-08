<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <div class="title-row">
            <span class="title-icon">
              <HerbLeafIcon :size="24" />
            </span>
            <h2>成品复核系统</h2>
          </div>
          <p>登录</p>
        </div>
      </template>
      <el-form ref="loginFormRef" :model="loginForm" :rules="rules" label-width="80px">
        <el-form-item label="账号" prop="userAccount">
          <el-input
            v-model="loginForm.userAccount"
            placeholder="请输入账号"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="userPwd">
          <el-input
            v-model="loginForm.userPwd"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width: 100%" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-tips">
        <p>测试用户名:fuhe/测试密码:fuhe123</p>
        <p><b>春风得意马蹄疾，一日看尽长安花。</b></p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import HerbLeafIcon from '@/components/icons/HerbLeafIcon.vue'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  userAccount: '',
  userPwd: ''
})

const rules = {
  userAccount: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  userPwd: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const success = await userStore.login(loginForm.userAccount, loginForm.userPwd)
      loading.value = false
      if (success) {
        router.push('/dashboard')
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background:
    radial-gradient(circle at 20% 16%, rgba(120, 146, 98, 0.07), transparent 35%),
    radial-gradient(circle at 80% 75%, rgba(74, 112, 35, 0.05), transparent 30%),
    var(--el-bg-color-page);
}

.login-card {
  width: 420px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 10px 28px rgba(62, 74, 50, 0.12);
}

.card-header {
  text-align: center;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.title-icon {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary-dark-2);
  background: rgba(120, 146, 98, 0.1);
  border: 1px solid rgba(120, 146, 98, 0.22);
}

.card-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 22px;
  font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
}

.card-header p {
  margin-top: 8px;
  color: #6a7665;
  font-size: 13px;
}

.login-tips {
  margin-top: 15px;
  text-align: center;
  color: #7a8473;
  font-size: 12px;
}

.login-tips p {
  margin: 5px 0;
}
</style>
