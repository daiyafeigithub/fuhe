<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :span="14">
        <el-card class="module-card">
          <template #header>
            <span>个人资料</span>
          </template>
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="90px"
            class="profile-form"
          >
            <el-form-item label="账号">
              <el-input v-model="profileForm.userAccount" disabled />
            </el-form-item>
            <el-form-item label="姓名" prop="userName">
              <el-input v-model="profileForm.userName" />
            </el-form-item>
            <el-form-item label="科室" prop="deptName">
              <el-input v-model="profileForm.deptName" />
            </el-form-item>
            <el-form-item label="岗位" prop="post">
              <el-input v-model="profileForm.post" />
            </el-form-item>
            <el-form-item label="电话">
              <el-input v-model="profileForm.phone" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="module-card">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="90px"
            class="password-form"
          >
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingPassword" @click="handleUpdatePassword">更新密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { getCurrentUserProfile, updateCurrentUserProfile, updateCurrentUserPassword } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const savingProfile = ref(false)
const savingPassword = ref(false)

const profileForm = reactive({
  userAccount: '',
  userName: '',
  deptName: '',
  post: '',
  phone: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileRules = {
  userName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  deptName: [{ required: true, message: '请输入科室', trigger: 'blur' }],
  post: [{ required: true, message: '请输入岗位', trigger: 'blur' }]
}

const validateConfirmPassword = (_, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
    return
  }
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
    return
  }
  callback()
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码不少于6位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

const loadProfile = async () => {
  try {
    const res = await getCurrentUserProfile()
    if (res.code === '0000') {
      Object.assign(profileForm, {
        userAccount: res.data.userAccount || '',
        userName: res.data.userName || '',
        deptName: res.data.deptName || '',
        post: res.data.post || '',
        phone: res.data.phone || ''
      })
    } else {
      ElMessage.error(res.msg || '个人信息加载失败')
    }
  } catch (error) {
    ElMessage.error('个人信息加载失败：' + error.message)
  }
}

const handleSaveProfile = async () => {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingProfile.value = true
    try {
      const res = await updateCurrentUserProfile({
        userName: profileForm.userName,
        deptName: profileForm.deptName,
        post: profileForm.post,
        phone: profileForm.phone
      })
      if (res.code === '0000') {
        userStore.setUserInfo({
          ...userStore.userInfo,
          userName: profileForm.userName,
          deptName: profileForm.deptName,
          post: profileForm.post,
          phone: profileForm.phone
        })
        ElMessage.success('个人资料保存成功')
      } else {
        ElMessage.error(res.msg || '保存失败')
      }
    } catch (error) {
      ElMessage.error('保存失败：' + error.message)
    } finally {
      savingProfile.value = false
    }
  })
}

const handleUpdatePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingPassword.value = true
    try {
      const res = await updateCurrentUserPassword({
        oldPassword: passwordForm.oldPassword,
        newPassword: passwordForm.newPassword
      })
      if (res.code === '0000') {
        ElMessage.success('密码更新成功，请牢记新密码')
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
      } else {
        ElMessage.error(res.msg || '密码更新失败')
      }
    } catch (error) {
      ElMessage.error('密码更新失败：' + error.message)
    } finally {
      savingPassword.value = false
    }
  })
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.1) 0%, rgba(120, 146, 98, 0.02) 58%);
}

.profile-form {
  max-width: 640px;
}

.profile-form :deep(.el-form-item),
.password-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
</style>
