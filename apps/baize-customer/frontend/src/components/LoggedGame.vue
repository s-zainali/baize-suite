<template>
    <div class="group flex w-full items-center gap-4 rounded-2xl border px-4 py-3 text-left transition-all" :class="khata.bills.some(b => b.ref === game.receiptId) ?
        'border-amber-700/60 bg-amber-500/10 hover:border-amber-600 hover:bg-amber-500/15' :
        'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'"
        :title="`View bill for ${typeLabel(game.tableType)} #${game.tableNumber}`">
        <div>
            <div>
                <h3 class="font-black">{{ game.clubName }}</h3>
                <p class="text-xs text-slate-500">{{ game.branch }}</p>
            </div>
        </div>
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border"
            :style="{ borderColor: `${typeColor(game.tableType)}40`, backgroundColor: `${typeColor(game.tableType)}14` }">
            <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: typeColor(game.tableType) }" />
        </span>

        <div class="min-w-0 flex-1">
            <p class="text-[9px] font-black uppercase tracking-wider" :style="{ color: typeColor(game.tableType) }">
                {{ typeLabel(game.tableType) }} #{{ game.tableNumber }}
            </p>
            <p class="mt-0.5 truncate text-xs font-bold text-slate-200">
                {{ playedLabel(game) }}
            </p>
        </div>

        <div class="shrink-0 text-right">
            <p class="font-mono text-xs font-bold text-slate-300">{{
                durationLabel(game.minutes) }}</p>
            <p class="font-mono text-[10px] text-slate-400">Rs {{ game.cost }}</p>
        </div>

        <button type="button" @click="$emit('open-receipt')"
            class="cursor-pointer shrink-0 rounded-lg border px-2.5 py-1 text-[8px] font-black uppercase tracking-widest transition-all"
            :class="khata.bills.some(b => b.ref === game.receiptId) ? 'border-amber-600/80 text-amber-400 hover:border-amber-400 hover:bg-amber-500/20' : 'border-slate-700 text-slate-400 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-400'">
            Bill
        </button>
    </div>
</template>
<script setup>
import { typeLabel, typeColor } from '@baize/ui';
const props = defineProps({
    game: { type: Object },
    khata: { type: Object },
    durationLabel : {type: Function}
})

const emit = defineEmits(['open-receipt'])

function playedLabel(game) {
    if (!game.playedAt) return game.date || ''
    const when = new Date(game.playedAt)
    const time = when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    const sameDay = (a, b) => a.toDateString() === b.toDateString()
    if (sameDay(when, today)) return `Today, ${time}`
    if (sameDay(when, yesterday)) return `Yesterday, ${time}`
    return `${when.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}, ${time}`
}
</script>