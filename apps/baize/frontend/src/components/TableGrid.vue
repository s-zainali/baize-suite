<template>
    <div class="border rounded-[3rem] p-6 pb-8 bg-border-slate-800/40 border-slate-700 shadow-md bg-slate-950/30">
        <!-- Lounge header -->
        <div class="flex justify-between items-center ml-2 mr-2 pb-6 border-b border-slate-600">
            <div class="flex items-center gap-2 group/name min-w-0">
                <template v-if="!editingName">
                    <h2 class="text-2xl font-bold text-slate-200 truncate tracking-widest">{{ lounge.name }}</h2>
                    <!-- <div>{{ bookings }}</div>
                    <div>{{ localTables }}</div> -->
                    <button @click="startRename" title="Rename lounge"
                        class="opacity-0 group-hover/name:opacity-100 text-slate-500 hover:text-white transition-all text-sm cursor-pointer">
                        ✎
                    </button>
                    <button v-if="localTables.length === 0 && props.canManage" @click="emit('remove-lounge', lounge.id)"
                        class="text-rose-500 hover:text-rose-400 border border-rose-500/30 hover:border-rose-400/60 rounded-lg px-2 py-1 transition-all font-bold text-[10px] cursor-pointer ml-1">
                        Remove Lounge ✕
                    </button>
                </template>
                <template v-else>
                    <input ref="nameInput" v-model.trim="nameDraft" @keyup.enter="commitRename"
                        @keyup.esc="cancelRename" @blur="commitRename" maxlength="60"
                        class="bg-slate-950/60 border border-slate-600 rounded-xl px-3 py-1 text-lg font-bold text-white outline-none w-64" />
                </template>
            </div>

            <button v-if="localTables.length > 1" @click="toggleRearrange"
                class="text-xs font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
                :class="rearrangeMode
                    ? 'bg-indigo-500 border-indigo-400 text-white'
                    : 'border-slate-700 text-slate-300 hover:text-white hover:border-slate-500'">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round"
                        d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
                {{ rearrangeMode ? 'Done' : 'Rearrange' }}
            </button>
        </div>

        <!-- Empty lounge -->
        <div v-if="localTables.length === 0"
            class="flex flex-col items-center justify-center text-center border-2 border-dashed border-slate-800 rounded-3xl p-8 mx-2 mt-8">
            <span class="text-3xl mb-2">🎱</span>
            <p class="text-sm font-bold text-slate-400">No tables in this lounge yet</p>
            <p class="text-xs text-slate-600 mt-1">Add tables here from the button above, or remove this lounge.</p>
        </div>

        <!-- Table grid -->
        <!-- The FLIP move is only wanted while dragging tables into a new order.
             Left always-on it also fired whenever the grid re-rendered — e.g.
             switching back to the dashboard re-inserts the cached view and the
             cards animated in from the top-left corner. Naming the group only in
             rearrange mode keeps the drag settle animation and drops that. -->
        <TransitionGroup v-else tag="main" :name="rearrangeMode ? 'tables' : 'nomove'"
            class="grid gap-y-6 gap-x-2 items-center justify-items-center grid-cols-[repeat(auto-fill,minmax(202px,1fr))]">
            <div v-for="(table, i) in localTables" :key="table.uid" :data-tidx="i" class="relative rounded-3xl" :class="[
                dragIndex === i ? 'z-50' : '',
                hoverIndex === i && dragIndex !== null && dragIndex !== i
                    ? 'ring-2 ring-emerald-400/70 ring-offset-4 ring-offset-slate-950'
                    : ''
            ]" :style="dragIndex === i ? { pointerEvents: 'none' } : null">
                <div :class="[
                    dragIndex === i ? 'transition-none scale-105 opacity-85' : 'transition-transform duration-200',
                    rearrangeMode && dragIndex === null ? 'lounge-wiggle' : ''
                ]" :style="dragIndex === i
                    ? { transform: `translate(${dragOffset.x}px, ${dragOffset.y}px) scale(1.05)` }
                    : null">
                    <component :is="componentFor(table.type)" :table="table" :current-rate="getCurrentRate(table.type)"
                        :canManage="canManage" :lounge-name="lounge.name" :bookings="bookings"
                        :locked="table.entitled === false && !table.isActive"
                        @update-status="emit('update-status', $event)" @open-receipt="emit('open-receipt', $event)"
                        @remove-table="emit('remove-table', $event)" @transfer-table="emit('transfer-table', $event)" />
                </div>

                <!-- Rearrange overlay: drag handle + input shield while in rearrange mode -->
                <div v-if="rearrangeMode"
                    class="absolute inset-0 z-40 rounded-3xl cursor-grab active:cursor-grabbing touch-none select-none flex items-start justify-center"
                    @pointerdown="onDragStart($event, i)" @pointermove="onDragMove" @pointerup="onDragEnd"
                    @pointercancel="onDragCancel">
                    <span
                        class="mt-2 px-2 py-0.5 rounded-full bg-slate-950/80 border border-slate-700 text-slate-400 text-[10px] font-black tracking-widest">
                        ⠿ DRAG
                    </span>
                </div>
            </div>
        </TransitionGroup>
    </div>
</template>

<script setup>
import { ref, computed, reactive, watch, nextTick } from 'vue';
import { authFetch, API_URL } from '@/Auth.js'
import PoolTable from './PoolTable.vue';
import Foosball from './Foosball.vue';
import ConsoleGame from './ConsoleGame.vue';

import { componentFor } from '@/composables/useTableTypes.js'

const props = defineProps({ lounge: Object, tableLounge: Array, rates: Object, canManage: Boolean, bookings: Object })
const emit = defineEmits(["open-receipt", "update-status", "remove-table", "transfer-table", "rename-lounge", "remove-lounge"])

// const API_URL = import.meta.env.VITE_API_URL

const getCurrentRate = (type) => {
    const rate = props.rates?.[type]
    if (!rate) return 0
    const day = new Date().getDay()
    const isWeekend = day === 0 || day === 6
    return isWeekend ? rate.weekend : rate.weekday
}

// ---------- LOUNGE NAME EDITING ----------
const editingName = ref(false)
const nameDraft = ref('')
const nameInput = ref(null)
let renameCommitted = false

async function startRename() {
    nameDraft.value = props.lounge.name
    editingName.value = true
    renameCommitted = false
    await nextTick()
    nameInput.value?.focus()
    nameInput.value?.select()
}

function commitRename() {
    if (renameCommitted) return // enter triggers blur too — commit once
    renameCommitted = true
    editingName.value = false
    const name = nameDraft.value.trim()
    if (name && name !== props.lounge.name) {
        emit('rename-lounge', { id: props.lounge.id, name })
    }
}

function cancelRename() {
    renameCommitted = true
    editingName.value = false
}

// ---------- LOCAL ORDER ----------
// Locally ordered copy so drags feel instant; re-synced when the parent's
// list changes, preserving the arrangement.
const localTables = ref([...(props.tableLounge || [])])


watch(() => props.tableLounge, (newTables) => {
    const order = localTables.value.map(t => t.uid)
    localTables.value = [...(newTables || [])].sort((a, b) => {
        const ia = order.indexOf(a.uid)
        const ib = order.indexOf(b.uid)
        if (ia === -1 && ib === -1) return 0
        if (ia === -1) return 1   // new tables go to the end
        if (ib === -1) return -1
        return ia - ib
    })
}, { deep: true })

// ---------- REARRANGE MODE ----------
// Drop-to-place model: the dragged card follows the pointer as a ghost
// (pure transform, no layout changes), the slot under the pointer gets a
// highlight, and the reorder happens once — on release.
const rearrangeMode = ref(false)
const dragIndex = ref(null)
const hoverIndex = ref(null)
const dragOffset = reactive({ x: 0, y: 0 })
let dragStart = { x: 0, y: 0 }

function toggleRearrange() {
    rearrangeMode.value = !rearrangeMode.value
    resetDrag()
}

function resetDrag() {
    dragIndex.value = null
    hoverIndex.value = null
    dragOffset.x = 0
    dragOffset.y = 0
}

function onDragStart(e, index) {
    e.preventDefault()
    dragIndex.value = index
    hoverIndex.value = null
    dragStart = { x: e.clientX, y: e.clientY }
    dragOffset.x = 0
    dragOffset.y = 0
    e.currentTarget.setPointerCapture(e.pointerId)
}

function onDragMove(e) {
    if (dragIndex.value === null) return
    dragOffset.x = e.clientX - dragStart.x
    dragOffset.y = e.clientY - dragStart.y

    // The dragged wrapper has pointer-events:none while dragging, so the
    // hit test finds the slot underneath the ghost.
    const el = document.elementFromPoint(e.clientX, e.clientY)?.closest('[data-tidx]')
    const over = el ? Number(el.dataset.tidx) : null
    hoverIndex.value = Number.isInteger(over) && over !== dragIndex.value ? over : null
}

function onDragEnd() {
    if (dragIndex.value === null) return

    if (hoverIndex.value !== null && hoverIndex.value !== dragIndex.value) {
        const arr = localTables.value
        const [moved] = arr.splice(dragIndex.value, 1)
        arr.splice(hoverIndex.value, 0, moved)
        persistOrder()
    }
    resetDrag()
}

function onDragCancel() {
    resetDrag()
}

async function persistOrder() {
    try {
        await authFetch(`${API_URL}/tables/reorder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: localTables.value.map(t => t.uid) }),
        })
    } catch (err) {
        console.error('Failed to save table arrangement', err)
    }
}
</script>

<style scoped>
/* FLIP animation when the grid settles into the new order */
.tables-move {
    transition: transform 0.25s ease;
}

/* Gentle wiggle while in rearrange mode (paused during an active drag) */
.lounge-wiggle {
    animation: lounge-wiggle 0.35s ease-in-out infinite;
}

@keyframes lounge-wiggle {

    0%,
    100% {
        transform: rotate(-0.5deg);
    }

    50% {
        transform: rotate(0.5deg);
    }
}
</style>