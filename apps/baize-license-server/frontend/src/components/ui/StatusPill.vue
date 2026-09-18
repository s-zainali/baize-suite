<template>
    <span class="px-2.5 py-1 text-[10px] rounded-lg font-black uppercase tracking-widest border shrink-0 inline-block" :class="cls">
      {{ label || status }}
    </span>
  </template>
  <script setup>
  import { computed } from 'vue'
  const props = defineProps({ status: String, label: String })
  const MAP = {
    active: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
    expired: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
    revoked: 'bg-rose-950/60 text-rose-400 border-rose-900/80',
    online: 'bg-indigo-950/60 text-indigo-300 border-indigo-800/80',
    trial: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
    local: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
    suspended: 'bg-rose-950/60 text-rose-400 border-rose-900/80',
  }
  const cls = computed(() => MAP[props.status] || 'bg-slate-800 text-slate-300 border-slate-700')
  </script>