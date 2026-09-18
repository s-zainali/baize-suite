<template>
    <div v-if="open" class="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md"
      @click.self="emit('cancel')">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-sm shadow-2xl">
        <h3 class="text-lg font-black text-white mb-2">{{ title }}</h3>
        <p class="text-sm text-slate-400 leading-relaxed mb-6">{{ message }}</p>
        <div class="flex gap-3 justify-end">
          <button @click="emit('cancel')" class="px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">
            {{ cancelLabel }}
          </button>
          <button @click="emit('confirm')" :disabled="busy"
            class="px-5 py-2.5 rounded-xl text-xs font-black text-white cursor-pointer disabled:opacity-50"
            :class="danger ? 'bg-rose-600 hover:bg-rose-500' : 'bg-emerald-600 hover:bg-emerald-500'">
            {{ busy ? 'Working…' : confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </template>
  <script setup>
  defineProps({
    open: Boolean, title: String, message: String, busy: Boolean, danger: Boolean,
    confirmLabel: { type: String, default: 'Confirm' }, cancelLabel: { type: String, default: 'Cancel' },
  })
  const emit = defineEmits(['confirm', 'cancel'])
  </script>