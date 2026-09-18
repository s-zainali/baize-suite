<template>
    <div class="absolute inset-0 bg-slate-950 overflow-y-auto text-slate-100 selection:bg-emerald-500 selection:text-slate-950">
      <div class="max-w-7xl mx-auto px-6 py-8">
        <header class="flex justify-between items-center mb-8 bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl px-6 py-4 rounded-3xl shadow-2xl">
          <div class="flex items-center gap-4">
            <div class="flex gap-3 items-center">
              <img src="/baize_logo.png" class="h-9" alt="">
              <img src="/baize_logo_text.png" class="h-4 hidden sm:block" alt="">
            </div>
            <span class="text-[10px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded-full uppercase tracking-wider">Central</span>
          </div>
          <nav class="flex items-center gap-1">
            <router-link v-for="l in links" :key="l.to" :to="l.to"
              class="px-3.5 py-2 rounded-xl text-xs font-bold transition-all"
              :class="isActive(l.to) ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-900'">
              {{ l.label }}
            </router-link>
            <button @click="signOut" class="ml-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-950 border border-slate-800 text-slate-400 hover:text-rose-300 hover:border-rose-900 transition-all cursor-pointer">
              Sign Out
            </button>
          </nav>
        </header>
        <slot />
      </div>
      <ToastHost />
    </div>
  </template>
  <script setup>
  import { useRouter, useRoute } from 'vue-router'
  import { useAdmin } from '@/stores/admin.js'
  import ToastHost from './ToastHost.vue'
  
  const router = useRouter()
  const route = useRoute()
  const admin = useAdmin()
  const links = [
    { to: '/dashboard', label: 'Venues' },
    { to: '/licenses', label: 'Licenses' },
    { to: '/audit', label: 'Audit' },
  ]
  const isActive = (to) => route.path === to || (to !== '/dashboard' && route.path.startsWith(to))
  function signOut() { admin.logout(); router.push('/login') }
  </script>