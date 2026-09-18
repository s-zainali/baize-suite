<template>
    <div class="flex-1 p-6 text-neutral-100">
        <div class="mb-2 flex flex-nowrap items-center justify-between gap-3">
            <h1 class=" flex-1 text-2xl font-black tracking-tight text-white sm:text-3xl">Live Overview</h1>

            <div class="flex flex-wrap items-center gap-3">
                <div v-if="offline"
                    class="rounded-full border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-rose-400">
                    Server Unreachable
                </div>
                <div v-else class="flex items-center gap-2">
                    <span class="relative flex h-2.5 w-2.5">
                        <span
                            class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                        <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                    </span>
                    <span class="text-[10px] font-black uppercase tracking-widest text-emerald-400">Live</span>
                </div>
                <span class="font-mono text-md sm:text-xl font-black tabular-nums text-white sm:text-2xl">{{ clockTime }}</span>
            </div>
        </div>

        <p class="-mt-2 mb-6 text-xs text-slate-500">{{ clockDate }}</p>

        <!-- KPI strip — hero (Today) spans 2, six uniform stat cards fill the rest.
             Every card shares one shell (label pinned top, value + context pinned
             bottom via justify-between + min-h) so numbers line up across the row.
             Grid tiles evenly at each width: 2-up mobile, 2×4 at md, one row at xl. -->
        
        <div>
            <BranchPicker :is-overview="true" :class="'mb-4 -mx-3'" />
        </div>

        <!-- All-branches board: the owner's comprehensive cross-branch pulse -->
        <div v-if="combined && branchBoard.length" class="mb-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            <button v-for="b in branchBoard" :key="b.id" @click="switchTo(b.id)"
                class="text-left rounded-2xl border border-neutral-800 bg-neutral-900/60 hover:border-emerald-500/40 p-4 transition-colors cursor-pointer">
                <div class="flex items-center justify-between gap-2 mb-3">
                    <div class="min-w-0">
                        <p class="text-sm font-black text-white truncate">{{ b.name }}</p>
                        <p class="text-[11px] text-neutral-500 truncate">{{ b.address || '—' }}</p>
                    </div>
                    <span class="shrink-0 text-[10px] font-black uppercase tracking-wider px-2 py-1 rounded-md"
                        :class="b.activeTables ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-neutral-800 text-neutral-500'">
                        {{ b.activeTables }}/{{ b.tables }} live
                    </span>
                </div>
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div><p class="text-lg font-black text-white tabular-nums">{{ formatRs(b.revenueToday) }}</p><p class="text-[9px] uppercase tracking-widest text-neutral-500">Today</p></div>
                    <div><p class="text-lg font-black text-white tabular-nums">{{ b.sessionsToday }}</p><p class="text-[9px] uppercase tracking-widest text-neutral-500">Sessions</p></div>
                    <div><p class="text-lg font-black tabular-nums" :class="b.owed ? 'text-amber-400' : 'text-white'">{{ formatRs(b.owed) }}</p><p class="text-[9px] uppercase tracking-widest text-neutral-500">Owed</p></div>
                </div>
                <p v-if="b.queue" class="mt-2 text-[11px] text-indigo-400">{{ b.queue }} waiting</p>
                <p class="mt-2 text-[10px] font-semibold text-emerald-400/70">Open this branch →</p>
            </button>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 mb-6">

            <!-- Today's takings — the hero metric -->
            <div
                class="col-span-2 flex flex-col justify-between min-h-[100px] rounded-2xl border border-emerald-500/30 bg-emerald-500/[0.06] p-4">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-emerald-500/80">Today</span>
                <div>
                    <span class="block font-mono text-3xl font-black tabular-nums leading-none text-emerald-400">Rs {{
                        formatRs(kpis.settledToday) }}</span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">{{ kpis.sessionsToday }} settled
                        session{{ kpis.sessionsToday === 1 ? '' : 's' }}</span>
                </div>
            </div>

            <!-- Avg ticket -->
            <div
                class="flex flex-col justify-between min-h-[100px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">Avg
                    Ticket</span>
                <div>
                    <span class="block font-mono text-2xl font-black tabular-nums leading-none text-emerald-400">Rs {{
                        formatRs(kpis.avgTicket) }}</span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">per session today</span>
                </div>
            </div>

            <!-- On the clock -->
            <div
                class="flex flex-col justify-between min-h-[100px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">On the
                    Clock</span>
                <div>
                    <span class="block font-mono text-2xl font-black tabular-nums leading-none text-indigo-400">Rs {{
                        formatRs(kpis.runningTotal) }}</span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">running, unsettled</span>
                </div>
            </div>

            <!-- Active now -->
            <div
                class="flex flex-col justify-between min-h-[100px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">Active
                    Now</span>
                <div>
                    <span class="block font-mono text-2xl font-black tabular-nums leading-none text-white">{{ kpis.active
                        }}<span class="text-base text-neutral-500">/{{ kpis.total }}</span></span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">tables in play</span>
                </div>
            </div>

            <!-- Occupancy — same shell, ring sits inline with the value -->
            <div
                class="flex flex-col justify-between min-h-[100px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">Occupancy</span>
                <div class="flex items-end justify-between gap-2">
                    <span class="font-mono text-2xl font-black tabular-nums leading-none" :style="{ color: occupancyColor }">{{
                        kpis.occupancy }}%</span>
                    <svg width="40" height="40" viewBox="0 0 46 46" class="-rotate-90 shrink-0">
                        <circle cx="23" cy="23" r="18" stroke="#262626" stroke-width="6" fill="none" />
                        <circle cx="23" cy="23" r="18" :stroke="occupancyColor" stroke-width="6" fill="none"
                            stroke-linecap="round" :stroke-dasharray="`${(kpis.occupancy / 100) * ringC} ${ringC}`"
                            class="transition-all duration-700" />
                    </svg>
                </div>
            </div>

            <!-- In queue -->
            <div
                class="flex flex-col justify-between min-h-[100px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">In
                    Queue</span>
                <div>
                    <span class="block font-mono text-2xl font-black tabular-nums leading-none"
                        :class="kpis.queue > 0 ? 'text-amber-400' : 'text-white'">{{ kpis.queue }}</span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">waiting</span>
                </div>
            </div>

            <!-- Sessions today -->
            <div
                class="flex flex-col justify-between min-h-[112px] rounded-2xl border border-neutral-800 bg-neutral-900 p-4 transition-colors hover:border-neutral-700">
                <span class="text-[10px] font-black uppercase tracking-widest leading-none text-neutral-500">Sessions</span>
                <div>
                    <span class="block font-mono text-2xl font-black tabular-nums leading-none text-white">{{
                        kpis.sessionsToday }}</span>
                    <span class="mt-2 block text-[10px] leading-none text-neutral-500">settled today</span>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- LEFT: floor map + rhythm -->
            <div class="lg:col-span-2 space-y-4">
                <div v-for="lounge in state.lounges" :key="lounge.uid"
                    class="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-sm font-black text-white">{{ lounge.name }}</span>
                        <div class="flex items-center gap-2">
                            <!-- mini occupancy dots -->
                            <div class="flex gap-1">
                                <span v-for="t in loungeTables(lounge.uid)" :key="t.uid"
                                    class="w-1.5 h-1.5 rounded-full transition-colors"
                                    :style="t.isActive ? { background: typeColor(t.type) } : { background: '#404040' }"></span>
                            </div>
                            <span class="text-[10px] font-mono text-neutral-500">
                                {{ loungeActive(lounge.uid) }}/{{ loungeTables(lounge.uid).length }}
                            </span>
                        </div>
                    </div>
                    <p v-if="loungeTables(lounge.uid).length === 0" class="text-xs text-neutral-600">No tables.</p>
                    <div v-else class="flex flex-wrap gap-2">
                        <div v-for="t in loungeTables(lounge.uid)" :key="t.uid"
                            class="w-[126px] rounded-xl border p-2.5 transition-colors" :style="t.isActive
                                ? { borderColor: typeColor(t.type), background: typeColor(t.type) + '14' }
                                : { borderColor: '#262626' }">
                            <div class="flex justify-between items-center">
                                <span class="text-[9px] font-black uppercase tracking-wider"
                                    :style="{ color: typeColor(t.type) }">{{ typeShort(t.type) }} #{{ t.id }}</span>
                                <span v-if="t.isActive" class="w-1.5 h-1.5 rounded-full animate-pulse"
                                    :style="{ background: typeColor(t.type) }"></span>
                            </div>
                            <template v-if="t.isActive">
                                <p class="text-[11px] font-extrabold text-white truncate mt-1">
                                    {{ t.bookingName || 'Walk-in Guest' }}</p>
                                <div class="flex justify-between items-baseline mt-0.5">
                                    <span class="text-[11px] font-mono font-bold text-neutral-300">{{
                                        formatElapsed(elapsedSeconds(t)) }}</span>
                                    <span class="text-[10px] font-mono font-bold text-emerald-400">Rs {{
                                        formatRs(runningCost(t)) }}</span>
                                </div>
                            </template>
                            <p v-else class="text-[10px] font-bold text-neutral-600 mt-1.5 mb-0.5">FREE</p>
                        </div>
                    </div>
                </div>

                <!-- Today's rhythm: revenue per hour -->
                <div class="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-[9px] uppercase font-black tracking-widest text-neutral-500">Today's
                            Rhythm</span>
                        <span class="text-[10px] font-mono text-neutral-500">revenue / hour</span>
                    </div>
                    <div class="flex items-end gap-[3px] h-25">
                        <div v-for="hr in hourlyToday" :key="hr.hour"
                            class="flex-1 rounded-t-sm min-h-[2px] transition-all" :class="hr.hour === currentHour
                                ? 'bg-emerald-500/80'
                                : hr.revenue > 0 ? 'bg-indigo-500/60' : 'bg-neutral-800/80'"
                            :style="{ height: hr.heightPct + '%' }"
                            :title="`${hr.label}: Rs ${formatRs(hr.revenue)} · ${hr.sessions} sessions`">
                        </div>
                    </div>
                    <div class="flex justify-between mt-1.5 text-[9px] font-mono text-neutral-600">
                        <span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>11 PM</span>
                    </div>
                </div>
            </div>

            <!-- RIGHT: sessions, queue, revenue mix -->
            <div
                class="space-y-4 lg:sticky lg:top-6 self-start lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto lg:pr-1 overview-scroll">
                <!-- Live sessions (compact, scrollable) -->
                <div class="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-[9px] uppercase font-black tracking-widest text-neutral-500">Live
                            Sessions</span>
                        <span v-if="activeSessions.length"
                            class="text-[9px] font-black font-mono bg-neutral-800 text-neutral-300 px-1.5 py-0.5 rounded-md">
                            {{ activeSessions.length }}</span>
                    </div>
                    <p v-if="activeSessions.length === 0" class="text-xs text-neutral-600">No sessions running.</p>
                    <div v-else class="space-y-1.5 max-h-[300px] overflow-y-auto pr-1 overview-scroll">
                        <div v-for="t in activeSessions" :key="t.uid"
                            class="flex items-center justify-between gap-2 bg-neutral-950/50 border border-neutral-800 rounded-lg px-2.5 py-1.5">
                            <div class="flex items-center gap-2 min-w-0">
                                <span class="w-1.5 h-1.5 rounded-full shrink-0"
                                    :style="{ background: typeColor(t.type) }"></span>
                                <div class="min-w-0">
                                    <p class="text-[11px] font-extrabold text-white truncate leading-tight">
                                        {{ t.bookingName || 'Walk-in Guest' }}</p>
                                    <p class="text-[8px] font-mono leading-tight" :style="{ color: typeColor(t.type) }">
                                        {{
                                        typeShort(t.type) }} #{{ t.id }}</p>
                                </div>
                            </div>
                            <div class="text-right shrink-0">
                                <p class="text-[10px] font-mono font-bold text-neutral-200 leading-tight">
                                    {{ formatElapsed(elapsedSeconds(t)) }}</p>
                                <p class="text-[9px] font-mono font-bold text-emerald-400 leading-tight">
                                    Rs {{ formatRs(runningCost(t)) }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Queue -->
                <div class="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-[9px] uppercase font-black tracking-widest text-neutral-500">Waiting
                            Queue</span>
                        <span v-if="state.queue.length"
                            class="text-[9px] font-black font-mono bg-neutral-800 text-neutral-300 px-1.5 py-0.5 rounded-md">
                            {{ state.queue.length }}</span>
                    </div>
                    <p v-if="state.queue.length === 0" class="text-xs text-neutral-600">Queue is empty.</p>
                    <div v-else class="space-y-1.5 max-h-[168px] overflow-y-auto pr-1 overview-scroll">
                        <div v-for="(g, i) in state.queue" :key="g.id"
                            class="flex justify-between items-center text-[11px]">
                            <span class="font-bold text-neutral-200 truncate">
                                <span class="text-neutral-600 font-mono mr-1.5">{{ i + 1 }}.</span>{{ g.name }}
                            </span>
                            <span class="font-mono text-[9px] shrink-0 ml-2"
                                :style="{ color: typeColor(g.tableType) }">{{
                                typeShort(g.tableType) }}</span>
                        </div>
                    </div>
                </div>

                <!-- Today by type: stacked bar + compact legend -->
                <div class="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
                    <span class="text-[9px] uppercase font-black tracking-widest text-neutral-500 block mb-3">Today by
                        Type</span>
                    <p v-if="todayByType.length === 0" class="text-xs text-neutral-600">No settled sessions yet.</p>
                    <template v-else>
                        <div class="h-2.5 w-full rounded-full overflow-hidden flex bg-neutral-800 mb-3">
                            <div v-for="row in todayByType" :key="row.type" class="h-full transition-all duration-500"
                                :style="{ width: row.pctOfTotal + '%', background: typeColor(row.type) }"
                                :title="`${typeShort(row.type)}: Rs ${formatRs(row.revenue)}`"></div>
                        </div>
                        <div class="space-y-1.5">
                            <div v-for="row in todayByType" :key="row.type"
                                class="flex justify-between items-center text-[10px]">
                                <span class="flex items-center gap-1.5 font-bold text-neutral-300">
                                    <span class="w-2 h-2 rounded-full"
                                        :style="{ background: typeColor(row.type) }"></span>
                                    {{ typeShort(row.type) }}
                                </span>
                                <span class="font-mono text-neutral-200">
                                    Rs {{ formatRs(row.revenue) }}
                                    <span class="text-neutral-500 ml-1">{{ row.pctOfTotal }}%</span>
                                </span>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { usePageBackground } from '@/composables/usePageBackground.js'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'
import BranchPicker from '@/components/BranchPicker.vue'
import { currentBranchId, canCombine, setBranch } from '@/composables/useBranch.js'

usePageBackground('#0a0a0a')

// const API_URL = import.meta.env.VITE_API_URL

const state = ref({ tables: [], queue: [], lounges: [], rates: {} })
const logs = ref([])
const branchBoard = ref([])
const combined = computed(() => currentBranchId.value == null && canCombine.value)
const now = ref(Date.now())
const offline = ref(false)

// ---------- POLLING ----------
let clockInterval, stateInterval, logsInterval

async function fetchState() {
    try {
        const res = await authFetch(`${API_URL}/state`)
        state.value = await res.json()
        offline.value = false
    } catch (_) {
        offline.value = true
    }
}

async function fetchBranchBoard() {
    if (!combined.value) { branchBoard.value = []; return }
    try {
        const res = await authFetch(`${API_URL}/branches/overview`)
        const d = await res.json()
        branchBoard.value = d.branches || []
    } catch (_) { /* keep last known */ }
}
function switchTo(id) { setBranch(id) }

async function fetchLogs() {
    try {
        const res = await authFetch(`${API_URL}/logs`)
        const data = await res.json()
        logs.value = data.logs
    } catch (_) { /* keep last known logs */ }
}

onMounted(() => {
    fetchState()
    fetchBranchBoard()
    fetchLogs()
    clockInterval = setInterval(() => { now.value = Date.now() }, 1000)
    stateInterval = setInterval(() => { fetchState(); fetchBranchBoard() }, 1000)
    logsInterval = setInterval(fetchLogs, 1000)
})

onUnmounted(() => {
    clearInterval(clockInterval)
    clearInterval(stateInterval)
    clearInterval(logsInterval)
})

// ---------- HELPERS ----------
const typeMeta = {
    snooker: { short: 'Snooker', color: '#34d399' },
    pool: { short: 'Pool', color: '#38bdf8' },
    privateSnooker: { short: 'VIP Snooker', color: '#fe9a00' },
    privatePool: { short: 'VIP Pool', color: '#c084fc' },
    ps5: { short: 'PS5', color: '#3b82f6' },
    foosball: { short: 'Foosball', color: '#a3e635' },
}
const typeColor = t => typeMeta[t]?.color || '#818cf8'
const typeShort = t => typeMeta[t]?.short || t

const formatRs = n => Math.round(n).toLocaleString('en-US')

const clockTime = computed(() =>
    new Date(now.value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
)
const clockDate = computed(() =>
    new Date(now.value).toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
)
const currentHour = computed(() => new Date(now.value).getHours())

const isWeekend = computed(() => {
    const day = new Date(now.value).getDay()
    return day === 0 || day === 6
})

const rateFor = (type) => {
    const rate = state.value.rates?.[type]
    if (!rate) return 0
    return isWeekend.value ? (rate.weekend ?? 0) : (rate.weekday ?? 0)
}

const elapsedSeconds = (t) =>
    t.startTime ? Math.max(0, Math.floor((now.value - new Date(t.startTime)) / 1000)) : 0

const formatElapsed = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    return h > 0
        ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
        : `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

const runningCost = (t) => Math.ceil(elapsedSeconds(t) / 60) * rateFor(t.type)

// ---------- DERIVED STATE ----------
const loungeTables = (loungeUid) => state.value.tables.filter(t => t.loungeUid === loungeUid)
const loungeActive = (loungeUid) => loungeTables(loungeUid).filter(t => t.isActive).length

const activeSessions = computed(() =>
    state.value.tables.filter(t => t.isActive).sort((a, b) => elapsedSeconds(b) - elapsedSeconds(a))
)

const todayLogs = computed(() => {
    const n = new Date(now.value)
    return logs.value.filter(l => {
        const d = new Date(l.date)
        return !isNaN(d.getTime())
            && d.getFullYear() === n.getFullYear()
            && d.getMonth() === n.getMonth()
            && d.getDate() === n.getDate()
    })
})

/**
 * Revenue by period, all from the same settled ledger.
 *
 * Calendar periods, not rolling windows: an owner asking "how did this quarter
 * go" means the quarter on the calendar, and a rolling 90 days would never
 * agree with his accountant.
 */
const periodRevenue = computed(() => {
    const n = new Date(now.value)
    const startOfDay = new Date(n.getFullYear(), n.getMonth(), n.getDate())

    // Week starts Monday — the trading week these clubs actually run on.
    const dayOffset = (n.getDay() + 6) % 7
    const startOfWeek = new Date(startOfDay)
    startOfWeek.setDate(startOfDay.getDate() - dayOffset)

    const startOfMonth = new Date(n.getFullYear(), n.getMonth(), 1)
    const startOfQuarter = new Date(n.getFullYear(), Math.floor(n.getMonth() / 3) * 3, 1)
    const startOfYear = new Date(n.getFullYear(), 0, 1)

    const totals = { today: 0, week: 0, month: 0, quarter: 0, year: 0 }
    const counts = { today: 0, week: 0, month: 0, quarter: 0, year: 0 }

    for (const log of logs.value) {
        const d = new Date(log.date)
        if (isNaN(d.getTime())) continue
        const amount = Number(log.totalCost) || 0

        // Each period contains the shorter ones, so no early exit.
        if (d >= startOfYear) { totals.year += amount; counts.year += 1 }
        if (d >= startOfQuarter) { totals.quarter += amount; counts.quarter += 1 }
        if (d >= startOfMonth) { totals.month += amount; counts.month += 1 }
        if (d >= startOfWeek) { totals.week += amount; counts.week += 1 }
        if (d >= startOfDay) { totals.today += amount; counts.today += 1 }
    }

    const quarter = Math.floor(n.getMonth() / 3) + 1
    return {
        totals,
        counts,
        labels: {
            today: 'Today',
            week: 'This Week',
            month: n.toLocaleDateString([], { month: 'long' }),
            quarter: `Q${quarter} ${n.getFullYear()}`,
            year: String(n.getFullYear()),
        },
    }
})

const periodCards = computed(() => {
    const { totals, counts, labels } = periodRevenue.value
    return ['today', 'week', 'month', 'quarter', 'year'].map((key) => ({
        key,
        label: labels[key],
        total: totals[key],
        sessions: counts[key],
    }))
})

const kpis = computed(() => {
    const tables = state.value.tables
    const active = tables.filter(t => t.isActive).length
    return {
        settledToday: todayLogs.value.reduce((s, l) => s + (Number(l.totalCost) || 0), 0),
        runningTotal: tables.filter(t => t.isActive).reduce((s, t) => s + runningCost(t), 0),
        active,
        total: tables.length,
        occupancy: tables.length ? Math.round((active / tables.length) * 100) : 0,
        queue: state.value.queue.length,
        sessionsToday: todayLogs.value.length,
        // Shown in place of today's total, which the period row now covers.
        avgTicket: todayLogs.value.length
            ? Math.round(todayLogs.value.reduce((s2, l) => s2 + (Number(l.totalCost) || 0), 0) / todayLogs.value.length)
            : 0,
    }
})

// Occupancy ring
const ringC = 2 * Math.PI * 18
const occupancyColor = computed(() =>
    kpis.value.occupancy >= 80 ? '#34d399' : kpis.value.occupancy >= 40 ? '#38bdf8' : '#737373'
)

// Revenue per hour today
const hourlyToday = computed(() => {
    const buckets = Array.from({ length: 24 }, (_, hour) => ({
        hour,
        label: hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`,
        revenue: 0,
        sessions: 0,
    }))
    for (const l of todayLogs.value) {
        const d = new Date(l.date)
        if (isNaN(d.getTime())) continue
        buckets[d.getHours()].revenue += Number(l.totalCost) || 0
        buckets[d.getHours()].sessions++
    }
    const max = Math.max(1, ...buckets.map(b => b.revenue))
    return buckets.map(b => ({ ...b, heightPct: Math.round((b.revenue / max) * 100) }))
})

// Share of today's revenue by type (percent of TOTAL, for the stacked bar)
const todayByType = computed(() => {
    const totals = {}
    for (const l of todayLogs.value) {
        totals[l.tableType] = (totals[l.tableType] || 0) + (Number(l.totalCost) || 0)
    }
    const grand = Object.values(totals).reduce((s, v) => s + v, 0) || 1
    return Object.entries(totals)
        .map(([type, revenue]) => ({ type, revenue, pctOfTotal: Math.round((revenue / grand) * 100) }))
        .sort((a, b) => b.revenue - a.revenue)
})


</script>

<style>
/* Slim scrollbar for the live-sessions list */
.overview-scroll::-webkit-scrollbar {
    width: 6px;
}

.overview-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.overview-scroll::-webkit-scrollbar-thumb {
    background: rgb(64 64 64);
    border-radius: 3px;
}

.overview-scroll::-webkit-scrollbar-thumb:hover {
    background: rgb(82 82 82);
}
</style>