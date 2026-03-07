<template>
  <div class="statistics-page">
    <el-card class="module-card">
      <template #header>
        <span>工作量统计</span>
      </template>
      <el-form :inline="true" class="query-form">
        <el-form-item label="统计维度">
          <el-select v-model="filters.statType" placeholder="请选择" @change="handleTypeChange">
            <el-option label="人员统计" value="USER" />
            <el-option label="时间统计" value="TIME" />
            <el-option label="处方统计" value="PRES" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filters.statType === 'USER'" label="复核人员">
          <el-select v-model="filters.checkBy" placeholder="全部">
            <el-option label="全部" :value="ALL_CHECKER_VALUE" />
            <el-option
              v-for="user in checkerOptions"
              :key="user.userAccount"
              :label="`${user.userName}(${user.userAccount})`"
              :value="user.userAccount"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filters.statType === 'TIME'" label="时间类型">
          <el-select v-model="filters.timeType" placeholder="请选择">
            <el-option label="日统计" value="DAY" />
            <el-option label="周统计" value="WEEK" />
            <el-option label="月统计" value="MONTH" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filters.statType === 'TIME'" label="统计时间">
          <el-date-picker
            v-model="filters.statTime"
            type="month"
            placeholder="选择月份"
            value-format="YYYY-MM"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">统计</el-button>
          <el-button type="success" @click="handleExport">导出报表</el-button>
        </el-form-item>
      </el-form>

      <el-row :gutter="20" class="stat-overview">
        <el-col :span="6">
          <el-statistic title="复核处方数" :value="stats.presTotal" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="复核饮片品种数" :value="stats.drugTotal" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="扫码次数" :value="stats.qrcodeTotal" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="错误总数" :value="stats.errorTotal" />
        </el-col>
      </el-row>

      <el-table :data="statList" stripe class="stat-table">
        <el-table-column prop="checkBy" label="复核人员" v-if="filters.statType === 'USER'" />
        <el-table-column prop="statTime" label="统计时间" v-if="filters.statType === 'TIME'" />
        <el-table-column prop="presNo" label="处方号" v-if="filters.statType === 'PRES'" />
        <el-table-column prop="presTotal" label="复核处方数" />
        <el-table-column prop="drugTotal" label="复核饮片品种数" />
        <el-table-column prop="qrcodeTotal" label="扫码次数" />
        <el-table-column prop="qualifiedPres" label="合格处方数" />
        <el-table-column prop="errorTotal" label="错误总数" />
        <el-table-column label="合格率" width="100">
          <template #default="{ row }">
            {{ row.presTotal > 0 ? ((row.qualifiedPres / row.presTotal) * 100).toFixed(1) : '0.0' }}%
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getWorkloadStat, generateStatReport, getUserList } from '@/api'
import { ElMessage } from 'element-plus'

const ALL_CHECKER_VALUE = '__ALL__'

const getCurrentMonth = () => {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

const filters = reactive({
  statType: 'USER',
  checkBy: ALL_CHECKER_VALUE,
  timeType: 'MONTH',
  statTime: getCurrentMonth()
})

const checkerOptions = ref([])

const stats = ref({
  presTotal: 0,
  drugTotal: 0,
  qrcodeTotal: 0,
  errorTotal: 0
})

const statList = ref([])

const loadCheckerOptions = async () => {
  try {
    const res = await getUserList({ page: 1, size: 200, status: 1 })
    if (res.code === '0000') {
      checkerOptions.value = (res.data.list || []).map(item => ({
        userAccount: item.userAccount,
        userName: item.userName
      }))
    }
  } catch {
    // 静默处理，人员下拉可退化为“全部”
  }
}

const ensureDefaultFilters = () => {
  if (!filters.statType) {
    filters.statType = 'USER'
  }

  if (filters.statType === 'USER' && !filters.checkBy) {
    filters.checkBy = ALL_CHECKER_VALUE
  }
}

const handleTypeChange = () => {
  filters.checkBy = ALL_CHECKER_VALUE
  filters.timeType = 'MONTH'
  filters.statTime = getCurrentMonth()
}

const handleSearch = async () => {
  try {
    ensureDefaultFilters()

    const params = {
      ...filters,
      checkBy: filters.checkBy === ALL_CHECKER_VALUE ? '' : filters.checkBy,
      page: 1,
      size: 20
    }
    const res = await getWorkloadStat(params)
    if (res.code === '0000') {
      const list = res.data.list || []
      statList.value = list
      stats.value = {
        presTotal: list.reduce((sum, item) => sum + (item.presTotal || 0), 0),
        drugTotal: list.reduce((sum, item) => sum + (item.drugTotal || 0), 0),
        qrcodeTotal: list.reduce((sum, item) => sum + (item.qrcodeTotal || 0), 0),
        errorTotal: list.reduce((sum, item) => sum + (item.errorTotal || 0), 0)
      }
    } else {
      ElMessage.error(res.msg || '统计失败')
    }
  } catch (error) {
    ElMessage.error('统计失败：' + error.message)
  }
}

const handleExport = async () => {
  try {
    const month = (filters.statTime || getCurrentMonth()).slice(0, 7)
    const [year, monthNumber] = month.split('-').map(Number)
    const start = new Date(year, monthNumber - 1, 1)
    const end = new Date(year, monthNumber, 0)
    const formatDate = (date) => {
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    }

    const startDate = formatDate(start)
    const endDate = formatDate(end)

    const res = await generateStatReport({
      startDate,
      endDate,
      reportType: 'detailed'
    })

    if (res.code === '0000') {
      ElMessage.success('报表导出成功')
      if (res.data.downloadUrl) {
        window.open(res.data.downloadUrl, '_blank')
      }
    } else {
      ElMessage.error(res.msg || '报表导出失败')
    }
  } catch (error) {
    ElMessage.error('报表导出失败：' + error.message)
  }
}

onMounted(() => {
  ensureDefaultFilters()
  loadCheckerOptions()
  handleSearch()
})
</script>

<style scoped>
.statistics-page {
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

.stat-overview {
  margin-bottom: 14px !important;
}

.module-card :deep(.el-statistic) {
  padding: 12px 14px;
  border: 1px solid #e8e3d8;
  border-radius: 6px;
  background: #fbfaf7;
}

.module-card :deep(.el-statistic__head) {
  color: #6c7568;
  font-size: 13px;
}

.module-card :deep(.el-statistic__content) {
  color: #32402d;
}

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}
</style>
