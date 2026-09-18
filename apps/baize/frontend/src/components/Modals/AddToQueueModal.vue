<template>
    <div class="fixed inset-0 z-51 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-sm rounded-3xl p-6 shadow-2xl" :class="showPopup ? 'blur-sm' : ''">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-black text-white">ADD GUEST TO QUEUE</h2>
                <button @click="emit('close-modal')" class="text-slate-500 hover:text-white hover:cursor-pointer">✕</button>
            </div>

            <div class="flex justify-between gap-1 mb-6">
                <div class="flex justify-end items-center gap-2">
                    <span class="text-xs uppercase font-bold text-slate-400">Specific Lounge</span>
                    <button type="button" role="switch" :aria-checked="specificLounge" @click="toggleSpecificLounge"
                        class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg px-0.5 items-center transition-colors duration-300 ease-in-out focus:outline-none"
                        :class="!specificLounge ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                        <span class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                            :class="specificLounge ? 'translate-x-5' : 'translate-x-0'" />
                    </button>
                </div>
                <div class="flex justify-end items-center gap-2">
                    <span class="text-xs uppercase font-bold text-slate-400">Specific Table</span>
                    <button type="button" role="switch" :aria-checked="specificTable" @click="toggleSpecificTable"
                        class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg px-0.5 items-center transition-colors duration-300 ease-in-out focus:outline-none"
                        :class="!specificTable ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                        <span class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                            :class="specificTable ? 'translate-x-5' : 'translate-x-0'" />
                    </button>
                </div>
            </div>

            <div class="space-y-4 mb-6">
                <TextField :id="'guest-name'" :placeholder="'Guest Name (optional)'" :label="'Guest Name (optional)'" :form="form" :field="'guestName'" :type="'text'" />

                <DropdownField v-if="specificLounge || specificTable" :form="form" :options="loungeOptions" :field="'loungeUid'" :label="'Lounge'" :placeholder="'Select Lounge'" />

                <div class="bg-slate-950/40 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 flex flex-col">
                    <span class="font-bold text-slate-300 text-xs mb-3 tracking-wide">{{ specificTable ? 'Specific Table' : 'Station Type' }}</span>
                    <button type="button" @click="showPopup = true" aria-haspopup="listbox" :disabled="specificTable && !form.loungeUid"
                        class="w-full flex items-center justify-between bg-slate-900 rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors cursor-pointer border-slate-800 hover:border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed">
                        <span class="flex gap-2 items-center min-w-0 px-2" :class="displaySelectionLabel !== defaultPlaceholder ? 'font-bold text-white' : 'font-normal text-slate-600'">
                            <span class="truncate">{{ displaySelectionLabel }}</span>
                        </span>
                        <svg class="w-4 h-4 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            </div>

            <button @click="handleSubmit" :disabled="loading || !isValid"
                class="w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
                {{ loading ? 'ADDING…' : 'ADD TO QUEUE' }}
            </button>
        </div>
    </div>

    <SelectTableModal v-if="showPopup"
        :title="specificTable ? 'Choose specific table' : 'Choose table type'"
        :options="popupOptions"
        :model-value="specificTable ? form.tableUid : form.tableType"
        :rates="rates"
        :hideId="!specificTable"
        :activateSelected="!specificTable"
        :empty-text="specificTable ? 'No occupied tables in this lounge.' : 'No occupied station types to queue for.'"
        @confirm="onPicked"
        @close="showPopup = false" />
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { types } from '@/composables/useTableTypes.js'
import TextField from '../Fields/TextField.vue'
import DropdownField from '../Fields/DropdownField.vue'
import SelectTableModal from './SelectTableModal.vue'

const props = defineProps({
    tableLounge: [Array, Object],
    lounges: [Array, Object],
    rates: { type: Object, default: () => ({}) },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' },
})
const emit = defineEmits(['close-modal', 'enqueue'])

const specificLounge = ref(false)
const specificTable = ref(false)
const showPopup = ref(false)

const form = reactive({ guestName: '', loungeUid: '', tableType: '', tableUid: '' })

function toggleSpecificLounge() {
    specificLounge.value = !specificLounge.value
    if (!specificLounge.value) { specificTable.value = false; form.loungeUid = ''; form.tableUid = '' }
}
function toggleSpecificTable() {
    specificTable.value = !specificTable.value
    if (specificTable.value) specificLounge.value = true
    else form.tableUid = ''
}
watch(() => form.loungeUid, () => { form.tableUid = ''; form.tableType = '' })

const occupiedTables = computed(() => {
    if (!props.tableLounge) return []
    const list = Array.isArray(props.tableLounge) ? props.tableLounge : Object.values(props.tableLounge)
    return list.filter((t) => t.isActive)
})
const loungeOptions = computed(() => {
    if (!props.lounges) return []
    const list = Array.isArray(props.lounges) ? props.lounges : Object.values(props.lounges)
    const occupied = new Set(occupiedTables.value.map((t) => t.loungeUid).filter(Boolean))
    return list.filter((l) => occupied.has(l.uid)).map((l) => ({ label: l.name || 'Unknown Lounge', value: l.uid }))
})
const tablesInLounge = computed(() =>
    form.loungeUid ? occupiedTables.value.filter((t) => t.loungeUid === form.loungeUid) : [])
const availableTypes = computed(() => {
    const target = specificLounge.value && form.loungeUid ? tablesInLounge.value : occupiedTables.value
    const inUse = new Set(target.map((t) => t.type).filter(Boolean))
    return types.filter((t) => inUse.has(t.id) && t.entitled !== false)
})

// One options shape, two modes.
const popupOptions = computed(() => specificTable.value
    ? tablesInLounge.value.map((t) => ({ id: t.uid, type: t.type, table: t }))
    : availableTypes.value.map((t) => ({ id: t.id, type: t.id, table: t.sampleObject })))

function onPicked(id) {
    if (specificTable.value) {
        const t = tablesInLounge.value.find((x) => x.uid === id)
        if (t) { form.tableUid = t.uid; form.tableType = t.type }
    } else {
        form.tableType = id
        form.tableUid = ''
    }
    showPopup.value = false
}

const defaultPlaceholder = computed(() => specificTable.value ? 'Select Specific Table' : 'Select Station Type')
const displaySelectionLabel = computed(() => {
    if (specificTable.value) {
        if (!form.tableUid) return defaultPlaceholder.value
        const table = occupiedTables.value.find((t) => t.uid === form.tableUid)
        if (!table) return defaultPlaceholder.value
        const label = types.find((t) => t.id === table.type)?.label || table.type?.toUpperCase()
        return `${label} #${table.id || table.name || ''}`
    }
    if (!form.tableType) return defaultPlaceholder.value
    return types.find((t) => t.id === form.tableType)?.label || form.tableType
})

const isValid = computed(() => {
    if (specificTable.value) return !!form.loungeUid && !!form.tableUid
    if (specificLounge.value) return !!form.loungeUid && !!form.tableType
    return !!form.tableType
})
function handleSubmit() {
    if (!isValid.value) return
    emit('enqueue', { ...form })
    emit('close-modal')
}
</script>