<template>
    <div class="group relative overflow-hidden rounded-2xl border p-4 transition-all duration-300"
        :class="isUnpaid ? 'border-amber-600/40 hover:border-amber-500/70' : 'border-slate-800 hover:border-slate-700'"
        :style="cardStyle">

        <!-- felt glow in the table's colour -->
        <div class="pointer-events-none absolute -right-10 -top-12 h-36 w-36 rounded-full opacity-20 blur-3xl transition-opacity duration-300 group-hover:opacity-40"
            :style="{ background: color }"></div>
        <!-- faint baize grid -->
        <div class="pointer-events-none absolute inset-0 opacity-[0.04] felt-grid"></div>
        <!-- glowing colour spine -->
        <div class="absolute inset-y-3 left-0 w-1 rounded-full"
            :style="{ background: color, boxShadow: `0 0 14px ${color}` }"></div>

        <div class="relative pl-3">
            <!-- header: club + type pill -->
            <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                    <h3 class="truncate text-sm font-black text-slate-100">{{ game.clubName || 'Session' }}</h3>
                    <p class="truncate text-[11px] text-slate-500">
                        {{ game.branch || '—' }}<span v-if="game.lounge"> · {{ game.lounge }}</span>
                    </p>
                </div>
                <span class="shrink-0 rounded-full px-2.5 py-1 text-[9px] font-black uppercase tracking-widest"
                    :style="{ color, backgroundColor: `${color}1a`, border: `1px solid ${color}40` }">
                    {{ typeLabel(game.tableType) }} <span class="opacity-70">#{{ game.tableNumber }}</span>
                </span>
            </div>

            <!-- hero: duration + total -->
            <div class="mt-4 flex items-end justify-between">
                <div>
                    <p class="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Played</p>
                    <p class="mt-0.5 font-mono text-2xl font-black leading-none text-slate-100">
                        {{ durationLabel(game.minutes) }}
                    </p>
                </div>
                <div class="text-right">
                    <p class="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Total</p>
                    <p class="mt-0.5 font-mono text-2xl font-black leading-none"
                        :class="isUnpaid ? 'text-amber-400' : 'text-emerald-400'">
                        <span class="align-top text-xs opacity-70">Rs </span>{{ game.cost }}
                    </p>
                </div>
            </div>

            <!-- footer: when · status · receipt -->
            <div class="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
                <span class="flex items-center gap-1.5 text-[10px] font-medium text-slate-400">
                    <span class="h-1 w-1 rounded-full" :style="{ background: color }"></span>
                    {{ playedLabel(game) }}
                </span>
                <div class="flex items-center gap-2">
                    <span v-if="isUnpaid"
                        class="rounded-md bg-amber-500/15 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-amber-400">
                        Unpaid
                    </span>
                    <button type="button" @click="$emit('open-receipt')"
                        class="cursor-pointer rounded-lg border px-3 py-1 text-[9px] font-black uppercase tracking-widest transition-all"
                        :class="isUnpaid
                            ? 'border-amber-600/60 text-amber-300 hover:bg-amber-500/20'
                            : 'border-slate-700 text-slate-300 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-300'">
                        Receipt
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { typeLabel, typeColor } from '@baize/ui'

const props = defineProps({
    game: { type: Object, required: true },
    khata: { type: Object, default: () => ({ bills: [] }) },
    durationLabel: { type: Function, required: true },
})
defineEmits(['open-receipt'])

const color = computed(() => typeColor(props.game.tableType))
const isUnpaid = computed(() =>
    (props.khata?.bills || []).some((b) => b.ref === props.game.receiptId))

// A whisper of the table's colour bled into the felt of the card.
const cardStyle = computed(() => ({
    background: `linear-gradient(135deg, ${color.value}12 0%, rgba(15,23,42,0.7) 46%, rgba(2,6,23,0.85) 100%)`,
}))

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
</script>

<style scoped>
/* subtle woven-baize texture */
.felt-grid {
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.6) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.6) 1px, transparent 1px);
    background-size: 7px 7px;
}
</style>