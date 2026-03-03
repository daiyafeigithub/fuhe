<template>
  <div class="alert-page">
    <el-card>
      <template #header>
        <span>错误记录</span>
      </template>
      <el-form :inline="true">
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
            <span v-else style="color: #909399">已处理</span>
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
import { ref, reactive } from 'vue'
import { getErrorList, handleError } from '@/api'
import { ElMessage } from 'element-plus'

const filters = reactive({
  errorType: '',
  presNo: ''
})

const errorList = ref([
  {
    errorId: 'ERR001',
    errorTime: '2026-02-28 10:30:00',
    presNo: 'CF20260228001',
    cjId: '13310',
    drugName: '盐巴戟天',
    errorType: 'DRUG_ERROR',
    errorDesc: '扫码规格5g与处方要求3g不匹配',
    errorStatus: 1
  },
  {
    errorId: 'ERR002',
    errorTime: '2026-02-28 10:25:00',
    presNo: 'CF20260228002',
    cjId: '13311',
    drugName: '当归',
    errorType: 'NUM_ERROR',
    errorDesc: '扫码数量3与处方要求2不匹配',
    errorStatus: 2
  }
])

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
      handleBy: 'current_user',
      ...processForm
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
</script>
