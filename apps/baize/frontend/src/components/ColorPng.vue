<template>
    <div
      class="inline-block transition-colors duration-200"
      :style="maskStyle"
      role="img"
      :aria-label="alt"
    />
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const props = defineProps({
    url: {
      type: String,
      required: true
    },
    color: {
      type: String,
      default: '#000000'
    },
    size: {
      type: [String, Number],
      default: '24px'
    },
    alt: {
      type: String,
      default: 'icon'
    }
  })
  
  const sizeValue = computed(() => 
    typeof props.size === 'number' ? `${props.size}px` : props.size
  )
  
  const maskStyle = computed(() => ({
    backgroundColor: props.color,
    maskImage: `url("${props.url}")`,
    WebkitMaskImage: `url("${props.url}")`,
    maskSize: 'contain',
    WebkitMaskSize: 'contain',
    maskRepeat: 'no-repeat',
    WebkitMaskRepeat: 'no-repeat',
    maskPosition: 'center',
    WebkitMaskPosition: 'center',
    width: sizeValue.value,
    height: sizeValue.value
  }))
  </script>