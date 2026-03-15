<template>
  <div class="label-card" :class="{ 'label-card--compact': compact }">
    <div class="label-card__backdrop">
      <div class="label-card__sheet">
        <div class="label-card__main">
          <div class="label-card__content">
            <div v-for="item in displayItems" :key="item.key" class="label-card__row">
              <span class="label-card__label-group">
                <span class="label-card__label-text">{{ item.labelDisplay }}</span>
                <span class="label-card__label-colon">：</span>
              </span>
              <span class="label-card__value">{{ item.value }}</span>
            </div>
          </div>
          <div class="label-card__code">
            <img v-if="qrcodeUrl" :src="qrcodeUrl" alt="标签二维码" />
            <div v-else class="label-card__placeholder">待生成二维码</div>
          </div>
        </div>
        <div class="label-card__stamp">质量合格</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: Object,
    default: () => ({})
  },
  qrcodeUrl: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const normalizeValue = (value) => {
  const text = String(value || '').trim()
  return text || '--'
}

const displayItems = computed(() => [
  { key: 'drugName', labelDisplay: '品　名', value: normalizeValue(props.label.drugName) },
  { key: 'drugOrigin', labelDisplay: '药材产地', value: normalizeValue(props.label.drugOrigin) },
  { key: 'labelAmount', labelDisplay: '装　量', value: normalizeValue(props.label.labelAmount) },
  { key: 'batchNo', labelDisplay: '产品批号', value: normalizeValue(props.label.batchNo) },
  { key: 'productionDate', labelDisplay: '生产日期', value: normalizeValue(props.label.productionDate) },
  { key: 'expiryDate', labelDisplay: '保质期至', value: normalizeValue(props.label.expiryDate) }
])
</script>

<style scoped>
.label-card {
  width: min(100%, 500px);
}

.label-card__backdrop {
  padding: 18px 20px;
  background: #aebfd2;
  border-radius: 2px;
}

.label-card__sheet {
  min-height: 350px;
  padding: 20px 24px 22px;
  border: 1px solid #bcc7d1;
  background: #fff;
  box-shadow: 0 5px 14px rgba(32, 47, 66, 0.18);
}

.label-card__main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 116px;
  gap: 18px;
  align-items: start;
}

.label-card__content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 10px;
}

.label-card__row {
  display: grid;
  grid-template-columns: 94px minmax(0, 1fr);
  gap: 6px;
  align-items: baseline;
  font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
  font-size: 14px;
  line-height: 1.24;
  color: #111;
  font-weight: 800;
}

.label-card__label-group {
  display: grid;
  grid-template-columns: 72px 10px;
  align-items: baseline;
}

.label-card__label-text {
  white-space: pre;
  letter-spacing: 0.02em;
}

.label-card__label-colon {
  display: inline-flex;
  justify-content: flex-end;
}

.label-card__value {
  min-width: 0;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

.label-card__code {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  min-height: 116px;
  padding-top: 2px;
}

.label-card__code img {
  width: 116px;
  aspect-ratio: 1;
  object-fit: contain;
}

.label-card__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 116px;
  aspect-ratio: 1;
  color: #6f7d89;
  font-size: 13px;
  border: 1px dashed #cad3db;
  background: #fafcfe;
}

.label-card__stamp {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 104px;
  height: 48px;
  margin: 22px auto 0;
  border: 2.5px solid #111;
  border-radius: 50%;
  font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #111;
  background: #fff;
}

.label-card--compact .label-card__backdrop {
  padding: 14px 16px;
}

.label-card--compact .label-card__sheet {
  min-height: 0;
  padding: 18px 20px 20px;
}

.label-card--compact .label-card__main {
  grid-template-columns: minmax(0, 1fr) 104px;
  gap: 16px;
}

.label-card--compact .label-card__row {
  grid-template-columns: 86px minmax(0, 1fr);
  font-size: 12px;
}

.label-card--compact .label-card__label-group {
  grid-template-columns: 66px 8px;
}

.label-card--compact .label-card__stamp {
  width: 88px;
  height: 42px;
  margin-top: 18px;
  font-size: 14px;
}

.label-card--compact .label-card__code img,
.label-card--compact .label-card__placeholder {
  width: 104px;
}

@media (max-width: 640px) {
  .label-card__backdrop {
    padding: 14px;
  }

  .label-card__sheet {
    padding: 18px;
  }

  .label-card__main {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .label-card__code {
    justify-content: center;
    min-height: 0;
    padding-top: 0;
  }

  .label-card__row {
    grid-template-columns: 90px minmax(0, 1fr);
    font-size: 13px;
  }

  .label-card__label-group {
    grid-template-columns: 68px 8px;
  }
}
</style>