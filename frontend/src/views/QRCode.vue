<template>
  <div class="qrcode-page">
    <el-card v-if="isGeneratePage" class="module-card">
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
                  :key="ent.enterpriseCode"
                  :label="ent.enterpriseName"
                  :value="ent.enterpriseCode"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="院内品名" prop="cjId">
              <el-select
                v-model="form.cjId"
                filterable
                remote
                clearable
                reserve-keyword
                style="width: 100%"
                placeholder="请输入品名或规格（支持拼音）"
                popper-class="drug-select-dropdown"
                :remote-method="handleDrugSearch"
                :loading="drugLoading"
                @change="handleDrugChange"
                @clear="handleDrugClear"
                @visible-change="handleDrugDropdownVisible"
              >
                <el-option
                  v-for="item in drugOptions"
                  :key="item.cjId"
                  :label="buildDrugOptionLabel(item)"
                  :value="item.cjId"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="院内编码">
              <el-input v-model="form.cjId" readonly placeholder="选择品名后自动带出编码" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="规格" prop="spec">
              <el-input v-model="form.spec" placeholder="如：5">
                <template #append>g</template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="批号" prop="batchNo">
              <el-input v-model="form.batchNo" placeholder="5-10位数字" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="药材产地" prop="drugOrigin">
              <el-input v-model="form.drugOrigin" placeholder="如：湖北麻城" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="form-row">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="生产日期" prop="productionDate">
              <el-date-picker
                v-model="form.productionDate"
                type="date"
                value-format="YYYY-MM-DD"
                format="YYYY.MM.DD"
                placeholder="请选择生产日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="保质期至" prop="expiryDate">
              <el-date-picker
                v-model="form.expiryDate"
                type="date"
                value-format="YYYY-MM-DD"
                format="YYYY.MM.DD"
                placeholder="请选择保质期至"
                style="width: 100%"
              />
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
            <el-form-item label="重量(kg)">
              <el-input-number v-model="form.weight" :min="0" :precision="4" style="width: 100%" :controls="false" readonly />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="form-row">
          <el-col :span="24">
            <el-form-item label="追溯网址" prop="traceUrl">
              <el-input v-model="form.traceUrl" placeholder="如：https://trace.example.com/xxx" />
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
        <div class="result-head">
          <h4>标签预览</h4>
          <el-tag :type="printerConfig.enablePrinter ? 'warning' : 'success'" effect="plain">
            {{ printerModeText }}
          </el-tag>
        </div>
        <p class="result-tip">{{ printerHintText }}</p>

        <LabelPrintCard :label="generatedLabelData" :qrcode-url="qrcodeUrl" />

        <div class="result-actions">
          <el-button type="primary" @click="handleDownload">下载二维码</el-button>
          <el-button type="success" :loading="printing" @click="handlePrint()">打印标签</el-button>
        </div>

        <div class="result-meta">
          <p><strong>追溯网址：</strong>{{ traceUrl }}</p>
          <p><strong>原始内容：</strong>{{ qrcodeContent }}</p>
          <p><strong>Base64编码：</strong>{{ base64Str }}</p>
        </div>
      </div>
    </el-card>

    <el-card v-if="isManagePage" class="module-card printer-card">
      <template #header>
        <span>喷码枪打印配置</span>
      </template>

      <el-form :model="printerConfig" label-width="110px" class="printer-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="启用喷码枪">
              <el-switch v-model="printerConfig.enablePrinter" inline-prompt active-text="开" inactive-text="关" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12" :lg="12">
            <el-form-item label="打印份数">
              <el-input-number v-model="printerConfig.copies" :min="1" :max="20" :step="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          class="printer-mode-alert"
          :title="printerConfig.enablePrinter ? '已启用喷码枪直连打印' : '已切换为浏览器打印标签，无需配置喷码枪参数'"
          :type="printerConfig.enablePrinter ? 'success' : 'info'"
          :closable="false"
        />

        <template v-if="printerConfig.enablePrinter">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="24" :md="12" :lg="12">
              <el-form-item label="打印机IP">
                <el-input v-model="printerConfig.printerHost" placeholder="如：192.168.1.100（可留空仅生成指令）" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="24" :md="12" :lg="12">
              <el-form-item label="端口">
                <el-input-number v-model="printerConfig.printerPort" :min="1" :max="65535" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :xs="24" :sm="24" :md="12" :lg="12">
              <el-form-item label="协议">
                <el-select v-model="printerConfig.printerProtocol" style="width: 100%">
                  <el-option label="ZPL" value="zpl" />
                  <el-option label="TSPL" value="tspl" />
                  <el-option label="RAW" value="raw" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="24" :md="12" :lg="12">
              <el-form-item label="超时(秒)">
                <el-input-number v-model="printerConfig.printerTimeout" :min="1" :max="30" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <el-form-item class="printer-actions">
          <el-button v-if="printerConfig.enablePrinter" :loading="connectionTesting" @click="handleTestConnection">连接测试</el-button>
          <el-button type="primary" plain @click="savePrinterConfig()">保存配置</el-button>
          <el-button @click="resetPrinterConfig">恢复默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="isManagePage" class="module-card history-card">
      <template #header>
        <div class="card-header">
          <span>二维码历史记录</span>
          <div class="history-actions">
            <el-tag type="info" effect="plain">已选 {{ selectedHistoryRows.length }}</el-tag>
            <el-button
              type="success"
              plain
              size="small"
              :loading="batchPrinting"
              :disabled="selectedHistoryRows.length === 0 || printing"
              @click="handleBatchPrint"
            >
              批量打印
            </el-button>
            <el-button size="small" @click="loadHistory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="historyList" stripe class="history-table" row-key="qrcodeId" @selection-change="handleHistorySelectionChange">
        <el-table-column type="selection" width="52" />
        <el-table-column prop="qrcodeId" label="二维码ID" min-width="190" show-overflow-tooltip />
        <el-table-column prop="drugName" label="品名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="drugOrigin" label="药材产地" min-width="120" show-overflow-tooltip />
        <el-table-column prop="labelAmount" label="装量" min-width="120" />
        <el-table-column prop="batchNo" label="批号" min-width="110" />
        <el-table-column prop="productionDateDisplay" label="生产日期" min-width="120" />
        <el-table-column prop="expiryDateDisplay" label="保质期至" min-width="120" />
        <el-table-column prop="generateTime" label="生成时间" min-width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看标签</el-button>
            <el-button link type="success" :loading="printing" :disabled="!row.qrcodeId || batchPrinting" @click="handlePrint(row)">打印</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-if="isManagePage" v-model="previewDialogVisible" title="标签预览" width="720px">
      <LabelPrintCard :label="previewLabelData" :qrcode-url="previewRecord?.qrcodeUrl || ''" compact />
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="printing" @click="handlePrint(previewRecord)">打印标签</el-button>
      </template>
    </el-dialog>

    <el-dialog v-if="isGeneratePage" v-model="batchDialogVisible" title="批量生成二维码" width="500px">
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
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { generateQRCode, generateBatchQRCode, printMergedQRCode, testPrinterConnection, getQRCodeHistory, getEnterpriseList, getQrcodeDrugList } from '@/api'
import LabelPrintCard from '@/components/LabelPrintCard.vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const route = useRoute()

const pageMode = computed(() => route.meta?.qrcodeMode || (route.path.includes('/qrcode/manage') ? 'manage' : 'generate'))
const isGeneratePage = computed(() => pageMode.value === 'generate')
const isManagePage = computed(() => pageMode.value === 'manage')

const formRef = ref(null)
const generating = ref(false)
const printing = ref(false)
const batchPrinting = ref(false)
const connectionTesting = ref(false)
const qrcodeUrl = ref('')
const qrcodeContent = ref('')
const base64Str = ref('')
const traceUrl = ref('')
const latestQrcodeId = ref('')
const batchDialogVisible = ref(false)
const batchCount = ref(10)
const selectedHistoryRows = ref([])
const generatedRecord = ref(null)
const previewDialogVisible = ref(false)
const previewRecord = ref(null)
const PRINTER_CONFIG_STORAGE_KEY = 'qrcodePrinterConfig'
const BROWSER_PRINT_TIP_STORAGE_KEY = 'qrcodeBrowserPrintTipShown'

const printerConfig = reactive({
  enablePrinter: false,
  printerHost: '',
  printerPort: 9100,
  printerProtocol: 'zpl',
  printerTimeout: 3,
  copies: 1
})

const enterprises = ref([])
const drugOptions = ref([])
const drugLoading = ref(false)
const drugLoadingMore = ref(false)
const drugKeyword = ref('')
const drugPage = ref(1)
const drugHasMore = ref(true)
const historyList = ref([])
const DRUG_PAGE_SIZE = 30
let drugDropdownWrapEl = null

const form = reactive({
  enterpriseCode: '',
  cjId: '',
  spec: '',
  batchNo: '',
  drugOrigin: '',
  productionDate: '',
  expiryDate: '',
  num: 7,
  weight: 0,
  traceUrl: ''
})

const rules = {
  enterpriseCode: [{ required: true, message: '请选择企业', trigger: 'change' }],
  cjId: [{ required: true, message: '请选择院内品名', trigger: 'change' }],
  spec: [
    { required: true, message: '请输入规格', trigger: 'blur' },
    { pattern: /^\d+(\.\d+)?$/, message: '规格必须为数字', trigger: 'blur' }
  ],
  batchNo: [
    { required: true, message: '请输入批号', trigger: 'blur' },
    { pattern: /^\d{5,10}$/, message: '批号为5-10位数字', trigger: 'blur' }
  ],
  drugOrigin: [{ required: true, message: '请输入药材产地', trigger: 'blur' }],
  productionDate: [{ required: true, message: '请选择生产日期', trigger: 'change' }],
  expiryDate: [{ required: true, message: '请选择保质期至', trigger: 'change' }],
  traceUrl: [
    { required: true, message: '请输入追溯网址', trigger: 'blur' },
    { pattern: /^https?:\/\//, message: '追溯网址需以 http:// 或 https:// 开头', trigger: 'blur' }
  ]
}

const selectedDrug = computed(() => drugOptions.value.find(item => item.cjId === form.cjId) || null)

const printerModeText = computed(() => (printerConfig.enablePrinter ? '喷码枪直连打印' : '浏览器打印标签'))

const printerHintText = computed(() => {
  if (printerConfig.enablePrinter) {
    return '打印时会把标签指令直接发送到已配置喷码枪。'
  }
  return '打印时会打开浏览器打印窗口，不需要配置喷码枪参数。'
})

const normalizeSpecText = (spec) => {
  const raw = String(spec || '').trim()
  if (!raw) return ''
  return /g$/i.test(raw) ? raw : `${raw}g`
}

const formatDateDisplay = (value, precision = 'day') => {
  const raw = String(value || '').trim()
  if (!raw) return '--'
  if (precision === 'month' && /^\d{4}年\d{1,2}月$/.test(raw)) return raw
  if (precision === 'day' && /^\d{4}\.\d{2}\.\d{2}$/.test(raw)) return raw
  if (precision === 'month') {
    const dottedMatch = raw.match(/^(\d{4})\.(\d{2})\.(\d{2})$/)
    if (dottedMatch) {
      return `${dottedMatch[1]}年${Number(dottedMatch[2])}月`
    }
    const monthMatch = raw.match(/^(\d{4})[-/.](\d{1,2})$/)
    if (monthMatch) {
      return `${monthMatch[1]}年${Number(monthMatch[2])}月`
    }
  }

  const normalized = raw.replace(/\//g, '-')
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    const [year, month, day] = normalized.split('-')
    if (precision === 'month') {
      return `${year}年${Number(month)}月`
    }
    return `${year}.${month}.${day}`
  }

  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return raw
  }

  const year = parsed.getFullYear()
  const month = `${parsed.getMonth() + 1}`.padStart(2, '0')
  const day = `${parsed.getDate()}`.padStart(2, '0')
  if (precision === 'month') {
    return `${year}年${Number(month)}月`
  }
  return `${year}.${month}.${day}`
}

const formatLabelAmount = ({ spec, num, unit }) => {
  const specText = normalizeSpecText(spec)
  if (!specText) return '--'

  const count = Number(num)
  const displayUnit = String(unit || '袋').trim() || '袋'
  if (!Number.isFinite(count) || count <= 0) {
    return specText
  }

  return `${specText}*${Math.trunc(count)}${displayUnit}`
}

const buildCurrentGeneratedRecord = () => ({
  qrcodeId: latestQrcodeId.value,
  qrcodeContent: qrcodeContent.value,
  qrcodeUrl: qrcodeUrl.value,
  traceUrl: traceUrl.value,
  drugName: selectedDrug.value?.drugName || '',
  drugOrigin: form.drugOrigin,
  spec: normalizeSpecText(form.spec),
  num: form.num,
  unit: selectedDrug.value?.unit || '袋',
  batchNo: form.batchNo,
  productionDate: form.productionDate,
  expiryDate: form.expiryDate,
  labelAmount: formatLabelAmount({
    spec: form.spec,
    num: form.num,
    unit: selectedDrug.value?.unit
  })
})

const buildLabelData = (source = {}) => {
  const fallbackDrugName = selectedDrug.value?.drugName || (source?.cjId ? `CJID:${source.cjId}` : '')
  const fallbackUnit = selectedDrug.value?.unit || source?.unit || '袋'

  return {
    drugName: String(source?.drugName || fallbackDrugName || '--').trim() || '--',
    drugOrigin: String(source?.drugOrigin || form.drugOrigin || '--').trim() || '--',
    labelAmount: String(
      source?.labelAmount ||
      formatLabelAmount({
        spec: source?.spec ?? form.spec,
        num: source?.num ?? form.num,
        unit: source?.unit || fallbackUnit
      })
    ).trim() || '--',
    batchNo: String(source?.batchNo || form.batchNo || '--').trim() || '--',
    productionDate: formatDateDisplay(source?.productionDateDisplay || source?.productionDate || form.productionDate, 'day'),
    expiryDate: formatDateDisplay(source?.expiryDateDisplay || source?.expiryDate || form.expiryDate, 'month')
  }
}

const generatedLabelData = computed(() => buildLabelData(generatedRecord.value || buildCurrentGeneratedRecord()))
const previewLabelData = computed(() => buildLabelData(previewRecord.value || {}))

const calculateWeight = () => {
  const specNum = Number(form.spec)
  const num = Number(form.num)
  if (!Number.isFinite(specNum) || specNum <= 0 || !Number.isFinite(num) || num <= 0) {
    form.weight = 0
    return
  }
  form.weight = Number((specNum * num / 1000).toFixed(4))
}

watch(() => [form.spec, form.num], calculateWeight, { immediate: true })

const unbindDrugDropdownScroll = () => {
  if (drugDropdownWrapEl) {
    drugDropdownWrapEl.removeEventListener('scroll', handleDrugDropdownScroll)
    drugDropdownWrapEl = null
  }
}

const bindDrugDropdownScroll = async () => {
  await nextTick()
  const wrap = document.querySelector('.drug-select-dropdown .el-select-dropdown__wrap')
  if (!wrap || wrap === drugDropdownWrapEl) return
  unbindDrugDropdownScroll()
  drugDropdownWrapEl = wrap
  drugDropdownWrapEl.addEventListener('scroll', handleDrugDropdownScroll)
}

const fetchDrugOptions = async ({ append = false } = {}) => {
  if (append) {
    if (drugLoadingMore.value || !drugHasMore.value) return
    drugLoadingMore.value = true
  } else {
    drugLoading.value = true
  }

  try {
    const res = await getQrcodeDrugList({
      keyword: drugKeyword.value,
      page: drugPage.value,
      size: DRUG_PAGE_SIZE
    })
    if (res.code !== '0000') {
      ElMessage.error(res.msg || '院内药品加载失败')
      return
    }

    const list = (res.data?.list || []).map(item => ({
      cjId: item.cjId,
      drugName: item.drugName,
      specRange: item.specRange,
      unit: item.unit || '袋',
      displayName: item.displayName || `${item.drugName || ''} ${item.specRange || ''}`.trim()
    }))

    if (append) {
      const exists = new Set(drugOptions.value.map(item => item.cjId))
      drugOptions.value = drugOptions.value.concat(list.filter(item => !exists.has(item.cjId)))
    } else {
      drugOptions.value = list
    }

    drugHasMore.value = !!res.data?.hasMore
  } catch (error) {
    ElMessage.error('院内药品加载失败：' + error.message)
  } finally {
    if (append) {
      drugLoadingMore.value = false
    } else {
      drugLoading.value = false
    }
  }
}

const buildDrugOptionLabel = (item) => {
  if (!item) return ''
  return item.displayName || `${item.drugName || ''} ${item.specRange || ''}`.trim()
}

const extractSpecValue = (specRange) => {
  const raw = String(specRange || '').trim().toLowerCase()
  if (!raw) return ''

  const gMatch = raw.match(/(\d+(?:\.\d+)?)\s*g/)
  if (gMatch?.[1]) return gMatch[1]

  const numberMatch = raw.match(/(\d+(?:\.\d+)?)/)
  if (numberMatch?.[1]) return numberMatch[1]

  return ''
}

const handleDrugSearch = (query) => {
  drugKeyword.value = (query || '').trim()
  drugPage.value = 1
  drugHasMore.value = true
  fetchDrugOptions({ append: false })
}

const handleDrugDropdownScroll = () => {
  if (!drugDropdownWrapEl || drugLoading.value || drugLoadingMore.value || !drugHasMore.value) return
  const nearBottom = drugDropdownWrapEl.scrollHeight - (drugDropdownWrapEl.scrollTop + drugDropdownWrapEl.clientHeight) <= 12
  if (!nearBottom) return
  drugPage.value += 1
  fetchDrugOptions({ append: true })
}

const handleDrugDropdownVisible = (visible) => {
  if (!visible) {
    unbindDrugDropdownScroll()
    return
  }
  bindDrugDropdownScroll()
  if (drugOptions.value.length === 0) {
    drugPage.value = 1
    drugHasMore.value = true
    fetchDrugOptions({ append: false })
  }
}

const handleDrugChange = (value) => {
  if (!value) {
    form.cjId = ''
    form.spec = ''
    return
  }

  const selected = drugOptions.value.find(item => item.cjId === value)
  form.cjId = selected?.cjId || String(value)
  form.spec = extractSpecValue(selected?.specRange)
}

const handleDrugClear = () => {
  form.cjId = ''
  form.spec = ''
}

const loadEnterprises = async () => {
  try {
    const res = await getEnterpriseList({ status: 1 })
    if (res.code !== '0000') {
      ElMessage.error(res.msg || '企业列表加载失败')
      return
    }
    enterprises.value = res.data?.list || []
    if (!form.enterpriseCode && enterprises.value.length > 0) {
      form.enterpriseCode = enterprises.value[0].enterpriseCode
    }
  } catch (error) {
    ElMessage.error('企业列表加载失败：' + error.message)
  }
}

const handleGenerate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    generating.value = true
    try {
      const data = {
        ...form,
        spec: normalizeSpecText(form.spec)
      }
      const res = await generateQRCode(data)
      if (res.code === '0000') {
        qrcodeUrl.value = res.data.qrcodeUrl
        qrcodeContent.value = res.data.qrcodeContent
        base64Str.value = res.data.base64Str
        traceUrl.value = res.data.traceUrl || form.traceUrl
        latestQrcodeId.value = res.data.qrcodeId || ''
        generatedRecord.value = {
          ...buildCurrentGeneratedRecord(),
          ...res.data
        }
        ElMessage.success('生成成功')
      } else {
        ElMessage.error(res.msg || '生成失败')
      }
    } catch (error) {
      ElMessage.error('生成失败：' + error.message)
    } finally {
      generating.value = false
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
  traceUrl.value = ''
  latestQrcodeId.value = ''
  generatedRecord.value = null
}

const handleDownload = () => {
  if (!qrcodeUrl.value) return
  const link = document.createElement('a')
  link.href = qrcodeUrl.value
  link.download = 'qrcode.png'
  link.click()
}

const normalizePrinterConfig = () => {
  const normalizedPort = Number(printerConfig.printerPort)
  const normalizedTimeout = Number(printerConfig.printerTimeout)
  const normalizedCopies = Number(printerConfig.copies)

  printerConfig.enablePrinter = Boolean(printerConfig.enablePrinter)
  printerConfig.printerHost = String(printerConfig.printerHost || '').trim()
  printerConfig.printerPort = Number.isFinite(normalizedPort) ? Math.min(Math.max(Math.trunc(normalizedPort), 1), 65535) : 9100
  printerConfig.printerTimeout = Number.isFinite(normalizedTimeout) ? Math.min(Math.max(Math.trunc(normalizedTimeout), 1), 30) : 3
  printerConfig.copies = Number.isFinite(normalizedCopies) ? Math.min(Math.max(Math.trunc(normalizedCopies), 1), 20) : 1
  if (!['zpl', 'tspl', 'raw'].includes(printerConfig.printerProtocol)) {
    printerConfig.printerProtocol = 'zpl'
  }
}

const loadPrinterConfig = () => {
  try {
    const raw = localStorage.getItem(PRINTER_CONFIG_STORAGE_KEY)
    if (!raw) {
      return
    }

    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return
    }

    printerConfig.enablePrinter = parsed.enablePrinter ?? Boolean(parsed.printerHost)
    printerConfig.printerHost = parsed.printerHost || ''
    printerConfig.printerPort = parsed.printerPort ?? 9100
    printerConfig.printerProtocol = parsed.printerProtocol || 'zpl'
    printerConfig.printerTimeout = parsed.printerTimeout ?? 3
    printerConfig.copies = parsed.copies ?? 1
    normalizePrinterConfig()
  } catch {
    printerConfig.enablePrinter = false
    printerConfig.printerHost = ''
    printerConfig.printerPort = 9100
    printerConfig.printerProtocol = 'zpl'
    printerConfig.printerTimeout = 3
    printerConfig.copies = 1
  }
}

const savePrinterConfig = (showMessage = true) => {
  normalizePrinterConfig()
  localStorage.setItem(PRINTER_CONFIG_STORAGE_KEY, JSON.stringify({
    enablePrinter: printerConfig.enablePrinter,
    printerHost: printerConfig.printerHost,
    printerPort: printerConfig.printerPort,
    printerProtocol: printerConfig.printerProtocol,
    printerTimeout: printerConfig.printerTimeout,
    copies: printerConfig.copies
  }))
  if (showMessage) {
    ElMessage.success('打印配置已保存')
  }
}

const resetPrinterConfig = () => {
  printerConfig.enablePrinter = false
  printerConfig.printerHost = ''
  printerConfig.printerPort = 9100
  printerConfig.printerProtocol = 'zpl'
  printerConfig.printerTimeout = 3
  printerConfig.copies = 1
  savePrinterConfig()
}

const handleTestConnection = async () => {
  savePrinterConfig(false)

  if (!printerConfig.enablePrinter) {
    ElMessage.warning('当前已关闭喷码枪直连打印')
    return
  }

  if (!printerConfig.printerHost) {
    ElMessage.warning('请先填写打印机IP')
    return
  }

  connectionTesting.value = true
  try {
    const res = await testPrinterConnection({
      printerHost: printerConfig.printerHost,
      printerPort: printerConfig.printerPort,
      printerTimeout: printerConfig.printerTimeout
    })

    if (res.code === '0000') {
      ElMessage.success(res.msg || '连接测试成功')
      return
    }

    ElMessage.error(res.msg || '连接测试失败')
  } catch (error) {
    ElMessage.error('连接测试失败：' + error.message)
  } finally {
    connectionTesting.value = false
  }
}

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const toAbsoluteAssetUrl = (url) => {
  const raw = String(url || '').trim()
  if (!raw) return ''
  if (/^https?:\/\//i.test(raw)) return raw
  return `${window.location.origin}${raw.startsWith('/') ? raw : `/${raw}`}`
}

const buildBrowserPrintHtml = (items) => {
  const buildLabelRowHtml = (label, value) => `
    <div class="print-label__row">
      <span class="print-label__label-group">
        <span class="print-label__label-text">${escapeHtml(label)}</span>
        <span class="print-label__label-colon">：</span>
      </span>
      <span class="print-label__value">${escapeHtml(value)}</span>
    </div>
  `

  const cards = items.map(item => `
    <section class="print-label">
      <div class="print-label__main">
        <div class="print-label__content">
          ${buildLabelRowHtml('品　名', item.label.drugName)}
          ${buildLabelRowHtml('药材产地', item.label.drugOrigin)}
          ${buildLabelRowHtml('装　量', item.label.labelAmount)}
          ${buildLabelRowHtml('产品批号', item.label.batchNo)}
          ${buildLabelRowHtml('生产日期', item.label.productionDate)}
          ${buildLabelRowHtml('保质期至', item.label.expiryDate)}
        </div>
        <div class="print-label__qr">
          ${item.qrcodeUrl ? `<img src="${escapeHtml(item.qrcodeUrl)}" alt="标签二维码" />` : '<div class="print-label__qr-placeholder">待生成二维码</div>'}
        </div>
      </div>
      <div class="print-label__stamp">质量合格</div>
    </section>
  `).join('')

  return `<!DOCTYPE html>
  <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <title></title>
      <style>
        @page {
          size: A4 portrait;
          margin: 0 !important;
        }

        * {
          box-sizing: border-box;
        }

        html,
        body {
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 0;
        }

        body {
          font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
          background: #f2f4f8;
          color: #111;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        .print-sheet {
          width: 210mm;
          min-height: 297mm;
          margin: 0 auto;
          padding: 1.5mm 2mm;
          display: flex;
          flex-wrap: wrap;
          align-content: flex-start;
          gap: 2mm;
          background: #fff;
          box-shadow: 0 8px 22px rgba(31, 47, 66, 0.16);
        }

        .print-label {
          width: 50mm;
          height: 35mm;
          min-height: 35mm;
          display: flex;
          flex-direction: column;
          padding: 2mm 2.2mm 2mm;
          border: none;
          background: #fff;
          break-inside: avoid;
          page-break-inside: avoid;
          box-shadow: none;
          overflow: hidden;
        }

        .print-label__main {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 14.4mm;
          gap: 1.5mm;
          align-items: start;
          flex: 1 1 auto;
          min-height: 0;
        }

        .print-label__content {
          display: flex;
          flex-direction: column;
          gap: 0.55mm;
          padding-top: 0;
        }

        .print-label__row {
          display: grid;
          grid-template-columns: 13.4mm minmax(0, 1fr);
          gap: 0.6mm;
          align-items: baseline;
          font-size: 6.9pt;
          line-height: 1.04;
          font-weight: 800;
        }

        .print-label__label-group {
          display: grid;
          grid-template-columns: 11.6mm 1.6mm;
          align-items: baseline;
        }

        .print-label__label-text {
          white-space: pre;
          letter-spacing: 0.02em;
        }

        .print-label__label-colon {
          display: inline-flex;
          justify-content: flex-end;
        }

        .print-label__value {
          min-width: 0;
          white-space: nowrap;
          overflow: visible;
          text-overflow: clip;
        }

        .print-label__qr {
          display: flex;
          align-items: flex-start;
          justify-content: flex-end;
          min-height: 14.4mm;
          padding-top: 0;
        }

        .print-label__qr img {
          width: 13mm;
          height: auto;
          object-fit: contain;
        }

        .print-label__qr-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 13mm;
          aspect-ratio: 1;
          color: #6f7d89;
          font-size: 6.2pt;
          border: 0.3mm dashed #cad3db;
          background: #fafcfe;
        }

        .print-label__stamp {
          display: none;
        }

        @media print {
          html,
          body {
            width: auto;
            height: auto;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible;
            background: #fff !important;
          }

          .print-sheet {
            width: 210mm;
            min-height: 297mm;
            padding: 1.5mm 2mm;
            margin: 0;
            gap: 2mm;
            box-shadow: none;
          }

          .print-label {
            width: 50mm;
            height: 35mm;
            min-height: 35mm;
            box-shadow: none;
            break-after: auto;
            page-break-after: auto;
            margin: 0;
          }
        }
      </style>
    </head>
    <body>
      <main class="print-sheet">${cards}</main>
      <script>
        const images = Array.from(document.images || []);
        document.title = '';
        Promise.all(images.map((img) => {
          if (img.complete) return Promise.resolve();
          return new Promise((resolve) => {
            img.onload = resolve;
            img.onerror = resolve;
          });
        })).then(() => {
          setTimeout(() => {
            window.focus();
            window.print();
          }, 120);
        });
        window.onafterprint = () => window.close();
      <\/script>
    </body>
  </html>`
}

const showBrowserPrintSettingTip = () => {
  let shouldShow = true

  try {
    shouldShow = localStorage.getItem(BROWSER_PRINT_TIP_STORAGE_KEY) !== '1'
    if (shouldShow) {
      localStorage.setItem(BROWSER_PRINT_TIP_STORAGE_KEY, '1')
    }
  } catch {
    shouldShow = true
  }

  if (shouldShow) {
    ElMessage.info('浏览器打印请在“更多设置”里关闭页眉和页脚，边距选“无”，纸张选 A4，缩放选“实际大小/100%”，标签规格使用 50mm x 35mm。')
  }
}

const openBrowserPrint = (rows = []) => {
  const repeatedRows = rows.flatMap(row => Array.from({ length: printerConfig.copies }, () => row))
  const printableItems = repeatedRows
    .map(row => ({
      label: buildLabelData(row || {}),
      qrcodeUrl: toAbsoluteAssetUrl(row?.qrcodeUrl || qrcodeUrl.value)
    }))
    .filter(item => item.qrcodeUrl)

  if (printableItems.length === 0) {
    ElMessage.warning('暂无可打印的标签')
    return false
  }

  const printWindow = window.open('', '_blank', 'width=960,height=720')
  if (!printWindow) {
    ElMessage.error('浏览器阻止了打印窗口，请允许弹窗后重试')
    return false
  }

  printWindow.document.write(buildBrowserPrintHtml(printableItems))
  printWindow.document.close()
  return true
}

const handlePrint = async (row = null) => {
  if (batchPrinting.value) {
    ElMessage.warning('批量打印进行中，请稍后')
    return
  }

  const targetRecord = row || generatedRecord.value || buildCurrentGeneratedRecord()
  const targetQrcodeId = targetRecord?.qrcodeId || latestQrcodeId.value
  const targetQrcodeContent = targetRecord?.qrcodeContent || qrcodeContent.value

  if (!targetQrcodeId && !targetQrcodeContent) {
    ElMessage.warning('暂无可打印的二维码')
    return
  }

  savePrinterConfig(false)

  if (!printerConfig.enablePrinter) {
    showBrowserPrintSettingTip()
    if (openBrowserPrint([targetRecord])) {
      ElMessage.success(`已打开浏览器打印窗口${printerConfig.copies > 1 ? `，共 ${printerConfig.copies} 份` : ''}`)
    }
    return
  }

  printing.value = true
  try {
    const res = await printMergedQRCode({
      qrcodeId: targetQrcodeId,
      qrcodeContent: targetQrcodeContent,
      copies: printerConfig.copies,
      printerHost: printerConfig.printerHost,
      printerPort: printerConfig.printerPort,
      printerProtocol: printerConfig.printerProtocol,
      printerTimeout: printerConfig.printerTimeout
    })

    if (res.code !== '0000') {
      ElMessage.error(res.msg || '打印失败')
      return
    }

    if (res.data?.sent) {
      ElMessage.success(res.data?.message || '打印任务已发送')
      return
    }

    const command = res.data?.command || ''
    if (command && navigator?.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(command)
        ElMessage.success((res.data?.message || '打印指令已生成') + '，指令已复制到剪贴板')
        return
      } catch {
        ElMessage.success(res.data?.message || '打印指令已生成')
        return
      }
    }

    ElMessage.success(res.data?.message || '打印指令已生成')
  } catch (error) {
    ElMessage.error('打印失败：' + error.message)
  } finally {
    printing.value = false
  }
}

const handleHistorySelectionChange = (rows) => {
  selectedHistoryRows.value = rows || []
}

const handleBatchPrint = async () => {
  if (selectedHistoryRows.value.length === 0) {
    ElMessage.warning('请先勾选需要打印的记录')
    return
  }

  if (printing.value) {
    ElMessage.warning('单条打印进行中，请稍后')
    return
  }

  batchPrinting.value = true
  savePrinterConfig(false)

  if (!printerConfig.enablePrinter) {
    showBrowserPrintSettingTip()
    if (openBrowserPrint(selectedHistoryRows.value)) {
      ElMessage.success(`已打开批量标签打印窗口，共 ${selectedHistoryRows.value.length * printerConfig.copies} 张`)
    }
    batchPrinting.value = false
    return
  }

  let successCount = 0
  let failCount = 0
  const commandList = []

  for (const row of selectedHistoryRows.value) {
    try {
      const res = await printMergedQRCode({
        qrcodeId: row?.qrcodeId,
        qrcodeContent: row?.qrcodeContent,
        copies: printerConfig.copies,
        printerHost: printerConfig.printerHost,
        printerPort: printerConfig.printerPort,
        printerProtocol: printerConfig.printerProtocol,
        printerTimeout: printerConfig.printerTimeout
      })

      if (res.code !== '0000') {
        failCount += 1
        continue
      }

      successCount += 1
      if (!res.data?.sent && res.data?.command) {
        commandList.push(`# ${row?.qrcodeId || 'UNKNOWN'}\n${res.data.command}`)
      }
    } catch {
      failCount += 1
    }
  }

  if (commandList.length > 0 && navigator?.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(commandList.join('\n\n'))
      ElMessage.success(`批量打印完成：成功 ${successCount} 条，失败 ${failCount} 条。打印指令已复制到剪贴板`)
      batchPrinting.value = false
      return
    } catch {
      // 忽略剪贴板失败，继续给出统计结果
    }
  }

  if (failCount > 0) {
    ElMessage.warning(`批量打印完成：成功 ${successCount} 条，失败 ${failCount} 条`)
  } else {
    ElMessage.success(`批量打印完成：成功 ${successCount} 条`)
  }

  batchPrinting.value = false
}

const handleBatchGenerate = () => {
  if (!form.enterpriseCode || !form.cjId || !form.spec || !form.batchNo || !form.drugOrigin || !form.productionDate || !form.expiryDate || !form.num || !form.traceUrl) {
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
        spec: normalizeSpecText(form.spec),
        batchNo,
        drugOrigin: form.drugOrigin,
        productionDate: form.productionDate,
        expiryDate: form.expiryDate,
        num: form.num,
        weight: form.weight,
        traceUrl: form.traceUrl
      }
    })

    const res = await generateBatchQRCode({
      createBy: userStore.userInfo.userAccount || 'admin',
      qrcodeList
    })

    if (res.code === '0000') {
      ElMessage.success(`批量生成完成：成功 ${res.data.successNum} 条，失败 ${res.data.failNum} 条`)
      batchDialogVisible.value = false
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
  previewRecord.value = row
  previewDialogVisible.value = true
}

const loadHistory = async () => {
  try {
    const res = await getQRCodeHistory({ page: 1, size: 10 })
    if (res.code === '0000') {
      historyList.value = (res.data.list || [])
        .filter(item => item.type === 'generate')
        .map(item => ({
          qrcodeId: item.qrcodeId,
          cjId: item.cjId,
          drugName: item.drugName,
          drugOrigin: item.drugOrigin,
          labelAmount: item.labelAmount,
          spec: item.spec,
          num: item.num,
          unit: item.unit,
          batchNo: item.batchNo,
          productionDate: item.productionDate,
          productionDateDisplay: item.productionDateDisplay,
          expiryDate: item.expiryDate,
          expiryDateDisplay: item.expiryDateDisplay,
          generateTime: item.generateTime,
          qrcodeUrl: item.qrcodeUrl,
          qrcodeContent: item.qrcodeContent || item.qrcodeOrigin,
          base64Str: item.base64Str,
          traceUrl: item.traceUrl
        }))
      selectedHistoryRows.value = []
    } else {
      ElMessage.error(res.msg || '历史记录加载失败')
    }
  } catch (error) {
    ElMessage.error('历史记录加载失败：' + error.message)
  }
}

watch(
  () => pageMode.value,
  (mode) => {
    if (mode === 'generate' && enterprises.value.length === 0) {
      loadEnterprises()
    }
    if (mode === 'manage') {
      loadHistory()
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadPrinterConfig()
})

onBeforeUnmount(() => {
  unbindDrugDropdownScroll()
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
  gap: 12px;
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
  border-radius: 12px;
  background: #faf9f5;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.result-head h4 {
  margin: 0;
  color: #3d4a36;
  font-size: 15px;
}

.result-tip {
  margin: 0 0 14px;
  color: #6f6555;
  font-size: 13px;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 16px 0 12px;
}

.result-meta {
  padding-top: 10px;
  border-top: 1px dashed #ddd4c3;
}

.result-meta p {
  margin: 8px 0 0;
  color: #4f4a40;
  word-break: break-all;
}

.printer-form {
  padding-top: 6px;
}

.printer-mode-alert {
  margin-bottom: 18px;
}

.printer-actions {
  margin-bottom: 0;
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

.history-card :deep(.el-table .cell) {
  word-break: break-word;
}

@media (max-width: 768px) {
  .card-header,
  .result-head,
  .history-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>