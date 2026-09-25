<template>
    <div 
        class="group flex flex-col justify-between rounded-2xl border border-slate-700 bg-slate-800 p-5 backdrop-blur-xl transition-all hover:border-slate-700 hover:bg-slate-700/50"
      >
        <div>
          <div class="flex items-center justify-between">
            <span 
              v-if="club.isFavourite" 
              class="rounded-md bg-amber-500/20 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-amber-400"
            >
              ★ Favorite
            </span>
            <span class="text-[10px] font-bold text-slate-400">
              {{ club.branchesCount }} {{ club.branchesCount === 1 ? 'Branch' : 'Branches' }}
            </span>
          </div>
          <div class="mt-3 flex items-center gap-3">
            <div class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-slate-900">
              <img v-if="logoSrc && !logoFailed" :src="logoSrc" alt="" class="h-full w-full object-cover" @error="logoFailed = true" />
              <span v-else class="text-base font-black text-emerald-400">{{ (club.name || 'C').charAt(0).toUpperCase() }}</span>
            </div>
            <div class="min-w-0">
              <h4 class="truncate text-base font-black text-slate-100 group-hover:text-emerald-400">{{ club.name }}</h4>
              <p class="truncate text-[11px] text-slate-400">{{ club.location }}</p>
            </div>
          </div>
        </div>
    
        <div class="mt-5  gap-2 flex items-center justify-end border-t border-slate-700/80 pt-3">
          <button 
            class="cursor-pointer rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-200 hover:border-emerald-500/50 hover:bg-emerald-600 hover:text-white transition-all"
          >
            View Arena
          </button>
          <button 
            @click="$emit(('select-club'))"
            class="cursor-pointer rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-200 hover:border-emerald-500/50 hover:bg-emerald-600 hover:text-white transition-all"
          >
            Create Booking
          </button>
        </div>
      </div>
    </template>
    <script setup>
    import { ref, computed } from 'vue'
    const props = defineProps({club : {type: Object}})
    const logoFailed = ref(false)
    const emit = defineEmits(['select-club'])
    const logoSrc = computed(() => props.club?.logoUrl || null)
    </script>