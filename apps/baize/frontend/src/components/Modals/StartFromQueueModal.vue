<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('closeModal')">

        <div class="bg-slate-900 border border-slate-800 w-full max-w-md max-h-[85vh] overflow-y-auto overscroll-contain rounded-3xl p-6 shadow-2xl">
            <h2 class="text-xl font-black text-white">Start session from queue</h2>
            <p class="text-xs text-slate-400 mb-6">
                Choose table to start session from the grid below
            </p>

            <p v-if="tables[props.newGuest.tableType].length === 0"
                class="text-xs text-slate-50 font-black mb-6 p-4 bg-rose-500/50 rounded-xl">No available tables - All
                tables busy</p>
            <div v-else class="mb-6 flex flex-col justify-center">
                <span class="text-s font-bold text-slate-300 capitalize tracking-wide mt-2 mb-1">{{ newGuest.tableType
                }}</span>
                <div
                    class="flex flex-wrap bg-slate-950/40 border border-slate-800 rounded-2xl p-4 transition-all hover:border-slate-700">
                    <button @click="to_uid = table.uid, isValid = true"
                        class="flex flex-column items-center justify-between py-3 px-1 m-1 rounded-2xl border transition-all text-left cursor-pointer hover:border-emerald-500 hover:bg-emerald-600/40 disabled:hover:bg-slate-800 disabled:hover:border-slate-800 disabled:cursor-default"
                        :disabled="table.isBooked"
                        :class="to_uid === table.uid
                            ? 'border-emerald-500 bg-emerald-600/40 shadow-md shadow-emerald-600'
                            : 'bg-slate-500/30'" v-for="table in tables[newGuest.tableType]">
                        <component :is="componentFor(table.type)" :table="table" :is-display="true" :bookings="bookings"
                            :current-rate="getCurrentRate(table.type)" :showBookingStatus="true" />
                    </button>
                </div>
            </div>
            <div class="flex gap-3">
                <button @click="emit('close-modal')"
                    class="flex-1 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">
                    Cancel
                </button>
                <button :disabled="!isValid" @click="emit('start-session', to_uid)"
                    class="flex-1 py-2 rounded-xl text-xs font-black bg-emerald-600 text-white hover:bg-emerald-500 cursor-pointer active:scale-99 disabled:bg-slate-800 disabled:text-slate-500 ">
                    Start
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { componentFor } from '@/composables/useTableTypes.js';

const to_uid = ref('')
const props = defineProps({ newGuest: Object, tableLounge: Array, rates: Object, bookings: Object })
const emit = defineEmits(['start-session', 'close-modal']);
const localTables = ref(props.tableLounge.map((table) => ({ ...table })));

// 2. Derive grouped visible tables dynamically from local state
const tables = computed(() => {
    const groups = {};
    groups[props.newGuest.tableType] = []

    const filtered = localTables.value.filter((table) => {
        if (table.isActive && table.uid !== to_uid) return false;
        if (table.type !== props.newGuest.tableType) return false
        return true;
    });

    filtered.forEach((table) => {
        if (!groups[table.type]) groups[table.type] = [];
        groups[table.type].push(table);
    });

    return groups;
});

const getCurrentRate = (type) => {
    const rate = props.rates?.[type]
    if (!rate) return 0
    const day = new Date().getDay()
    const isWeekend = day === 0 || day === 6
    return isWeekend ? rate.weekend : rate.weekday
}

const isValid = ref(false)
</script>