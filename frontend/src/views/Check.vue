<template>
  <div class="check-page">
    <el-card class="module-card">
      <template #header>
        <span>扫码复核</span>
      </template>
      <el-form :inline="true" class="init-form">
        <el-form-item label="处方号">
          <el-input v-model="presNo" placeholder="请输入处方号" clearable @keyup.enter="handleInit" />
        </el-form-item>
        <el-form-item label="复核台">
          <el-input v-model="checkStation" placeholder="如：T01" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleInit">初始化</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="initialized">
        <el-alert
          title="处方信息"
          type="info"
          :closable="false"
          class="prescription-alert"
        >
          <p>处方号：{{ prescription.presNo }}</p>
          <p>患者姓名：{{ prescription.patientName }}</p>
          <p>开方医生：{{ prescription.docName }}</p>
          <p>复核人员：{{ currentUser }}</p>
        </el-alert>

        <el-form :inline="true" class="scan-form">
          <el-form-item label="筐号">
            <el-select v-model="currentBasket" placeholder="请选择筐号" style="width: 200px">
              <el-option
                v-for="basket in baskets"
                :key="basket"
                :label="basket"
                :value="basket"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="扫码">
            <el-input
              v-model="scanContent"
              placeholder="扫描二维码"
              clearable
              @keyup.enter="handleScan"
            >
              <template #append>
                <el-button icon="Scan" @click="handleScan" />
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="success" @click="handleSaveProgress">保存进度</el-button>
            <el-button type="primary" @click="handleSubmit">提交复核</el-button>
          </el-form-item>
        </el-form>

        <el-divider />

        <h4 class="progress-title">复核进度：{{ checkedCount }} / {{ totalCount }}</h4>
        <el-progress :percentage="progressPercentage" :status="progressStatus" />

        <el-table :data="drugList" stripe class="check-table">
          <el-table-column prop="cjId" label="院内编码" />
          <el-table-column prop="drugName" label="药品名称" />
          <el-table-column prop="spec" label="规格" />
          <el-table-column prop="presNum" label="处方数量" />
          <el-table-column prop="scanNum" label="扫码数量" />
          <el-table-column label="状态">
            <template #default="{ row }">
              <el-tag :type="row.isCheck ? 'success' : 'info'">
                {{ row.isCheck ? '已复核' : '未复核' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { initCheck, scanCheck, saveProgress, submitCheck, getBasketList } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()

const presNo = ref('')
const checkStation = ref('T01')
const initialized = ref(false)
const scanContent = ref('')
const currentBasket = ref('')
const currentUser = computed(() => userStore.userInfo.userAccount || 'admin')

const prescription = ref({})
const drugList = ref([])
const baskets = ref([])

const checkedCount = computed(() => drugList.value.filter(item => item.isCheck).length)
const totalCount = computed(() => drugList.value.length)
const progressPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((checkedCount.value / totalCount.value) * 100)
})
const progressStatus = computed(() => {
  if (progressPercentage.value === 100) return 'success'
  if (progressPercentage.value > 0) return ''
  return 'exception'
})

const loadBasketOptions = async () => {
  try {
    const res = await getBasketList({ status: 1 })
    if (res.code === '0000') {
      baskets.value = (res.data.list || []).map(item => item.basketNo)
      if (!currentBasket.value && baskets.value.length > 0) {
        currentBasket.value = baskets.value[0]
      }
    }
  } catch {
    // 静默处理，避免影响复核流程
  }
}

const handleInit = async () => {
  if (!presNo.value) {
    ElMessage.warning('请输入处方号')
    return
  }
  try {
    const res = await initCheck({
      presNo: presNo.value,
      checkBy: currentUser.value,
      checkStation: checkStation.value
    })
    if (res.code === '0000') {
      prescription.value = res.data.prescription || {
        presNo: res.data.presNo,
        patientName: '-',
        docName: '-'
      }
      const list = Array.isArray(res.data.drugList) ? res.data.drugList : []
      drugList.value = list.map(item => ({
        ...item,
        scanNum: item.scanNum || 0,
        isCheck: !!item.isCheck
      }))
      if (Array.isArray(res.data.baskets) && res.data.baskets.length > 0) {
        baskets.value = res.data.baskets
        if (!currentBasket.value) {
          currentBasket.value = baskets.value[0]
        }
      }
      initialized.value = true
      ElMessage.success(res.data.status === 'inProgress' ? '已恢复复核进度' : '初始化成功')
    } else {
      ElMessage.error(res.msg || '初始化失败')
    }
  } catch (error) {
    ElMessage.error('初始化失败：' + error.message)
  }
}

const handleScan = async () => {
  if (!scanContent.value) {
    ElMessage.warning('请扫描二维码')
    return
  }
  if (!currentBasket.value) {
    ElMessage.warning('请选择筐号')
    return
  }
  try {
    const res = await scanCheck({
      presNo: presNo.value,
      basketNo: currentBasket.value,
      qrcodeContent: scanContent.value,
      checkBy: currentUser.value
    })
    if (res.code === '0000') {
      const payload = res.data || {}
      const drugInfo = payload.drugInfo || {
        cjId: payload.cjId,
        drugName: payload.drugName,
        spec: payload.spec,
        presNum: payload.presNum || 1
      }
      const scanResult = payload.scanResult || payload.scanResultText || payload.scan_result_text || 'match'
      let drug = drugList.value.find(item => item.cjId === drugInfo.cjId)
      if (drug) {
        drug.scanNum += 1
        if (drug.scanNum >= drug.presNum) {
          drug.isCheck = true
        }
      } else if (scanResult === 'match' || scanResult === 'SUCCESS') {
        drug = {
          cjId: drugInfo.cjId,
          drugName: drugInfo.drugName || drugInfo.cjId,
          spec: drugInfo.spec || '-',
          presNum: drugInfo.presNum || 1,
          scanNum: 1,
          isCheck: (drugInfo.presNum || 1) <= 1
        }
        drugList.value.push(drug)
      }
      if (scanResult === 'match' || scanResult === 'SUCCESS') {
        ElMessage.success('扫码成功')
      } else if (scanResult === 'mismatch' || scanResult === 'MISMATCH') {
        ElMessage.warning('药品不匹配')
      } else {
        ElMessage.info('扫码完成')
      }
    } else {
      ElMessage.error(res.msg || '扫码失败')
    }
  } catch (error) {
    ElMessage.error('扫码失败：' + error.message)
  }
  scanContent.value = ''
}

const handleSaveProgress = async () => {
  try {
    const res = await saveProgress({
      presNo: presNo.value,
      checkBy: currentUser.value,
      finishedDrugs: drugList.value.filter(item => item.isCheck).map(item => item.cjId),
      unfinishedDrugs: drugList.value.filter(item => !item.isCheck).map(item => item.cjId),
      currentBasket: currentBasket.value
    })
    if (res.code === '0000') {
      ElMessage.success('进度保存成功')
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

const handleSubmit = async () => {
  if (checkedCount.value < totalCount.value) {
    ElMessage.warning('请完成所有药品复核')
    return
  }
  try {
    await ElMessageBox.confirm('确定提交复核结果吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await submitCheck({
      presNo: presNo.value,
      checkBy: currentUser.value
    })
    if (res.code === '0000') {
      ElMessage.success('提交成功')
      initialized.value = false
    } else {
      ElMessage.error(res.msg || '提交失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败：' + error.message)
    }
  }
}

onMounted(() => {
  loadBasketOptions()
})
</script>

<style scoped>
.check-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.1) 0%, rgba(120, 146, 98, 0.02) 58%);
}

.init-form,
.scan-form {
  padding: 4px 0 8px;
}

.init-form :deep(.el-form-item),
.scan-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.prescription-alert {
  margin-bottom: 18px;
  border-color: #d6dfca;
  background: rgba(120, 146, 98, 0.08);
}

.el-alert p {
  margin: 5px 0;
}

.progress-title {
  margin-bottom: 10px;
  color: #3d4a36;
  font-size: 15px;
}

.check-table {
  margin-top: 18px;
}

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}
</style>
