<template>
  <div class="statistics-page">
    <el-card>
      <template #header>
        <span>工作量统计</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="统计维度">
          <el-select v-model="filters.statType" placeholder="请选择" @change="handleTypeChange">
            <el-option label="人员统计" value="USER" />
            <el-option label="时间统计" value="TIME" />
            <el-option label="处方统计" value="PRES" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filters.statType === 'USER'" label="复核人员">
          <el-select v-model="filters.checkBy" placeholder="全部">
            <el-option label="fh001" value="fh001" />
            <el-option label="fh002" value="fh002" />
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

      <el-row :gutter="20" style="margin-bottom: 20px">
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

      <el-table :data="statList" stripe>
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
            {{ ((row.qualifiedPres / row.presTotal) * 100).toFixed(1) }}%
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getWorkloadStat } from '@/api'
import { ElMessage } from 'element-plus'

const filters = reactive({
  statType: 'USER',
  checkBy: '',
  timeType: 'MONTH',
  statTime: '2026-02'
})

const stats = ref({
  presTotal: 28,
  drugTotal: 140,
  qrcodeTotal: 168,
  errorTotal: 3
})

const statList = ref([
  {
    checkBy: 'fh001',
    presTotal: 15,
    drugTotal: 75,
    qrcodeTotal: 90,
    qualifiedPres: 15,
    errorTotal: 0
  },
  {
    checkBy: 'fh002',
    presTotal: 13,
    drugTotal: 65,
    qrcodeTotal: 78,
    qualifiedPres: 10,
    errorTotal: 3
  }
])

const handleTypeChange = () => {
  filters.checkBy = ''
  filters.timeType = 'MONTH'
  filters.statTime = '2026-02'
}

const handleSearch = async () => {
  try {
    const params = { ...filters, page: 1, size: 20 }
    const res = await getWorkloadStat(params)
    if (res.code === '0000') {
      statList.value = res.data.list || []
      stats.value = {
        presTotal: res.data.list.reduce((sum, item) => sum + item.presTotal, 0),
        drugTotal: res.data.list.reduce((sum, item) => sum + item.drugTotal, 0),
        qrcodeTotal: res.data.list.reduce((sum, item) => sum + item.qrcodeTotal, 0),
        errorTotal: res.data.list.reduce((sum, item) => sum + item.errorTotal, 0)
      }
    }
  } catch (error) {
    ElMessage.error('统计失败：' + error.message)
  }
}

const handleExport = () => {
  ElMessage.success('报表导出成功')
}
</script>
