<template>
    <div v-if="roster.length" class="flex items-center justify-center gap-2 mb-2">
        <span class="text-[10px] text-nowrap font-bold text-slate-100/50 uppercase tracking-wider transition-all">{{
            roster.length }} {{ roster.length === 1 ? 'Player' : 'Players' }}</span>
        <button @click="emit('view')"
            class="pointer-events-auto transform rounded-lg w-full  text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 disabled:opacity-50 text-center bg-slate-800/50 hover:bg-slate-900/90 text-white/90 px-2 py-0.5">
            View
        </button>
    </div>
</template>

<script setup>
const props = defineProps({
    roster: { type: Array, default: () => [] },
})

const emit = defineEmits(['view'])
</script>