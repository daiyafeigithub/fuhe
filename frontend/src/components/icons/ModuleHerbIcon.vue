<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    class="module-herb-icon"
  >
    <g v-if="normalizedVariant === 'dashboard'">
      <rect x="4" y="7" width="24" height="18" rx="4" :stroke-width="strokeWidth" stroke="currentColor" />
      <path d="M16 20V12" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M16 12C14.2 12 12.8 10.8 12.6 9C14.6 9 16 10.2 16 12Z" fill="currentColor" opacity="0.2" />
      <path d="M16 14C17.8 14 19.2 12.8 19.4 11C17.4 11 16 12.2 16 14Z" fill="currentColor" opacity="0.2" />
      <path d="M8.5 20H23.5" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" opacity="0.7" />
    </g>

    <g v-else-if="normalizedVariant === 'qrcode'">
      <path d="M6 6H12V8H8V12H6V6Z" fill="currentColor" />
      <path d="M20 6H26V12H24V8H20V6Z" fill="currentColor" />
      <path d="M6 20H8V24H12V26H6V20Z" fill="currentColor" />
      <path d="M24 20H26V26H20V24H24V20Z" fill="currentColor" />
      <path
        d="M16 10.5C12.9 10.6 10.5 12.9 10.5 16C10.5 18.9 12.6 21.2 15.4 21.5C18.6 21.8 21.5 19.3 21.5 16.1C21.5 13 19.1 10.5 16 10.5Z"
        fill="currentColor"
        opacity="0.14"
      />
      <path
        d="M16 10.5C12.9 10.6 10.5 12.9 10.5 16C10.5 18.9 12.6 21.2 15.4 21.5C18.6 21.8 21.5 19.3 21.5 16.1C21.5 13 19.1 10.5 16 10.5Z"
        :stroke-width="strokeWidth"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path d="M13.8 18.5C14.8 15.9 16.8 13.8 19.8 12.6" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
    </g>

    <g v-else-if="normalizedVariant === 'check'">
      <circle cx="14" cy="14" r="6.2" :stroke-width="strokeWidth" stroke="currentColor" />
      <path d="M18.7 18.7L23.5 23.5" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M14 17.6V11.8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M14 12C12.6 12 11.5 11.1 11.3 9.8C12.8 9.8 14 10.7 14 12Z" fill="currentColor" opacity="0.2" />
      <path d="M14 13.3C15.5 13.3 16.6 12.3 16.8 11C15.2 11 14 12 14 13.3Z" fill="currentColor" opacity="0.2" />
    </g>

    <g v-else-if="normalizedVariant === 'alert'">
      <path d="M16 6.5L26.5 24H5.5L16 6.5Z" :stroke-width="strokeWidth" stroke="currentColor" stroke-linejoin="round" />
      <path d="M16 12.2V18" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <circle cx="16" cy="21.2" r="1.1" fill="currentColor" />
      <path d="M16 9.8C14.9 9.8 13.9 9.1 13.7 8C15 8 16 8.7 16 9.8Z" fill="currentColor" opacity="0.18" />
    </g>

    <g v-else-if="normalizedVariant === 'basket'">
      <path d="M8 13H24L22.5 24.5H9.5L8 13Z" :stroke-width="strokeWidth" stroke="currentColor" stroke-linejoin="round" />
      <path d="M11 13C11 10.2 13.2 8 16 8C18.8 8 21 10.2 21 13" :stroke-width="strokeWidth" stroke="currentColor" />
      <path d="M13.2 18.5C14.4 16.5 16.2 15.3 19 14.8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path
        d="M14.3 19.8C12.5 19.9 11.1 18.6 11.1 16.8C12.9 16.7 14.3 17.9 14.3 19.8Z"
        fill="currentColor"
        opacity="0.16"
      />
    </g>

    <g v-else-if="normalizedVariant === 'trace'">
      <path d="M7 24C11.3 19.5 14.9 16 25 10" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <circle cx="8.5" cy="24" r="2.2" :stroke-width="strokeWidth" stroke="currentColor" />
      <circle cx="24" cy="10" r="2.2" :stroke-width="strokeWidth" stroke="currentColor" />
      <path
        d="M16.4 17.4C14.4 17.4 12.8 16 12.6 14C14.8 14 16.4 15.4 16.4 17.4Z"
        fill="currentColor"
        opacity="0.18"
      />
    </g>

    <g v-else-if="normalizedVariant === 'statistics'">
      <path d="M7 25V19" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M12.8 25V15" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M18.6 25V12" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M24.4 25V9" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M6 25.5H26" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path
        d="M20.8 9.8C19.2 9.8 18 8.7 17.8 7.2C19.5 7.2 20.8 8.3 20.8 9.8Z"
        fill="currentColor"
        opacity="0.2"
      />
    </g>

    <g v-else-if="normalizedVariant === 'system'">
      <circle cx="16" cy="16" r="5.4" :stroke-width="strokeWidth" stroke="currentColor" />
      <path d="M16 5.2V8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M16 24V26.8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M5.2 16H8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M24 16H26.8" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M8.4 8.4L10.4 10.4" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M21.6 21.6L23.6 23.6" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M23.6 8.4L21.6 10.4" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M10.4 21.6L8.4 23.6" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M16 19V13" :stroke-width="strokeWidth" stroke="currentColor" stroke-linecap="round" />
      <path d="M16 13.2C14.7 13.2 13.7 12.3 13.6 11C15 11 16 11.8 16 13.2Z" fill="currentColor" opacity="0.16" />
    </g>

    <g v-else>
      <path
        d="M23.8 7.2C17.6 7.4 12 11.6 10.8 17.5C9.6 23.1 13.4 27.3 18.6 27.1C24.6 26.9 29.2 21.9 29.1 15.5C29 10.4 26.9 7.1 23.8 7.2Z"
        fill="currentColor"
        opacity="0.16"
      />
      <path
        d="M23.8 7.2C17.6 7.4 12 11.6 10.8 17.5C9.6 23.1 13.4 27.3 18.6 27.1C24.6 26.9 29.2 21.9 29.1 15.5C29 10.4 26.9 7.1 23.8 7.2Z"
        :stroke-width="strokeWidth"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M14.1 23.5C15.8 18.5 19.3 14.2 24.7 11.6"
        :stroke-width="strokeWidth"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: [Number, String],
    default: 18
  },
  strokeWidth: {
    type: [Number, String],
    default: 1.8
  },
  variant: {
    type: String,
    default: 'leaf'
  }
})

const normalizedVariant = computed(() => String(props.variant || 'leaf').toLowerCase())
</script>

<style scoped>
.module-herb-icon {
  display: block;
}
</style>
