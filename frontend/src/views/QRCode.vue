<template>
  <div class="qrcode-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>二维码生成</span>
          <el-button type="primary" size="small" @click="handleBatchGenerate">批量生成</el-button>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
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
          <el-col :span="12">
            <el-form-item label="院内编码" prop="cjId">
              <el-input v-model="form.cjId" placeholder="请输入院内编码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规格" prop="spec">
              <el-input v-model="form.spec" placeholder="如：5g">
                <template #append>g</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="批号" prop="batchNo">
              <el-input v-model="form.batchNo" placeholder="5-10位数字" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数量" prop="num">
              <el-input-number v-model="form.num" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
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

    <el-card style="margin-top: 20px">
      <template #header>
        <span>二维码历史记录</span>
      </template>
      <el-table :data="historyList" stripe>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { generateQRCode, getQRCodeHistory } from '@/api'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const generating = ref(false)
const qrcodeUrl = ref('')
const qrcodeContent = ref('')
const base64Str = ref('')

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
        const res = await generateQRCode(data)
        if (res.code === '0000') {
          qrcodeUrl.value = res.data.qrcode_url
          qrcodeContent.value = res.data.qrcode_content
          base64Str.value = res.data.base64_str
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
  ElMessage.info('批量生成功能开发中')
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
            qrcodeId: item.qrcode_id,
            cjId: item.cj_id,
            spec: item.spec,
            batchNo: item.batch_no,
            generateTime: item.generate_time,
            qrcodeUrl: item.qrcode_url,
            qrcodeContent: item.qrcode_origin,
            base64Str: item.base64_str
          }))
        }
  } catch (error) {
    console.error('加载历史记录失败', error)
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.qrcode-result {
  padding: 20px;
}

.qrcode-preview {
  text-align: center;
  margin: 20px 0;
}

.qrcode-preview img {
  max-width: 200px;
  border: 1px solid #ddd;
  padding: 10px;
}
</style>
