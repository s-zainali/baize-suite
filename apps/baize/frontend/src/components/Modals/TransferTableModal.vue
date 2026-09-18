<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">

        <div
            class="bg-slate-900 border border-slate-800 min-w-xl max-w-3xl rounded-3xl p-6 shadow-2xl flex flex-col gap-4">
            <div class="flex gap-6 justify-between">
                <div>
                    <h2 class="text-xl font-black text-white">Move session from table {{ from_table_id }} to:</h2>
                    <p class="text-xs text-slate-400">
                        Choose table to transfer session to from the grid below
                    </p>
                </div>
                <div class="flex flex-col gap-1">
                    <div class="flex justify-end items-center gap-2">
                        <!-- Label Text -->
                        <span class="text-xs uppercase font-bold text-slate-400">
                            Transfer to any type
                        </span>

                        <!-- Toggle Button Track -->
                        <button type="button" role="switch" :aria-checked="transferAnywhere"
                            @click="transferAnywhere = !transferAnywhere"
                            class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg flex px-0.5  items-center transition-colors duration-300 ease-in-out  focus:outline-none"
                            :class="!transferAnywhere ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                            <!-- Sliding Knob -->
                            <span
                                class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                                :class="transferAnywhere ? 'translate-x-5' : 'translate-x-0'" />
                        </button>
                    </div>
                    <div class="flex justify-end items-center gap-2">
                        <!-- Label Text -->
                        <span class="text-xs uppercase font-bold text-slate-400">
                            Swap active sessions
                        </span>

                        <!-- Toggle Button Track -->
                        <button type="button" role="switch" :aria-checked="enableSwapActive"
                            @click="enableSwapActive = !enableSwapActive"
                            class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg flex px-0.5  items-center transition-colors duration-300 ease-in-out  focus:outline-none"
                            :class="!enableSwapActive ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                            <!-- Sliding Knob -->
                            <span
                                class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                                :class="enableSwapActive ? 'translate-x-5' : 'translate-x-0'" />
                        </button>
                    </div>
                </div>
            </div>
            <div class="max-h-[60vh] space-y-2 overflow-y-scroll overscroll-contain rounded-2xl">
                <TransitionGroup name="list">
                    <div class="flex flex-col justify-center" v-for="type in Object.keys(tables)" :key="type">
                        <div
                            class="flex flex-col gap-2 bg-slate-950/40 border border-slate-800 rounded-2xl p-4 transition-all hover:border-slate-700">
                            <span class="text-md font-bold text-slate-300 capitalize tracking-widest">{{ type
                                }}</span>
                            <div class="flex flex-wrap gap-2">
                                <p v-if="tables[type].length === 0"
                                    class="text-xs text-slate-50 w-full p-4 bg-rose-600/50 rounded-xl font-black">No
                                    available tables </p>
                                <div class="text-white">
                                </div>
                                <TransitionGroup name="list">
                                    <button @click="handleSelect(table.uid)" :key="table"
                                        class="flex flex-column items-center justify-between py-2  rounded-2xl transition-all text-left text-slate-200 cursor-pointer border  disabled:hover:bg-slate-800 disabled:hover:border-slate-800 disabled:cursor-default"
                                        :disabled="table.isBooked" :class="to_uid === table.uid
                                            ? 'border-slate-400 bg-slate-400/40 hover:border-slate-400 hover:bg-slate-400/40 shadow-md shadow-slate-600'
                                            : 'hover:border-slate-600 hover:bg-slate-600/60 bg-slate-800 border-slate-800'" v-for="table in tables[type]">
                                        <component :is="componentFor(table.type)" :table="table" :is-display="true"
                                            :showBookingStatus="true" :bookings="bookings"
                                            :current-rate="getCurrentRate(table.type)" :selected="to_uid === table.uid" />
                                    </button>
                                </TransitionGroup>
                            </div>
                        </div>
                    </div>
                </TransitionGroup>
            </div>
            <div class="flex gap-3">
                <button @click="emit('close-modal')"
                    class="flex-1 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">
                    Cancel
                </button>
                <button @click="emit('transfer-table', { from_uid, to_uid, allowActive: enableSwapActive })" :disabled="!isValid"
                    class=" flex-1 w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
                    {{ selectedIsActive ? 'Swap' : 'Transfer' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { componentFor } from '@/composables/useTableTypes.js';

const props = defineProps({ from_uid: String, tableLounge: Array, rates: Object, bookings: Object });
const emit = defineEmits(['transfer-table', 'close-modal']);

const to_uid = ref(null);
const transferAnywhere = ref(false);   // allow a different station GROUP
const enableSwapActive = ref(false);   // allow picking an occupied station (swaps the two tabs)

const fromTable = props.tableLounge.find((table) => table.uid === props.from_uid);
const from_table_id = fromTable?.id;

const groupOf = (type) =>
    ['ps5', 'ps4', 'xboxx', 'xbox1', 'pc'].includes(type) ? 'console' : type === 'foosball' ? 'foosball' : 'billiards';
const fromGroup = groupOf(fromTable?.type);

// Grouped, filtered destinations. Read straight from props — selection lives in
// `to_uid`, so there's no need to clone or mutate the tables.
const tables = computed(() => {
    const groups = {};
    props.tableLounge
        .filter((table) => {
            if (table.uid === props.from_uid) return false;                       // not itself
            if (!enableSwapActive.value && table.isActive) return false;          // hide occupied unless swapping
            if (!transferAnywhere.value && groupOf(table.type) !== fromGroup) return false;
            return true;
        })
        .forEach((table) => {
            (groups[table.type] ||= []).push(table);
        });
    return groups;
});

function handleSelect(tableUid) {
    to_uid.value = to_uid.value === tableUid ? null : tableUid;
}

const isValid = computed(() => !!to_uid.value);
const selectedIsActive = computed(() =>
    !!to_uid.value && !!props.tableLounge.find((t) => t.uid === to_uid.value)?.isActive);

const getCurrentRate = (type) => {
    const rate = props.rates?.[type];
    if (!rate) return 0;
    const day = new Date().getDay();
    return (day === 0 || day === 6) ? rate.weekend : rate.weekday;
};
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
    transition: all 0.2s ease;
}

.list-enter-from,
.list-leave-to {
    opacity: 0;
    transform: scale(0.5);
}
</style>