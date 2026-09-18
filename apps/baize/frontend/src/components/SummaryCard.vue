<template>
    <div v-if="tableSummary[t.id]?.total !== 0"
        class="shrink-0 flex-grow min-w-[125px] bg-slate-950/40 border border-slate-700/60 rounded-2xl p-2 [container-type:inline-size]">
        <h3 class="text-[9px] sm:text-[11px] text-center font-black text-slate-400 uppercase tracking-[0.15rem] mb-1.5 truncate mb-2 pb-1 border-b border-slate-800">
            {{ t.id.includes('ps') ? t.id : t.label }}</h3>

        <div class="flex justify-evenly mb-2">
            <div class="text-center">
                <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-white block leading-none">
                    {{ tableSummary[t.id]?.total || 0 }}</span>
                <span class="text-[7px] font-bold uppercase tracking-wider text-slate-500">Total</span>
            </div>
            <div class="text-center">
                <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-emerald-500 block leading-none">
                    {{ tableSummary[t.id]?.free || 0 }}</span>
                <span class="text-[7px] font-bold uppercase tracking-wider text-slate-500">Free</span>
            </div>
            <div class="text-center">
                <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-rose-400 block leading-none">
                    {{ tableSummary[t.id]?.occupied || 0 }}</span>
                <span class="text-[7px] font-bold uppercase tracking-wider text-slate-500">Busy</span>
            </div>
            <div class="text-center">
                <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-amber-400 block leading-none">
                    {{ tableSummary[t.id]?.queueCount || 0 }}</span>
                <span class="text-[7px] font-bold uppercase tracking-wider text-slate-500">Queue</span>
            </div>
        </div>

        <!-- occupancy bar -->
        <div class="w-full flex h-1 bg-emerald-500 rounded-full overflow-hidden">
            <div class="h-full bg-rose-500 transition-all duration-500" :style="{
                width: tableSummary[t.id]?.total > 0
                    ? (tableSummary[t.id].occupied / tableSummary[t.id].total) * 100 + '%'
                    : '0%',
            }"></div>
            <div class="h-full bg-amber-500 transition-all duration-500" :style="{
                width: tableSummary[t.id]?.total > 0
                    ? (tableSummary[t.id].resumable / tableSummary[t.id].total) * 100 + '%'
                    : '0%',
            }"></div>
        </div>
    </div>

</template>
<script setup>
const props = defineProps({ t: Object, tableSummary: Object })
</script>