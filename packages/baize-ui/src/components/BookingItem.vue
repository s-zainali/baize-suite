<template>
    <div
        class="bg-slate-950/40 border border-slate-800 rounded-2xl flex items-center justify-between gap-2 overflow-hidden h-12">
        <button v-if="!forCustomer && !isActive" @click="emit('start-from-booking', booking.id)" title="Start Session"
            class="w-8 flex items-center justify-center text-emerald-400 hover:text-white hover:bg-emerald-500 transition-colors cursor-pointer transition-all h-full">
            ✓
        </button>
        <div class="flex gap-4 flex-1 min-w-0 justify-between" :class="forCustomer? 'pl-4' : 'pl-0'">
            <div class="min-w-0">
                <div class="flex items-center gap-2">
                    <span class="text-[9px] font-black uppercase tracking-wider shrink-0"
                        :style="{ color: typeColor(booking.tableType) }">
                        {{ typeLabel(booking.tableType) }} #{{ booking.tableNumber }}</span>
                    <span v-if="isActive"
                        class="shrink-0 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-1.5 py-px text-[8px] font-black uppercase tracking-widest text-emerald-400">
                        Active
                    </span>
                </div>
                <p class="text-xs font-mono font-black tracking-[0.2em] text-white truncate mt-0.5"
                    :title="booking.guestName">{{ booking.code || '—' }}</p>
            </div>
    
            <div class="flex items-center gap-2 shrink-0">
                <div class="text-right">
                    <p class="text-[11px] font-mono font-bold leading-tight" :class="timeClass">{{ whenLabel }}</p>
                    <p class="text-[11px] font-mono text-slate-500 leading-tight">{{ clockLabel }}</p>
                </div>
            </div>
        </div>
        <span v-if="isActive"
            class="w-8 flex items-center justify-center h-full text-emerald-400" title="Session in progress">
            <span class="relative flex h-2 w-2">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
        </span>
        <button v-else @click="emit('cancel')" title="Cancel booking" :disabled="!forCustomer && whenLabel?.slice(0, 2) === 'in'"
            class="w-8 flex items-center justify-center text-rose-400 hover:text-white hover:bg-rose-500 transition-colors cursor-pointer transition-all h-full disabled:cursor-default disabled:hover:text-rose-400/80 disabled:hover:bg-rose-500/20">
            ✕
        </button>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { typeLabel, typeColor } from '../composables/tableTypeMeta.js'

const props = defineProps({ booking: { type: Object, required: true }, forCustomer: { type: Boolean, default: false } })
const emit = defineEmits(['cancel', 'start-from-booking'])

/** Started by staff, not yet stopped and billed. */
const isActive = computed(() => props.booking.status === 'active')


const start = computed(() => new Date(props.booking.startTime))

const clockLabel = computed(() =>
    start.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
)

// relative "in 20m" / "now" / "15m ago", recomputed whenever the parent re-renders
const whenLabel = computed(() => {
    if (isActive.value) return 'In progress'
    const diffMin = Math.round((start.value - Date.now()) / 60000)
    if (diffMin <= -1) return `${Math.abs(diffMin)}m ago`
    if (diffMin <= 0) return 'now'
    if (diffMin < 60) return `in ${diffMin}m`
    const h = Math.floor(diffMin / 60), m = diffMin % 60
    return m ? `in ${h}h ${m}m` : `in ${h}h`
})

const timeClass = computed(() => {
    // A running session isn't late, however long ago it was due to start
    if (isActive.value) return 'text-emerald-400'
    const diffMin = (start.value - Date.now()) / 60000
    if (diffMin <= 0) return 'text-rose-400'      // overdue / now
    if (diffMin <= 15) return 'text-amber-400'    // soon
    return 'text-slate-300'
})
</script>