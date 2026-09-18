<template>
    <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close')">
        <div class="relative flex flex-col gap-6 bg-slate-900 border-2 border-slate-800 p-6 rounded-3xl max-w-3xl max-h-[85vh]">
            <button @click="emit('close')" title="Close"
                class="absolute right-6 top-6 text-slate-300 hover:text-rose-400 cursor-pointer text-lg">✕</button>

            <h3 class="text-xl font-black tracking-tight text-white pr-8">{{ title }}</h3>

            <div v-if="options.length" class="grid gap-4 overflow-y-auto p-1"
                :style="{ gridTemplateColumns: `repeat(${columns}, minmax(116px, 1fr))` }">
                <button v-for="opt in options" :key="opt.id" type="button" @click="selected = opt.id"
                    class="cursor-pointer px-2 py-4 rounded-3xl border transition duration-300 ease-in-out hover:bg-slate-800 hover:border-slate-700"
                    :class="selected === opt.id ? 'bg-slate-800 border-slate-600 ring-2 ring-emerald-500/60' : 'border-slate-800'">
                    <component :is="componentFor(opt.type)"
                        :table="displayTable(opt)"
                        :current-rate="rateFor(opt.type)"
                        :hideId="hideId" :isDisplay="true" :showBookingStatus="false" :canManage="false" />
                </button>
            </div>
            <p v-else class="text-sm text-slate-500 py-12 text-center">{{ emptyText }}</p>

            <button @click="confirm" :disabled="!hasSelection"
                class="py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 transition duration-300 ease-in-out disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-default text-white cursor-pointer">
                Select
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { componentFor } from '@/composables/useTableTypes.js'

const props = defineProps({
    title: { type: String, default: 'Choose an option' },
    // [{ id, type, table }] — `table` is what the station card renders,
    // `type` picks which card, `id` is emitted on confirm.
    options: { type: Array, default: () => [] },
    modelValue: { type: [String, Number, null], default: null },
    rates: { type: Object, default: () => ({}) },
    // Hide the station number on the rendered card (renderers accept hideId).
    // Right for type-picking; off for real tables.
    hideId: { type: Boolean, default: false },
    // Light the selected card up as "active" — only for inactive sample cards.
    activateSelected: { type: Boolean, default: false },
    columns: { type: Number, default: 5 },
    emptyText: { type: String, default: 'Nothing to choose from.' },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'close'])

const selected = ref(props.modelValue)
watch(() => props.modelValue, (v) => { selected.value = v })
watch(selected, (v) => emit('update:modelValue', v))

const hasSelection = computed(() =>
    selected.value !== null && selected.value !== undefined && selected.value !== '')

// Fresh object every render — never mutate the shared sample/table (that was the bug).
function displayTable(opt) {
    if (!props.activateSelected) return opt.table
    return { ...opt.table, isActive: selected.value === opt.id }
}

function rateFor(type) {
    const r = props.rates?.[type]
    if (!r) return 0
    const day = new Date().getDay()
    return (day === 0 || day === 6) ? (r.weekend ?? 0) : (r.weekday ?? 0)
}

function confirm() {
    if (hasSelection.value) emit('confirm', selected.value)
}
</script>