<template>
    <div v-if="open" class="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md" @click.self="emit('cancel')">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-sm shadow-2xl">
        <h3 class="text-lg font-black text-white mb-1">Renew license</h3>
        <p class="text-xs text-slate-400 mb-5">Extends from the later of today or the current expiry, and re-mints the token.</p>
        <label class="text-xs font-bold text-slate-400 pl-1 uppercase tracking-wider">Add days</label>
        <input type="number" v-model.number="days" min="1"
          class="w-full mt-1.5 mb-6 bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-3 text-sm font-bold text-white outline-none">
        <div class="flex gap-3 justify-end">
          <button @click="emit('cancel')" class="px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">Cancel</button>
          <button @click="emit('confirm', days)" :disabled="busy || !days"
            class="px-5 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer disabled:opacity-50">
            {{ busy ? 'Renewing…' : 'Renew' }}
          </button>
        </div>
      </div>
    </div>
  </template>
  <script setup>
  import { ref } from 'vue'
  defineProps({ open: Boolean, busy: Boolean })
  const emit = defineEmits(['confirm', 'cancel'])
  const days = ref(365)
  </script>