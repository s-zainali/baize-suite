<template>
    <div :style="isDisplay ? { width: '101px', height: `${isSnooker ? '190px' : '175px'}` } : {}">
        <div class="w-[202px] relative flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : ' mt-12'">

            <!-- VIP Container Indicator -->
            <div v-if="isPrivatePool || isPrivateSnooker"
                class="absolute -inset-y-4 inset-x-0 rounded-[2rem] bg-slate-950/40 border-2 border-dashed pointer-events-none z-0 transition-colors duration-500"
                :class="[
                    props.table.isActive
                        ? 'border-amber-500/80 shadow-amber-950/30'
                        : 'border-amber-800/40'
                ]">
                <!-- <div class="absolute -top-3 left-1/2 -translate-x-1/2 text-white font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full uppercase shadow-md whitespace-nowrap transition-colors duration-500"
                    :class="isPrivateSnooker ? (props.table.isActive ? 'bg-amber-600' : 'bg-amber-950') : 'bg-purple-600'">
                    {{ isPrivateSnooker ? 'VIP SNOOKER' : 'VIP POOL' }} #{{ table.id }}
                </div> -->
            </div>

            <div class="flex flex-col items-center w-full relative z-10 group">
                <div class="relative w-full rounded-2xl border-[0.8rem] shadow-xl transition-all duration-500"
                    :class="[isSnooker ? 'h-[380px]' : 'h-[350px]', tableThemeClasses, isDisplay ? 'flex items-center justify-center' : '']">
                    <PoolHole v-for="pos in holePositions" :key="pos" :position="pos" />
                    <span v-if="showBookingStatus && isDisplay && table.isActive"
                        class="absolute top-20 bg-amber-400 py-0.5 px-2 rounded-lg font-black tracking-widest uppercase text-md text-slate-900/90">!
                        ACTIVE</span>
                    <div class="inset-x-0 flex flex-col items-center px-4 pointer-events-none text-center z-10"
                        :class="isDisplay ? 'gap-4 h-full items-center justify-between py-4' : 'absolute top-1.5'">
                        <div class="h-8 flex flex-col items-center justify-center">
                            <span class="flex flex-col items-center font-black uppercase tracking-[0.2em] leading-tight"
                                :class="labelColorClass, isDisplay ? 'text-xl' : 'text-[9px]'">
                                <template v-if="isPrivateSnooker">
                                    <span>Snooker</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else-if="table.type === 'privatePool'">
                                    <span>Pool</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else>
                                    <span>{{ table.type.toUpperCase() }}</span>
                                </template>
                            </span>
                        </div>

                        <span class="font-black drop-shadow-md tracking-tight leading-none"
                            :class="isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white'">
                            {{ table.id }}
                        </span>
                    </div>

                    <div v-if="!isDisplay"
                        class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-center z-10 w-full px-3">
                        <div class="text-2xl font-mono font-bold tracking-wider px-2 py-0.5 rounded-lg transition-all duration-200 py-1"
                            :class="timerClasses">
                            {{ formattedTime }}
                        </div>
                        <div v-if="canResume"
                            class="mt-1 text-sm font-black font-mono text-amber-300 bg-slate-950/50 rounded-md px-2 py-0.5">
                            Rs {{ pendingTotal }}
                        </div>
                    </div>
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span
                            class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒
                            LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                </div>
            </div>

            <p v-if="error"
                class="absolute -bottom-6 inset-x-0 text-center text-[9px] font-bold text-rose-400 px-1 leading-tight z-30">
                {{ error }}
            </p>
        </div>
    </div>
</template>

<script setup>

import { computed, ref } from 'vue'
import PoolHole from './PoolHole.vue'

const props = defineProps({
    locked: { type: Boolean, default: false },
    table: Object, currentRate: Number,
    loungeName: { type: String, default: '' },
    isDisplay: { type: Boolean, default: false },
    showBookingStatus: { type: Boolean, default: true },
    canManage: Boolean,
    selected: { type: Boolean, default: false },
    slotBooked: { type: Boolean, default: false },
    bookings: Object,
    hideId: { type: Boolean, default: false },
    hideDisplayRate: { type: Boolean, default: false }
})

const holePositions = [
    'top-left',
    'top-right',
    'mid-left',
    'mid-right',
    'bottom-left',
    'bottom-right',
]

const isSnooker = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('snooker'),
)
const isPool = computed(() => props.table.type && props.table.type.toLowerCase().includes('pool'))
const isPrivatePool = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('private'),
)
const isPrivateSnooker = computed(() => props.table.type === 'privateSnooker')

const tableThemeClasses = computed(() => {
    if (isPrivateSnooker.value) {
        return props.table.isActive
            ? 'border-amber-500/90 bg-emerald-700 shadow-2xl '
            : 'border-amber-950 bg-emerald-900'
    }

    if (isSnooker.value)
        return props.table.isActive
            ? 'border-pool-wood-500 bg-emerald-700 shadow-2xl '
            : 'border-pool-wood-900 bg-emerald-900'

    if (isPrivatePool.value)
        return props.table.isActive
            ? 'border-amber-500/90 bg-sky-600 shadow-2xl '
            : 'border-amber-950 bg-sky-800'

    if (isPool.value)
        return props.table.isActive
            ? 'border-pool-wood-500  bg-sky-600 shadow-2xl'
            : 'border-pool-wood-900 bg-sky-800'

    return props.table.isActive
        ? 'border-purple-400 bg-sky-600 shadow-2xl shadow-purple-500/40'
        : 'border-purple-900 bg-sky-600'
})
</script>