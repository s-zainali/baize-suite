<template>
    <div class="bg-slate-900 text-slate-100 p-6">
        <div v-if="selectedTable" class="block sm:hidden fixed right-4 bottom-4 z-400">
            <button @click="scrollToTop()" class="bg-emerald-600 px-4 py-2 rounded-lg text-xs font-black shadow-lg shadow-slate-950">CONFIRM</button>
        </div>
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
            <div class="flex gap-4 items-center">
                <RouterLink :to="'/home'"
                    class=" sm:hidden sticky top-0 w-10 h-10 flex items-center rounded-xl active:bg-slate-600 justify-center bg-slate-800">
                    <svg xmlns="http://w3.org" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke-width="4"
                        stroke="currentColor" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                    </svg>
                </RouterLink>
                <div>
                    <h1 class="text-2xl font-black text-white tracking-tight">Book a Station</h1>
                    <p class="text-xs text-slate-500 mt-0.5">Reserve a table or console for a guest.</p>
                </div>
            </div>
            <div class="flex gap-4 justify-center">
                <RouterLink :to="'/home'"
                    class="hidden sm:flex text-xs tracking-widest text-slate-100 font-bold bg-slate-800 border border-slate-600 hover:bg-slate-700 transition duration-300 ease-in-out items-center justify-center px-4 rounded-xl">
                    Back to Home</RouterLink>
                <CustomerMenu v-if="isSignedIn" />
            </div>
        </div>

        <!-- Initial load: club + branch data on the way from the venue -->
        <div v-if="!firstLoadDone"
            class="flex flex-col items-center justify-center py-32 rounded-2xl border-2 border-dashed border-slate-700 bg-slate-950/40">
            <span class="h-10 w-10 mb-4 rounded-full border-2 border-slate-600 border-t-emerald-400 animate-spin"></span>
            <p class="text-sm font-bold text-slate-300">Loading club…</p>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-4">
            <!-- LEFT: booking form -->
            <div
                class="bg-slate-950/40 border border-slate-700 rounded-2xl p-5 h-fit w-full mx-auto lg:mx-0 lg:sticky lg:top-6">
                <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-4">
                    Reservation Details</span>

                <div class="space-y-4">
                    <!-- Identity comes from the signed-in account: a guest can't
                         book under someone else's name, and doesn't retype their own. -->
                    <div class="rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2.5">
                        <span class="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">
                            Booking as</span>
                        <p class="truncate text-sm font-bold text-white">{{ customer.profile?.name }}</p>
                        <p class="truncate font-mono text-[10px] text-slate-500">{{ myPhone }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2.5">
                        <span class="mb-1 block text-[10px] font-black uppercase tracking-widest text-slate-500">
                            Club</span>
                        <div class="flex items-center gap-2">
                            <div v-if="clubLogo"
                                class="flex h-6 w-6 shrink-0 items-center justify-center overflow-hidden rounded-md border border-white/10 bg-slate-900">
                                <img :src="clubLogo" alt="" class="h-full w-full object-cover" @error="clubLogo = null" />
                            </div>
                            <p class="truncate text-sm font-bold text-white">{{ clubName }}</p>
                        </div>
                    </div>

                    <DropdownField :form="form" :field="'branch'" :options="branchOptions" :label="'Branch'"
                        :placeholder="'Select a branch'" />

                    <div>
                        <label class="text-[10px] uppercase font-black tracking-widest text-slate-300 block mb-1.5">
                            Date</label>
                        <DateField v-model="form.date" :min="todayStr" placeholder="Pick date" />
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-[10px] uppercase font-black tracking-widest text-slate-300 block mb-1.5">
                                Start Time</label>
                            <TimeField v-model="form.startTime" :min="minStartTime" :max="maxStartTime"
                                placeholder="Pick time" />
                        </div>
                        <div>
                            <label class="text-[10px] uppercase font-black tracking-widest text-slate-300 block mb-1.5">
                                End Time</label>
                            <TimeField v-model="form.endTime" :min="minEndTime" :max="maxEndTime"
                                placeholder="Pick time" />
                        </div>
                    </div>

                    <p v-if="duration" class="text-[10px] font-bold text-slate-400 -mt-1">
                        Duration <span class="text-white">{{ duration }}</span>
                        <span class="text-slate-400 font-normal"> · minimum 30 min</span>
                        <span class="text-slate-400 font-normal"> · Maximum 3 hours</span>
                    </p>

                    <div class="pt-2 border-t border-slate-700">
                        <span class="text-[10px] uppercase font-black tracking-widest text-slate-300 block mb-1">
                            Selected Station</span>
                        <p v-if="selectedTable" class="text-sm font-black text-emerald-500">
                            {{ typeLabel(selectedTable.type) }} #{{ selectedTable.id }}
                        </p>
                        <p v-else class="text-sm text-slate-400 font-bold">Pick a station on the right →</p>
                    </div>

                    <p v-if="incompleteBookings"
                        class="text-[10px] font-bold text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-xl px-3 py-2 leading-snug">
                        Some bookings have no end time recorded, so their clashes can't be
                        checked — those stations are blocked for the whole day as a precaution.
                        Restarting the backend repairs old rows automatically.
                    </p>

                    <p v-if="error"
                        class="text-[10px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 uppercase tracking-wide">
                        {{ error }}</p>
                    <p v-if="success"
                        class="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2 uppercase tracking-wide">
                        {{ success }}</p>

                    <button @click="submitBooking" :disabled="!canSubmit || submitting"
                        class="w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-all cursor-pointer">
                        {{ submitting ? 'BOOKING…' : 'CONFIRM BOOKING' }}
                    </button>
                </div>
            </div>

            <!-- RIGHT: station grid grouped by lounge -->
            <div class=" space-y-4">
                <!-- Loading a branch's stations -->
                <div v-if="loading"
                    class="flex flex-col items-center justify-center text-center py-24 rounded-2xl border-2 border-dashed border-slate-700 bg-slate-950/40">
                    <span class="h-8 w-8 mb-3 rounded-full border-2 border-slate-600 border-t-emerald-400 animate-spin"></span>
                    <p class="text-sm font-bold text-slate-300">Loading stations…</p>
                </div>
                <template v-else>
                <div v-if="state.branches.length > 1 && !form.branch"
                    class="flex flex-col items-center justify-center text-center py-24 rounded-2xl border-2 border-dashed border-slate-700 bg-slate-950/40">
                    <span class="text-3xl mb-3 opacity-40">🏢</span>
                    <p class="text-sm font-bold text-slate-300">Select a branch to see its stations</p>
                    <p class="text-xs text-slate-500 mt-1">Choose a location on the left to start a booking.</p>
                </div>
                <div v-for="lounge in state.lounges" :key="lounge.uid"
                    class="bg-slate-950/40 border border-slate-700 rounded-2xl p-4">
                    <span class="text-sm font-black text-white block mb-3">{{ lounge.name }}</span>
                    <div class="grid grid-cols-[repeat(auto-fill,minmax(117px,1fr))] gap-2">
                        <button :disabled="isBooked(t.uid)" v-for="t in loungeTables(lounge.uid)" :key="t.uid"
                            type="button" @click="selectTable(t)"
                            :title="isBooked(t.uid) ? `Booked ${clashLabel(t.uid)}` : ''"
                            class="rounded-xl border p-3 text-left transition-all shrink-0 flex flex-col items-center justify-center h-[245px]"
                            :class="tileClass(t), isBooked(t.uid) ? 'cursor-default' : 'cursor-pointer'">
                            <div class="flex h-full items-center">
                                <TableVisual :table="t" :showBookingStatus="false" :current-rate="t.currentRate"
                                    :is-display="true" :slot-booked="isBooked(t.uid)" :bookings="state.bookings" />
                            </div>
                            <div class="mt-2">
                                <p v-if="isBooked(t.uid)"
                                    class="max-w-[90px] text-wrap text-[8px] font-bold text-amber-500 leading-tight whitespace-nowrap text-center z-30 tracking-widest">
                                    {{ clashLabel(t.uid) }}
                                </p>
                                <div v-else-if="t.uid === selectedTable?.uid"
                                    class="max-w-[90px] text-wrap text-[10px] font-bold text-emerald-100 bg-emerald-600 px-3 rounded-sm -my-1 py-1 leading-tight whitespace-nowrap text-center z-30 uppercase tracking-widest">
                                    Selected
                                </div>
                                <div v-else-if="t.isActive"
                                    class="max-w-[90px] text-wrap text-[10px] font-bold text-rose-400 leading-tight whitespace-nowrap text-center z-30 uppercase tracking-widest">
                                    busy now
                                </div>
                                <p v-else
                                    class="max-w-[90px] text-wrap text-[10px] font-bold text-emerald-400 leading-tight whitespace-nowrap text-center z-30 uppercase tracking-widest">
                                    Available
                                </p>
                            </div>

                        </button>
                    </div>
                </div>
                </template>
            </div>
        </div>
        <PoweredByZain :for-customer="true" />

        <BookingConfirmModal v-if="confirmed" v-bind="confirmed" @close="confirmed = null; router.push('/home')" />
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { typeLabel } from '@baize/ui'
import { useRouter, useRoute } from 'vue-router'
import { apiGet, apiPost, isSignedIn, customer } from '../auth.js'
import { formatPhoneDisplay } from '@baize/ui'
import { usePageBackground } from '@baize/ui'
import CustomerMenu from '../components/CustomerMenu.vue'
import { DateField } from '@baize/ui'
import { DropdownField } from '@baize/ui'
import { TimeField } from '@baize/ui'
import {
    toMinutes, toISODate,
    earliestStart, latestStart, earliestEnd, formatDuration, validateRange, overlaps,
    formatTime12,
    latestEnd,
} from '@baize/ui'
import { PoweredByZain } from '@baize/ui'
import BookingConfirmModal from '../components/BookingConfirmModal.vue'
import { TableVisual } from '@baize/ui'
import { fetchAvailability } from '@/api.js'

usePageBackground('#0f172a')
const router = useRouter()
const route = useRoute()
const clubUid = computed(() => route.query.clubId || '')
const clubName = ref('')
const clubLogo = ref(null)
const myPhone = computed(() => formatPhoneDisplay(customer.profile?.phone || ''))

const state = ref({ tables: [], lounges: [], bookings: [], branches: [] })
const loading = ref(false)         // user-initiated fetch (initial + branch/date)
const firstLoadDone = ref(false)   // gate the very first club load
const selectedTable = ref(null)
const selectedBranch = computed(() => state.value.branches.find(branch => branch.uid === form.branch))
const selectedLounge = computed(() => state.value.lounges.find(lounge => lounge.uid === selectedTable.value.loungeUid))
const branchOptions = computed(() => state.value.branches.map(b => ({ value: b.uid, label: b.name })))
const submitting = ref(false)
const error = ref('')
const success = ref('')
// Set to the booking details after a successful booking; drives the confirm
// modal. Redirect to /home happens only when the guest closes it.
const confirmed = ref(null)


// Both tick so a form left open across midnight (or past the slot the guest was
// about to book) corrects itself instead of silently going stale.
const clock = ref(new Date())
const todayStr = computed(() => toISODate(clock.value))

const initialStart = earliestStart(toISODate(new Date()), new Date())

const form = reactive({
    branch: '',
    date: toISODate(new Date()),
    startTime: initialStart,
    endTime: earliestEnd(initialStart) || '23:30',
})

// Nothing before now on today's date, and nothing so late that the minimum
// booking would spill past midnight.
const minStartTime = computed(() => earliestStart(form.date, clock.value))
const maxStartTime = computed(() => latestStart())
const minEndTime = computed(() => earliestEnd(form.startTime) || '')
const maxEndTime = computed(() => latestEnd(form.endTime) || '')
const duration = computed(() => formatDuration(form.startTime, form.endTime))
const rangeError = computed(() => validateRange(form.date, form.startTime, form.endTime, clock.value))

// Keep the pair coherent: pull the start forward if it has fallen into the past,
// and push the end out whenever less than the minimum is left between them.
function reconcileTimes() {
    const floor = minStartTime.value
    if (floor && form.startTime < floor) form.startTime = floor
    if (form.startTime > maxStartTime.value) form.startTime = maxStartTime.value
    const endFloor = minEndTime.value
    if (endFloor && (!form.endTime || form.endTime < endFloor)) form.endTime = endFloor
}
watch(() => [form.date, form.startTime], reconcileTimes, { immediate: true })

let poll
async function fetchState(showLoading = false) {
    if (!clubUid.value) { firstLoadDone.value = true; return }
    if (showLoading) loading.value = true

    try {
        // Pass club_uid so backend can look up Club.public_url
        const data = await fetchAvailability({
            date : form.date, 
            clubUid : clubUid.value,
            branchUid: form.branch
        })

        if (!form.branch && data.selectedBranch) form.branch = data.selectedBranch

        clubName.value = data.club
        clubLogo.value = data.logoUrl || null
        
        state.value = {
            tables: data.tables || [],
            lounges: data.lounges || [],
            branches: data.branches || [],
            bookings: (data.busy || []).map(b => ({
                tableUid: b.tableUid,
                startTime: b.startTime,
                endTime: b.endTime,
                mine: b.mine,
            })),
        }

        if (selectedTable.value) {
            state.value.tables.forEach(table => {
                if (table.uid == selectedTable.value.uid) {
                    table.isActive = true
                }
            })
        }

    } catch (_) { /* transient: the poll will retry */ }
    finally {
        loading.value = false
        firstLoadDone.value = true
    }
}
let tick
// Availability is per-day, so refetch whenever the chosen date moves
watch(() => form.date, () => fetchState(true))
watch(() => form.branch, () => { selectedTable.value = null; fetchState(true) })

onMounted(() => {
    fetchState(true)                                  // initial load — show the loader
    poll = setInterval(() => fetchState(false), 20000)  // silent background refresh
    tick = setInterval(() => { clock.value = new Date(); reconcileTimes() }, 30000)
})
onUnmounted(() => { clearInterval(poll); clearInterval(tick) })

const loungeTables = (uid) => state.value.tables.filter(t => t.loungeUid === uid)
/**
 * Is this station taken for the range currently in the form?
 *
 * Compares whole intervals rather than just the start instant — a station booked
 * 4:00-6:00 is unavailable at 5:00 even though no booking *starts* at 5:00.
 */
/**
 * The existing booking that blocks this station for the range in the form, or
 * null if it's free.
 *
 * Whole intervals are compared, not just start instants: a station held from
 * 9:00 to 11:00 is unavailable at 10:00 even though no booking begins at 10:00.
 */
/**
 * A booking with no end time is a row that predates the end_time column. The
 * migration backfills those on startup, but until then they have to be handled.
 *
 * Guessing a length here would be actively dangerous: assuming the minimum
 * would make a 09:00-11:00 booking look free at 10:00 and wave through a double
 * booking. When the end is unknown we block the rest of the day instead, and say
 * loudly why.
 */
const incompleteBookings = computed(() =>
    (state.value.bookings || []).some(b => !b.endTime)
)

const END_OF_DAY = 24 * 60

const clashFor = (uid) => {
    const start = toMinutes(form.startTime)
    const end = toMinutes(form.endTime)
    if (start === null || end === null) return null

    return (state.value.bookings || []).find(b => {
        if (b.tableUid !== uid) return false
        if (b.startTime.slice(0, 10) !== form.date) return false
        const bStart = toMinutes(b.startTime.slice(11, 16))
        // Unknown end: assume the worst rather than the shortest.
        const bEnd = b.endTime ? toMinutes(b.endTime.slice(11, 16)) : END_OF_DAY
        return overlaps(start, end, bStart, bEnd)
    }) || null
}

const isBooked = (uid) => clashFor(uid) !== null

/** 'Booked 9:00 AM - 11:00 AM - Ali' — so it's clear why a tile is unavailable. */
const clashLabel = (uid) => {
    const b = clashFor(uid)
    if (!b) return ''
    const from = formatTime12(b.startTime.slice(11, 16))
    const to = b.endTime ? formatTime12(b.endTime.slice(11, 16)) : ''
    return to ? `${from} – ${to}` : `from ${from}`
}
// Changing the time can invalidate a station that was already picked
watch(() => [form.date, form.startTime, form.endTime], () => {
    if (selectedTable.value && isBooked(selectedTable.value.uid)) selectedTable.value = null
})

function selectTable(t) {
    if (selectedTable.value === t) {
        selectedTable.value.isActive = false
        selectedTable.value = null
    }
    else {
        state.value.lounges
            .forEach(lounge => loungeTables(lounge.uid)
                .forEach(table => table === selectedTable.value ? table.isActive = false : ''))
        selectedTable.value = t
        selectedTable.value.isActive = true
        error.value = ''
        success.value = ''
    }
}

function tileClass(t) {
    if (selectedTable.value?.uid === t.uid) return 'bg-slate-700/80 border-slate-600 ring-2 ring-emerald-500/60'
    if (isBooked(t.uid)) return 'border-amber-500/40 bg-amber-500/5 hover:border-amber-400/60'
    return 'border-slate-700 bg-slate-800 hover:bg-slate-700/70 hover:border-slate-600'
}

// Name and phone come from the signed-in account — a guest shouldn't be able
// to book under someone else's name, and shouldn't have to retype their own.
const canSubmit = computed(() =>
    !!form.date && !!selectedTable.value && !rangeError.value
)

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
};

async function submitBooking() {
    if (submitting.value) return
    if (rangeError.value) { error.value = rangeError.value; return }
    if (!canSubmit.value) return
    submitting.value = true
    error.value = ''
    success.value = ''
    try {
        // combine date + time into a local ISO string
        const startTime = `${form.date}T${form.startTime}:00`
        const endTime = `${form.date}T${form.endTime}:00`
        const res = await apiPost('/bookings', {
            clubUid: clubUid.value,
            branchUid: form.branch,
            tableType: selectedTable.value.type,
            tableNumber: selectedTable.value.id,
            loungeUid: selectedTable.value.loungeUid,
            tableUid: selectedTable.value.uid,
            startTime,
            endTime,
        }, { auth: true })
        // Hold the details for the confirmation modal; the redirect waits until
        // the guest dismisses it, so they get a chance to screenshot the code.
        confirmed.value = {
            club: clubName.value,
            branch: selectedBranch.value.name,
            lounge: selectedLounge.value.name,
            code: res.code || '',
            tableType: selectedTable.value.type,
            tableNumber: selectedTable.value.id,
            date: form.date,
            startTime: form.startTime,
            endTime: form.endTime,
        }
    } catch (e) {
        error.value = e.message
    } finally {
        submitting.value = false
    }
}
</script>