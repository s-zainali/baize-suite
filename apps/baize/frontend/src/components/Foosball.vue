<template>
    <div :class="isDisplay ? 'w-[101px] h-[190px]' : ''">
        <div class="w-[202px] relative  flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : 'mt-12'">

            <div class="flex flex-col items-center w-full relative z-10 group">
                <!-- Rate + remove row (same as PoolTable) -->
                <div v-if="!isDisplay"
                    class="w-full flex justify-between items-center px-1.5 mb-1.5 text-[10px] font-semibold tracking-wider text-slate-400">
                    <span>{{ currentRate }} Rs/min</span>
                    <button v-if="!props.table.isActive" @click="$emit('remove-table', table.uid)"
                        class="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-400 transition-all font-bold text-[9px] cursor-pointer">
                        Remove ✕
                    </button>
                </div>
                <!-- Station card -->
                <div class="relative w-full h-[380px] rounded-2xl border-2 shadow-xl transition-all duration-500 bg-slate-950 flex flex-col items-center px-3 py-6 overflow-hidden"
                    :class="props.table.isActive
                        ? isDisplay && showBookingStatus
                            ? 'border-red-600'
                            : 'border-lime-400 shadow-2xl shadow-lime-400/40'
                        : 'border-slate-800',
                        isDisplay ? 'gap-4 items-center justify-between' : ''">

                    <!-- Header: type label + station number -->
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒 LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl top-0">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                    <div class="flex flex-col gap-2 w-full items-center">
                        <span class="font-black uppercase tracking-[0.2em] leading-tight transition-colors duration-500"
                            :class="props.table.isActive && !isDisplay ? 'text-lime-300/70' : 'text-slate-500', isDisplay ? 'text-xl' : 'text-[9px]'">
                            Foosball
                        </span>
    
                        <!-- Mini pitch (contained illustration, landscape) -->
                        <div class="w-full mt-2 mb-4 relative">
                            <!-- ambient glow when live -->
                            <div v-if="!isDisplay"
                                class="absolute -inset-2 rounded-xl bg-lime-400/20 blur-lg transition-opacity duration-500 pointer-events-none"
                                :class="props.table.isActive ? 'opacity-100' : 'opacity-0'"></div>
    
                            <div class="relative w-full h-[88px] rounded-lg border-[3px] overflow-hidden transition-all duration-500"
                                :class="props.table.isActive
                                    ? isDisplay && showBookingStatus
                                        ? 'bg-red-600/20 border-red-500/50'
                                        : 'bg-gradient-to-br from-emerald-500 to-emerald-700 border-slate-700'
                                    : !bookedIn()
                                        ? 'bg-gradient-to-br from-slate-900 to-slate-950 border-slate-700'
                                        : bookedIn() > 60
                                            ? 'border-emerald-400 bg-emerald-500/50'
                                            : bookedIn() > 30
                                                ? 'border-amber-400 bg-amber-500/50'
                                                : 'border-red-400 bg-red-500/50'">
    
                                <!-- markings -->
                                <div class="absolute inset-y-0 left-1/2 w-px bg-white/15"></div>
                                <div
                                    class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 rounded-full border border-white/15">
                                </div>
                                <!-- goals -->
                                <div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-7 bg-slate-950 rounded-r"></div>
                                <div class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-7 bg-slate-950 rounded-l"></div>
    
                                <!-- four rods, alternating teams -->
                                <div v-for="rod in rods" :key="rod.x" class="absolute inset-y-0" :style="{ left: rod.x }">
                                    <div class="absolute inset-y-0 left-0 w-[2px] -translate-x-1/2 bg-white/15"></div>
                                    <!-- figures -->
                                    <div class="absolute left-0 -translate-x-1/2 flex flex-col justify-around h-full py-2">
                                        <div v-for="n in rod.count" :key="n"
                                            class="w-2.5 h-1.5 rounded-full transition-all duration-500" :class="rod.team === 'red'
                                                ? (props.table.isActive ? 'bg-rose-400' : 'bg-slate-600')
                                                : (props.table.isActive ? 'bg-sky-400' : 'bg-slate-700')">
                                        </div>
                                    </div>
                                </div>
    
                                <!-- ball: mini football (center pentagon + rim patches, ⚽ style) -->
                                <div class="absolute top-[38%] left-[56%] -translate-x-1/2 -translate-y-1/2 transition-all duration-500"
                                    :class="props.table.isActive ? 'opacity-100 animate-pulse' : 'opacity-30'">
                                    <svg viewBox="0 0 20 20" class="w-3 h-3 drop-shadow-[0_0_3px_rgba(255,255,255,0.4)]">
                                        <defs>
                                            <clipPath id="fb-ball-clip">
                                                <circle cx="10" cy="10" r="8.4" />
                                            </clipPath>
                                        </defs>
                                        <!-- body -->
                                        <circle cx="10" cy="10" r="8.6" fill="#f8fafc" stroke="#0f172a"
                                            stroke-width="1.2" />
                                        <!-- center pentagon -->
                                        <polygon points="10,6.6 13.2,8.9 12,12.7 8,12.7 6.8,8.9" fill="#0f172a" />
                                        <!-- rim patches, clipped by the ball's edge -->
                                        <g fill="#0f172a" clip-path="url(#fb-ball-clip)">
                                            <circle cx="15.2" cy="2.9" r="2.6" />
                                            <circle cx="18.4" cy="12.7" r="2.6" />
                                            <circle cx="10" cy="18.8" r="2.6" />
                                            <circle cx="1.6" cy="12.7" r="2.6" />
                                            <circle cx="4.8" cy="2.9" r="2.6" />
                                        </g>
                                    </svg>
                                </div>
                            </div>
    
                            <!-- Handles protruding past the frame (outside the clipped pitch) -->
                            <template v-for="rod in rods" :key="'handle-' + rod.x">
                                <div class="absolute -top-1.5 -translate-x-1/2 w-[5px] h-3 rounded-full bg-slate-600 border border-slate-800 transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-slate-500' : ''" :style="{ left: rod.x }"></div>
                                <div class="absolute -bottom-1.5 -translate-x-1/2 w-[5px] h-3 rounded-full bg-slate-600 border border-slate-800 transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-slate-500' : ''" :style="{ left: rod.x }"></div>
                            </template>
                        </div>
                        
                    </div>

                    <span class="font-black drop-shadow-md tracking-tight leading-none"
                        :class="isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white'">
                        {{ table.id }}
                    </span>

                    <span v-if="isDisplay && !hideDisplayRate" class="text-xl font-semibold tracking-wider text-slate-200 mt-4">{{
                        currentRate }} Rs/min</span>

                    <!-- Scoreboard: the clock, and beneath it whoever is playing.
                         This is the card's display surface, so the names belong
                         here rather than under the button where there is no room. -->
                    <div v-if="!isDisplay"
                        class="w-full mt-2.5 rounded-lg bg-slate-900 border border-slate-800 py-1.5 px-1 flex flex-col items-center justify-center">
                        <span class="text-xl font-mono font-bold tracking-wider transition-colors duration-300" :class="props.table.isActive
                            ? 'text-lime-300 drop-shadow-[0_0_6px_rgba(163,230,53,0.5)]'
                            : 'text-slate-700'">
                            {{ formattedTime }}
                        </span>
                        <PlayerChips v-if="roster.length && playersModal" :players="roster"
                            :removable="!props.table.isActive" @remove="removePlayer" @close="playersModal = false" />
                    </div>

                    <!-- Player (name while active, input while idle) -->
                    <div v-if="!isDisplay" class="w-full mt-2 flex flex-col gap-2">
                        <div v-if="props.table.isActive" class="text-center">
                            <span class="block text-[8px] font-bold uppercase tracking-wide text-slate-500">
                                Playing</span>
                        </div>
                        <div v-else-if="canResume" class="text-center">
                            <span class="block text-[8px] font-bold uppercase tracking-wide text-amber-400/80">
                                Paused</span>
                        </div>
                        <PlayerPicker v-else v-model="roster" :chips="false" @link="linking = true" />
                        <PlayerIndicator v-if="roster.length" :roster="roster" @view="playersModal = true" />
                    </div>

                    <!-- Buttons -->
                    <div v-if="!isDisplay || showBookingStatus" class="w-full mt-auto text-center px-6">
                        <button v-if="props.table.isActive && !isDisplay"
                            @click="emit('transfer-table', { from_uid: props.table.uid, fromTableNumber: props.table.id, bookingName: props.table.bookingName })"
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 bg-lime-400 text-slate-900">
                            Transfer
                        </button>
                        <button v-else-if="canResume && !isDisplay" @click="resumeSession" :disabled="busy"
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 disabled:opacity-50"
                            :class="resumeButtonClasses">
                            Resume
                        </button>
                        <div v-if="bookedIn() && !table.isActive && !table.resumable" class="rounded-lg">
                            <div class="uppercase text-[10px] font-bold  flex flex-row items-center justify-center rounded-lg gap-2 mb-2"
                                :class="[
                                    (bookedIn() > 60
                                        ? 'text-emerald-400'
                                        : bookedIn() < 30
                                            ? 'text-red-400 '
                                            : 'text-amber-400'),
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
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                            :class="props.table.isActive || canResume
                                ? 'bg-rose-500 text-white hover:bg-rose-400'
                                : 'bg-lime-400 text-slate-900 hover:bg-lime-300'">
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
import { ref, computed } from 'vue'
import { useStation } from '@/composables/useStation.js'
import PlayerPicker from './PlayerPicker.vue'
import PlayerChips from './PlayerChips.vue'
import LinkPlayerModal from './Modals/LinkPlayerModal.vue'
import PlayerIndicator from './PlayerIndicator.vue'

const props = defineProps({
    locked: { type: Boolean, default: false }, 
    table: Object, 
    currentRate: Number, 
    isDisplay: { type: Boolean, default: false }, 
    loungeName: { type: String, default: '' }, 
    showBookingStatus: { type: Boolean, default: true }, 
    slotBooked: { type: Boolean, default: false }, 
    bookings: Object, 
    hideId: {type: Boolean, default:false},
    hideDisplayRate: {type: Boolean, default:false} })
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

const playerLabel = computed(() => playerNames.value.join(', ') || 'Walk-in Guest')

const playersModal = ref(false)

// Four fits a doubles game, which is what a foosball table usually holds.
const MAX_SHOWN = 4
const shownPlayers = computed(() => playerNames.value.slice(0, MAX_SHOWN))
const hiddenPlayerCount = computed(() => Math.max(0, playerNames.value.length - MAX_SHOWN))

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
/** Take someone off the table before play starts. */
function removePlayer(index) {
    roster.value = roster.value.filter((_, i) => i !== index)
}

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

const resumeButtonClasses = 'bg-emerald-500 text-white hover:bg-emerald-400'

// Idle -> start, running -> pause, paused -> settle and print the bill
const mainAction = () => (canResume.value ? endSession() : toggleTimer())
const mainActionLabel = computed(() => {
    if (props.table.isActive) return 'Stop'
    return canResume.value ? 'End & Bill' : 'Start Session'
})

const rods = [
    { x: '18%', count: 2, team: 'red' },
    { x: '39%', count: 3, team: 'blue' },
    { x: '61%', count: 3, team: 'red' },
    { x: '82%', count: 2, team: 'blue' },
]

</script>