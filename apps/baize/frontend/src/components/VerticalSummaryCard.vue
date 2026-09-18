<template>
    <div class="flex flex-col justify-evenly gap-2 z-200 bg-slate-800/50 p-4 rounded-xl border-slate-800">
        <div :class="categoryClass">
            <span class="text-[15px] font-bold uppercase tracking-wider text-slate-500">Total</span>
            <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-white block leading-none">
                {{ tableSummary?.total || 0 }}</span>
        </div>
        <div :class="categoryClass">
            <span class="text-[15px] font-bold uppercase tracking-wider text-slate-500">Free</span>
            <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-emerald-500 block leading-none">
                {{ tableSummary?.free || 0 }}</span>
        </div>
        <div :class="categoryClass">
            <span class="text-[15px] font-bold uppercase tracking-wider text-slate-500">Busy</span>
            <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-rose-400 block leading-none">
                {{ tableSummary?.occupied || 0 }}</span>
        </div>
        <div :class="categoryClass">
            <span class="text-[15px] font-bold uppercase tracking-wider text-slate-500">Queue</span>
            <span class="text-[clamp(0.875rem,11cqw,1.5rem)] font-black text-amber-400 block leading-none">
                {{ tableSummary?.queueCount || 0 }}</span>
        </div>
    </div>
</template>

<script setup>
const props = defineProps({
    tableSummary: Object
})

const categoryClass = 'text-center flex gap-2 justify-between items-center w-full'
</script>