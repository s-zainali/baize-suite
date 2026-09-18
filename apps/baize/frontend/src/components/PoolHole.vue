<template>
  <div
    class="z-4 absolute rounded-full bg-neutral-900 border border-neutral-950 border-1 shadow-[0px_0px_3px_0px_black]"
    :class="positionClasses, isBadge? 'h-6 w-6' : 'h-4 w-4'"
  ></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  position: {
    type: String,
    required: true,
  },
  isBadge: {
    type: Boolean,
    default: false
  }
})

const positionClasses = computed(() => {
  const mapping = {
    'top-left': '-top-1.5 -left-1.5',
    'top-right': '-top-1.5 -right-1.5',
    'mid-left': 'top-1/2 -left-1.5 -translate-y-1/2',
    'mid-right': 'top-1/2 -right-1.5 -translate-y-1/2',
    'bottom-left': '-bottom-1.5 -left-1.5',
    'bottom-right': '-bottom-1.5 -right-1.5',
  }

  return mapping[props.position] || ''
})
</script>
