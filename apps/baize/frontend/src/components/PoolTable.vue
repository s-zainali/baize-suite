<template>
    <div :style="isDisplay ? { width: '101px', height: `${isSnooker ? '190px' : '175px'}` } : {}">
        <div class="w-[202px] relative flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : ' mt-12'">
            <div v-if="!isDisplay"
                class="absolute -top-10 inset-x-3 flex flex-col items-center pointer-events-none z-30">
                <div class="flex justify-between w-2/3 h-5">
                    <div class="w-[1px] h-full bg-slate-700/60"></div>
                    <div class="w-[1px] h-full bg-slate-700/60"></div>
                </div>

                <div class="w-full h-2.5 rounded-full bg-slate-950 border border-slate-800 transition-all duration-500 relative"
                    :class="[props.table.isActive ? 'border-white/20' : '']">
                    <div class="absolute inset-x-1 bottom-0 h-[2px] rounded-full transition-all duration-500" :class="[
                        props.table.isActive
                            ? `${canopyGlowColorClass} opacity-100 shadow-[0_3px_15px_4px_rgba(255,255,255,1)]`
                            : 'bg-slate-800 opacity-60 shadow-none',
                    ]"></div>
                </div>

                <div class="w-full h-8 transition-all duration-500 origin-top transform scale-x-110 filter blur-sm clip-cone"
                    :class="[props.table.isActive ? `${canopyBeamColorClass} opacity-25` : 'bg-transparent opacity-0']">
                </div>
            </div>

            <!-- VIP Container Indicator -->
            <div v-if="isPrivatePool || isPrivateSnooker"
                class="absolute -inset-y-4 inset-x-0 rounded-[2rem] bg-slate-950/40 border-2 border-dashed pointer-events-none z-0 transition-colors duration-500"
                :class="[
                    props.table.isActive
                        ? 'border-amber-500/80 shadow-amber-950/30'
                        : 'border-amber-800/40'
                ]">
                <!-- <div class="absolute -top-3 left-1/2 -translate-x-1/2 text-white font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full uppercase shadow-md whitespace-nowrap transition-colors duration-500"
                    :class="isPrivateSnooker ? (props.table.isActive ? 'bg-amber-600' : 'bg-amber-950') : 'bg-purple-600'">
                    {{ isPrivateSnooker ? 'VIP SNOOKER' : 'VIP POOL' }} #{{ table.id }}
                </div> -->
            </div>

            <div class="flex flex-col items-center w-full relative z-10 group">
                <div v-if="!isDisplay"
                    class="w-full flex justify-between items-center px-1.5 mb-1.5 text-[10px] font-semibold tracking-wider text-slate-400">
                    <span>{{ currentRate }} Rs/min</span>
                    <button v-if="!props.table.isActive && props.canManage" @click="$emit('remove-table', table.uid)"
                        class="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-400 transition-all font-bold text-[9px] cursor-pointer">
                        Remove ✕
                    </button>
                </div>
                <div class="relative w-full rounded-2xl border-[0.8rem] shadow-xl transition-all duration-500"
                    :class="[isSnooker ? 'h-[380px]' : 'h-[350px]', tableThemeClasses, isDisplay ? 'flex items-center justify-center' : '']">
                    <PlayerChips v-if="roster.length && playersModal" :players="roster" :removable="!table.isActive"
                        @close="playersModal = false" />
                    <PoolHole v-for="pos in holePositions" :key="pos" :position="pos" />
                    <span v-if="showBookingStatus && isDisplay && table.isActive"
                        class="absolute top-20 bg-amber-400 py-0.5 px-2 rounded-lg font-black tracking-widest uppercase text-md text-slate-900/90">!
                        ACTIVE</span>
                    <div class="inset-x-0 flex flex-col items-center px-4 pointer-events-none text-center z-10"
                        :class="isDisplay ? 'gap-4 h-full items-center justify-between py-4' : 'absolute top-1.5'">
                        <div class="h-8 flex flex-col items-center justify-center">
                            <span class="flex flex-col items-center font-black uppercase tracking-[0.2em] leading-tight"
                                :class="labelColorClass, isDisplay ? 'text-xl' : 'text-[9px]'">
                                <template v-if="isPrivateSnooker">
                                    <span>Snooker</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else-if="table.type === 'privatePool'">
                                    <span>Pool</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else>
                                    <span>{{ table.type.toUpperCase() }}</span>
                                </template>
                            </span>
                        </div>

                        <span class="font-black drop-shadow-md tracking-tight leading-none"
                            :class="isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white'">
                            {{ table.id }}
                        </span>

                        <span v-if="isDisplay && !hideDisplayRate" class="text-xl font-semibold tracking-wider text-slate-200">{{
                            currentRate }}
                            Rs/min</span>


                        <div class="w-full mt-2" v-if="!isDisplay">
                            <PlayerIndicator v-if="roster.length" :roster="roster" @view="playersModal = true" />
                            <div v-if="props.table.isActive" class="text-center">
                                <span
                                    class="block text-[8px] font-bold uppercase tracking-wide opacity-60 text-white mb-0.5">Playing</span>
                                <p v-if="!roster.length"
                                    class="text-xs font-extrabold text-white truncate max-w-[105px] mx-auto">
                                    {{ playerLabel }}
                                </p>
                            </div>
                            <div v-else-if="canResume" class="text-center">
                                <span
                                    class="block text-[8px] font-bold uppercase tracking-wide text-amber-300/80 mb-0.5">Paused</span>
                                <p v-if="!roster.length"
                                    class="text-xs font-extrabold text-white/90 truncate max-w-[105px] mx-auto">
                                    {{ playerLabel }}
                                </p>
                            </div>
                            <PlayerPicker v-else v-model="roster" @link="linking = true" />

                        </div>
                    </div>

                    <div v-if="!isDisplay"
                        class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-center z-10 w-full px-3">
                        <div class="text-2xl font-mono font-bold tracking-wider px-2 py-0.5 rounded-lg transition-all duration-200 py-1"
                            :class="timerClasses">
                            {{ formattedTime }}
                        </div>
                        <div v-if="canResume"
                            class="mt-1 text-sm font-black font-mono text-amber-300 bg-slate-950/50 rounded-md px-2 py-0.5">
                            Rs {{ pendingTotal }}
                        </div>
                    </div>
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒 LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked)  && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>

                    <div class="absolute  inset-x-0 px-6 text-center z-10" v-if="!isDisplay || showBookingStatus"
                        :class="isDisplay ? 'bottom-5' : 'bottom-12'">
                        <button v-if="props.table.isActive && !isDisplay"
                            @click="emit('transfer-table', { from_uid: props.table.uid, fromTableNumber: props.table.id, bookingName: props.table.bookingName })"
                            class="pointer-events-auto transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2"
                            :class="tButtonClasses">
                            {{ 'Shift Table' }}
                        </button>
                        <button v-else-if="canResume && !isDisplay" @click="resumeSession" :disabled="busy"
                            class="pointer-events-auto transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 disabled:opacity-50"
                            :class="resumeButtonClasses">
                            Resume
                        </button>
                        <div v-if="bookedIn() && !table.isActive && !table.resumable"
                            class="rounded-lg bg-slate-900 -mx-2">
                            <div class="uppercase text-[10px] font-bold  flex flex-row items-center justify-center py-1 rounded-lg border-2 gap-4"
                                :class="[
                                    (bookedIn() > 60
                                        ? 'text-emerald-100 border-emerald-400 bg-emerald-500/50'
                                        : bookedIn() < 30
                                            ? 'text-red-100 border-red-400 bg-red-500/50'
                                            : 'text-amber-100 border-amber-400 bg-amber-500/50'),
                                    (isPool ? 'mb-3' : 'mb-5'),
                                ]">
                                <span class="h-full text-2xl">!</span>
                                <div class="flex flex-col items-start justify-center"
                                    :class="isDisplay ? 'text-xs' : ''">
                                    <span :class="isDisplay ? '' : ''">Booking in</span>
                                    <div :class="isDisplay ? ' ' : ''" class="flex">
                                        <span v-if="bookedIn() > 60"> 1 H : {{ bookedIn() - 60 }} M</span>
                                        <span class="font-black text-sm" v-else>{{
                                            bookedIn() }} M</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <button v-if="!isDisplay" @click="mainAction" :disabled="busy"
                            class="pointer-events-auto transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                            :class="buttonClasses">
                            {{ mainActionLabel }}
                        </button>
                    </div>
                </div>
            </div>

            <p v-if="error"
                class="absolute -bottom-6 inset-x-0 text-center text-[9px] font-bold text-rose-400 px-1 leading-tight z-30">
                {{ error }}
            </p>
            <LinkPlayerModal v-if="linking" v-model="roster" @linked="onLinked" @update:modelValue="roster = $event"
                @close-modal="linking = false" />

        </div>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import PoolHole from './PoolHole.vue'
import { useStation } from '@/composables/useStation.js'
import LinkPlayerModal from './Modals/LinkPlayerModal.vue'
import PlayerPicker from './PlayerPicker.vue'
import PlayerChips from './PlayerChips.vue'
import PlayerIndicator from './PlayerIndicator.vue'

const props = defineProps({
    locked: { type: Boolean, default: false }, 
    table: Object, currentRate: Number, 
    loungeName: { type: String, default: '' }, 
    isDisplay: { type: Boolean, default: false }, 
    showBookingStatus: { type: Boolean, default: true }, 
    canManage: Boolean, 
    selected : {type: Boolean, default:false},
    slotBooked: { type: Boolean, default: false }, 
    bookings: Object, 
    hideId: { type: Boolean, default: false },
    hideDisplayRate : {type: Boolean, default: false} })
/**
 * Who the card should say is playing.
 *
 * Prefers the roster, because the table's own bookingName lags a poll behind
 * on a table just started — the field it used to come from is gone. Falls back
 * to bookingName for a table whose session began elsewhere, e.g. a transfer.
 */
const playerNames = computed(() => {
    const roster = (props.table.players || []).map((p) => p.name).filter(Boolean)
    if (roster.length) return roster
    const label = (props.table.bookingName || '').trim()
    return label ? label.split(',').map((n) => n.trim()).filter(Boolean) : []
})

const playersModal = ref(false)

const playerLabel = computed(() => playerNames.value.join(', ') || 'Walk-in Guest')

/**
 * Who's playing. Held here until the session starts, exactly as the single
 * name was, and mirrored onto the table object so useStation can send it.
 */
const linking = ref(false)
const roster = computed({
    get: () => props.table.players || [],
    set: (list) => { props.table.players = list },
})

/**
 * The dialog vets its own additions, but this is the last gate before the
 * roster changes — and a guest with no account still needs de-duplicating by
 * name, which an id comparison alone can never do.
 */
function onLinked(player) {
    const clash = roster.value.some((p) => (
        player.customerId
            ? p.customerId === player.customerId
            : !p.customerId && p.name.toLowerCase() === player.name.toLowerCase()
    ))
    if (!clash) roster.value = [...roster.value, player]
}

const emit = defineEmits(['open-receipt', 'update-status', 'remove-table', 'transfer-table'])

const {
    formattedTime,
    busy,
    canResume,
    pendingTotal,
    error,
    bookedIn,
    toggleTimer,
    resumeSession,
    endSession,
} = useStation(props, emit)

const holePositions = [
    'top-left',
    'top-right',
    'mid-left',
    'mid-right',
    'bottom-left',
    'bottom-right',
]

const isSnooker = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('snooker'),
)
const isPool = computed(() => props.table.type && props.table.type.toLowerCase().includes('pool'))
const isPrivatePool = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('private'),
)
const isPrivateSnooker = computed(() => props.table.type === 'privateSnooker')

const tableThemeClasses = computed(() => {
    if (isPrivateSnooker.value) {
        return props.table.isActive
            ? 'border-amber-500/90 bg-emerald-700 shadow-2xl '
            : 'border-amber-950 bg-emerald-900'
    }

    if (isSnooker.value)
        return props.table.isActive
            ? 'border-pool-wood-500 bg-emerald-700 shadow-2xl '
            : 'border-pool-wood-900 bg-emerald-900'

    if (isPrivatePool.value)
        return props.table.isActive
            ? 'border-amber-500/90 bg-sky-600 shadow-2xl '
            : 'border-amber-950 bg-sky-800'

    if (isPool.value)
        return props.table.isActive
        ? 'border-pool-wood-500  bg-sky-600 shadow-2xl'
        : 'border-pool-wood-900 bg-sky-800'

    return props.table.isActive
        ? 'border-purple-400 bg-sky-600 shadow-2xl shadow-purple-500/40'
        : 'border-purple-900 bg-sky-600'
})

const canopyGlowColorClass = computed(() =>
    isPrivateSnooker.value
        ? 'bg-amber-200 shadow-amber-300'
        : isSnooker.value
            ? 'bg-amber-100 shadow-sky-100'
            : isPrivatePool.value
                ? 'bg-amber-200 shadow-amber-300'
                : 'bg-amber-100 shadow-sky-100',
)

const canopyBeamColorClass = computed(() =>
    isPrivateSnooker.value
        ? 'bg-gradient-to-b from-amber-200/50 to-transparent'
        : isSnooker.value
            ? 'bg-gradient-to-b from-amber-100/50 to-transparent'
            : isPrivatePool.value
                ? 'bg-gradient-to-b from-amber-200/50 to-transparent'
                : 'bg-gradient-to-b from-amber-100/50 to-transparent',
)

const labelColorClass = computed(() =>
    isSnooker.value
        ? 'text-emerald-200/60'
        : 'text-sky-200/60',
)

const timerClasses = computed(() =>
    !props.table.isActive ? 'text-slate-950/40 w-full' : 'text-white bg-slate-950/30 w-full  border-2 border-slate-800/20',
)
const buttonClasses = computed(() =>
    props.table.isActive || canResume.value
        ? 'bg-rose-500 text-white hover:bg-rose-400'
        : 'bg-amber-500 text-slate-900'
)

const tButtonClasses = computed(() =>
    'bg-amber-500 text-slate-900'
)

const resumeButtonClasses = computed(() => 'bg-emerald-500 text-white hover:bg-emerald-400')

// Idle -> start, running -> pause, paused -> settle and print the bill
const mainAction = () => (canResume.value ? endSession() : toggleTimer())
const mainActionLabel = computed(() => {
    if (props.table.isActive) return 'Stop'
    return canResume.value ? 'End & Bill' : 'Start Session'
})

function flash(message) {
    notice.value = message
    setTimeout(() => { notice.value = '' }, 2200)
}

function addPlayer(player) {
    if (full.value) return flash(`Up to ${props.max} players`)

    // Same person twice — by name, or by an account already on the list.
    const clash = players.value.some((p) =>
        (player.customerId && p.customerId === player.customerId)
        || p.name.toLowerCase() === player.name.toLowerCase(),
    )
    if (clash) return flash(`${player.name} is already on this table`)

    emit('update:modelValue', [...players.value, player])
}
</script>

<style scoped>
.clip-cone {
    clip-path: polygon(15% 0%, 85% 0%, 100% 100%, 0% 100%);
}
</style>