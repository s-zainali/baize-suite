<template>
    <div class="mb-4 border border-slate-700 flex flex-col justify-center items-start z-40 bg-slate-800 shadow-md p-4 left-0 rounded-[1.5rem]"
        :class="sticky ? 'sticky top-0' : ''">
        <div class="flex justify-between w-full items-center pb-1">
            <h1 class="text-xl font-black tracking-wide text-white ml-2">Summary</h1>
            <div class="flex gap-4 items-center">
                <button
                    class="hidden sm:block text-[10px] w-25 uppercase font-bold bg-slate-900/80 px-2 py-1 rounded-md text-slate-300 hover:text-slate-50 cursor-pointer transition duration-300 ease-in-out active:scale-98"
                    :class="large ? 'hover:bg-rose-600/70' : 'hover:bg-emerald-600/70'" @click="toggleLarge">
                    {{ large ? 'Small' : 'Large' }}
                </button>
                <button
                    class="hidden sm:block text-[10px] w-25 uppercase font-bold bg-slate-900/80 px-2 py-1 rounded-md text-slate-300 hover:text-slate-50 cursor-pointer transition duration-300 ease-in-out active:scale-98"
                    :class="sticky ? 'hover:bg-rose-600/70' : 'hover:bg-emerald-600/70'" @click="toggleSticky">
                    {{ sticky ? 'hide' : 'show on top' }}
                </button>
                <div
                    class="flex items-center gap-3 shrink-0 bg-slate-950/40 border border-slate-700/60 rounded-2xl px-3 py-1.5">
                    <div class="relative w-8 h-8">
                        <svg width="32" height="32" viewBox="0 0 44 44" class="-rotate-90">
                            <circle cx="22" cy="22" r="18" stroke="#1e293b" stroke-width="5" fill="none" />
                            <circle cx="22" cy="22" r="18" :stroke="occupancyColor" stroke-width="5" fill="none"
                                stroke-linecap="round" :stroke-dasharray="`${(occupancyPct / 100) * ringC} ${ringC}`"
                                class="transition-all duration-700" />
                        </svg>
                        <span class="absolute inset-0 flex items-center justify-center text-[8px] font-black font-mono"
                            :style="{ color: occupancyColor }">
                            {{ occupancyPct }}%</span>
                    </div>

                    <span class="text-[8px] uppercase font-black tracking-widest text-slate-500 leading-tight">
                        Occupancy</span>
                </div>
            </div>
        </div>

        <div class="flex flex-nowrap gap-4 items-center w-full justify-between min-w-0 flex-1">
            <div class="flex gap-2 items-center min-w-0 flex-1 queue-scroll transition-all duration-300 ease-in-out"
                :class="large
                    ? 'flex-wrap overflow-y-auto'
                    : 'flex-nowrap overflow-x-auto'">
                <TransitionGroup name="card-list">
                    <SummaryCard v-for="t in tableTypes" :key="t.id" :t="t" :tableSummary="tableSummary"
                        class="transition-all duration-300 ease-in-out" :class="large
                            ? 'flex-1 min-w-[250px] max-w-[250px]'
                            : 'flex-1 min-w-[80px] shrink-0'" />
                </TransitionGroup>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import SummaryCard from './SummaryCard.vue'
import { loadSettings, settingValue, setSetting } from '@/composables/useSettings.js'

const props = defineProps({ tableTypes: Array, tableSummary: Object })

// Persisted across sessions/refreshes via the backend (key: summary_sticky).
const sticky = ref(settingValue('summary_sticky', false))
const large = ref(settingValue('summary_large', false))
onMounted(async () => {
    await loadSettings()
    sticky.value = settingValue('summary_sticky', false)
    large.value = settingValue('summary_large', false)
})
const toggleSticky = () => {
    sticky.value = !sticky.value
    setSetting('summary_sticky', sticky.value)
}
const toggleLarge = () => {
    large.value = !large.value
    setSetting('summary_large', large.value)
}

const totals = computed(() => {
    const sum = { total: 0, free: 0, occupied: 0, queueCount: 0 }
    for (const t of props.tableTypes || []) {
        const s = props.tableSummary?.[t.id]
        if (!s) continue
        sum.total += s.total || 0
        sum.free += s.free || 0
        sum.occupied += s.occupied || 0
        sum.queueCount += s.queueCount || 0
    }
    return sum
})

const occupancyPct = computed(() =>
    totals.value.total ? Math.round((totals.value.occupied / totals.value.total) * 100) : 0
)

// Ring geometry + color (same treatment as the overview page)
const ringC = 2 * Math.PI * 18

const occupancyColor = computed(() =>
    occupancyPct.value >= 80 ? '#34d399' : occupancyPct.value >= 40 ? '#38bdf8' : '#94a3b8'
)
</script>

<style scoped>
/* Vue TransitionGroup reordering & enter/leave animations */
.card-list-move,
.card-list-enter-active,
.card-list-leave-active {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-list-enter-from,
.card-list-leave-to {
    opacity: 0;
    transform: scale(0.95);
}

.card-list-leave-active {
    position: absolute;
}
</style>