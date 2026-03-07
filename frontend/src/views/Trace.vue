<template>
  <div class="trace-page">
    <el-card class="module-card">
      <template #header>
        <span>溯源查询</span>
      </template>
      <el-form :inline="true" class="query-form">
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

      <el-table :data="traceList" stripe class="trace-table">
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
import { ref, reactive, onMounted } from 'vue'
import { getTraceRecords, getTraceVideo, generateReport } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const filters = reactive({
  presNo: '',
  checkBy: ''
})

const dateRange = ref([])
const traceList = ref([])

const detailDialogVisible = ref(false)
const videoDialogVisible = ref(false)
const currentDetail = ref({})
const videoUrl = ref('')

const formatDateTimeForApi = (dateTime) => {
  if (!dateTime) return ''
  const dt = new Date(dateTime)
  if (Number.isNaN(dt.getTime())) {
    return String(dateTime).replace('T', ' ').slice(0, 19)
  }
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const d = String(dt.getDate()).padStart(2, '0')
  const hh = String(dt.getHours()).padStart(2, '0')
  const mm = String(dt.getMinutes()).padStart(2, '0')
  const ss = String(dt.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

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
    } else {
      ElMessage.error(res.msg || '查询失败')
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

const handleViewVideo = async (row) => {
  currentDetail.value = row
  videoUrl.value = ''
  try {
    const res = await getTraceVideo({
      presNo: row.presNo,
      scanTime: formatDateTimeForApi(row.scanTime),
      checkStation: row.checkStation || 'T01'
    })
    if (res.code === '0000') {
      const video = (res.data.videos || [])[0]
      if (!video || !video.videoUrl) {
        ElMessage.warning('未找到对应视频')
        return
      }
      videoUrl.value = video.videoUrl
      videoDialogVisible.value = true
    } else {
      ElMessage.error(res.msg || '视频查询失败')
    }
  } catch (error) {
    ElMessage.error('视频查询失败：' + error.message)
  }
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
      generateBy: userStore.userInfo.userAccount || 'current_user'
    })
    if (res.code === '0000') {
      ElMessage.success('报告生成成功')
      if (res.data.downloadUrl) {
        window.open(res.data.downloadUrl, '_blank')
      }
    } else {
      ElMessage.error(res.msg || '生成失败')
    }
  } catch (error) {
    ElMessage.error('生成失败：' + error.message)
  }
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.trace-page {
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

.video-container {
  background: linear-gradient(180deg, rgba(51, 51, 51, 0.92), rgba(51, 51, 51, 0.84));
  padding: 14px;
  border-radius: 6px;
  border: 1px solid #4a4f47;
}
</style>
