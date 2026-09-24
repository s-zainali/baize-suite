<template>
    <div class="overflow-hidden rounded-2xl border transition-colors"
        :class="isUnpaid ? 'border-amber-700/50 bg-amber-500/[0.04]' : 'border-slate-800 bg-slate-900/50'">

        <!-- collapsed row — club name + logo always visible; tap to expand -->
        <button type="button" @click="open = !open"
            class="flex w-full items-center gap-3 px-3.5 py-3 text-left transition-colors hover:bg-white/[0.02]">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-slate-800">
                <img v-if="game.clubLogo && !logoFailed" :src="game.clubLogo" alt="" class="h-full w-full object-cover"
                    @error="logoFailed = true" />
                <span v-else class="h-2.5 w-2.5 rounded-full" :style="{ background: color }"></span>
            </div>
            <div class="min-w-0 flex-1">
                <p class="truncate text-xs font-bold text-slate-100">{{ game.clubName || 'Session' }}</p>
                <p class="truncate text-[10px] text-slate-500">
                    {{ typeLabel(game.tableType) }} #{{ game.tableNumber }} · {{ playedLabel(game) }}
                </p>
            </div>
            <span v-if="isUnpaid"
                class="shrink-0 rounded-md bg-amber-500/15 px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider text-amber-400">
                Unpaid
            </span>
            <p class="shrink-0 font-mono text-xs font-bold" :class="isUnpaid ? 'text-amber-400' : 'text-slate-300'">
                Rs {{ game.cost }}
            </p>
            <svg class="h-4 w-4 shrink-0 text-slate-500 transition-transform duration-200"
                :class="open ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 8l4 4 4-4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
        </button>

        <!-- expanded — everything, one clean flow -->
        <div v-if="open" class="border-t border-white/5 px-3.5 pb-3.5 pt-3">
            <!-- club header -->
            <div class="flex items-center gap-3">
                <div class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-slate-800">
                    <img v-if="game.clubLogo && !logoFailed" :src="game.clubLogo" alt="" class="h-full w-full object-cover" />
                    <span v-else class="text-sm font-black" :style="{ color }">{{ (game.clubName || 'S').charAt(0) }}</span>
                </div>
                <div class="min-w-0">
                    <p class="truncate text-sm font-black text-slate-100">{{ game.clubName || 'Session' }}</p>
                    <p class="truncate text-[11px] text-slate-500">
                        {{ game.branch || '—' }}<span v-if="game.lounge"> · {{ game.lounge }}</span>
                    </p>
                </div>
            </div>

            <!-- detail rows -->
            <dl class="mt-3 space-y-2 rounded-xl bg-black/20 p-3">
                <div class="flex items-center justify-between">
                    <dt class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Station</dt>
                    <dd class="text-xs font-bold" :style="{ color }">{{ typeLabel(game.tableType) }} #{{ game.tableNumber }}</dd>
                </div>
                <div class="flex items-center justify-between">
                    <dt class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Played</dt>
                    <dd class="text-xs font-bold text-slate-200">{{ playedFull(game) }}</dd>
                </div>
                <div class="flex items-center justify-between">
                    <dt class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Duration</dt>
                    <dd class="font-mono text-xs font-bold text-slate-200">{{ durationLabel(game.minutes) }}</dd>
                </div>
                <div class="flex items-center justify-between">
                    <dt class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Amount</dt>
                    <dd class="font-mono text-xs font-bold" :class="isUnpaid ? 'text-amber-400' : 'text-emerald-400'">
                        Rs {{ game.cost }}
                    </dd>
                </div>
                <div class="flex items-center justify-between">
                    <dt class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Status</dt>
                    <dd>
                        <span class="rounded-md px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider"
                            :class="isUnpaid ? 'bg-amber-500/15 text-amber-400' : 'bg-emerald-500/15 text-emerald-400'">
                            {{ isUnpaid ? 'Unpaid · settle at counter' : 'Paid' }}
                        </span>
                    </dd>
                </div>
            </dl>

            <button type="button" @click.stop="$emit('open-receipt')"
                class="mt-3 w-full cursor-pointer rounded-xl border py-2 text-[9px] font-black uppercase tracking-widest transition-colors"
                :class="isUnpaid
                    ? 'border-amber-600/60 text-amber-300 hover:bg-amber-500/15'
                    : 'border-slate-700 text-slate-300 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-300'">
                View receipt
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { typeLabel, typeColor } from '@baize/ui'

const props = defineProps({
    game: { type: Object, required: true },
    khata: { type: Object, default: () => ({ bills: [] }) },
    durationLabel: { type: Function, required: true },
})
defineEmits(['open-receipt'])

const open = ref(false)
const logoFailed = ref(false)
const color = computed(() => typeColor(props.game.tableType))
const isUnpaid = computed(() =>
    (props.khata?.bills || []).some((b) => b.ref === props.game.receiptId))

function playedLabel(game) {
    if (!game.playedAt) return game.date || ''
    const when = new Date(game.playedAt)
    const time = when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    const today = new Date()
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
    const sameDay = (a, b) => a.toDateString() === b.toDateString()
    if (sameDay(when, today)) return `Today, ${time}`
    if (sameDay(when, yesterday)) return `Yesterday, ${time}`
    return `${when.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}, ${time}`
}
function playedFull(game) {
    if (!game.playedAt) return game.date || '—'
    const when = new Date(game.playedAt)
    return when.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
        + ', ' + when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}
</script>