<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-5xl rounded-3xl p-6 shadow-2xl">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-black text-white">Global Billing Scales</h2>
                <button @click="emit('close-modal')"
                    class="text-slate-500 hover:text-white hover:cursor-pointer">✕</button>
            </div>

            <div class="grid grid-cols-3 gap-4 mb-6">
                <div v-for="t in rows" :key="t.key"
                    class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 transition-all hover:border-slate-700">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-xs font-bold text-slate-300 capitalize tracking-wide">{{ t.label }}</span>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <StepperField v-model="local[t.key].weekday" label="Weekday" suffix="Rs" accent="slate" />
                        <StepperField v-model="local[t.key].weekend" label="Weekend" suffix="Rs" accent="amber" />
                    </div>
                </div>
                <p v-if="!rows.length" class="col-span-3 text-center text-sm text-slate-500 py-6">
                    No billable station types for this branch.
                </p>
            </div>

            <button @click="emit('save-configuration', deepCopy(local))"
                class="w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white transition-all cursor-pointer">
                SAVE CONFIGURATION
            </button>
        </div>
    </div>
</template>

<script setup>
import StepperField from '../Fields/StepperField.vue'
import { reactive, computed, watchEffect } from 'vue'
import { entitledTypes } from '@/composables/useTableTypes.js'

const props = defineProps({ rates: Object })
const emit = defineEmits(['close-modal', 'save-configuration'])

const deepCopy = (obj) => JSON.parse(JSON.stringify(obj))

// display order by category, not alphabetical
const ORDER = ['pool', 'privatePool', 'snooker', 'privateSnooker', 'ps5', 'foosball']
const rank = (key) => {
    const i = ORDER.indexOf(key)
    return i === -1 ? ORDER.length : i   // unknown types fall to the end
}

// local working copy so edits aren't committed until Save.
// tolerates either the new nested shape or a legacy flat number.
const local = reactive(
    Object.fromEntries(
        Object.entries(props.rates || {})
            .sort(([a], [b]) => rank(a) - rank(b))
            .map(([key, val]) => {
                if (val && typeof val === 'object') {
                    return [key, { weekday: val.weekday ?? 0, weekend: val.weekend ?? 0 }]
                }
                return [key, { weekday: val ?? 0, weekend: Math.round((val ?? 0) * 1.3) }]
            })
    )
)

// Only show billable rows for station types this branch is LICENSED for and that
// actually exist — no rates for unlicensed or unknown types. Existing rates for
// other types are left untouched in `local` and preserved on save.
watchEffect(() => {
    for (const t of entitledTypes.value) {
        if (!local[t.key]) local[t.key] = { weekday: 0, weekend: 0 }
    }
})
const rows = computed(() =>
    entitledTypes.value.slice().sort((a, b) => rank(a.key) - rank(b.key))
)
</script>