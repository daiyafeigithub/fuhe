<template>
  <div class="alert-page">
    <el-card class="module-card">
      <template #header>
        <span>错误记录</span>
      </template>
      <el-form :inline="true" class="query-form">
        <el-form-item label="错误类型">
          <el-select v-model="filters.errorType" placeholder="全部" clearable style="width: 150px">
            <el-option label="药品错误" value="DRUG_ERROR" />
            <el-option label="数量错误" value="NUM_ERROR" />
          </el-select>
        </el-form-item>
        <el-form-item label="处方号">
          <el-input v-model="filters.presNo" placeholder="请输入" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="errorList" stripe>
        <el-table-column prop="errorTime" label="错误时间" width="180" />
        <el-table-column prop="presNo" label="处方号" width="150" />
        <el-table-column prop="cjId" label="院内编码" width="120" />
        <el-table-column prop="drugName" label="药品名称" width="120" />
        <el-table-column prop="errorType" label="错误类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.errorType === 'DRUG_ERROR' ? 'danger' : 'warning'">
              {{ row.errorType === 'DRUG_ERROR' ? '药品错误' : '数量错误' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="errorDesc" label="错误描述" show-overflow-tooltip />
        <el-table-column prop="errorStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.errorStatus === 1 ? 'danger' : 'success'">
              {{ row.errorStatus === 1 ? '未处理' : '已处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.errorStatus === 1"
              link
              type="primary"
              @click="handleProcess(row)"
            >
              处理
            </el-button>
            <span v-else class="status-text">已处理</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="错误处理" width="500px">
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="处理类型">
          <el-select v-model="processForm.handleType" placeholder="请选择">
            <el-option label="错抓更换" value="REPLACE" />
            <el-option label="少包补加" value="ADD" />
            <el-option label="误扫取消" value="CANCEL" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理描述">
          <el-input
            v-model="processForm.handleDesc"
            type="textarea"
            :rows="3"
            placeholder="请输入处理描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmProcess">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getErrorList, handleError } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const filters = reactive({
  errorType: '',
  presNo: ''
})

const errorList = ref([])

const dialogVisible = ref(false)
const currentError = ref(null)
const processForm = reactive({
  handleType: '',
  handleDesc: ''
})

const handleSearch = async () => {
  try {
    const res = await getErrorList({
      ...filters,
      page: 1,
      size: 20
    })
    if (res.code === '0000') {
      errorList.value = res.data.list || []
    }
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  }
}

const handleReset = () => {
  filters.errorType = ''
  filters.presNo = ''
  handleSearch()
}

const handleProcess = (row) => {
  currentError.value = row
  processForm.handleType = ''
  processForm.handleDesc = ''
  dialogVisible.value = true
}

const handleConfirmProcess = async () => {
  if (!processForm.handleType) {
    ElMessage.warning('请选择处理类型')
    return
  }
  try {
    const res = await handleError({
      errorId: currentError.value.errorId,
      handleBy: userStore.userInfo.userAccount || 'admin',
      handleResult: processForm.handleType,
      handleDesc: processForm.handleDesc
    })
    if (res.code === '0000') {
      ElMessage.success('处理成功')
      dialogVisible.value = false
      currentError.value.errorStatus = 2
      handleSearch()
    } else {
      ElMessage.error(res.msg || '处理失败')
    }
  } catch (error) {
    ElMessage.error('处理失败：' + error.message)
  }
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.alert-page {
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

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

.module-card :deep(.el-tag) {
  border-radius: 4px;
}

.status-text {
  color: #8c9488;
}

:deep(.el-dialog__body) {
  padding-top: 14px;
}
</style>
