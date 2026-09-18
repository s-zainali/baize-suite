<template>
    <div class="fixed top-5 right-5 z-[200] flex flex-col gap-2 w-80 max-w-[90vw]">
      <transition-group name="toast">
        <div v-for="t in toasts" :key="t.id" @click="remove(t.id)"
          class="cursor-pointer rounded-2xl border px-4 py-3 text-sm font-bold shadow-2xl backdrop-blur-xl flex items-start gap-2"
          :class="{
            'bg-emerald-950/80 border-emerald-800 text-emerald-200': t.type === 'success',
            'bg-rose-950/80 border-rose-800 text-rose-200': t.type === 'error',
            'bg-slate-900/90 border-slate-700 text-slate-200': t.type === 'info',
          }">
          <span class="shrink-0">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ' }}</span>
          <span class="flex-1 leading-snug">{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </template>
  <script setup>
  import { useToast } from '@/composables/useToast.js'
  const { toasts, remove } = useToast()
  </script>
  <style scoped>
  .toast-enter-active, .toast-leave-active { transition: all .25s ease; }
  .toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(20px); }
  </style>