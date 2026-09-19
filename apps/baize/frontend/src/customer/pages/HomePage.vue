<template>
    <div class="relative min-h-screen overflow-hidden bg-slate-950 text-white">

        <div class="relative mx-auto flex min-h-screen  flex-col p-6">
            <!-- Header: unchanged -->
            <header class="grid grid-cols-2 sm:grid-cols-[9rem_1fr_9rem] gap-4 items-center justify-between pb-4">
                <div class="order-2 sm:order-1">
                    <p class="text-[10px] font-black uppercase tracking-widest text-emerald-500">Signed in</p>
                    <h1 class="text-xl font-black">{{ fullName }}</h1>
                </div>
                <div
                    class="order-1 sm:order-2 col-span-2 sm:col-span-1 flex flex-1 gap-4 flex-col items-center justify-center bg-gradient-to-r from-transparent via-slate-900 to-transparent">
                    <div
                        class="h-[1px]  w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent rounded-full">
                    </div>
                    <h1 class="text-xl text-center font-bold text-slate-100 uppercase tracking-[0.5rem]"> {{ clubName || 'Club Name Here' }}
                    </h1>
                    <div
                        class="h-[1px]  w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent rounded-full">
                    </div>
                </div>
                <button @click="signOut()"
                    class="order-3 cursor-pointer rounded-xl border border-slate-800 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-slate-400 transition-colors hover:border-rose-400 hover:bg-rose-500/50 hover:text-rose-100">
                    Sign Out
                </button>
            </header>
 
            <!-- Summary strip -->
            <section class="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-3 lg:grid-cols-5">
                <div v-for="stat in stats" :key="stat.label"
                    class="group relative overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-800/50 px-5 py-4 backdrop-blur-xl transition-colors hover:border-slate-700"
                    :class="stat.label === 'Owed' ? 'col-span-2 sm:col-span-1' : ''">
                    <span class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent to-transparent"
                        :class="stat.accent" />
                    <p class="text-[9px] font-black uppercase tracking-widest text-slate-300">{{ stat.label }}</p>
                    <p class="mt-1.5 truncate text-2xl font-black leading-none" :class="stat.color ? '' : stat.tone"
                        :style="stat.color ? { color: stat.color } : null">
                        {{ stat.value }}
                    </p>
                    <p class="mt-1 text-[10px] text-slate-400">{{ stat.hint }}</p>
                </div>
            </section>

            <!-- Both cards share one height and scroll internally, so the page
                 itself never grows past the viewport however much either holds. -->
            <div class="mt-4 grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-5">

                <!-- Bookings -->
                <section
                    class="flex h-[26rem] min-h-0 flex-col rounded-3xl border border-slate-800 bg-slate-800/50 p-6 backdrop-blur-xl sm:h-[30rem] lg:col-span-2 lg:h-[34rem]">
                    <div class="flex shrink-0 items-baseline justify-between">
                        <div>
                            <h2 class="text-lg font-black tracking-tight">Your Bookings</h2>
                            <p class="mt-0.5 text-[10px] text-slate-400">Upcoming reservations</p>
                        </div>
                        <span v-if="upcoming.length"
                            class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-emerald-400">
                            {{ activeCount ? `${activeCount} playing` : `${upcoming.length} booked` }}
                        </span>
                    </div>

                    <div class="mt-5 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1
                                [scrollbar-color:theme(colors.slate.700)_transparent] [scrollbar-width:thin]
                                [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-700/70
                                [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">
                        <div v-if="loading" class="py-10 text-center text-[11px] font-bold text-slate-600">
                            Loading…
                        </div>

                        <div v-else-if="!upcoming.length"
                            class="rounded-2xl border border-dashed border-slate-600 py-10 text-center">
                            <p class="text-[11px] font-bold text-slate-400">Nothing booked yet</p>
                            <p class="mx-auto mt-1 max-w-[15rem] text-[10px] leading-relaxed text-slate-500">
                                Reserve a table and it'll appear here.
                            </p>
                        </div>

                        <BookingItem v-else v-for="booking in upcoming" :key="booking.id" class="w-full"
                            :for-customer="true" :booking="booking" @cancel="cancelBooking(booking.id)" />
                    </div>

                    <RouterLink to="/booking"
                        class="mt-5 flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-3.5 text-[10px] font-black uppercase tracking-widest text-white shadow-lg shadow-emerald-950/40 transition-all hover:bg-emerald-500 active:scale-[0.99]">
                        Book a Table
                        <span class="text-sm leading-none">&rsaquo;</span>
                    </RouterLink>
                </section>

                <!-- Games -->
                <section
                    class="flex h-[26rem] min-h-0 flex-col rounded-3xl border border-slate-800 bg-slate-800/50 p-6 backdrop-blur-xl sm:h-[30rem] lg:h-[34rem]" :class="khata.outstanding? 'lg:col-span-2' : 'lg:col-span-3'">
                    <div class="flex shrink-0 items-baseline justify-between">
                        <div>
                            <h2 class="text-lg font-black tracking-tight">My Games</h2>
                            <p class="mt-0.5 text-[10px] text-slate-500">Your recent sessions</p>
                        </div>
                        <span v-if="summary.gamesPlayed"
                            class="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-sky-400">
                            {{ summary.gamesPlayed }} played
                        </span>
                    </div>

                    <div v-if="gamesLoading"
                        class="mt-5 flex min-h-0 flex-1 items-center justify-center text-[11px] font-bold text-slate-600">
                        Loading…
                    </div>

                    <div v-else-if="!games.length" class="mt-5 flex min-h-0 flex-1 items-center justify-center">
                        <div class="rounded-2xl border border-dashed border-slate-800 px-6 py-10 text-center">
                            <p class="text-[11px] font-bold text-slate-500">No games yet</p>
                            <p class="mx-auto mt-1 max-w-[17rem] text-[10px] leading-relaxed text-slate-600">
                                Sessions you play on a booked table will show up here once they're
                                finished and billed.
                            </p>
                        </div>
                    </div>

                    <ul v-else class="mt-5 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1
                               [scrollbar-color:theme(colors.slate.700)_transparent] [scrollbar-width:thin]
                               [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-700/70
                               [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">
                        <li v-for="game in games" :key="game.id">
                            <div class="group flex w-full items-center gap-4 rounded-2xl border  px-4 py-3 text-left transition-colors"
                                :class="khata.bills.some(b => b.ref === game.receiptId) ?
                                'border-amber-700 bg-amber-400/10 hover:border-amber-600 hover:bg-amber-500/10' :
                                'border-slate-700 bg-slate-800/40 hover:border-slate-700 hover:bg-slate-900/70'"
                                :title="`View bill for ${typeLabel(game.tableType)} #${game.tableNumber}`">
                                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border"
                                    :style="{ borderColor: `${typeColor(game.tableType)}40`, backgroundColor: `${typeColor(game.tableType)}14` }">
                                    <span class="h-2.5 w-2.5 rounded-full"
                                        :style="{ backgroundColor: typeColor(game.tableType) }" />
                                </span>

                                <div class="min-w-0 flex-1">
                                    <p class="text-[9px] font-black uppercase tracking-wider"
                                        :style="{ color: typeColor(game.tableType) }">
                                        {{ typeLabel(game.tableType) }} #{{ game.tableNumber }}
                                    </p>
                                    <p class="mt-0.5 truncate text-xs font-bold text-slate-200">
                                        {{ playedLabel(game) }}
                                    </p>
                                </div>

                                <div class="shrink-0 text-right">
                                    <p class="font-mono text-xs font-bold text-slate-300">
                                        {{ durationLabel(game.minutes) }}
                                    </p>
                                    <p class="font-mono text-[10px] text-slate-400">Rs {{ game.cost }}</p>
                                </div>

                                <button type="button" @click="openReceipt(game)"
                                    class="cursor-pointer shrink-0 rounded-lg border px-2 py-1 text-[8px] font-black uppercase tracking-widest transition-colors "
                                    :class="khata.bills.some(b => b.ref === game.receiptId) ? 'border-amber-600 text-amber-600 hover:border-amber-400 hover:text-amber-400' : 'border-slate-600 text-slate-400 hover:border-emerald-600/50 hover:text-emerald-400'">
                                    Bill
                                </button>
                            </div>
                        </li>
                    </ul>
                </section>
                <section v-if="khata.outstanding"
                    class="rounded-3xl border border-amber-600/40 bg-amber-300/10 p-5 backdrop-blur-xl">
                    <div class="flex flex-wrap items-start justify-between gap-4">
                        <div>
                            <h2 class="text-[10px] font-black uppercase tracking-widest text-amber-500">Your Khata</h2>
                            <p class="mt-1 font-mono text-3xl font-black text-amber-400">
                                Rs {{ khata.outstanding }}
                            </p>
                            <p class="mt-1 text-[10px] text-slate-500">
                                {{ khata.bills.length }} unpaid bill{{ khata.bills.length === 1 ? '' : 's' }} ·
                                settle at the counter
                            </p>
                        </div>

                        <!-- One code clears everything owed. Paying it settles
                             every bill below in a single go. -->
                        <div v-if="khata.payUrl" class="flex flex-col items-center justify-center gap-2 p-2 w-full">
                            <svg :viewBox="qrViewBox(khata.payUrl)" class="w-36 rounded-lg bg-white p-1.5"
                                shape-rendering="crispEdges" role="img" aria-label="Scan to pay everything owed">
                                <path :d="qrPath(khata.payUrl)" fill="#0f172a" />
                            </svg>
                            <p class="text-center text-[9px] font-bold text-amber-400">
                                Scan to pay all Rs {{ khata.outstanding }}
                            </p>
                            <p class="max-w-[10rem] text-center text-[9px] leading-relaxed text-slate-500">
                                Clears every bill at once. Or open a bill below to pay it on its own.
                            </p>
                        </div>
                    </div>

                    <ul class="mt-4 space-y-1.5 border-t border-amber-600/20 pt-3">
                        <li v-for="bill in khata.bills" :key="`${bill.kind}-${bill.id}`"
                            class="rounded-xl bg-slate-950/30 px-3 py-2">
                            <div class="flex items-center justify-between gap-3 font-mono text-[11px]">
                                <span class="flex min-w-0 items-center gap-2">
                                    <span class="shrink-0 rounded px-1.5 py-0.5 text-[8px] font-black uppercase tracking-widest"
                                        :class="bill.kind === 'canteen'
                                            ? 'bg-amber-500/15 text-amber-400'
                                            : 'bg-sky-500/15 text-sky-400'">
                                        {{ bill.kind === 'canteen' ? 'Canteen' : 'Table' }}
                                    </span>
                                    <span class="truncate text-slate-300">{{ bill.label }}</span>
                                </span>
                                <div class="flex shrink-0 items-center gap-2">
                                    <span class="font-bold text-slate-200">Rs {{ bill.total }}</span>
                                    <button v-if="bill.payUrl" @click="toggleBill(bill)"
                                        class="cursor-pointer rounded-lg border px-2 py-1 text-[9px] font-black uppercase tracking-widest transition-colors"
                                        :class="openBill === billKey(bill)
                                            ? 'border-emerald-600/50 bg-emerald-600/15 text-emerald-300'
                                            : 'border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'">
                                        Pay
                                    </button>
                                </div>
                            </div>

                            <!-- Scanning this settles THIS bill only. -->
                            <div v-if="openBill === billKey(bill)"
                                class="mt-2 flex items-center gap-3 border-t border-slate-800 pt-2">
                                <svg :viewBox="qrViewBox(bill.payUrl)" class="h-24 w-24 shrink-0 rounded-lg bg-white p-1"
                                    shape-rendering="crispEdges" role="img" aria-label="Scan to pay this bill">
                                    <path :d="qrPath(bill.payUrl)" fill="#0f172a" />
                                </svg>
                                <p class="text-[10px] leading-relaxed text-slate-500">
                                    Pays <span class="font-bold text-slate-300">Rs {{ bill.total }}</span> for this
                                    {{ bill.kind === 'canteen' ? 'order' : 'table bill' }} only — the rest stays on
                                    your balance.
                                </p>
                            </div>
                        </li>
                    </ul>
                </section>
            </div>

            <!-- Account -->
            <section class="mt-4 rounded-3xl border border-slate-800 bg-slate-800/50 p-5 backdrop-blur-xl">
                <h2 class="mb-3 text-[9px] font-black uppercase tracking-widest text-slate-500">Account</h2>
                <dl class="grid grid-cols-1 gap-2 sm:grid-cols-3">
                    <div class="flex items-center justify-between rounded-xl bg-slate-900/50 border-1 border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Name</dt>
                        <dd class="truncate pl-3 text-xs font-bold">{{ fullName }}</dd>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-slate-900/50 border-1 border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Phone</dt>
                        <dd class="font-mono text-xs font-bold">{{ displayPhone }}</dd>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-slate-900/50 border-1 border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Email</dt>
                        <dd class="truncate pl-3 text-xs font-bold">{{ customer.profile?.email }}</dd>
                    </div>
                </dl>
            </section>

            <PoweredByZain :forCustomer="true"/>
        </div>

        <!-- Receipt overlay -->
        <div v-if="receiptOpen"
            class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4"
            :class="receipt? '' : 'bg-slate-950/80 backdrop-blur-sm'"
            @click.self="closeReceipt">
            <div v-if="receiptLoading"
                class="rounded-2xl border border-slate-800 bg-slate-900 px-6 py-4 text-[11px] font-bold text-slate-400">
                Loading bill…
            </div>
            <div v-else-if="receiptError"
                class="max-w-xs rounded-2xl border border-rose-500/30 bg-slate-900 px-6 py-5 text-center">
                <p class="text-[11px] font-bold text-rose-400">{{ receiptError }}</p>
                <button @click="closeReceipt"
                    class="mt-4 cursor-pointer rounded-xl bg-slate-800 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-300">
                    Close
                </button>
            </div>
            <BillingReceipt v-else-if="receipt" :receipt="receipt" :read-only="true" @close="closeReceipt" />
        </div>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { typeLabel, typeColor } from '@/composables/useTableTypes.js'

// Club branding is public (set by the activated license). Fetched directly from
// the public endpoint so the customer bundle stays independent of staff auth.
const clubName = ref('')

fetch(API_URL + '/branding')
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => { if (d) clubName.value = d.clubName || '' })
    .catch(() => {})

import { customer, signOut, apiGet, apiDelete } from '../auth.js'
import { formatPhoneDisplay } from '@/utils/phone.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import { qrMatrix, qrSvgPath } from '@/utils/qr.js'
import BookingItem from '@/components/BookingItem.vue'
import PoweredByZain from '@/components/PoweredByZain.vue'
// Shared presentation only — BillingReceipt imports nothing but Vue and the QR
// helper, so reusing it here doesn't pull staff code into the guest bundle.
import BillingReceipt from '@/components/BillingReceipt.vue'
import { API_URL, authFetch } from '@/Auth.js'

const fullName = computed(() => (customer.profile?.name || 'Guest').trim())
const displayPhone = computed(() => formatPhoneDisplay(customer.profile?.phone || ''))

const bookings = ref([])
const loading = ref(true)

/**
 * Upcoming or in progress.
 *
 * An active session keeps its place even once the booked end time has passed —
 * the guest is still playing, and dropping it would look like the booking
 * vanished mid-game.
 */
const upcoming = computed(() =>
    [...bookings.value]
        .filter((b) => b.status === 'active' || new Date(b.endTime) > new Date())
        .sort((a, b) => {
            if (a.status !== b.status) return a.status === 'active' ? -1 : 1
            return new Date(a.startTime) - new Date(b.startTime)
        }),
)

const activeCount = computed(() => upcoming.value.filter((b) => b.status === 'active').length)

// ── station styling, shared with BookingItem's vocabulary ──────────────────

// ── game history ──────────────────────────────────────────────────────────
const khata = ref({ outstanding: 0, bills: [], payUrl: null })

const QR_QUIET = 4

/**
 * Codes now encode the SERVER's payment links rather than a merchant payload,
 * so scanning opens the payment page and settles the bill it belongs to.
 * Matrices are cached — re-encoding on every render would rebuild them each
 * frame, and a balance can hold a dozen bills.
 */
const matrices = new Map()
function matrixFor(url) {
    if (!matrices.has(url)) matrices.set(url, qrMatrix(url, { ecLevel: 'M' }))
    return matrices.get(url)
}
const qrPath = (url) => qrSvgPath(matrixFor(url))
const qrViewBox = (url) => {
    const span = matrixFor(url).length + QR_QUIET * 2
    return `${-QR_QUIET} ${-QR_QUIET} ${span} ${span}`
}

const openBill = ref(null)
const billKey = (bill) => `${bill.kind}-${bill.id}`
const toggleBill = (bill) => {
    openBill.value = openBill.value === billKey(bill) ? null : billKey(bill)
}

const games = ref([])
const gamesLoading = ref(true)
const summary = ref({ gamesPlayed: 0, minutesPlayed: 0, favourite: null })

/** '95' -> '1h 35m'. Server sends billable minutes; the shaping is ours. */
function durationLabel(minutes) {
    const total = Number(minutes) || 0
    const h = Math.floor(total / 60)
    const m = total % 60
    if (!h) return `${m}m`
    return m ? `${h}h ${m}m` : `${h}h`
}

/** 'Today, 8:15 PM' / 'Yesterday, …' / 'Sat, 12 Aug'. */
function playedLabel(game) {
    if (!game.playedAt) return game.date || ''   // rows from before created_at existed
    const when = new Date(game.playedAt)
    const time = when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    const sameDay = (a, b) => a.toDateString() === b.toDateString()
    if (sameDay(when, today)) return `Today, ${time}`
    if (sameDay(when, yesterday)) return `Yesterday, ${time}`
    return `${when.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}, ${time}`
}

const stats = computed(() => [
    {
        label: 'Upcoming', value: upcoming.value.length,
        hint: upcoming.value.length === 1 ? 'reservation' : 'reservations',
        tone: 'text-emerald-400', accent: 'via-emerald-500/60',
    },
    {
        label: 'Games Played', value: summary.value.gamesPlayed,
        hint: summary.value.gamesPlayed === 1 ? 'session so far' : 'sessions so far',
        tone: 'text-sky-400', accent: 'via-sky-500/60',
    },
    {
        label: 'Time Played', value: totalPlayed.value,
        hint: 'across all stations', tone: 'text-violet-400', accent: 'via-violet-500/60',
    },
    {
         label: 'Favourite', value: favourite.value.label,
         hint: favourite.value.hint, tone: 'text-amber-400', accent: 'via-amber-500/60',
         color: favourite.value.color,
    },
    {
        label: 'Owed', value: `Rs ${khata.value.outstanding}`,
        hint: `${khata.value.bills.length} unpaid`,
        tone: 'text-amber-400', accent: 'via-amber-500/60',
    },
])

// Lifetime, not just the page of games shown below.
const totalPlayed = computed(() => durationLabel(summary.value.minutesPlayed))

/** Most-played station, computed server-side across every session. */
const favourite = computed(() => {
    const fav = summary.value.favourite
    if (!fav) return { label: '—', hint: 'no games yet', color: null }
    return {
        label: typeLabel(fav.type),
        hint: `${fav.plays} ${fav.plays === 1 ? 'session' : 'sessions'}`,
        color: typeColor(fav.type),
    }
})

// ── receipts ──────────────────────────────────────────────────────────────
const receiptOpen = ref(false)
const receiptLoading = ref(false)
const receiptError = ref('')
const receipt = ref(null)

async function openReceipt(game) {
    receiptOpen.value = true
    receiptLoading.value = true
    receiptError.value = ''
    receipt.value = null
    try {
        const data = await apiGet(`/games/${game.id}/receipt`)
        receipt.value = data.receipt
    } catch (error) {
        receiptError.value = error.message || "Couldn't load that bill"
    } finally {
        receiptLoading.value = false
    }
}

function closeReceipt() {
    receiptOpen.value = false
    receipt.value = null
    receiptError.value = ''
}

// ── data ──────────────────────────────────────────────────────────────────
async function cancelBooking(bookingId) {
    try {
        await apiDelete(`/bookings/${bookingId}`)
        bookings.value = bookings.value.filter((b) => b.id !== bookingId)
    } catch (error) {
        console.error('Failed to cancel booking:', error)
    }
}

async function fetchState() {
    // Both in flight together — one slow call shouldn't hold up the other card.
    const [bookingsResult, gamesResult, khataResult] = await Promise.allSettled([
        apiGet('/bookings'),
        apiGet('/games?limit=50'),
        apiGet('/khata'),
    ])

    if (bookingsResult.status === 'fulfilled') {
        bookings.value = bookingsResult.value.bookings || []
    } else {
        console.error('Failed to fetch bookings:', bookingsResult.reason)
    }
    loading.value = false

    if (gamesResult.status === 'fulfilled') {
        games.value = gamesResult.value.games || []
        summary.value = gamesResult.value.summary || summary.value
    } else {
        console.error('Failed to fetch games:', gamesResult.reason)
    }
    gamesLoading.value = false

    if (khataResult.status === 'fulfilled') {
        khata.value = {
            outstanding: khataResult.value.outstanding || 0,
            payUrl: khataResult.value.payUrl || null,
            bills: khataResult.value.bills || []
        }
    }
}

// Fetching once on mount meant a booking that staff started (or that was made
// on another device) sat stale here until a manual refresh.
useAutoRefresh(fetchState, 15000)
</script>