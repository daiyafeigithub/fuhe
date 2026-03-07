<template>
  <div class="dashboard">
    <el-card class="overview-card" shadow="never">
      <div class="overview-head">
        <div>
          <div class="overview-title">
            <span class="overview-icon">
              <HerbLeafIcon :size="20" />
            </span>
            <h2>中药材管理工作台</h2>
          </div>
          <p>新中式极简 · 实时业务总览</p>
        </div>
        <div class="update-meta">
          <span>最后更新</span>
          <strong>{{ updateTimeText }}</strong>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card card-pres" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon-wrap">
              <ModuleHerbIcon variant="check" class="stat-icon" :size="22" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayPres }}</div>
              <div class="stat-label">今日复核处方</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card card-rate" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon-wrap">
              <ModuleHerbIcon variant="statistics" class="stat-icon" :size="22" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.qualifiedRate }}%</div>
              <div class="stat-label">复核合格率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card card-error" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon-wrap">
              <ModuleHerbIcon variant="alert" class="stat-icon" :size="22" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayErrors }}</div>
              <div class="stat-label">今日错误数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card card-pending" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon-wrap">
              <ModuleHerbIcon variant="dashboard" class="stat-icon" :size="22" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingPres }}</div>
              <div class="stat-label">待复核处方</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :span="16">
        <el-card class="table-card">
          <template #header>
            <span>最近复核记录</span>
          </template>
          <el-table :data="recentRecords" stripe v-loading="loading">
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
        <el-card class="viz-card">
          <template #header>
            <span>近 10 单状态分布</span>
          </template>
          <div class="viz-list">
            <div v-for="item in statusDistribution" :key="item.key" class="viz-item">
              <div class="viz-label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }} 单</strong>
              </div>
              <el-progress
                :percentage="item.percentage"
                :stroke-width="10"
                :show-text="false"
                :color="item.color"
              />
            </div>
          </div>
        </el-card>

        <el-card class="quick-card">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/qrcode')">
              <template #icon>
                <ModuleHerbIcon variant="qrcode" :size="15" />
              </template>
              生成二维码
            </el-button>
            <el-button plain @click="$router.push('/check')">
              <template #icon>
                <ModuleHerbIcon variant="check" :size="15" />
              </template>
              扫码复核
            </el-button>
            <el-button plain @click="$router.push('/trace')">
              <template #icon>
                <ModuleHerbIcon variant="trace" :size="15" />
              </template>
              溯源查询
            </el-button>
            <el-button plain @click="$router.push('/statistics')">
              <template #icon>
                <ModuleHerbIcon variant="statistics" :size="15" />
              </template>
              工作量统计
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getDashboardOverview } from '@/api'
import { ElMessage } from 'element-plus'
import HerbLeafIcon from '@/components/icons/HerbLeafIcon.vue'
import ModuleHerbIcon from '@/components/icons/ModuleHerbIcon.vue'

const stats = ref({
  todayPres: 0,
  qualifiedRate: 0,
  todayErrors: 0,
  pendingPres: 0
})

const recentRecords = ref([])
const loading = ref(false)
const updatedAt = ref(new Date())

const updateTimeText = computed(() => {
  const date = updatedAt.value
  if (!date) return '--'
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
})

const statusDistribution = computed(() => {
  const rows = recentRecords.value || []
  const total = rows.length || 1
  const summary = {
    checked: 0,
    checking: 0,
    abnormal: 0,
    pending: 0
  }

  rows.forEach((item) => {
    if (item.status === 2) summary.checked += 1
    else if (item.status === 4) summary.checking += 1
    else if (item.status === 3) summary.abnormal += 1
    else summary.pending += 1
  })

  const source = [
    { key: 'checked', label: '已复核', value: summary.checked, color: '#789262' },
    { key: 'checking', label: '复核中', value: summary.checking, color: '#9eb287' },
    { key: 'pending', label: '未复核', value: summary.pending, color: '#c6c0b0' },
    { key: 'abnormal', label: '复核异常', value: summary.abnormal, color: '#b22222' }
  ]

  return source.map((item) => ({
    ...item,
    percentage: Math.round((item.value / total) * 100)
  }))
})

onMounted(() => {
  loadDashboardData()
})

const loadDashboardData = async () => {
  loading.value = true
  try {
    const res = await getDashboardOverview()
    if (res.code === '0000') {
      stats.value = {
        todayPres: res.data.todayPres || 0,
        qualifiedRate: res.data.qualifiedRate || 0,
        todayErrors: res.data.todayErrors || 0,
        pendingPres: res.data.pendingPres || 0
      }
      recentRecords.value = res.data.recentRecords || []
      updatedAt.value = new Date()
    } else {
      ElMessage.error(res.msg || '工作台数据加载失败')
    }
  } catch (error) {
    ElMessage.error('工作台数据加载失败：' + error.message)
  } finally {
    loading.value = false
  }
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
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-card {
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.08) 0%, rgba(120, 146, 98, 0.01) 55%);
}

.overview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.overview-head h2 {
  font-size: 24px;
  color: #2f3a2b;
  line-height: 1.3;
}

.overview-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary-dark-2);
  background: rgba(120, 146, 98, 0.12);
  border: 1px solid rgba(120, 146, 98, 0.24);
}

.overview-head p {
  margin-top: 6px;
  color: #617058;
  font-size: 13px;
}

.update-meta {
  min-width: 180px;
  text-align: right;
}

.update-meta span {
  display: block;
  color: #6a7461;
  font-size: 12px;
}

.update-meta strong {
  display: block;
  margin-top: 6px;
  color: #2f3a2b;
  font-size: 16px;
  font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
}

.stats-row,
.content-row {
  margin: 0 !important;
}

.stat-card {
  border: 1px solid var(--el-border-color-light);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(120, 146, 98, 0.12);
}

.stat-icon {
  font-size: 22px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2f3a2b;
  line-height: 1;
}

.stat-label {
  color: #667161;
  font-size: 13px;
  margin-top: 8px;
}

.card-pres .stat-icon-wrap {
  color: #4a7023;
}

.card-rate .stat-icon-wrap {
  color: #5a7f3a;
}

.card-pending .stat-icon-wrap {
  color: #83785f;
}

.card-error .stat-icon-wrap {
  color: #b22222;
  background: rgba(178, 34, 34, 0.1);
}

.quick-card {
  margin-top: 16px;
}

.quick-actions,
.viz-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.viz-item {
  padding: 8px 10px;
  border: 1px solid #ebe7dc;
  border-radius: 6px;
  background: #faf9f5;
}

.viz-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #4e5c49;
  font-size: 13px;
}

.viz-label strong {
  color: #2f3a2b;
  font-size: 12px;
}

.quick-actions :deep(.el-button) {
  height: 40px;
  width: 100%;
  justify-content: flex-start;
  padding: 0 14px;
  box-sizing: border-box;
}

.quick-actions :deep(.el-button .el-icon) {
  margin-right: 6px;
}

.quick-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.table-card :deep(.el-tag--success),
.table-card :deep(.el-tag--warning),
.table-card :deep(.el-tag--danger),
.table-card :deep(.el-tag--info) {
  border-radius: 4px;
  font-weight: 500;
}
</style>
