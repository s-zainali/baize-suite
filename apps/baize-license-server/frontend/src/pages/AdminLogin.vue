<template>
    <div class="absolute inset-0 bg-slate-950 flex items-center justify-center p-4">
      <div class="w-full max-w-sm">
        <div class="text-center mb-8 flex flex-col items-center gap-3">
          <div class="flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
            <img src="/baize_logo.png" alt="Baize" class="w-9" />
          </div>
          <div class="flex flex-col items-center gap-1.5">
            <img src="/baize_logo_text.png" alt="Baize" class="h-5" />
            <span class="text-[10px] font-black uppercase tracking-[0.45em] text-emerald-500/70 pl-[0.45em]">Central</span>
          </div>
          <p class="text-xs text-slate-500">Vendor administration portal</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
          <h2 class="text-lg font-black text-white mb-6">Authorize</h2>
          <form @submit.prevent="handleLogin" class="space-y-5">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-slate-400 pl-1 uppercase tracking-wider">Admin Token</label>
              <input type="password" v-model="inputToken" required placeholder="••••••••••••••••" autofocus
                class="w-full bg-slate-950/60 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-3 text-sm font-bold text-white outline-none transition-colors placeholder:text-slate-600 placeholder:font-normal">
            </div>
            <p v-if="error" class="text-xs font-bold text-rose-400">{{ error }}</p>
            <button type="submit" :disabled="loading || !inputToken"
              class="w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
              {{ loading ? 'Verifying…' : 'Access Portal' }}
            </button>
          </form>
        </div>
        <p class="text-center text-[10px] text-slate-600 mt-6 font-mono">Authorized personnel only · session expires automatically</p>
      </div>
    </div>
  </template>
  <script setup>
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { useAdmin } from '@/stores/admin.js'
  
  const router = useRouter()
  const admin = useAdmin()
  const inputToken = ref('')
  const error = ref('')
  const loading = ref(false)
  
  async function handleLogin() {
    if (!inputToken.value || loading.value) return
    loading.value = true; error.value = ''
    try {
      await admin.login(inputToken.value)
      router.push('/dashboard')
    } catch (e) { error.value = e.message } finally { loading.value = false }
  }
  </script>