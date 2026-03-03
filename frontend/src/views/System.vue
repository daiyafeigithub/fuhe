<template>
  <div class="system-page">
    <el-card>
      <template #header>
        <span>用户管理</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="账号">
          <el-input v-model="userFilters.userAccount" placeholder="请输入账号" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userFilters.userName" placeholder="请输入姓名" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearchUser">查询</el-button>
          <el-button type="success" @click="handleAddUser">新增用户</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="userList" stripe>
        <el-table-column prop="userAccount" label="账号" />
        <el-table-column prop="userName" label="姓名" />
        <el-table-column prop="deptName" label="所属科室" />
        <el-table-column prop="post" label="岗位" />
        <el-table-column prop="phone" label="联系电话" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditUser(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDeleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>角色管理</span>
      </template>
      <el-button type="primary" @click="handleAddRole">新增角色</el-button>

      <el-table :data="roleList" stripe style="margin-top: 15px">
        <el-table-column prop="roleCode" label="角色编码" />
        <el-table-column prop="roleName" label="角色名称" />
        <el-table-column prop="rolePermission" label="权限标识" show-overflow-tooltip />
        <el-table-column prop="roleDesc" label="角色描述" show-overflow-tooltip />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditRole(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="userDialogVisible" :title="userDialogTitle" width="600px">
      <el-form ref="userFormRef" :model="userForm" :rules="userRules" label-width="100px">
        <el-form-item label="账号" prop="userAccount">
          <el-input v-model="userForm.userAccount" :disabled="isEditUser" />
        </el-form-item>
        <el-form-item label="姓名" prop="userName">
          <el-input v-model="userForm.userName" />
        </el-form-item>
        <el-form-item label="密码" prop="userPwd" v-if="!isEditUser">
          <el-input v-model="userForm.userPwd" type="password" />
        </el-form-item>
        <el-form-item label="所属科室" prop="deptName">
          <el-input v-model="userForm.deptName" />
        </el-form-item>
        <el-form-item label="岗位" prop="post">
          <el-input v-model="userForm.post" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="userForm.phone" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="userForm.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getUserList, saveUser, deleteUser, saveRole } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const userFilters = reactive({
  userAccount: '',
  userName: ''
})

const userList = ref([
  {
    id: 1,
    userAccount: 'admin',
    userName: '管理员',
    deptName: '信息科',
    post: '系统管理员',
    phone: '13800138000',
    status: 1
  },
  {
    id: 2,
    userAccount: 'fh001',
    userName: '张复核',
    deptName: '中药房',
    post: '复核员',
    phone: '13900139000',
    status: 1
  }
])

const roleList = ref([
  {
    id: 1,
    roleCode: 'ADMIN',
    roleName: '超级管理员',
    rolePermission: 'all',
    roleDesc: '系统最高权限',
    status: 1
  },
  {
    id: 2,
    roleCode: 'CHECKER',
    roleName: '复核员',
    rolePermission: 'check:scan,check:save,basket:manage',
    roleDesc: '饮片复核人员',
    status: 1
  }
])

const userDialogVisible = ref(false)
const userDialogTitle = ref('新增用户')
const userFormRef = ref(null)
const isEditUser = ref(false)

const userForm = reactive({
  id: null,
  userAccount: '',
  userPwd: '',
  userName: '',
  deptName: '',
  post: '',
  phone: '',
  status: 1
})

const userRules = {
  userAccount: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  userName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  userPwd: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  deptName: [{ required: true, message: '请输入所属科室', trigger: 'blur' }],
  post: [{ required: true, message: '请输入岗位', trigger: 'blur' }]
}

const handleSearchUser = async () => {
  try {
    const res = await getUserList({
      ...userFilters,
      page: 1,
      size: 20
    })
    if (res.code === '0000') {
      userList.value = res.data.list || []
    }
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  }
}

const handleAddUser = () => {
  userDialogTitle.value = '新增用户'
  isEditUser.value = false
  Object.assign(userForm, {
    id: null,
    userAccount: '',
    userPwd: '',
    userName: '',
    deptName: '',
    post: '',
    phone: '',
    status: 1
  })
  userDialogVisible.value = true
}

const handleEditUser = (row) => {
  userDialogTitle.value = '编辑用户'
  isEditUser.value = true
  Object.assign(userForm, row)
  userDialogVisible.value = true
}

const handleSaveUser = async () => {
  if (!userFormRef.value) return
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const res = await saveUser({
          ...userForm,
          createBy: 'current_user'
        })
        if (res.code === '0000') {
          ElMessage.success('保存成功')
          userDialogVisible.value = false
          handleSearchUser()
        } else {
          ElMessage.error(res.msg || '保存失败')
        }
      } catch (error) {
        ElMessage.error('保存失败：' + error.message)
      }
    }
  })
}

const handleDeleteUser = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${row.userName} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await deleteUser({ id: row.id, operateBy: 'current_user' })
    if (res.code === '0000') {
      ElMessage.success('删除成功')
      handleSearchUser()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

const handleAddRole = () => {
  ElMessage.info('角色编辑功能开发中')
}

const handleEditRole = () => {
  ElMessage.info('角色编辑功能开发中')
}
</script>
