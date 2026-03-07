<template>
  <div class="qrcode-page">
    <el-card class="module-card">
      <template #header>
        <div class="card-header">
          <span>二维码生成</span>
          <el-button type="primary" size="small" @click="handleBatchGenerate">批量生成</el-button>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="generator-form">
        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="企业标志" prop="enterpriseCode">
              <el-select v-model="form.enterpriseCode" placeholder="请选择企业" style="width: 100%">
                <el-option
                  v-for="ent in enterprises"
                  :key="ent.code"
                  :label="ent.name"
                  :value="ent.code"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="院内编码" prop="cjId">
              <el-input v-model="form.cjId" placeholder="请输入院内编码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="规格" prop="spec">
              <el-input v-model="form.spec" placeholder="如：5g">
                <template #append>g</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="批号" prop="batchNo">
              <el-input v-model="form.batchNo" placeholder="5-10位数字" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="数量" prop="num">
              <el-input-number v-model="form.num" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="重量(kg)" prop="weight">
              <el-input-number v-model="form.weight" :min="0" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="handleGenerate">生成二维码</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="qrcodeUrl" class="qrcode-result">
        <h4>生成结果</h4>
        <div class="qrcode-preview">
          <img :src="qrcodeUrl" alt="二维码" />
        </div>
        <p><strong>原始内容：</strong>{{ qrcodeContent }}</p>
        <p><strong>Base64编码：</strong>{{ base64Str }}</p>
        <el-button type="primary" @click="handleDownload">下载二维码</el-button>
      </div>
    </el-card>

    <el-card class="module-card history-card">
      <template #header>
        <span>二维码历史记录</span>
      </template>
      <el-table :data="historyList" stripe class="history-table">
        <el-table-column prop="qrcodeId" label="二维码ID" />
        <el-table-column prop="cjId" label="院内编码" />
        <el-table-column prop="spec" label="规格" />
        <el-table-column prop="batchNo" label="批号" />
        <el-table-column prop="generateTime" label="生成时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="batchDialogVisible" title="批量生成二维码" width="500px">
      <el-form label-width="100px">
        <el-form-item label="批量数量">
          <el-input-number v-model="batchCount" :min="1" :max="100" />
        </el-form-item>
        <el-alert
          title="将基于当前表单参数批量生成，批号会在当前批号基础上自动递增。"
          type="info"
          :closable="false"
        />
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleConfirmBatchGenerate">开始生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { generateQRCode, generateBatchQRCode, getQRCodeHistory } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const formRef = ref(null)
const generating = ref(false)
const qrcodeUrl = ref('')
const qrcodeContent = ref('')
const base64Str = ref('')
const batchDialogVisible = ref(false)
const batchCount = ref(10)

const enterprises = ref([
  { code: 1, name: '亳州市沪谯药业有限公司' },
  { code: 2, name: '湖南三湘中药饮片有限公司' },
  { code: 3, name: '长沙新林制药有限公司' },
  { code: 4, name: '安徽亳药千草中药饮片有限公司' },
  { code: 5, name: '北京仟草中药饮片有限公司' },
  { code: 6, name: '天津尚药堂制药有限公司' }
])

const form = reactive({
  enterpriseCode: '',
  cjId: '',
  spec: '',
  batchNo: '',
  num: 7,
  weight: 0
})

const rules = {
  enterpriseCode: [{ required: true, message: '请选择企业', trigger: 'change' }],
  cjId: [{ required: true, message: '请输入院内编码', trigger: 'blur' }],
  spec: [
    { required: true, message: '请输入规格', trigger: 'blur' },
    { pattern: /^\d+(\.\d+)?$/, message: '规格必须为数字', trigger: 'blur' }
  ],
  batchNo: [
    { required: true, message: '请输入批号', trigger: 'blur' },
    { pattern: /^\d{5,10}$/, message: '批号为5-10位数字', trigger: 'blur' }
  ]
}

const historyList = ref([])

const handleGenerate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      generating.value = true
      try {
        const data = { ...form, spec: form.spec + 'g', createBy: 'current_user' }
        data.createBy = userStore.userInfo.userAccount || 'admin'
        const res = await generateQRCode(data)
        if (res.code === '0000') {
          qrcodeUrl.value = res.data.qrcodeUrl
          qrcodeContent.value = res.data.qrcodeContent
          base64Str.value = res.data.base64Str
          ElMessage.success('生成成功')
          loadHistory()
        } else {
          ElMessage.error(res.msg || '生成失败')
        }
      } catch (error) {
        ElMessage.error('生成失败：' + error.message)
      } finally {
        generating.value = false
      }
    }
  })
}

const handleReset = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  qrcodeUrl.value = ''
  qrcodeContent.value = ''
  base64Str.value = ''
}

const handleDownload = () => {
  if (!qrcodeUrl.value) return
  const link = document.createElement('a')
  link.href = qrcodeUrl.value
  link.download = 'qrcode.png'
  link.click()
}

const handleBatchGenerate = () => {
  if (!form.enterpriseCode || !form.cjId || !form.spec || !form.batchNo || !form.num || !form.weight) {
    ElMessage.warning('请先完善上方二维码参数后再批量生成')
    return
  }
  batchDialogVisible.value = true
}

const handleConfirmBatchGenerate = async () => {
  generating.value = true
  try {
    const width = String(form.batchNo).length
    const baseBatch = Number(form.batchNo)
    const qrcodeList = Array.from({ length: batchCount.value }).map((_, index) => {
      const batchNo = Number.isFinite(baseBatch)
        ? String(baseBatch + index).padStart(width, '0')
        : form.batchNo
      return {
        enterpriseCode: form.enterpriseCode,
        cjId: form.cjId,
        spec: form.spec + 'g',
        batchNo,
        num: form.num,
        weight: form.weight
      }
    })

    const res = await generateBatchQRCode({
      createBy: userStore.userInfo.userAccount || 'admin',
      qrcodeList
    })

    if (res.code === '0000') {
      ElMessage.success(`批量生成完成：成功 ${res.data.successNum} 条，失败 ${res.data.failNum} 条`)
      batchDialogVisible.value = false
      loadHistory()
    } else {
      ElMessage.error(res.msg || '批量生成失败')
    }
  } catch (error) {
    ElMessage.error('批量生成失败：' + error.message)
  } finally {
    generating.value = false
  }
}

const handleView = (row) => {
  qrcodeUrl.value = row.qrcodeUrl
  qrcodeContent.value = row.qrcodeContent
  base64Str.value = row.base64Str
}

const loadHistory = async () => {
  try {
        const res = await getQRCodeHistory({ page: 1, size: 10 })
        if (res.code === '0000') {
          historyList.value = (res.data.list || []).map(item => ({
            qrcodeId: item.qrcodeId,
            cjId: item.cjId,
            spec: item.spec,
            batchNo: item.batchNo,
            generateTime: item.generateTime,
            qrcodeUrl: item.qrcodeUrl,
            qrcodeContent: item.qrcodeOrigin,
            base64Str: item.base64Str
          }))
        } else {
          ElMessage.error(res.msg || '历史记录加载失败')
        }
  } catch (error) {
    ElMessage.error('历史记录加载失败：' + error.message)
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.qrcode-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.1) 0%, rgba(120, 146, 98, 0.02) 58%);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.generator-form {
  padding: 6px 0 10px;
}

.generator-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.generator-form :deep(.el-form-item__content) {
  min-height: 38px;
}

.generator-form :deep(.el-form-item__error) {
  position: static;
  padding-top: 6px;
  line-height: 1.35;
}

.form-row {
  row-gap: 2px;
}

.generator-form :deep(.el-form-item:last-child) {
  margin-bottom: 6px;
}

.qrcode-result {
  margin-top: 6px;
  padding: 18px;
  border: 1px solid #e7e2d6;
  border-radius: 6px;
  background: #faf9f5;
}

.qrcode-result h4 {
  margin-bottom: 10px;
  color: #3d4a36;
  font-size: 15px;
}

.qrcode-preview {
  text-align: center;
  margin: 16px 0;
}

.qrcode-preview img {
  max-width: 200px;
  border: 1px solid #d6d0c2;
  border-radius: 6px;
  background: #fff;
  padding: 10px;
}

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}
</style>
