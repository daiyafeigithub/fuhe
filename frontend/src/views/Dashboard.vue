<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Reading /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayPres }}</div>
              <div class="stat-label">今日复核处方</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><SuccessFilled /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.qualifiedRate }}%</div>
              <div class="stat-label">复核合格率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C"><Warning /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayErrors }}</div>
              <div class="stat-label">今日错误数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#E6A23C"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingPres }}</div>
              <div class="stat-label">待复核处方</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>最近复核记录</span>
          </template>
          <el-table :data="recentRecords" stripe>
            <el-table-column prop="presNo" label="处方号" />
            <el-table-column prop="patientName" label="患者姓名" />
            <el-table-column prop="checkBy" label="复核人员" />
            <el-table-column prop="checkTime" label="复核时间" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" icon="Plus" @click="$router.push('/qrcode')">
              生成二维码
            </el-button>
            <el-button type="success" icon="Reading" @click="$router.push('/check')">
              扫码复核
            </el-button>
            <el-button type="warning" icon="Search" @click="$router.push('/trace')">
              溯源查询
            </el-button>
            <el-button type="info" icon="DataAnalysis" @click="$router.push('/statistics')">
              工作量统计
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  todayPres: 0,
  qualifiedRate: 0,
  todayErrors: 0,
  pendingPres: 0
})

const recentRecords = ref([])

onMounted(() => {
  loadStats()
  loadRecentRecords()
})

const loadStats = () => {
  stats.value = {
    todayPres: 28,
    qualifiedRate: 98.5,
    todayErrors: 3,
    pendingPres: 12
  }
}

const loadRecentRecords = () => {
  recentRecords.value = [
    { presNo: 'CF20260228001', patientName: '张三', checkBy: 'fh001', checkTime: '2026-02-28 10:30', status: 2 },
    { presNo: 'CF20260228002', patientName: '李四', checkBy: 'fh002', checkTime: '2026-02-28 10:25', status: 2 },
    { presNo: 'CF20260228003', patientName: '王五', checkBy: 'fh001', checkTime: '2026-02-28 10:20', status: 3 }
  ]
}

const getStatusType = (status) => {
  const map = { 1: 'info', 2: 'success', 3: 'danger', 4: 'warning' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { 1: '未复核', 2: '已复核', 3: '复核异常', 4: '复核中' }
  return map[status] || '未知'
}
</script>

<style scoped>
.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  font-size: 48px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-top: 5px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.quick-actions .el-button {
  width: 100%;
}
</style>
