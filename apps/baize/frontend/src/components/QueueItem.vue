<template>
    <div
        class="flex justify-between items-center bg-slate-900 rounded-xl border border-slate-800 overflow-hidden transition-all h-12 gap-2">
        <button  @click="emit('start-from-queue', props.guest.id)"
            class="w-8 flex items-center justify-center text-emerald-400 hover:text-white hover:bg-emerald-500 transition-colors cursor-pointer transition-all h-full">
            ✓
        </button>
        <div class="min-w-0 flex items-center gap-3">
            <span class="shrink-0 text-lg font-black leading-none text-white tabular-nums">{{
                props.guest.number ?? '—' }}</span>
            <div class="min-w-0">
                <span class="block text-[9px] font-black uppercase tracking-wider"
                    :style="{ color: typeColor(props.guest.tableType) }">
                    {{ typeLabel(props.guest.tableType) }}</span>
                <p v-if="props.guest.guestName" class="text-[11px] font-bold text-slate-400 truncate leading-tight">{{
                    props.guest.guestName }}</p>
            </div>
        </div>
        <button @click="emit('removeGuest', props.guest.id)"
            class="w-8 flex items-center justify-center text-rose-400 hover:text-white hover:bg-rose-500 transition-colors cursor-pointer transition-all h-full">
            ✕
        </button>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { typeLabel, typeColor } from '@/composables/useTableTypes.js';

const props = defineProps({ guest: Object })
const emit = defineEmits(['removeGuest', 'start-from-queue'])

function typeInitials(type) {
    if (!type) return ''
    if (type === 'ps5') return 'PS5'
    const words = type
        .replace(/([a-z])([A-Z])/g, '$1 $2')   // split camelCase: 
        .split(/[\s\-_]+/)
        .filter(Boolean)
    return words
        .slice(0, 2)
        .map(w => w[0].toUpperCase())
        .join('')
}
</script>