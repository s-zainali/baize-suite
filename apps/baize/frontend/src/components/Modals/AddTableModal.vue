<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-md rounded-3xl p-6 shadow-2xl relative"
            :class="showPopup ? 'blur-sm' : ''">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h2 class="text-xl font-black tracking-tight text-white">Add New Station</h2>
                    <p class="text-[11px] text-slate-500 mt-0.5">Name it whatever your staff call it.</p>
                </div>
                <button @click="emit('close-modal')" class="text-slate-500 hover:text-white text-lg p-1 cursor-pointer">✕</button>
            </div>

            <div class="space-y-4">
                <div class="bg-slate-950/40 border rounded-2xl p-4 transition-all"
                    :class="nameError ? 'border-rose-500/50' : 'border-slate-800 hover:border-slate-700'">
                    <label for="station-name" class="block text-xs font-bold text-slate-300 tracking-wide mb-3">Station Name</label>
                    <input id="station-name" v-model="form.tableId" type="text" maxlength="24"
                        placeholder="e.g. 1, or Corner Table" autocomplete="off" @keydown.enter="isValid && confirm()"
                        class="w-full bg-slate-900 rounded-xl border px-3 py-2.5 text-sm font-bold text-white outline-none transition-colors placeholder:font-normal placeholder:text-slate-600"
                        :class="nameError ? 'border-rose-500/50' : 'border-slate-800 focus:border-slate-600'" />
                    <p v-if="nameError" class="mt-2 text-[10px] font-bold text-rose-400">{{ nameError }}</p>
                    <p v-else class="mt-2 text-[10px] leading-snug text-slate-600">A number or a name — whatever's painted on the table. Must be unique.</p>
                </div>

                <DropdownField :form="form" :options="loungeOptions" :field="'loungeUid'" :label="'Lounge'" :placeholder="'Select Lounge'" />

                <div class="bg-slate-950/40 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 flex flex-col">
                    <span class="font-bold text-slate-300 text-xs mb-3 tracking-wide">Station Type</span>
                    <button type="button" @click="showPopup = true" aria-haspopup="listbox"
                        class="w-full flex items-center justify-between bg-slate-900 rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors cursor-pointer border-slate-800 hover:border-slate-700">
                        <span class="flex gap-2 items-center min-w-0 px-2" :class="selectedLabel ? 'font-bold text-white' : 'font-normal text-slate-600'">
                            <span v-if="form.type" class="h-2.5 w-2.5 rounded-full shrink-0" :style="{ backgroundColor: typeColor }"></span>
                            <span class="truncate">{{ selectedLabel || 'Select Station Type' }}</span>
                        </span>
                        <svg class="w-4 h-4 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>

                <div v-if="form.type" class="flex items-center justify-between rounded-2xl border p-4"
                    :style="{ borderColor: typeColor, backgroundColor: typeColor + '14' }">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl flex items-center justify-center font-bold"
                            :style="{ backgroundColor: typeColor + '1a', color: typeColor }">{{ selType.badge }}</div>
                        <div>
                            <p class="text-sm font-black text-white">{{ preview.label }}</p>
                            <p class="text-[10px] text-slate-500">{{ preview.loungeName }}</p>
                        </div>
                    </div>
                    <div class="text-right leading-tight">
                        <p class="text-xs font-mono font-bold" :style="{ color: typeColor }">{{ rate.weekday }} Rs/m</p>
                        <p class="text-[9px] font-mono font-bold text-amber-500/80">{{ rate.weekend }} wknd</p>
                    </div>
                </div>
            </div>

            <div class="flex gap-3 justify-end mt-6">
                <button @click="emit('close-modal')" class="px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 cursor-pointer">Cancel</button>
                <button @click="confirm" :disabled="!isValid"
                    class="px-5 py-2.5 rounded-xl text-xs font-black bg-gradient-to-r from-purple-600 to-indigo-600 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 text-white cursor-pointer">
                    Confirm Creation
                </button>
            </div>
        </div>
    </div>

    <SelectTableModal v-if="showPopup"
        title="Choose station type"
        :options="typeSelectOptions"
        :model-value="form.type"
        :rates="rates"
        :hideId="true"
        :activateSelected="true"
        empty-text="No station types configured."
        @confirm="onTypePicked"
        @close="showPopup = false" />
</template>

<script setup>
import { ref, computed } from 'vue'
import DropdownField from '../Fields/DropdownField.vue'
import SelectTableModal from './SelectTableModal.vue'
import { types, entitledTypes } from '@/composables/useTableTypes.js'

const props = defineProps({
    rates: { type: Object, default: () => ({}) },
    lounges: { type: Array, default: () => [] },
    tableTypes: { type: Array, default: () => [] },
    /**
     * Names already in use, so a clash is caught before the server. Every
     * existing station's `tableId` — the check is club-wide, since staff say
     * "table 3" without naming the room.
     */
    existingNames: { type: Array, default: () => [] },
})
const emit = defineEmits(['confirm-creation', 'close-modal'])

const form = ref({ tableId: '', type: '', loungeUid: '' })
const showPopup = ref(false)

const loungeOptions = computed(() => props.lounges.map((l) => ({ value: l.uid, label: l.name })))

// Visual picker renders each type's sample card. Single source: the registry.
const typeSelectOptions = computed(() =>
    entitledTypes.value.map((t) => ({ id: t.id, type: t.id, table: t.sampleObject })))
function onTypePicked(id) { form.value.type = id; showPopup.value = false }

const selectedType = computed(() => types.find((t) => t.id === form.value.type) || null)
const selectedLabel = computed(() => selectedType.value?.label || '')
const selType = computed(() => selectedType.value || {})
const typeColor = computed(() => selType.value.color || '#818cf8')

// ── validation ──────────────────────────────────────────────────────────────
const trimmedName = computed(() => form.value.tableId.trim())
const takenNames = computed(() => new Set(props.existingNames.map((n) => String(n).trim().toLowerCase())))
const nameError = computed(() => {
    const name = trimmedName.value
    if (!name) return ''
    if (takenNames.value.has(name.toLowerCase())) return 'A station already uses that name'
    if (name.length > 24) return 'Keep it under 24 characters'
    return ''
})
const isValid = computed(() =>
    !!trimmedName.value && !nameError.value && !!form.value.type && form.value.loungeUid !== '')
function confirm() {
    if (!isValid.value) return
    emit('confirm-creation', { ...form.value, tableId: trimmedName.value })
}

// ── preview ───────────────────────────────────────────────────────────────
const rate = computed(() => {
    const r = props.rates?.[form.value.type]
    return { weekday: r?.weekday ?? 0, weekend: r?.weekend ?? 0 }
})
const preview = computed(() => {
    const lounge = loungeOptions.value.find((l) => l.value === form.value.loungeUid)
    const label = selectedLabel.value || 'Station'
    return {
        label: trimmedName.value ? `${label} — ${trimmedName.value}` : label,
        loungeName: lounge?.label ?? 'No lounge selected',
    }
})
</script>