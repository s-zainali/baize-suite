<template>
    <div v-if="true" class="px-3 pt-3">
        <div class="relative">
            <button @click="open = !open"
                class="w-full flex items-center justify-between gap-2 rounded-xl border px-3 py-2.5 text-left cursor-pointer"
                :class="isOverview ? 'bg-neutral-900 hover:border-neutral-600 border-neutral-800' : 'bg-slate-900 hover:border-slate-600 border-slate-800'">
                <span class="min-w-0">
                    <span class="block text-[9px] font-black uppercase tracking-widest text-slate-500">Branch</span>
                    <span class="block truncate text-sm font-bold text-white">{{ currentBranch?.name || (isOverview && canCombine ? 'All branches' : 'Select branch') }}</span>
                </span>
                <span class="text-slate-500 text-xs">▾</span>
            </button>
            <div v-if="open"
                class="absolute left-0 right-0 z-50 mt-1 rounded-xl border  shadow-2xl overflow-hidden transition duration-300 ease-in-out"
                :class="isOverview? 'border-neutral-800 bg-neutral-900' : 'border-slate-800 bg-slate-900'">
                <button v-if="isOverview && canCombine" @click="pick(null)"
                    class="w-full text-left px-3 py-2.5 text-sm font-bold cursor-pointer border-b"
                    :class="[currentBranchId == null ? 'text-emerald-300' : 'text-slate-300', isOverview ? 'hover:bg-neutral-800 border-neutral-800' : 'hover:bg-slate-800 border-slate-800']">
                    All branches
                    <span v-if="currentBranchId == null" class="float-right w-5 h-5 bg-emerald-600 text-center rounded-md">✓</span>
                </button>
                <button v-for="b in branches" :key="b.id" @click="pick(b.id)"
                    class="w-full text-left px-3 py-2.5 text-sm font-bold  cursor-pointer"
                    :class="b.id === currentBranchId ? 'text-slate-100' : 'text-slate-300', isOverview ?'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                    {{ b.name }}
                    <span v-if="b.id === currentBranchId" class="float-right w-5 h-5 bg-emerald-600 text-center rounded-md">✓</span>
                </button>
            </div>
        </div>
    </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { branches, currentBranch, currentBranchId, multiBranch, canCombine, loadBranches, setBranch } from '@/composables/useBranch.js'

const props = defineProps({isOverview : {type:Boolean, default:false}})
const open = ref(false)
const show = computed(() => multiBranch.value)   // owner sees it to add; others only when >1

onMounted(loadBranches)

function pick(id) {
    open.value = false
    if (id !== currentBranchId.value) setBranch(id)   // id=null → All branches (combined); persists + reloads
}
</script>