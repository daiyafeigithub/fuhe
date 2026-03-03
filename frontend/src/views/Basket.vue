<template>
  <div class="basket-page">
    <el-card>
      <template #header>
        <span>分筐管理</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="筐号">
          <el-input v-model="basketForm.basketNo" placeholder="请输入筐号" style="width: 200px" />
        </el-form-item>
        <el-form-item label="筐名">
          <el-input v-model="basketForm.basketName" placeholder="请输入筐名" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAddBasket">添加筐号</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="basketList" stripe>
        <el-table-column prop="basketNo" label="筐号" />
        <el-table-column prop="basketName" label="筐名" />
        <el-table-column prop="createType" label="创建类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.createType === 1 ? 'primary' : 'success'">
              {{ row.createType === 1 ? '系统生成' : '人工自定义' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '作废' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 1"
              link
              type="danger"
              @click="handleDisable(row)"
            >
              作废
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>处方分筐关联</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="处方号">
          <el-input v-model="presNo" placeholder="请输入处方号" />
        </el-form-item>
        <el-form-item label="筐号">
          <el-select v-model="selectedBasket" placeholder="请选择筐号" style="width: 200px">
            <el-option
              v-for="basket in basketList"
              :key="basket.basketNo"
              :label="basket.basketNo"
              :value="basket.basketNo"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLoadDrugs">加载药品</el-button>
          <el-button type="success" @click="handleSaveRelation">保存关联</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="drugList"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="cjId" label="院内编码" />
        <el-table-column prop="drugName" label="药品名称" />
        <el-table-column prop="spec" label="规格" />
        <el-table-column prop="presNum" label="数量" />
        <el-table-column prop="basketNo" label="所属筐号" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { saveBasket, saveBasketRelation } from '@/api'
import { ElMessage } from 'element-plus'

const basketForm = reactive({
  basketNo: '',
  basketName: ''
})

const basketList = ref([
  {
    basketNo: 'K20260228001',
    basketName: '处方CF20260228001专用筐',
    createType: 1,
    status: 1,
    createTime: '2026-02-28 09:00:00'
  },
  {
    basketNo: 'K20260228002',
    basketName: '处方CF20260228002专用筐',
    createType: 2,
    status: 1,
    createTime: '2026-02-28 09:10:00'
  }
])

const presNo = ref('')
const selectedBasket = ref('')
const drugList = ref([])
const selectedDrugs = ref([])

const handleAddBasket = async () => {
  if (!basketForm.basketNo) {
    ElMessage.warning('请输入筐号')
    return
  }
  try {
    const res = await saveBasket({
      ...basketForm,
      status: 1,
      createBy: 'current_user'
    })
    if (res.code === '0000') {
      ElMessage.success('添加成功')
      basketForm.basketNo = ''
      basketForm.basketName = ''
    } else {
      ElMessage.error(res.msg || '添加失败')
    }
  } catch (error) {
    ElMessage.error('添加失败：' + error.message)
  }
}

const handleDisable = (row) => {
  row.status = 0
  ElMessage.success('已作废')
}

const handleLoadDrugs = () => {
  drugList.value = [
    {
      cjId: '13310',
      drugName: '盐巴戟天',
      spec: '5g',
      presNum: 2,
      basketNo: ''
    },
    {
      cjId: '13311',
      drugName: '当归',
      spec: '3g',
      presNum: 3,
      basketNo: ''
    }
  ]
}

const handleSelectionChange = (selection) => {
  selectedDrugs.value = selection
}

const handleSaveRelation = async () => {
  if (!presNo.value || !selectedBasket.value) {
    ElMessage.warning('请输入处方号并选择筐号')
    return
  }
  if (selectedDrugs.value.length === 0) {
    ElMessage.warning('请选择药品')
    return
  }
  try {
    const res = await saveBasketRelation({
      presNo: presNo.value,
      basketNo: selectedBasket.value,
      cjIdList: selectedDrugs.value.map(item => item.cjId),
      createBy: 'current_user'
    })
    if (res.code === '0000') {
      ElMessage.success('关联成功')
      drugList.value.forEach(drug => {
        if (selectedDrugs.value.includes(drug)) {
          drug.basketNo = selectedBasket.value
        }
      })
    } else {
      ElMessage.error(res.msg || '关联失败')
    }
  } catch (error) {
    ElMessage.error('关联失败：' + error.message)
  }
}
</script>
