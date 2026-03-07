<template>
  <div class="system-page">
    <el-card class="module-card">
      <template #header>
        <span>用户管理</span>
      </template>
      <el-form :inline="true" class="query-form">
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

      <el-table :data="userList" stripe class="user-table">
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

    <el-card class="module-card role-card">
      <template #header>
        <span>角色管理</span>
      </template>
      <div class="role-toolbar">
        <el-button type="primary" @click="handleAddRole">新增角色</el-button>
      </div>

      <el-table :data="roleList" stripe class="role-table">
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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditRole(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDeleteRole(row)">删除</el-button>
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

    <el-dialog v-model="roleDialogVisible" :title="roleDialogTitle" width="600px">
      <el-form ref="roleFormRef" :model="roleForm" :rules="roleRules" label-width="100px">
        <el-form-item label="角色编码" prop="roleCode">
          <el-input v-model="roleForm.roleCode" :disabled="isEditRole" />
        </el-form-item>
        <el-form-item label="角色名称" prop="roleName">
          <el-input v-model="roleForm.roleName" />
        </el-form-item>
        <el-form-item label="权限标识" prop="rolePermission">
          <el-input v-model="roleForm.rolePermission" placeholder="如：check:scan,check:save" />
        </el-form-item>
        <el-form-item label="角色描述" prop="roleDesc">
          <el-input v-model="roleForm.roleDesc" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="roleForm.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRole">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUserList, saveUser, deleteUser, getRoleList, saveRole, deleteRole } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const userFilters = reactive({
  userAccount: '',
  userName: ''
})

const userList = ref([])

const roleList = ref([])

const userDialogVisible = ref(false)
const userDialogTitle = ref('新增用户')
const userFormRef = ref(null)
const isEditUser = ref(false)

const roleDialogVisible = ref(false)
const roleDialogTitle = ref('新增角色')
const roleFormRef = ref(null)
const isEditRole = ref(false)

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

const roleForm = reactive({
  id: null,
  roleCode: '',
  roleName: '',
  rolePermission: '',
  roleDesc: '',
  status: 1
})

const roleRules = {
  roleCode: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
  roleName: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  rolePermission: [{ required: true, message: '请输入权限标识', trigger: 'blur' }]
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
  roleDialogTitle.value = '新增角色'
  isEditRole.value = false
  Object.assign(roleForm, {
    id: null,
    roleCode: '',
    roleName: '',
    rolePermission: '',
    roleDesc: '',
    status: 1
  })
  roleDialogVisible.value = true
}

const handleEditRole = (row) => {
  roleDialogTitle.value = '编辑角色'
  isEditRole.value = true
  Object.assign(roleForm, row)
  roleDialogVisible.value = true
}

const loadRoleList = async () => {
  try {
    const res = await getRoleList()
    if (res.code === '0000') {
      roleList.value = res.data.list || []
    }
  } catch (error) {
    ElMessage.error('角色列表加载失败：' + error.message)
  }
}

const handleSaveRole = async () => {
  if (!roleFormRef.value) return
  await roleFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const res = await saveRole({
        roleCode: roleForm.roleCode,
        roleName: roleForm.roleName,
        rolePermission: roleForm.rolePermission,
        roleDesc: roleForm.roleDesc,
        status: roleForm.status
      })
      if (res.code === '0000') {
        ElMessage.success('角色保存成功')
        roleDialogVisible.value = false
        loadRoleList()
      } else {
        ElMessage.error(res.msg || '角色保存失败')
      }
    } catch (error) {
      ElMessage.error('角色保存失败：' + error.message)
    }
  })
}

const handleDeleteRole = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除角色 ${row.roleName} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await deleteRole({ id: row.id, operateBy: 'current_user' })
    if (res.code === '0000') {
      ElMessage.success('角色删除成功')
      loadRoleList()
    } else {
      ElMessage.error(res.msg || '角色删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('角色删除失败：' + error.message)
    }
  }
}

onMounted(() => {
  handleSearchUser()
  loadRoleList()
})
</script>

<style scoped>
.system-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.1) 0%, rgba(120, 146, 98, 0.02) 58%);
}

.query-form {
  padding: 4px 0 10px;
}

.query-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.role-toolbar {
  margin-bottom: 10px;
}

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

.module-card :deep(.el-tag) {
  border-radius: 4px;
}

:deep(.el-dialog__body) {
  padding-top: 14px;
}
</style>
