<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>湖南省二附院精致饮片复核系统</h2>
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
        <p>默认管理员账号：admin / 123456a@</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.login-tips {
  margin-top: 15px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.login-tips p {
  margin: 5px 0;
}
</style>
