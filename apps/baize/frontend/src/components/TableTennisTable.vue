<template>
    <div :style="isDisplay ? { width: '101px', height: '175px' } : {}">
        <div class="w-[202px] relative flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : 'mt-12'">
            <!-- Overhead Light Canopy -->
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
                            ? 'bg-amber-100 shadow-sky-100 opacity-100 shadow-[0_3px_15px_4px_rgba(255,255,255,1)]'
                            : 'bg-slate-800 opacity-60 shadow-none',
                    ]"></div>
                </div>

                <div class="w-full h-8 transition-all duration-500 origin-top transform scale-x-110 filter blur-sm clip-cone"
                    :class="[props.table.isActive ? 'bg-gradient-to-b from-amber-100/50 to-transparent opacity-25' : 'bg-transparent opacity-0']">
                </div>
            </div>

            <!-- VIP Container Indicator -->
            <div v-if="isPrivateTT"
                class="absolute -inset-y-4 inset-x-0 rounded-2xl bg-slate-950/40 border-2 border-dashed pointer-events-none z-0 transition-colors duration-500"
                :class="[
                    props.table.isActive
                        ? 'border-amber-500/80 shadow-blue-950/30'
                        : 'border-amber-800/40'
                ]">
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

                <!-- Main Table Surface -->
                <div class="relative w-full rounded-lg shadow-xl transition-all duration-500 h-[350px]"
                    :class="[tableThemeClasses, isDisplay ? 'flex items-center justify-center' : '']">

                    <!-- ── Table-tennis markings ── -->
                    <!-- subtle sheen on the playing surface -->
                    <div
                        class="absolute inset-0 rounded-lg pointer-events-none z-0 bg-gradient-to-br from-white/10 via-transparent to-black/10">
                    </div>
                    <!-- white boundary (side + end lines) -->
                    <div class="absolute inset-0 border-2 rounded-lg pointer-events-none z-0"
                    :class="isPrivateTT ? 'border-amber-600' : 'border-white/85'"></div>
                    <!-- centre line, lengthwise (doubles line) -->
                    <div
                        class="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[1.5px] bg-white/60 pointer-events-none z-0">
                    </div>
                    <!-- net across the middle — just a line, with holders protruding -->
                    <div
                        class="absolute -inset-x-2.5 top-1/2 -translate-y-1/2 z-[6] pointer-events-none flex items-center">
                        <span class="h-3 w-1 rounded-sm bg-slate-300"></span>
                        <span class="flex-1 h-[2px] bg-white/90"></span>
                        <span class="h-3 w-1 rounded-sm bg-slate-300"></span>
                    </div>

                    <!-- rackets: round rubber blade · light grip · black cap. Blade sits in the
                         corner, handle points INWARD. Red top-left, black bottom-right. -->
                    <!-- Red Top-Left Corner Racket -->
                    <div class="absolute top-1 -left-4 z-50 rotate-200  pointer-events-none">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 290"height="50">
                            <!-- Wooden Blade Base / Neck Throat -->
                            <path d="M 118 160 C 118 178 127 195 130 215 L 170 215 C 173 195 182 178 182 160 Z"
                                fill="#EBDCB9" />

                            <!-- Outer Dark Red Edge Tape / Base Rim -->
                            <path
                                d="M 150 15 C 205 15 238 55 238 107 C 238 153 208 181 182 187 C 168 190 132 190 118 187 C 92 181 62 153 62 107 C 62 55 95 15 150 15 Z"
                                fill="#9E1B2B" />

                            <!-- Main Red Rubber Face -->
                            <path
                                d="M 150 21 C 200 21 232 58 232 107 C 232 149 203 176 179 181 C 166 184 134 184 121 181 C 97 176 68 149 68 107 C 68 58 100 21 150 21 Z"
                                fill="#D32238" />

                            <!-- Slightly Increased Handle Length -->
                            <path
                                d="M 130 200 C 138 193 162 193 170 200 C 167 225 163 248 173 280 C 174 284 171 286 166 286 L 134 286 C 129 286 126 284 127 280 C 137 248 133 225 130 200 Z"
                                fill="#EBDCB9" />

                            <!-- Handle Inner Shadow / Bevel Detail -->
                            <path
                                d="M 158 197 C 164 198 170 200 170 200 C 167 225 163 248 173 280 C 174 284 171 286 166 286 L 156 286 C 160 281 155 248 158 197 Z"
                                fill="#D2BF9A" />

                            <!-- Handle Base Pin / Lens Dot -->
                            <circle cx="140" cy="274" r="2.5" fill="#B59B73" />
                        </svg>
                    </div>

                    <!-- Ball -->
                     <div class="absolute top-10 left-4 h-3 w-3 bg-slate-100 z-50 rounded-full"></div>
                    <!-- Black Bottom-Right Corner Racket -->
                    <div class="absolute bottom-1 -right-4 z-50 rotate-20 pointer-events-none">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 290"height="50">
                            <!-- Wooden Blade Base / Neck Throat -->
                            <path d="M 118 160 C 118 178 127 195 130 215 L 170 215 C 173 195 182 178 182 160 Z"
                                fill="#EBDCB9" />

                            <!-- Outer Dark Red Edge Tape / Base Rim -->
                            <path
                                d="M 150 15 C 205 15 238 55 238 107 C 238 153 208 181 182 187 C 168 190 132 190 118 187 C 92 181 62 153 62 107 C 62 55 95 15 150 15 Z"
                                fill="#9E1B2B" />

                            <!-- Main Red Rubber Face -->
                            <path
                                d="M 150 21 C 200 21 232 58 232 107 C 232 149 203 176 179 181 C 166 184 134 184 121 181 C 97 176 68 149 68 107 C 68 58 100 21 150 21 Z"
                                fill="#D32238" />

                            <!-- Slightly Increased Handle Length -->
                            <path
                                d="M 130 200 C 138 193 162 193 170 200 C 167 225 163 248 173 280 C 174 284 171 286 166 286 L 134 286 C 129 286 126 284 127 280 C 137 248 133 225 130 200 Z"
                                fill="#EBDCB9" />

                            <!-- Handle Inner Shadow / Bevel Detail -->
                            <path
                                d="M 158 197 C 164 198 170 200 170 200 C 167 225 163 248 173 280 C 174 284 171 286 166 286 L 156 286 C 160 281 155 248 158 197 Z"
                                fill="#D2BF9A" />

                            <!-- Handle Base Pin / Lens Dot -->
                            <circle cx="140" cy="274" r="2.5" fill="#B59B73" />
                        </svg>
                    </div>

                    <PlayerChips v-if="roster.length && playersModal" :players="roster" :removable="!table.isActive"
                        @close="playersModal = false" />

                    <span v-if="showBookingStatus && isDisplay && table.isActive"
                        class="absolute top-20 bg-amber-400 py-0.5 px-2 rounded-lg font-black tracking-widest uppercase text-md text-slate-900/90 z-20">!
                        ACTIVE</span>

                    <!-- Station Info Overlay -->
                    <div class="inset-x-0 flex flex-col items-center px-4 pointer-events-none text-center z-10"
                        :class="isDisplay ? 'gap-4 h-full items-center justify-between py-4' : 'absolute top-1.5'">
                        <div class="h-8 flex flex-col items-center justify-center">
                            <span
                                class="flex flex-col items-center font-black uppercase tracking-[0.2em] leading-tight text-blue-100/80 backdrop-blur-[2px]"
                                :class="isDisplay ? 'text-xl mt-4' : 'text-[9px]'">
                                <span>Table Tennis</span>
                                <span v-if="isPrivateTT" class="opacity-70 mt-0.5"
                                    :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP Room</span>
                            </span>
                        </div>

                        <span class="font-black drop-shadow-[0_2px_3px_rgba(0,0,0,0.6)] tracking-tight leading-none"
                            :class="[isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white']">
                            {{ table.id }}
                        </span>

                        <span v-if="isDisplay && !hideDisplayRate"
                            class="text-xl font-semibold tracking-wider text-slate-100 drop-shadow">
                            {{ currentRate }} Rs/min
                        </span>

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

                    <!-- Timer Display -->
                    <div v-if="!isDisplay"
                        class="absolute top-[43%] left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-center z-10 w-full px-3">
                        <div class="text-2xl font-mono font-bold tracking-wider px-2 py-0.5 rounded-lg transition-all duration-200 py-1"
                            :class="timerClasses,  canResume? 'translate-y-4': ''"">
                            {{ formattedTime }}
                        </div>
                        <div v-if="canResume"
                            class="mt-1 text-sm font-black font-mono text-amber-300 bg-slate-950/50 rounded-md px-2 py-0.5"
                            :class=" canResume? 'translate-y-6': ''">
                            Rs {{ pendingTotal }}
                        </div>
                    </div>

                    <!-- Overlays: License Lock & Booking State -->
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-[100] text-slate-300 bg-slate-950/80 rounded-xl pointer-events-auto">
                        <span
                            class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒
                            LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-[100] text-rose-600 bg-slate-900/70 rounded-xl pointer-events-auto">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>

                    <!-- Action Controls -->
                    <div class="absolute inset-x-0 px-6 text-center z-10" v-if="!isDisplay || showBookingStatus"
                        :class="isDisplay ? 'bottom-5' : 'bottom-12'">
                        <button v-if="props.table.isActive && !isDisplay"
                            @click="emit('transfer-table', { from_uid: props.table.uid, fromTableNumber: props.table.id, bookingName: props.table.bookingName })"
                            class="pointer-events-auto transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 bg-amber-500 text-slate-900">
                            Shift Table
                        </button>
                        <button v-else-if="canResume && !isDisplay" @click="resumeSession" :disabled="busy"
                            class="pointer-events-auto transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 disabled:opacity-50 bg-emerald-500 text-white hover:bg-emerald-400">
                            Resume
                        </button>

                        <!-- Advance Booking Notice -->
                        <div v-if="bookedIn() && !table.isActive && !table.resumable"
                            class="rounded-lg bg-slate-900 -mx-2 mb-3">
                            <div class="uppercase text-[10px] font-bold flex flex-row items-center justify-center py-1 rounded-lg border-2 gap-4"
                                :class="bookedIn() > 60
                                    ? 'text-emerald-100 border-emerald-400 bg-emerald-500/50'
                                    : bookedIn() < 30
                                        ? 'text-red-100 border-red-400 bg-red-500/50'
                                        : 'text-amber-100 border-amber-400 bg-amber-500/50'">
                                <span class="h-full text-2xl">!</span>
                                <div class="flex flex-col items-start justify-center"
                                    :class="isDisplay ? 'text-xs' : ''">
                                    <span>Booking in</span>
                                    <div class="flex">
                                        <span v-if="bookedIn() > 60"> 1 H : {{ bookedIn() - 60 }} M</span>
                                        <span class="font-black text-sm" v-else>{{ bookedIn() }} M</span>
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
import { useStation } from '@/composables/useStation.js'
import LinkPlayerModal from './Modals/LinkPlayerModal.vue'
import PlayerPicker from './PlayerPicker.vue'
import PlayerChips from './PlayerChips.vue'
import PlayerIndicator from './PlayerIndicator.vue'

const props = defineProps({
    locked: { type: Boolean, default: false },
    table: Object,
    currentRate: Number,
    loungeName: { type: String, default: '' },
    isDisplay: { type: Boolean, default: false },
    showBookingStatus: { type: Boolean, default: true },
    canManage: Boolean,
    selected: { type: Boolean, default: false },
    slotBooked: { type: Boolean, default: false },
    bookings: Object,
    hideId: { type: Boolean, default: false },
    hideDisplayRate: { type: Boolean, default: false }
})

const emit = defineEmits(['open-receipt', 'update-status', 'remove-table', 'transfer-table'])

const playerNames = computed(() => {
    const roster = (props.table.players || []).map((p) => p.name).filter(Boolean)
    if (roster.length) return roster
    const label = (props.table.bookingName || '').trim()
    return label ? label.split(',').map((n) => n.trim()).filter(Boolean) : []
})

const playersModal = ref(false)
const playerLabel = computed(() => playerNames.value.join(', ') || 'Walk-in Guest')

const linking = ref(false)
const roster = computed({
    get: () => props.table.players || [],
    set: (list) => { props.table.players = list },
})

function onLinked(player) {
    const clash = roster.value.some((p) => (
        player.customerId
            ? p.customerId === player.customerId
            : !p.customerId && p.name.toLowerCase() === player.name.toLowerCase()
    ))
    if (!clash) roster.value = [...roster.value, player]
}

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

const isPrivateTT = computed(() => props.table.type && props.table.type.toLowerCase().includes('private'))

const tableThemeClasses = computed(() => {
    if (isPrivateTT.value) {
        return props.table.isActive
            ? 'border-amber-500/90 bg-sky-700 shadow-2xl'
            : 'border-amber-950 bg-sky-900'
    }

    return props.table.isActive
        ? 'border-slate-800 bg-sky-600 shadow-2xl '
        : 'border-slate-900 bg-sky-900'
})

const timerClasses = computed(() =>
    !props.table.isActive ? 'text-slate-950/60 w-full' : 'backdrop-blur-xs text-white bg-slate-950/40 w-full border-2 border-slate-800/20'
)

const buttonClasses = computed(() =>
    props.table.isActive || canResume.value
        ? 'bg-rose-500 text-white hover:bg-rose-400'
        : 'bg-amber-500 text-slate-900'
)

const mainAction = () => (canResume.value ? endSession() : toggleTimer())
const mainActionLabel = computed(() => {
    if (props.table.isActive) return 'Stop'
    return canResume.value ? 'End & Bill' : 'Start Session'
})
</script>

<style scoped>
.clip-cone {
    clip-path: polygon(15% 0%, 85% 0%, 100% 100%, 0% 100%);
}
</style>