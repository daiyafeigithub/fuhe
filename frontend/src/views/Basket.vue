<template>
  <div class="basket-page">
    <el-card class="module-card">
      <template #header>
        <span>分筐管理</span>
      </template>
      <el-form :inline="true" class="query-form">
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

    <el-card class="module-card relation-card">
      <template #header>
        <span>处方分筐关联</span>
      </template>
      <el-form :inline="true" class="relation-form">
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
import { ref, reactive, onMounted, computed } from 'vue'
import { saveBasket, saveBasketRelation, getBasketList, getBasketRelations, disableBasket } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const currentUserAccount = computed(() => userStore.userInfo.userAccount || 'admin')

const basketForm = reactive({
  basketNo: '',
  basketName: ''
})

const basketList = ref([])

const presNo = ref('')
const selectedBasket = ref('')
const drugList = ref([])
const selectedDrugs = ref([])

const loadBasketList = async () => {
  try {
    const res = await getBasketList()
    if (res.code === '0000') {
      basketList.value = res.data.list || res.data.baskets || []
      if (selectedBasket.value && !basketList.value.some(item => item.basketNo === selectedBasket.value)) {
        selectedBasket.value = ''
      }
    }
  } catch (error) {
    ElMessage.error('加载分筐列表失败：' + error.message)
  }
}

const handleAddBasket = async () => {
  if (!basketForm.basketNo) {
    ElMessage.warning('请输入筐号')
    return
  }
  try {
    const res = await saveBasket({
      basketNo: basketForm.basketNo,
      basketName: basketForm.basketName,
      createBy: currentUserAccount.value,
      status: 1
    })
    if (res.code === '0000') {
      ElMessage.success('添加成功')
      basketForm.basketNo = ''
      basketForm.basketName = ''
      await loadBasketList()
    } else {
      ElMessage.error(res.msg || '添加失败')
    }
  } catch (error) {
    ElMessage.error('添加失败：' + error.message)
  }
}

const handleDisable = async (row) => {
  try {
    await ElMessageBox.confirm(`确定作废分筐 ${row.basketNo} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await disableBasket({ basketNo: row.basketNo, operateBy: currentUserAccount.value })
    if (res.code === '0000') {
      ElMessage.success('已作废')
      await loadBasketList()
    } else {
      ElMessage.error(res.msg || '作废失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('作废失败：' + error.message)
    }
  }
}

const handleLoadDrugs = async () => {
  if (!presNo.value) {
    ElMessage.warning('请输入处方号')
    return
  }
  try {
    const res = await getBasketRelations({
      presNo: presNo.value,
      basketNo: selectedBasket.value || undefined
    })
    if (res.code === '0000') {
      drugList.value = (res.data.list || []).map(item => ({
        id: item.id,
        cjId: item.cjId,
        drugName: item.drugName,
        spec: item.spec,
        presNum: item.presNum,
        basketNo: item.basketNo || ''
      }))
      selectedDrugs.value = []
    } else {
      ElMessage.error(res.msg || '加载药品失败')
    }
  } catch (error) {
    ElMessage.error('加载药品失败：' + error.message)
  }
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
      createBy: currentUserAccount.value,
      checkMainId: 0
    })
    if (res.code === '0000') {
      ElMessage.success('关联成功')
      await handleLoadDrugs()
      await loadBasketList()
    } else {
      ElMessage.error(res.msg || '关联失败')
    }
  } catch (error) {
    ElMessage.error('关联失败：' + error.message)
  }
}

onMounted(() => {
  loadBasketList()
})
</script>

<style scoped>
.basket-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card :deep(.el-card__header) {
  background: linear-gradient(90deg, rgba(120, 146, 98, 0.1) 0%, rgba(120, 146, 98, 0.02) 58%);
}

.query-form,
.relation-form {
  padding: 4px 0 10px;
}

.query-form :deep(.el-form-item),
.relation-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.relation-card :deep(.el-table),
.module-card :deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

.module-card :deep(.el-tag) {
  border-radius: 4px;
}
</style>
