<template>
  <div class="trace-page">
    <el-card>
      <template #header>
        <span>溯源查询</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="处方号">
          <el-input v-model="filters.presNo" placeholder="请输入处方号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="复核人员">
          <el-input v-model="filters.checkBy" placeholder="请输入账号" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleGenerateReport">生成溯源报告</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="traceList" stripe>
        <el-table-column prop="presNo" label="处方号" width="150" />
        <el-table-column prop="cjId" label="院内编码" width="120" />
        <el-table-column prop="drugName" label="药品名称" width="120" />
        <el-table-column prop="scanTime" label="扫码时间" width="180" />
        <el-table-column prop="checkBy" label="复核人员" width="100" />
        <el-table-column prop="basketNo" label="筐号" width="120" />
        <el-table-column prop="scanResult" label="扫码结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.scanResult === 1 ? 'success' : 'danger'">
              {{ row.scanResult === 1 ? '匹配' : '不匹配' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">查看详情</el-button>
            <el-button link type="primary" @click="handleViewVideo(row)">查看视频</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailDialogVisible" title="溯源详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="处方号">{{ currentDetail.presNo }}</el-descriptions-item>
        <el-descriptions-item label="患者姓名">{{ currentDetail.patientName }}</el-descriptions-item>
        <el-descriptions-item label="院内编码">{{ currentDetail.cjId }}</el-descriptions-item>
        <el-descriptions-item label="药品名称">{{ currentDetail.drugName }}</el-descriptions-item>
        <el-descriptions-item label="处方规格">{{ currentDetail.spec }}</el-descriptions-item>
        <el-descriptions-item label="扫码规格">{{ currentDetail.scanSpec }}</el-descriptions-item>
        <el-descriptions-item label="扫码时间">{{ currentDetail.scanTime }}</el-descriptions-item>
        <el-descriptions-item label="复核人员">{{ currentDetail.checkBy }}</el-descriptions-item>
        <el-descriptions-item label="筐号">{{ currentDetail.basketNo }}</el-descriptions-item>
        <el-descriptions-item label="复核台编号">{{ currentDetail.checkStation }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="videoDialogVisible" title="视频监控" width="800px">
      <div class="video-container">
        <video :src="videoUrl" controls style="width: 100%">
          您的浏览器不支持视频播放
        </video>
      </div>
      <p>录像时间：{{ currentDetail.scanTime }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getTraceRecords, generateReport } from '@/api'
import { ElMessage } from 'element-plus'

const filters = reactive({
  presNo: '',
  checkBy: ''
})

const dateRange = ref([])
const traceList = ref([
  {
    presNo: 'CF20260228001',
    cjId: '13310',
    drugName: '盐巴戟天',
    scanTime: '2026-02-28 10:30:00',
    checkBy: 'fh001',
    basketNo: 'K20260228001',
    scanResult: 1,
    patientName: '张三',
    spec: '5g',
    scanSpec: '5g',
    checkStation: 'T01'
  },
  {
    presNo: 'CF20260228002',
    cjId: '13311',
    drugName: '当归',
    scanTime: '2026-02-28 10:25:00',
    checkBy: 'fh002',
    basketNo: 'K20260228002',
    scanResult: 0,
    patientName: '李四',
    spec: '3g',
    scanSpec: '5g',
    checkStation: 'T02'
  }
])

const detailDialogVisible = ref(false)
const videoDialogVisible = ref(false)
const currentDetail = ref({})
const videoUrl = ref('')

const handleSearch = async () => {
  try {
    const [startDate, endDate] = dateRange.value || []
    const res = await getTraceRecords({
      ...filters,
      startTime: startDate ? `${startDate} 00:00:00` : '',
      endTime: endDate ? `${endDate} 23:59:59` : '',
      page: 1,
      size: 20
    })
    if (res.code === '0000') {
      traceList.value = res.data.list || []
    }
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  }
}

const handleReset = () => {
  filters.presNo = ''
  filters.checkBy = ''
  dateRange.value = []
  handleSearch()
}

const handleViewDetail = (row) => {
  currentDetail.value = row
  detailDialogVisible.value = true
}

const handleViewVideo = (row) => {
  currentDetail.value = row
  videoUrl.value = `http://example.com/video/${row.presNo}_${row.scanTime}.mp4`
  videoDialogVisible.value = true
}

const handleGenerateReport = async () => {
  const presNos = traceList.value.map(item => item.presNo)
  if (presNos.length === 0) {
    ElMessage.warning('请先查询数据')
    return
  }
  try {
    const res = await generateReport({
      presNoList: [...new Set(presNos)],
      reportType: 'PDF',
      generateBy: 'current_user'
    })
    if (res.code === '0000') {
      ElMessage.success('报告生成成功')
      window.open(res.data.downloadUrl, '_blank')
    } else {
      ElMessage.error(res.msg || '生成失败')
    }
  } catch (error) {
    ElMessage.error('生成失败：' + error.message)
  }
}
</script>

<style scoped>
.video-container {
  background-color: #000;
  padding: 20px;
  border-radius: 4px;
}
</style>
