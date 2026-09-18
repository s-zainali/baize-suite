<template>
    <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-3xl p-6 shadow-2xl">
            <div class="flex justify-between items-start mb-5">
                <div>
                    <h3 class="text-lg font-black text-white">Filter Sessions</h3>
                    <p class="text-xs text-slate-400 mt-1">Filters apply as you type.</p>
                </div>
                <button @click="emit('close-modal')"
                    class="text-slate-500 hover:text-white text-lg p-1 cursor-pointer">✕</button>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Receipt
                        Ref</label>
                    <input v-model.trim="filters.receiptId" type="text" placeholder="e.g. 1042"
                        class="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 focus:border-slate-600 rounded-xl px-3 py-2 text-xs text-white font-mono outline-none transition-colors placeholder:text-slate-600" />
                </div>
                <div>
                    <label
                        class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Player</label>
                    <input v-model.trim="filters.player" type="text" placeholder="Name contains…"
                        class="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 focus:border-slate-600 rounded-xl px-3 py-2 text-xs text-white font-bold outline-none transition-colors placeholder:text-slate-600" />
                </div>

                <!-- TABLE TYPE — custom dropdown -->
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Table
                        Type</label>
                    <div ref="typeRoot" class="relative">
                        <button type="button" @click="toggleTypeDropdown"
                            class="w-full flex items-center justify-between bg-slate-950/60 rounded-xl border px-3 py-2 text-xs outline-none transition-colors cursor-pointer"
                            :class="typeDropdownOpen ? 'border-slate-600' : 'border-slate-800 hover:border-slate-700'">
                            <span :class="selectedType ? 'font-bold text-white' : 'text-slate-600'">
                                {{ selectedType ? selectedType.label : 'All types' }}
                            </span>
                            <svg class="w-3.5 h-3.5 text-slate-500 transition-transform duration-200"
                                :class="typeDropdownOpen ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24"
                                stroke="currentColor" stroke-width="2.5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        <Transition enter-active-class="transition duration-150 ease-out"
                            enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0"
                            leave-active-class="transition duration-100 ease-in"
                            leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
                            <div v-if="typeDropdownOpen"
                                class="absolute left-0 right-0 top-full mt-2 z-20 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-slate-950/80 overflow-hidden p-1">
                                <button v-for="type in tableTypes" :key="type.value" type="button"
                                    @click="selectType(type)"
                                    class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-left transition-colors cursor-pointer"
                                    :class="filters.tableType === type.value
                                        ? 'bg-emerald-600/15 text-emerald-400 font-bold'
                                        : 'text-slate-300 font-bold hover:bg-slate-800 hover:text-white'">
                                    {{ type.label }}
                                    <svg v-if="filters.tableType === type.value" class="w-3.5 h-3.5" fill="none"
                                        viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                </button>
                            </div>
                        </Transition>
                    </div>
                </div>

                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Table
                        #</label>
                    <input v-model.trim="filters.tableId" type="text" placeholder="e.g. 3"
                        class="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 focus:border-slate-600 rounded-xl px-3 py-2 text-xs text-white font-bold font-mono outline-none transition-colors placeholder:text-slate-600" />
                </div>

                <!-- From Date -->
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">From Date</label>
                    <DateField v-model="filters.dateFrom" placeholder="Any date" />
                </div>

                <!-- To Date -->
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">To Date</label>
                    <DateField v-model="filters.dateTo" placeholder="Any date" />
                </div>

                <!-- From Time -->
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">From Time</label>
                    <TimeField v-model="filters.timeFrom" placeholder="Any time" />
                </div>

                <!-- To Time -->
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">To Time</label>
                    <TimeField v-model="filters.timeTo" placeholder="Any time" />
                </div>

                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Min
                        Cost (Rs)</label>
                    <input v-model.number="filters.minCost" type="number" min="0" placeholder="0"
                        class="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 focus:border-slate-600 rounded-xl px-3 py-2 text-xs text-white font-bold font-mono outline-none transition-colors placeholder:text-slate-600" />
                </div>
                <div>
                    <label class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-1.5">Max
                        Cost (Rs)</label>
                    <input v-model.number="filters.maxCost" type="number" min="0" placeholder="∞"
                        class="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 focus:border-slate-600 rounded-xl px-3 py-2 text-xs text-white font-bold font-mono outline-none transition-colors placeholder:text-slate-600" />
                </div>
            </div>

            <div class="flex justify-between items-center mt-6 pt-4 border-t border-slate-800">
                <button @click="emit('clear')"
                    class="text-xs font-bold text-slate-400 hover:text-red-400 px-3 py-2 cursor-pointer transition-colors">
                    Clear all
                </button>
                <div class="flex items-center gap-3">
                    <span class="text-[10px] text-slate-500 font-mono">{{ matchCount }} match{{
                        matchCount === 1 ? '' : 'es' }}</span>
                    <button @click="emit('close-modal')"
                        class="text-xs font-black text-white bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-xl transition-colors cursor-pointer">
                        Done
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, Transition } from 'vue'
import { tableTypeOptions } from '@/composables/useTableTypes.js'
import DateField from '../Fields/DateField.vue'
import TimeField from '../Fields/TimeField.vue'

// `filters` is the parent's reactive object — this component mutates its
// fields directly so the log table filters live as the user types.
const props = defineProps({
    filters: { type: Object, required: true },
    matchCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close-modal', 'clear'])

const { filters } = props

// ---------- TABLE TYPE DROPDOWN ----------
const tableTypes = computed(() => [{ value: '', label: 'All types' }, ...tableTypeOptions.value])

const typeDropdownOpen = ref(false)
const typeRoot = ref(null)

const selectedType = computed(() =>
    tableTypes.value.find(t => t.value === filters.tableType && t.value !== '') || null
)

function toggleTypeDropdown() {
    typeDropdownOpen.value = !typeDropdownOpen.value
}

function selectType(type) {
    filters.tableType = type.value
    typeDropdownOpen.value = false
}

// ---------- CLICK OUTSIDE ----------
function handleClickOutside(e) {
    if (typeRoot.value && !typeRoot.value.contains(e.target)) typeDropdownOpen.value = false
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
/* Number inputs: remove native spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

input[type="number"] {
    -moz-appearance: textfield;
    appearance: textfield;
}
</style>

<style>
/* Time picker scrollbar (unscoped: panel is rendered by an inline child component) */
.lounge-time-scroll::-webkit-scrollbar {
    width: 6px;
}

.lounge-time-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.lounge-time-scroll::-webkit-scrollbar-thumb {
    background: rgb(51 65 85);
    /* slate-700 */
    border-radius: 3px;
}

.lounge-time-scroll::-webkit-scrollbar-thumb:hover {
    background: rgb(71 85 105);
    /* slate-600 */
}
</style>