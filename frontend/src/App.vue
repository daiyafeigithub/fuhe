<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --zh-bamboo-green: #789262;
  --zh-bamboo-green-deep: #4a7023;
  --zh-rice-paper: #f7f5f0;
  --zh-rice-paper-deep: #f1eee5;
  --zh-ink: #333333;
  --zh-ink-secondary: #5a6154;
  --zh-border: #d9d3c5;
  --zh-cinnabar: #b22222;

  --el-color-primary: var(--zh-bamboo-green);
  --el-color-primary-light-3: #91a87d;
  --el-color-primary-light-5: #a9bb98;
  --el-color-primary-light-8: #d7e1cf;
  --el-color-primary-dark-2: var(--zh-bamboo-green-deep);

  --el-bg-color-page: var(--zh-rice-paper);
  --el-bg-color: #fbfaf7;
  --el-text-color-primary: var(--zh-ink);
  --el-text-color-regular: var(--zh-ink-secondary);
  --el-border-color: var(--zh-border);
  --el-border-color-light: #e6e1d6;
  --el-border-color-lighter: #ede9df;
  --el-border-radius-base: 6px;
  --el-font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: var(--el-font-family);
}

body {
  color: var(--el-text-color-primary);
  background-color: var(--zh-rice-paper);
  background-image:
    radial-gradient(circle at 12% 18%, rgba(120, 146, 98, 0.05), transparent 36%),
    radial-gradient(circle at 86% 78%, rgba(74, 112, 35, 0.04), transparent 30%),
    repeating-linear-gradient(
      135deg,
      rgba(51, 51, 51, 0.014) 0,
      rgba(51, 51, 51, 0.014) 1px,
      transparent 1px,
      transparent 18px
    );
}

.el-card {
  border-radius: 6px;
  border-color: var(--el-border-color-light);
  box-shadow: 0 6px 16px rgba(62, 74, 50, 0.08);
}

.el-card__header {
  border-bottom-color: var(--el-border-color-lighter);
  font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
  font-size: 16px;
  letter-spacing: 0.5px;
}

h1,
h2,
h3,
h4,
h5,
h6,
.el-dialog__title,
.el-descriptions__label {
  font-family: "Songti SC", "STSong", "Source Han Serif SC", serif;
  font-weight: 600;
}

.el-button,
.el-card,
.el-input__wrapper,
.el-textarea__inner,
.el-menu-item,
.el-table__row {
  transition: all 0.28s ease-in-out;
}

.el-button--primary {
  background-color: var(--zh-bamboo-green);
  border-color: var(--zh-bamboo-green);
}

.el-button--primary:hover,
.el-button--primary:focus {
  background-color: var(--zh-bamboo-green-deep);
  border-color: var(--zh-bamboo-green-deep);
  box-shadow: 0 0 0 3px rgba(120, 146, 98, 0.15);
}

.el-button.is-plain,
.el-button--default {
  color: var(--zh-bamboo-green-deep);
  border-color: #bfcab1;
  background: rgba(247, 245, 240, 0.7);
}

.el-button.is-plain:hover,
.el-button--default:hover {
  color: var(--zh-bamboo-green-deep);
  border-color: var(--zh-bamboo-green);
  background: rgba(120, 146, 98, 0.08);
}

.el-input__wrapper,
.el-textarea__inner {
  box-shadow: 0 0 0 1px #d7d2c7 inset;
}

.el-input__wrapper:hover,
.el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #bfcab1 inset;
}

.el-input__wrapper.is-focus,
.el-textarea__inner:focus {
  box-shadow: 0 0 0 1px var(--zh-bamboo-green) inset !important;
}

.el-table {
  --el-table-header-bg-color: #ece8dd;
  --el-table-tr-bg-color: #fcfbf8;
  --el-table-row-hover-bg-color: #f0f5eb;
  --el-table-border-color: #e2deD3;
  color: var(--zh-ink);
}

.el-table .el-table__cell {
  padding: 12px 0;
}

.el-table .el-table__body tr:nth-child(even) > td.el-table__cell {
  background-color: rgba(120, 146, 98, 0.035);
}

.el-tag--danger {
  background-color: rgba(178, 34, 34, 0.1);
  border-color: rgba(178, 34, 34, 0.25);
  color: var(--zh-cinnabar);
}

.el-loading-mask {
  background-color: rgba(247, 245, 240, 0.72);
  backdrop-filter: blur(1.5px);
}

.el-loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.el-loading-spinner .circular {
  display: none;
}

.el-loading-spinner::before {
  content: "";
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 25%, #f7f5f0 0 3px, transparent 3.5px),
    radial-gradient(circle at 50% 75%, var(--zh-bamboo-green-deep) 0 3px, transparent 3.5px),
    radial-gradient(circle at 50% 50%, transparent 0 11px, rgba(255, 255, 255, 0.08) 11px 12px, transparent 12px),
    conic-gradient(from 90deg, var(--zh-bamboo-green) 0 180deg, #d7e1cf 180deg 360deg);
  box-shadow: 0 0 0 1px rgba(74, 112, 35, 0.15), 0 4px 10px rgba(74, 112, 35, 0.14);
  animation: zhTaijiSpin 1.6s ease-in-out infinite;
}

.el-loading-spinner::after {
  content: "";
  position: absolute;
  top: -8px;
  width: 56px;
  height: 56px;
  border: 1px solid rgba(120, 146, 98, 0.22);
  border-radius: 55% 45% 55% 45% / 45% 55% 45% 55%;
  animation: zhLeafPulse 1.8s ease-in-out infinite;
}

.el-loading-spinner .el-loading-text {
  margin-top: 0;
  color: #5e6a58;
  letter-spacing: 0.4px;
  font-size: 13px;
}

@keyframes zhTaijiSpin {
  0% {
    transform: rotate(0deg) scale(0.94);
  }

  50% {
    transform: rotate(180deg) scale(1);
  }

  100% {
    transform: rotate(360deg) scale(0.94);
  }
}

@keyframes zhLeafPulse {
  0% {
    opacity: 0.25;
    transform: scale(0.86) rotate(0deg);
  }

  50% {
    opacity: 0.55;
    transform: scale(1) rotate(8deg);
  }

  100% {
    opacity: 0.25;
    transform: scale(0.86) rotate(0deg);
  }
}
</style>
