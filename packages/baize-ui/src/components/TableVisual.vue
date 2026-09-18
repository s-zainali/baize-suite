<template>
    <!-- Display-only station graphic. Zero staff logic — pure visual, shared by
         the club app (which wraps it with controls) and the customer app. -->
    <div :style="{ width: '101px', height: heightPx }">
        <div class="w-[202px] relative flex-none px-4 scale-50 origin-top-left">
            <!-- VIP frame -->
            <div v-if="isPrivate"
                class="absolute -inset-y-4 inset-x-0 rounded-[2rem] bg-slate-950/40 border-2 border-dashed border-amber-800/40 pointer-events-none z-0"></div>

            <div class="flex flex-col items-center w-full relative z-10">
                <!-- ── POOL / SNOOKER ── -->
                <div v-if="isCue"
                    class="relative w-full rounded-2xl border-[0.8rem] shadow-xl flex items-center justify-center"
                    :class="[isSnooker ? 'h-[380px]' : 'h-[350px]', feltClasses]">
                    <span v-for="pos in holePositions" :key="pos" class="absolute w-5 h-5 rounded-full bg-slate-950/90 border border-black/40" :class="holeClass(pos)"></span>
                    <div class="inset-x-0 flex flex-col items-center px-4 text-center z-10 gap-4 h-full justify-between py-4">
                        <div class="h-8 flex flex-col items-center justify-center">
                            <span class="flex flex-col items-center font-black uppercase tracking-[0.2em] leading-tight text-xl" :class="labelColorClass">
                                <template v-if="isPrivate"><span>{{ isSnooker ? 'Snooker' : 'Pool' }}</span><span class="opacity-70 mt-0.5 text-xs">VIP Room</span></template>
                                <template v-else><span>{{ label }}</span></template>
                            </span>
                        </div>
                        <span class="font-black drop-shadow-md tracking-tight leading-none text-6xl" :class="hideId ? 'text-transparent' : 'text-white'">{{ id }}</span>
                        <span v-if="!hideRate && rate != null" class="text-xl font-semibold tracking-wider text-slate-200">{{ rate }} Rs/min</span>
                    </div>
                    <div v-if="booked" class="absolute h-full w-full flex items-center justify-center z-40 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                </div>

                <!-- ── CONSOLE (PlayStation / Xbox / PC) ── -->
                <div v-else-if="isConsole"
                    class="relative w-full h-[390px] rounded-2xl border-2 shadow-xl bg-slate-950 flex flex-col items-center px-3 pb-8 overflow-hidden gap-4 pt-4 justify-between"
                    :class="active ? consoleBorder : 'border-slate-800'">
                    <div class="relative w-full aspect-[16/10] rounded-lg border-[3px] border-slate-700 overflow-hidden mt-2" :class="screenClasses"></div>
                    <span class="font-black uppercase tracking-[0.2em] text-xl" :class="consoleText">{{ label }}</span>
                    <span class="font-black text-6xl" :class="hideId ? 'text-transparent' : 'text-white'">{{ id }}</span>
                    <span v-if="!hideRate && rate != null" class="text-lg font-semibold tracking-wider text-slate-300">{{ rate }} Rs/min</span>
                    <div class="mx-auto w-8 h-1.5 bg-slate-700"></div>
                    <div v-if="booked" class="absolute h-full w-full flex items-center justify-center z-40 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                </div>

                <!-- ── FOOSBALL ── -->
                <div v-else
                    class="relative w-full h-[380px] rounded-2xl border-2 shadow-xl bg-slate-950 flex flex-col items-center px-3 py-6 overflow-hidden gap-4 justify-between"
                    :class="active ? 'border-lime-400 shadow-2xl shadow-lime-400/40' : 'border-slate-800'">
                    <span class="font-black uppercase tracking-[0.2em] text-xl text-slate-400">Foosball</span>
                    <div class="w-full h-[88px] rounded-lg border-[3px] border-slate-700 relative overflow-hidden"
                        :class="active ? 'bg-gradient-to-br from-emerald-500 to-emerald-700' : 'bg-gradient-to-br from-slate-900 to-slate-950'">
                        <div class="absolute inset-y-0 left-1/2 w-px bg-white/15"></div>
                        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 rounded-full border border-white/15"></div>
                        <div v-for="x in ['22%','40%','60%','78%']" :key="x" class="absolute inset-y-0 w-[2px] bg-white/15" :style="{ left: x }"></div>
                    </div>
                    <span class="font-black text-6xl" :class="hideId ? 'text-transparent' : 'text-white'">{{ id }}</span>
                    <span v-if="!hideRate && rate != null" class="text-lg font-semibold tracking-wider text-slate-300">{{ rate }} Rs/min</span>
                    <div v-if="booked" class="absolute h-full w-full flex items-center justify-center z-40 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
    type: { type: String, required: true },     // snooker | pool | privateSnooker | privatePool | ps5 | ps4 | xboxx | xbox1 | pc | foosball
    id: { type: [String, Number], default: '' },
    rate: { type: [Number, String], default: null },
    booked: { type: Boolean, default: false },
    active: { type: Boolean, default: false },
    hideId: { type: Boolean, default: false },
    hideRate: { type: Boolean, default: false },
    label: { type: String, default: '' },
})
const t = computed(() => (props.type || '').toLowerCase())
const isSnooker = computed(() => t.value.includes('snooker'))
const isPool = computed(() => t.value.includes('pool'))
const isPrivate = computed(() => t.value.includes('private'))
const isCue = computed(() => isSnooker.value || isPool.value)
const isConsole = computed(() => ['ps5', 'ps4', 'xboxx', 'xbox1', 'pc'].includes(t.value))
const isPlaystation = computed(() => t.value.startsWith('ps'))
const isPc = computed(() => t.value === 'pc')

const heightPx = computed(() => (isSnooker.value ? '190px' : isConsole.value ? '195px' : '190px'))
const label = computed(() => props.label || (props.type || '').toUpperCase())

const feltClasses = computed(() => {
    if (props.type === 'privateSnooker') return props.active ? 'border-amber-500/90 bg-emerald-700' : 'border-amber-950 bg-emerald-900'
    if (isSnooker.value) return props.active ? 'border-pool-wood-500 bg-emerald-700' : 'border-pool-wood-900 bg-emerald-900'
    if (props.type === 'privatePool') return props.active ? 'border-amber-500/90 bg-sky-600' : 'border-amber-950 bg-sky-800'
    return props.active ? 'border-pool-wood-500 bg-sky-600' : 'border-pool-wood-900 bg-sky-800'
})
const labelColorClass = computed(() => (isSnooker.value ? 'text-emerald-200/60' : 'text-sky-200/60'))
const holePositions = ['top-left', 'top-right', 'mid-left', 'mid-right', 'bottom-left', 'bottom-right']
const holeClass = (pos) => ({
    'top-left': 'top-1 left-1', 'top-right': 'top-1 right-1',
    'mid-left': 'top-1/2 -translate-y-1/2 left-0.5', 'mid-right': 'top-1/2 -translate-y-1/2 right-0.5',
    'bottom-left': 'bottom-1 left-1', 'bottom-right': 'bottom-1 right-1',
}[pos])

const consoleBorder = computed(() => (isPlaystation.value ? 'border-blue-400' : isPc.value ? 'border-purple-400' : 'border-green-500'))
const consoleText = computed(() => (isPlaystation.value ? 'text-blue-300/70' : isPc.value ? 'text-purple-300/70' : 'text-green-600/70'))
const screenClasses = computed(() => (isPlaystation.value
    ? 'bg-gradient-to-br from-sky-300 via-sky-500 to-sky-300'
    : isPc.value ? 'bg-gradient-to-br from-purple-400 via-purple-600 to-purple-400'
        : 'bg-gradient-to-br from-emerald-400 via-emerald-600 to-emerald-400'))
</script>