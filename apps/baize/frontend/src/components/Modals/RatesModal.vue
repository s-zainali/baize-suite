<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-3xl border border-slate-800 bg-slate-900 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 p-5">
                <div>
                    <h2 class="text-lg font-black text-white">Billing Scales</h2>
                    <p class="text-[11px] text-slate-500">Tap a station type to set its rates.</p>
                </div>
                <button @click="emit('close-modal')"
                    class="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-800 hover:text-white">✕</button>
            </div>

            <div class="flex-1 space-y-2.5 overflow-y-auto p-5">
                <div v-for="t in rows" :key="t.key"
                    class="overflow-hidden rounded-2xl border transition-colors"
                    :class="openKey === t.key ? 'border-slate-700 bg-slate-950/40' : 'border-slate-800 bg-slate-950/20 hover:border-slate-700'">

                    <!-- collapsed label row -->
                    <button type="button" @click="toggle(t.key)"
                        class="flex w-full items-center gap-3 px-4 py-3 text-left">
                        <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: t.color || '#64748b' }"></span>
                        <span class="flex-1 truncate text-sm font-black capitalize tracking-wide text-slate-100">{{ t.label }}</span>
                        <span class="rounded-md px-2 py-0.5 text-[9px] font-black uppercase tracking-wider"
                            :class="local[t.key].mode === 'per_minute' ? 'bg-slate-700/60 text-slate-300' : 'bg-emerald-500/15 text-emerald-400'">
                            {{ modeLabel(local[t.key].mode) }}
                        </span>
                        <span class="hidden font-mono text-xs font-bold text-slate-400 sm:inline">{{ summary(t.key) }}</span>
                        <svg class="h-4 w-4 shrink-0 text-slate-500 transition-transform duration-200"
                            :class="openKey === t.key ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="none"
                            stroke="currentColor" stroke-width="2">
                            <path d="M6 8l4 4 4-4" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                    </button>

                    <!-- expanded body -->
                    <div v-if="openKey === t.key" class="border-t border-slate-800 px-4 pb-4 pt-3">
                        <!-- one mode toggle for everything -->
                        <div class="flex gap-1.5 rounded-xl bg-slate-900 p-1">
                            <button type="button" @click="local[t.key].mode = 'per_minute'"
                                class="flex-1 cursor-pointer rounded-lg py-1.5 text-[10px] font-black uppercase tracking-wider transition-colors"
                                :class="local[t.key].mode === 'per_minute' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'">
                                Per Minute
                            </button>
                            <button type="button" @click="local[t.key].mode = 'per_game'"
                                class="flex-1 cursor-pointer rounded-lg py-1.5 text-[10px] font-black uppercase tracking-wider transition-colors"
                                :class="local[t.key].mode === 'per_game' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'">
                                Per Game
                            </button>
                            <button v-if="showSubgame(t.key)" type="button" @click="local[t.key].mode = 'per_subgame'"
                                class="flex-1 cursor-pointer rounded-lg py-1.5 text-[10px] font-black uppercase tracking-wider transition-colors"
                                :class="local[t.key].mode === 'per_subgame' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'">
                                Per Subgame
                            </button>
                        </div>

                        <!-- rate inputs — same selectors for every mode -->
                        <div class="mt-3">
                            <!-- per subgame: a rate per game type -->
                            <div v-if="local[t.key].mode === 'per_subgame' && gameTypesFor(t.key).length" class="space-y-2">
                                <div v-for="gt in gameTypesFor(t.key)" :key="gt"
                                    class="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                                    <div class="mb-2 text-[11px] font-black uppercase tracking-wider text-slate-200">{{ gt }}</div>
                                    <div class="grid grid-cols-2 gap-2">
                                        <StepperField v-model="local[t.key].gameRates[gt].weekday" label="Weekday" suffix="Rs" accent="slate" />
                                        <StepperField v-model="local[t.key].gameRates[gt].weekend" label="Weekend" suffix="Rs" accent="amber" />
                                    </div>
                                </div>
                            </div>
                            <!-- per game: one flat game rate -->
                            <div v-else-if="local[t.key].mode === 'per_game'" class="grid grid-cols-2 gap-3">
                                <StepperField v-model="local[t.key].weekdayGame" label="Weekday" suffix="Rs" accent="slate" />
                                <StepperField v-model="local[t.key].weekendGame" label="Weekend" suffix="Rs" accent="amber" />
                            </div>
                            <!-- per minute -->
                            <div v-else class="grid grid-cols-2 gap-3">
                                <StepperField v-model="local[t.key].weekday" label="Weekday" suffix="Rs" accent="slate" />
                                <StepperField v-model="local[t.key].weekend" label="Weekend" suffix="Rs" accent="amber" />
                            </div>
                        </div>
                    </div>
                </div>

                <p v-if="!rows.length" class="py-8 text-center text-sm text-slate-500">
                    No billable station types for this branch.
                </p>
            </div>

            <div class="border-t border-slate-800 p-4">
                <button @click="emit('save-configuration', deepCopy(local))"
                    class="w-full cursor-pointer rounded-xl bg-emerald-600 py-3 text-xs font-black uppercase tracking-wider text-white transition-all hover:bg-emerald-500">
                    Save Configuration
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import StepperField from '../Fields/StepperField.vue'
import { reactive, ref, computed, watchEffect } from 'vue'
import { entitledTypes } from '@/composables/useTableTypes.js'

const props = defineProps({
    rates: Object,
    gameTracking: { type: Boolean, default: false },
})
const emit = defineEmits(['close-modal', 'save-configuration'])

const deepCopy = (obj) => JSON.parse(JSON.stringify(obj))

// Which game variants (subgames) apply to each station type.
const GAME_TYPES = {
    pool: ['8-ball', '9-ball', '10-ball'],
    privatePool: ['8-ball', '9-ball', '10-ball'],
    snooker: ['snooker-15', 'snooker-10', 'snooker-6', 'century'],
    privateSnooker: ['snooker-15', 'snooker-10', 'snooker-6', 'century'],
}
const gameTypesFor = (key) => GAME_TYPES[key] || []
// Per-subgame is only meaningful for cue tables, and only once game tracking is on.
const showSubgame = (key) => props.gameTracking && gameTypesFor(key).length > 0

const ORDER = ['pool', 'privatePool', 'snooker', 'privateSnooker', 'ps5', 'foosball']
const rank = (key) => {
    const i = ORDER.indexOf(key)
    return i === -1 ? ORDER.length : i
}

const openKey = ref(null)
const toggle = (key) => { openKey.value = openKey.value === key ? null : key }

const modeLabel = (m) => (m === 'per_subgame' ? 'Per subgame' : m === 'per_game' ? 'Per game' : 'Per min')

const ensureGameRates = (key, gr) => {
    const out = gr && typeof gr === 'object' ? { ...gr } : {}
    for (const gt of gameTypesFor(key)) {
        out[gt] = { weekday: out[gt]?.weekday ?? 0, weekend: out[gt]?.weekend ?? 0 }
    }
    return out
}

const normalise = (key, val) => {
    const v = val && typeof val === 'object' ? val : { weekday: val ?? 0, weekend: Math.round((val ?? 0) * 1.3) }
    return {
        weekday: v.weekday ?? 0,
        weekend: v.weekend ?? 0,
        mode: v.mode ?? 'per_minute',
        weekdayGame: v.weekdayGame ?? 0,
        weekendGame: v.weekendGame ?? 0,
        gameRates: ensureGameRates(key, v.gameRates),
    }
}

const local = reactive(
    Object.fromEntries(
        Object.entries(props.rates || {})
            .sort(([a], [b]) => rank(a) - rank(b))
            .map(([key, val]) => [key, normalise(key, val)])
    )
)

watchEffect(() => {
    for (const t of entitledTypes.value) {
        if (!local[t.key]) local[t.key] = normalise(t.key, null)
        else local[t.key].gameRates = ensureGameRates(t.key, local[t.key].gameRates)
        // a type set to per_subgame but no longer eligible falls back gracefully
        if (local[t.key].mode === 'per_subgame' && !showSubgame(t.key)) local[t.key].mode = 'per_game'
    }
})

const rows = computed(() =>
    entitledTypes.value.slice().sort((a, b) => rank(a.key) - rank(b.key))
)

function summary(key) {
    const r = local[key]
    if (r.mode === 'per_subgame') {
        const vals = gameTypesFor(key).map((gt) => r.gameRates[gt]?.weekday || 0).filter(Boolean)
        return vals.length ? `Rs ${Math.min(...vals)}–${Math.max(...vals)}` : 'Rs 0'
    }
    if (r.mode === 'per_game') return `Rs ${r.weekdayGame}/${r.weekendGame}`
    return `Rs ${r.weekday}/${r.weekend}`
}
</script>