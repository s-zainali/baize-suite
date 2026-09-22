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
      <h4 class="mt-2 text-base font-black text-slate-100 group-hover:text-emerald-400">{{ club.name }}</h4>
      <p class="mt-1 text-[11px] text-slate-400">{{ club.location }}</p>
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
const props = defineProps({club : {type: Object}})
const emit = defineEmits(['select-club'])
</script>