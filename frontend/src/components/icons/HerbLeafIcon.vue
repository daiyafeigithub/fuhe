<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    class="herb-leaf-icon"
  >
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
    <path
      d="M4.8 21.7H18.2C18 24.8 15.4 27.2 12.3 27.2H10.7C7.6 27.2 5 24.8 4.8 21.7Z"
      :stroke-width="strokeWidth"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M9.8 19.2L13.4 15.6"
      :stroke-width="strokeWidth"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
defineProps({
  size: {
    type: [Number, String],
    default: 20
  },
  strokeWidth: {
    type: [Number, String],
    default: 1.8
  }
})
</script>

<style scoped>
.herb-leaf-icon {
  display: block;
}
</style>
