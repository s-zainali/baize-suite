<template>
    <div class="bg-slate-900 p-6 pt-0 text-slate-100">
        <div class="flex flex-col">
            <header
                class="sticky top-0 left-0 z-50 -mr-6 -ml-6 mb-6 flex flex-row flex-wrap items-start justify-between gap-4 bg-slate-900 px-6 pt-6 pb-6 lg:items-center">
                <h2 class="text-3xl font-black text-white">Analytics</h2>

                <RouterLink v-if="filtered" to="/logs"
                    class="rounded-xl border border-indigo-500/40 bg-indigo-500/10 px-3 py-1.5 text-xs font-bold text-indigo-300 hover:bg-indigo-500/20">
                    {{ activeFilterCount }} filter{{ activeFilterCount > 1 ? 's' : '' }} applied — adjust in the log
                </RouterLink>
                <div class="flex items-center gap-2">
                    <!-- Range pills -->
                    <div class="flex bg-slate-950/60 border border-slate-800 rounded-xl p-1 gap-1">
                        <button v-for="r in ranges" :key="r.id" type="button" v-show="rangeAvailable(r)"
                            @click="rangeId = r.id"
                            class="px-3 py-1 rounded-lg text-[10px] font-black tracking-wider transition-colors cursor-pointer"
                            :class="[
                                rangeId === r.id
                                    ? 'bg-indigo-500 text-white'
                                    : 'text-slate-400 hover:text-white hover:bg-slate-800',
                                r.kind !== 'rolling' ? 'border-1 border-slate-800 first:border-l-0 ml-0.5 pl-3' : '',
                            ]">
                            {{ r.label }}
                        </button>
                    </div>
                </div>
            </header>

            <!-- Analytics crunches the full history, so it loads on demand
                 rather than pegging the CPU on every visit. -->
            <div v-if="!insightsLoaded"
                class="flex-1 flex flex-col items-center justify-center text-center py-24 border border-slate-800 rounded-2xl bg-slate-950/40">
                <span class="text-4xl mb-4">📊</span>
                <p class="text-base font-black text-white">Analytics is ready to build</p>
                <p class="text-xs text-slate-500 mt-1 mb-6 max-w-sm">This processes your full history — loaded on demand so it never slows the rest of the app. It can take a few seconds for a busy year.</p>
                <button @click="loadInsights" :disabled="insightsLoading"
                    class="px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white cursor-pointer flex items-center gap-2">
                    <svg v-if="insightsLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                    {{ insightsLoading ? 'Crunching your history…' : 'Load Insights' }}
                </button>
                <p v-if="insightsLoading" class="text-[11px] text-slate-500 mt-3 font-mono">Fetching &amp; aggregating — hang tight, you can wait here.</p>
                <p v-else-if="loadError" class="text-[11px] text-rose-400 mt-3">{{ loadError }}</p>
            </div>

            <!-- Empty state -->
            <div v-else-if="scopedLogs.length === 0 && scopedOrders.length === 0"
                class="flex-1 flex flex-col items-center justify-center text-center py-20 border border-slate-800 rounded-2xl bg-slate-950/40">
                <span class="text-4xl mb-3">📊</span>
                <p class="text-sm font-bold text-slate-300">No activity in this period</p>
                <p class="text-xs text-slate-500 mt-1">Try a wider range, or settle some tables first.</p>
            </div>

            <!-- Body -->
            <div v-else-if="insightsLoaded" class="flex-1 overflow-y-auto space-y-4 pr-1 lounge-analytics-scroll">
                <!-- TOTAL REVENUE — the number people open this page for -->
                <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                    <div class="flex flex-wrap items-end justify-between gap-4">
                        <div>
                            <span class="block text-[10px] font-black uppercase tracking-widest text-slate-500">
                                Total Revenue · {{ activeRange.caption }}
                            </span>
                            <span class="mt-1 block font-mono text-4xl font-black text-emerald-400">
                                Rs {{ formatRs(revenue.total) }}
                            </span>
                        </div>
                        <div class="flex gap-6">
                            <div>
                                <span
                                    class="block text-[10px] font-black uppercase tracking-widest text-slate-500">Games</span>
                                <span class="mt-0.5 block font-mono text-lg font-black text-sky-400">Rs {{
                                    formatRs(revenue.games) }}</span>
                                <span class="font-mono text-[10px] text-slate-600">{{ revenue.gamesPct }}% · {{
                                    kpis.sessions }} sessions</span>
                            </div>
                            <div>
                                <span
                                    class="block text-[10px] font-black uppercase tracking-widest text-slate-500">Canteen</span>
                                <span class="mt-0.5 block font-mono text-lg font-black text-amber-400">Rs {{
                                    formatRs(revenue.counter) }}</span>
                                <span class="font-mono text-[10px] text-slate-600">{{ revenue.counterPct }}% · {{
                                    revenue.orders }} orders</span>
                            </div>
                        </div>
                    </div>

                    <!-- proportion bar -->
                    <div class="mt-4 flex h-2 overflow-hidden rounded-full bg-slate-800">
                        <div class="bg-sky-500 transition-all" :style="{ width: revenue.gamesPct + '%' }" />
                        <div class="bg-amber-500 transition-all" :style="{ width: revenue.counterPct + '%' }" />
                    </div>

                    <p v-if="revenue.onTab" class="mt-3 text-[10px] leading-snug text-slate-500">
                        A further <span class="font-mono font-bold text-slate-300">Rs {{ formatRs(revenue.onTab)
                            }}</span>
                        of canteen items was charged to table tabs — already counted inside Games revenue, so it isn't
                        added again here.
                    </p>
                </div>

                <!-- KPI CARDS -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <span
                            class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">Sessions</span>
                        <span class="text-2xl font-black text-white font-mono mt-2 block">{{ kpis.sessions }}</span>
                    </div>
                    <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <span
                            class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">Avg
                            Game Ticket</span>
                        <span class="text-2xl font-black text-indigo-400 font-mono mt-2 block">Rs {{
                            formatRs(kpis.avgTicket) }}</span>
                    </div>
                    <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <span
                            class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">Avg
                            Session</span>
                        <span class="text-2xl font-black text-sky-400 font-mono mt-2 block">{{ kpis.avgSession }}</span>
                    </div>
                    <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <span
                            class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">Avg
                            Canteen Order</span>
                        <span class="text-2xl font-black text-amber-400 font-mono mt-2 block">Rs {{
                            formatRs(revenue.avgOrder) }}</span>
                    </div>
                </div>

                <!-- HEADLINE CHARTS — both cover games AND canteen, so they sit
                     above the canteen-specific breakdown below. -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <!-- REVENUE TREND -->
                    <div class="lg:col-span-2 bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <div class="grid grid-cols-3 mb-3">
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500">Revenue
                                Trend</span>
                            <span class="text-[10px] font-mono text-slate-500 text-center">
                                {{ activeRange.caption }} games + canteen
                            </span>
                            <div class="flex justify-end shrink-0 text-nowrap">
                                <button
                                    class="text-[10px] w-30 uppercase font-bold bg-slate-800 px-2 py-1 rounded-md text-slate-300 hover:text-slate-50 cursor-pointer transition duration-300 ease-in-out active:scale-98"
                                    :class="showTrendline ? 'hover:bg-rose-600/70' : 'hover:bg-emerald-600/70'"
                                    @click="showTrendline = !showTrendline">{{ showTrendline ? 'Hide' : 'Show' }}
                                    Trendline</button>
                            </div>
                        </div>
                        <svg :viewBox="`0 0 ${chart.W} ${chart.H}`" class="w-full" preserveAspectRatio="none">
                            <defs>
                                <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stop-color="#047857" stop-opacity="0.35" />
                                    <stop offset="100%" stop-color="#047857" stop-opacity="0" />
                                </linearGradient>
                            </defs>
                            <!-- gridlines -->
                            <g v-for="g in gridLines" :key="g.y">
                                <line :x1="chart.padL" :x2="chart.W - chart.padR" :y1="g.y" :y2="g.y" stroke="#1e293b"
                                    stroke-width="1" />
                                <text :x="chart.padL - 6" :y="g.y + 3" text-anchor="end" fill="#64748b" font-size="9"
                                    font-family="monospace">{{ g.label }}</text>
                            </g>
                            <!-- area + line -->
                            <path :d="areaPath" fill="url(#revFill)" />
                            <path :d="linePath" class="transition duration-400 ease-in-out"
                                :class="showTrendline ? 'opacity-40' : ''" fill="none" stroke="#059669" stroke-width="2"
                                stroke-linejoin="round" stroke-linecap="round" />
                            <!-- dots (skipped on long ranges) -->
                            <g v-if="trendDays.length <= 31">
                                <circle class="transition duration-400 ease-in-out"
                                    :class="showTrendline ? 'opacity-40' : ''" v-for="(p, i) in trendPoints" :key="i"
                                    :cx="p.x" :cy="p.y" r="2" fill="#0f172a" stroke="#10b981" stroke-width="1.5">
                                    <title>{{ trendDays[i].label }}: Rs {{ formatRs(trendDays[i].revenue) }} ({{
                                        trendDays[i].sessions }} sessions, {{ trendDays[i].orders }} canteen orders)
                                    </title>
                                </circle>
                            </g>
                            <TransitionGroup name="fade" tag="g">
                                <path v-if="showTrendline" :d="trendlinePath" fill="none" stroke="#00ffb0"
                                    stroke-width="2" />
                            </TransitionGroup>
                            <!-- x labels -->
                            <text v-for="l in xLabels" :key="l.x" :x="l.x" :y="chart.H - 6" text-anchor="middle"
                                fill="#64748b" font-size="9" font-family="monospace">{{ l.label }}</text>
                        </svg>
                    </div>
                    <div class="flex flex-col gap-4 row-span-2">
                        <!-- REVENUE BY TABLE TYPE (donut) -->
                        <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex-1 flex flex-col">
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 mb-3">Revenue
                                by
                                Table Type</span>
                            <div class="flex-1 flex items-center gap-4">
                                <div class="relative shrink-0">
                                    <svg viewBox="0 0 120 120" class="w-35 h-35">
                                        <circle cx="60" cy="60" r="48" fill="none" stroke="#1e293b" stroke-width="14" />
                                        <circle v-for="seg in donutSegments" :key="seg.type" cx="60" cy="60" r="48"
                                            fill="none" :stroke="seg.color" stroke-width="14"
                                            :stroke-dasharray="`${seg.length} ${donutC}`"
                                            :stroke-dashoffset="seg.offset" transform="rotate(-90 60 60)"
                                            stroke-linecap="butt">
                                            <title>{{ seg.label }}: Rs {{ formatRs(seg.revenue) }} ({{ seg.pct }}%)
                                            </title>
                                        </circle>
                                    </svg>
                                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                                        <span
                                            class="text-[8px] uppercase font-black tracking-widest text-slate-500">Total</span>
                                        <span class="text-[11px] font-black text-white font-mono">Rs {{
                                            formatRs(kpis.revenue) }}</span>
                                    </div>
                                </div>
                                <div class="flex-1 space-y-2">
                                    <div v-for="seg in donutSegments" :key="seg.type"
                                        class="flex items-center justify-between gap-2">
                                        <div class="flex items-center gap-1.5 min-w-0">
                                            <span class="w-2 h-2 rounded-full shrink-0"
                                                :style="{ background: seg.color }"></span>
                                            <span class="text-[10px] font-bold text-slate-300 truncate">{{ seg.label
                                                }}</span>
                                        </div>
                                        <span class="text-[10px] font-mono text-slate-400 shrink-0">{{ seg.pct
                                            }}%</span>
                                    </div>
                                </div>
                            </div>
                            <!-- REVENUE BY CANTEEN ITEM (donut, matching Table Type) -->
                        </div>
                        <div v-if="itemDonut.length"
                            class="flex-1 bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex flex-col">
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 mb-3">Revenue
                                by
                                Canteen Item</span>
                            <div class="flex-1 flex items-center gap-4">
                                <div class="relative shrink-0">
                                    <svg viewBox="0 0 120 120" class="w-35 h-35">
                                        <circle cx="60" cy="60" r="48" fill="none" stroke="#1e293b" stroke-width="14" />
                                        <circle v-for="seg in itemDonut" :key="seg.name" cx="60" cy="60" r="48"
                                            fill="none" :stroke="seg.color" stroke-width="14"
                                            :stroke-dasharray="`${seg.length} ${donutC}`"
                                            :stroke-dashoffset="seg.offset" transform="rotate(-90 60 60)"
                                            stroke-linecap="butt">
                                            <title>{{ seg.name }}: Rs {{ formatRs(seg.revenue) }} ({{ seg.pct }}%) ·
                                                {{ seg.qty }} sold</title>
                                        </circle>
                                    </svg>
                                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                                        <span
                                            class="text-[8px] uppercase font-black tracking-widest text-slate-500">Sold</span>
                                        <span class="text-[11px] font-black text-white font-mono">Rs {{
                                            formatRs(itemRevenueTotal) }}</span>
                                    </div>
                                </div>
                                <div class="flex-1 space-y-2">
                                    <div v-for="seg in itemDonut" :key="seg.name"
                                        class="flex items-center justify-between gap-2">
                                        <div class="flex items-center gap-1.5 min-w-0">
                                            <span class="w-2 h-2 rounded-full shrink-0"
                                                :style="{ background: seg.color }"></span>
                                            <span class="text-[10px] font-bold text-slate-300 truncate">{{ seg.name
                                                }}</span>
                                        </div>
                                        <span class="text-[10px] font-mono text-slate-400 shrink-0">{{ seg.pct
                                            }}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="lg:col-span-2 bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <div class="flex justify-between items-center mb-3">
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500">Activity by
                                Hour</span>
                            <span v-if="peakHour" class="text-[10px] font-mono text-slate-500">
                                peak: <span class="text-emerald-400 font-bold">{{ peakHour.label }}</span>
                            </span>
                        </div>
                        <div class="flex items-end gap-1 h-28">
                            <div v-for="hr in hourly" :key="hr.hour"
                                class="flex-1 rounded-t-md transition-all cursor-default min-h-[2px]" :class="hr.count === peakHour?.count && hr.count > 0
                                    ? 'bg-emerald-500/80 hover:bg-emerald-400'
                                    : 'bg-indigo-500/50 hover:bg-indigo-400/70'"
                                :style="{ height: hr.heightPct + '%' }"
                                :title="`${hr.label}: ${hr.sessions} sessions, ${hr.orders} canteen orders · Rs ${formatRs(hr.revenue)}`">
                            </div>
                        </div>
                        <div class="flex justify-between mt-1.5 text-[9px] font-mono text-slate-600">
                            <span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>11 PM</span>
                        </div>
                    </div>

                    <!-- Donuts stacked in one column so the trend gets the width -->

                    <!-- CANTEEN DETAIL — same three-column rhythm as the games row -->

                    <!-- COUNTER TAKINGS BY METHOD -->
                    <div v-if="paymentSplit.length"
                        class=" bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex flex-col">
                        <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 mb-3">Counter
                            Takings by Method</span>
                        <div class="flex-1 space-y-2.5">
                            <div v-for="row in paymentSplit" :key="row.method">
                                <div class="flex items-center justify-between gap-2 mb-1">
                                    <span class="text-[10px] font-bold capitalize text-slate-300">{{ row.method
                                        }}</span>
                                    <span class="text-[10px] font-mono font-bold text-slate-200">Rs {{
                                        formatRs(row.value) }}</span>
                                </div>
                                <div class="h-1.5 overflow-hidden rounded-full bg-slate-800">
                                    <div class="h-full rounded-full"
                                        :style="{ width: row.pct + '%', backgroundColor: row.color }" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- TOP MEMBERS -->
                    <div class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4">
                        <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 block mb-3">Top
                            Members</span>
                        <div v-if="topPlayers.length" class="space-y-2.5">
                            <div v-for="(p, i) in topPlayers" :key="p.customerId">
                                <div class="flex justify-between items-baseline mb-1">
                                    <span class="text-[11px] font-bold text-white truncate max-w-[60%]">
                                        <span class="text-slate-600 font-mono mr-1">{{ i + 1 }}.</span>{{ p.name }}
                                    </span>
                                    <span class="text-[10px] font-mono text-emerald-400 font-bold">Rs {{
                                        formatRs(p.revenue) }}</span>
                                </div>
                                <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                    <div class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
                                        :style="{ width: p.widthPct + '%' }"></div>
                                </div>
                            </div>
                        </div>
                        <p v-else class="text-xs text-slate-500">No member play yet.</p>
                    </div>
                    <div class="bg-slate-950/40 border rounded-2xl p-4 flex flex-col justify-between"
                        :class="credit.total ? 'border-amber-600/40' : 'border-slate-800'">

                        <div>
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500">Total Owed</span>
                            <p class="mt-2 font-mono text-3xl font-black"
                                :class="credit.total ? 'text-amber-400' : 'text-slate-600'">
                                Rs {{ formatRs(credit.total) }}
                            </p>
                        </div>
                        <div class="bg-slate-950/40 border rounded-2xl p-4 flex flex-col justify-center"
                            :class="outstanding ? 'border-amber-600/40' : 'border-slate-800'">
                            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500">Unsettled
                                Canteen</span>
                            <span class="mt-2 font-mono text-2xl font-black"
                                :class="outstanding ? 'text-amber-400' : 'text-slate-600'">
                                Rs {{ formatRs(outstanding) }}
                            </span>
                        </div>
                        <p class="mt-2 text-[10px] leading-snug text-slate-600">
                            {{ credit.total
                                ? `${credit.bills} unpaid bill${credit.bills === 1 ? '' : 's'} across ${credit.people}
                            guest${credit.people === 1 ? '' : 's'}`
                                : 'Everything has been collected.' }}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { RouterLink } from 'vue-router'
import {
    canteenOrders, filteredLogs, activeFilterCount, loadLedger,
} from '@/composables/useLedger.js'
import { usePageBackground } from '@/composables/usePageBackground.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import { canFloor } from '@/Auth.js'
import { types } from '@/composables/useTableTypes'


const showTrendline = ref(false)
// ---------- RANGE ----------
// ---------- RANGE ----------
//
// Two kinds of range, deliberately side by side. Rolling windows answer "how
// are we doing lately"; calendar quarters answer "how did Q2 go" — the
// question an owner asks his accountant, and one a rolling 90 days can never
// answer, because it never lines up with a quarter.
const ranges = [
    { id: '7d', label: '7D', kind: 'rolling', days: 7 },
    { id: '30d', label: '30D', kind: 'rolling', days: 30 },
    { id: '90d', label: '90D', kind: 'rolling', days: 90 },
    { id: 'q1', label: 'Q1', kind: 'quarter', quarter: 0 },
    { id: 'q2', label: 'Q2', kind: 'quarter', quarter: 1 },
    { id: 'q3', label: 'Q3', kind: 'quarter', quarter: 2 },
    { id: 'q4', label: 'Q4', kind: 'quarter', quarter: 3 },
    { id: 'year', label: 'Year', kind: 'year' },
]

const rangeId = ref('30d')

const MS_DAY = 86400000

function endOf(day) {
    return new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59, 999)
}

/** Inclusive day count. Compared at midnight, since `end` is an end-of-day. */
function spanDays(start, end) {
    const a = new Date(start.getFullYear(), start.getMonth(), start.getDate())
    const b = new Date(end.getFullYear(), end.getMonth(), end.getDate())
    return Math.max(1, Math.round((b - a) / MS_DAY) + 1)
}

/** The selected range, resolved to a concrete window. */
const activeRange = computed(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const range = ranges.find((r) => r.id === rangeId.value) || ranges[1]

    if (range.kind === 'rolling') {
        // Built from date parts rather than millisecond arithmetic, so a clock
        // change can't shift the window by a day.
        const start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (range.days - 1))
        return { start, end: endOf(today), days: range.days, caption: `last ${range.days} days` }
    }

    if (range.kind === 'year') {
        const start = new Date(now.getFullYear(), 0, 1)
        // Never chart into the future — an empty tail reads as a collapse.
        const end = endOf(today)
        return { start, end, days: spanDays(start, end), caption: String(now.getFullYear()) }
    }

    const start = new Date(now.getFullYear(), range.quarter * 3, 1)
    const quarterEnd = new Date(now.getFullYear(), range.quarter * 3 + 3, 0)
    const end = endOf(quarterEnd < today ? quarterEnd : today)
    return {
        start, end, days: spanDays(start, end),
        caption: `${range.label} ${now.getFullYear()}`,
    }
})

/** A quarter that hasn't started yet has nothing to show. */
const rangeAvailable = (range) => {
    if (range.kind !== 'quarter') return true
    return range.quarter * 3 <= new Date().getMonth()
}

const rangeDays = ref(30)

// ---------- HELPERS ----------
const pad = n => String(n).padStart(2, '0')
const dayKey = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const monthsShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// date_string is stored as a locale string like "7/7/2026, 3:45:12 PM"
const parseLogDate = (dateString) => {
    const d = new Date(dateString)
    return isNaN(d.getTime()) ? null : d
}

const formatRs = n => Math.round(n).toLocaleString('en-US')


const typeMeta = types
console.log(typeMeta)

// ---------- SCOPED LOGS (within selected range, with parsed date attached) ----------
const scopedLogs = computed(() => {
    const { start, end } = activeRange.value
    return (filteredLogs.value || [])
        .map(log => ({ ...log, _date: parseLogDate(log.date) }))
        .filter(log => log._date && log._date >= start && log._date <= end)
})

/**
 * Canteen sales inside the range, EXCLUDING tab orders.
 *
 * A tab order is billed with the table session, so its value is already inside
 * that session's totalCost. Counting it again here would inflate revenue —
 * this is the one trap in combining the two ledgers.
 */
/**
 * Canteen sales in range — ALL of them, tab included.
 *
 * Table bills now record play time only, so a tab order is no longer inside
 * any session total. Counting the whole canteen ledger here is both correct
 * and the thing the question actually asks: what did the canteen take?
 */
const scopedOrders = computed(() => {
    const { start, end } = activeRange.value
    return (canteenOrders.value || [])
        .filter((o) => o.status !== 'void')
        .map((o) => ({ ...o, _date: o.at ? new Date(o.at) : null }))
        .filter((o) => o._date && o._date >= start && o._date <= end)
})

/** Tab sales, shown for context — these were billed with a table. */
const scopedTabOrders = computed(() => {
    const { start, end } = activeRange.value
    return (canteenOrders.value || [])
        .filter((o) => o.status !== 'void' && o.method === 'tab')
        .map((o) => ({ ...o, _date: o.at ? new Date(o.at) : null }))
        .filter((o) => o._date && o._date >= start && o._date <= end)
})

const revenue = computed(() => {
    const games = scopedLogs.value.reduce((sum, l) => sum + (Number(l.totalCost) || 0), 0)
    const counter = scopedOrders.value.reduce((sum, o) => sum + (Number(o.total) || 0), 0)
    const onTab = scopedTabOrders.value.reduce((sum, o) => sum + (Number(o.total) || 0), 0)
    const total = games + counter
    return {
        games, counter, onTab, total,
        gamesPct: total ? Math.round((games / total) * 100) : 0,
        counterPct: total ? Math.round((counter / total) * 100) : 0,
        orders: scopedOrders.value.length,
        avgOrder: scopedOrders.value.length ? counter / scopedOrders.value.length : 0,
    }
})

/** Counter takings split by how they were paid. */
const paymentSplit = computed(() => {
    const totals = {}
    for (const order of scopedOrders.value) {
        order.method === 'tab' ? null : totals[order.method] = (totals[order.method] || 0) + (Number(order.total) || 0)
    }
    for (const log of scopedLogs.value) {
        if (log.paymentMethod === '') {
            totals['cash'] = (totals['cash'] || 0) + Number(log.totalCost) || 0
        } else {
            totals[log.paymentMethod] = (totals[log.paymentMethod] || 0) + (Number(log.totalCost) || 0)
        }
    }
    const sum = Object.values(totals).reduce((a, b) => a + b, 0)
    const colours = { cash: '#34d399', easypaisa: '#38bdf8', jazzcash: '#f472b6' }
    return Object.entries(totals)
        .sort((a, b) => b[1] - a[1])
        .map(([method, value]) => ({
            method, value,
            pct: sum ? Math.round((value / sum) * 100) : 0,
            color: colours[method] || '#818cf8',
        }))
})

/**
 * Best-selling canteen items by revenue.
 *
 * Counts EVERY non-void sale, tab included — the question here is what the
 * kitchen actually sells, which doesn't change because a guest put it on their
 * table bill. (The revenue banner above deliberately excludes tab orders, since
 * that money is already inside the session totals.)
 */
const itemRevenue = computed(() => {
    const { start, end } = activeRange.value
    const totals = {}

    for (const order of canteenOrders.value || []) {
        if (order.status === 'void') continue
        const when = order.at ? new Date(order.at) : null
        if (!when || when < start || when > end) continue
        for (const line of order.items || []) {
            const row = totals[line.name] || (totals[line.name] = { name: line.name, qty: 0, revenue: 0 })
            row.qty += Number(line.qty) || 0
            row.revenue += Number(line.lineTotal) || 0
        }
    }

    const rows = Object.values(totals).sort((a, b) => b.revenue - a.revenue)
    const top = rows[0]?.revenue || 0
    return rows.map((r) => ({ ...r, pct: top ? Math.round((r.revenue / top) * 100) : 0 }))
})

const itemRevenueTotal = computed(() =>
    itemRevenue.value.reduce((sum, r) => sum + r.revenue, 0),
)

// Palette for the item ring. A menu can run to dozens of lines, so only the top
// few get their own slice and the tail is folded into "Other" — otherwise the
// donut turns into confetti and the legend runs off the card.
const ITEM_COLORS = ['#f59e0b', '#34d399', '#38bdf8', '#c084fc', '#f472b6', '#64748b']
const TOP_ITEM_SLICES = 5

const itemDonut = computed(() => {
    const rows = itemRevenue.value
    if (!rows.length) return []

    const top = rows.slice(0, TOP_ITEM_SLICES)
    const rest = rows.slice(TOP_ITEM_SLICES)
    const slices = [...top]
    if (rest.length) {
        slices.push({
            name: `Other (${rest.length})`,
            qty: rest.reduce((sum, r) => sum + r.qty, 0),
            revenue: rest.reduce((sum, r) => sum + r.revenue, 0),
        })
    }

    const grand = slices.reduce((sum, r) => sum + r.revenue, 0) || 1
    let cum = 0
    return slices.map((row, i) => {
        const frac = row.revenue / grand
        const seg = {
            ...row,
            color: ITEM_COLORS[i] || '#475569',
            pct: Math.round(frac * 100),
            length: frac * donutC,
            offset: -cum * donutC,
        }
        cum += frac
        return seg
    })
})

/**
 * Credit exposure across both ledgers, for the whole book rather than the
 * selected range — a debt from two months ago is still owed today, so
 * date-filtering it would understate the risk.
 */
const credit = computed(() => {
    const people = {}
    let bills = 0
    let total = 0

    for (const log of filteredLogs.value || []) {
        if (log.paymentStatus !== 'pending') continue
        const name = (log.khataName || log.player || 'Unknown').trim() || 'Unknown'
        people[name] = (people[name] || 0) + (Number(log.totalCost) || 0)
        total += Number(log.totalCost) || 0
        bills += 1
    }
    for (const order of canteenOrders.value || []) {
        if (order.status === 'void' || order.method === 'tab') continue
        if (order.paymentStatus === 'paid' || !order.khataName) continue
        const name = order.khataName.trim() || 'Unknown'
        people[name] = (people[name] || 0) + (Number(order.total) || 0)
        total += Number(order.total) || 0
        bills += 1
    }

    const ranked = Object.entries(people)
        .map(([name, amount]) => ({ name, total: amount }))
        .sort((a, b) => b.total - a.total)
        .slice(0, 5)
    const top = ranked[0]?.total || 1

    // Of everything billed, what share actually came in.
    const billed = (filteredLogs.value || []).reduce((sum, l) => sum + (Number(l.totalCost) || 0), 0)
        + (canteenOrders.value || [])
            .filter((o) => o.status !== 'void' && o.method !== 'tab')
            .reduce((sum, o) => sum + (Number(o.total) || 0), 0)

    return {
        total,
        bills,
        people: Object.keys(people).length,
        debtors: ranked.map((p) => ({ ...p, widthPct: Math.round((p.total / top) * 100) })),
        collectionRate: billed ? Math.round(((billed - total) / billed) * 100) : null,
    }
})

/** Money still owed: bills on khata plus unsettled counter sales. */
const outstanding = computed(() =>
    (canteenOrders.value || [])
        .filter((o) => o.status !== 'void' && o.method !== 'tab' && o.paymentStatus !== 'paid')
        .reduce((sum, o) => sum + (Number(o.total) || 0), 0),
)

// ---------- KPIS ----------
const kpis = computed(() => {
    const logs = scopedLogs.value
    const revenue = logs.reduce((s, l) => s + (Number(l.totalCost) || 0), 0)
    const sessions = logs.length
    const totalMins = logs.reduce((s, l) => s + (Number(l.billableMins) || 0), 0)
    const avgMins = sessions ? totalMins / sessions : 0
    const hh = Math.floor(avgMins / 60)
    const mm = Math.round(avgMins % 60)
    return {
        revenue,
        sessions,
        avgTicket: sessions ? revenue / sessions : 0,
        avgSession: hh > 0 ? `${hh}h ${mm}m` : `${mm}m`,
    }
})

// ---------- REVENUE TREND ----------
const chart = { W: 600, H: 170, padL: 44, padR: 10, padT: 12, padB: 20 }

const trendDays = computed(() => {
    const { start, end } = activeRange.value
    const days = []
    let curr = new Date(start.getFullYear(), start.getMonth(), start.getDate())
    const last = new Date(end.getFullYear(), end.getMonth(), end.getDate())

    while (curr <= last) {
        days.push({
            key: dayKey(curr), label: `${curr.getDate()} ${monthsShort[curr.getMonth()]}`,
            revenue: 0, sessions: 0, orders: 0
        })
        curr = new Date(curr.getFullYear(), curr.getMonth(), curr.getDate() + 1)
    }
    const map = Object.fromEntries(days.map(d => [d.key, d]))
    for (const log of scopedLogs.value) {
        const k = dayKey(log._date)
        if (map[k]) {
            map[k].revenue += Number(log.totalCost) || 0
            map[k].sessions++
        }
    }
    // Counter canteen sales are revenue too. Tab sales are deliberately left
    // out — they're already inside the session totals added above, and counting
    // them here would make the trend disagree with the headline figure.
    for (const order of scopedOrders.value) {
        const k = dayKey(order._date)
        if (map[k]) {
            map[k].revenue += Number(order.total) || 0
            map[k].orders = (map[k].orders || 0) + 1
        }
    }
    return days
})

const trendMax = computed(() => Math.max(1, ...trendDays.value.map(d => d.revenue)))

const trendPoints = computed(() => {
    const n = trendDays.value.length
    const innerW = chart.W - chart.padL - chart.padR
    const innerH = chart.H - chart.padT - chart.padB
    return trendDays.value.map((d, i) => ({
        x: chart.padL + (n > 1 ? (i * innerW) / (n - 1) : innerW / 2),
        y: chart.padT + innerH * (1 - d.revenue / trendMax.value),
    }))
})

const trendlinePoints = computed(() => {
    const rawData = trendDays.value.map(d => d.revenue)
    const n = rawData.length
    if (n === 0) return []

    // Moving average window to smooth out daily spikes
    const windowSize = Math.max(3, Math.floor(n / 5))
    const smoothedData = rawData.map((_, i, arr) => {
        const start = Math.max(0, i - Math.floor(windowSize / 2))
        const end = Math.min(n - 1, i + Math.floor(windowSize / 2))
        let sum = 0, count = 0
        for (let j = start; j <= end; j++) {
            sum += arr[j]
            count++
        }
        return sum / count
    })

    const innerW = chart.W - chart.padL - chart.padR
    const innerH = chart.H - chart.padT - chart.padB
    return smoothedData.map((val, i) => ({
        x: chart.padL + (n > 1 ? (i * innerW) / (n - 1) : innerW / 2),
        y: chart.padT + innerH * (1 - Math.max(0, val) / trendMax.value)
    }))
})

const trendlinePath = computed(() => {
    const pts = trendlinePoints.value
    if (pts.length === 0) return ''
    if (pts.length === 1) return `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`

    let d = `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`
    for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[Math.max(0, i - 1)]
        const p1 = pts[i]
        const p2 = pts[i + 1]
        const p3 = pts[Math.min(pts.length - 1, i + 2)]

        const cp1x = p1.x + (p2.x - p0.x) * 0.2
        const cp1y = p1.y + (p2.y - p0.y) * 0.2
        const cp2x = p2.x - (p3.x - p1.x) * 0.2
        const cp2y = p2.y - (p3.y - p1.y) * 0.2

        d += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`
    }
    return d
})

const linePath = computed(() =>
    trendPoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
)

const areaPath = computed(() => {
    const pts = trendPoints.value
    if (!pts.length) return ''
    const baseline = chart.H - chart.padB
    return `${linePath.value} L${pts[pts.length - 1].x.toFixed(1)},${baseline} L${pts[0].x.toFixed(1)},${baseline} Z`
})

const gridLines = computed(() => {
    const innerH = chart.H - chart.padT - chart.padB
    const compact = v => v >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 0 : 1)}k` : `${Math.round(v)}`
    return [0, 0.5, 1].map(f => ({
        y: chart.padT + innerH * (1 - f),
        label: compact(trendMax.value * f),
    }))
})

const xLabels = computed(() => {
    const n = trendDays.value.length
    const step = Math.max(1, Math.ceil(n / 6))
    return trendPoints.value
        .map((p, i) => ({ x: p.x, label: trendDays.value[i].label, i }))
        .filter(l => l.i % step === 0)
})

// ---------- DONUT: REVENUE BY TYPE ----------
const donutC = 2 * Math.PI * 48

const donutSegments = computed(() => {
    const totals = {}
    for (const log of scopedLogs.value) {
        totals[log.tableType] = (totals[log.tableType] || 0) + (Number(log.totalCost) || 0)
    }
    const grand = Object.values(totals).reduce((s, v) => s + v, 0) || 1
    let cum = 0
    return Object.entries(totals)
        .sort((a, b) => b[1] - a[1])
        .map(([type, revenue]) => {
            const frac = revenue / grand
            const seg = {
                type,
                label: typeMeta.find(_type => _type.id == type)?.label || type,
                color: typeMeta.find(_type => _type.id == type)?.color,
                revenue,
                pct: Math.round(frac * 100),
                length: frac * donutC,
                offset: -cum * donutC,
            }
            cum += frac
            return seg
        })
})

// ---------- SESSIONS BY HOUR ----------
const hourly = computed(() => {
    const buckets = Array.from({ length: 24 }, (_, hr) => ({
        hour: hr,
        label: hr === 0 ? '12 AM' : hr < 12 ? `${hr} AM` : hr === 12 ? '12 PM' : `${hr - 12} PM`,
        count: 0,
        sessions: 0,
        orders: 0,
        revenue: 0,
    }))
    for (const log of scopedLogs.value) {
        const b = buckets[log._date.getHours()]
        b.sessions++
        b.count++
        b.revenue += Number(log.totalCost) || 0
    }
    // Counter sales count towards how busy an hour is, and towards its takings.
    for (const order of scopedOrders.value) {
        const b = buckets[order._date.getHours()]
        b.orders++
        b.count++
        b.revenue += Number(order.total) || 0
    }
    const max = Math.max(1, ...buckets.map(b => b.count))
    return buckets.map(b => ({ ...b, heightPct: Math.round((b.count / max) * 100) }))
})

const peakHour = computed(() => {
    const best = hourly.value.reduce((a, b) => (b.count > a.count ? b : a), hourly.value[0])
    return best && best.count > 0 ? best : null
})

// ---------- TOP MEMBERS ----------
//
// Only accounts are ranked — walk-in names are cosmetic and never count. Each
// session's members come from the normalized roster the server now sends as
// `log.members`; the cost is split across the members on that tab, so two
// members sharing a table each carry half and the board sums to real members'
// spend rather than inflating it. Keyed on customerId, never on name: two
// accounts can share a name, and one account is one entity however it's typed.
//
// (Want walk-ins to dilute a member's share too? divide by `log.playerCount`
//  instead of members.length. Want each member credited the FULL session?
//  drop the division.)
const topPlayers = computed(() => {
    const totals = {}   // customerId -> { customerId, name, revenue }
    for (const log of scopedLogs.value) {
        const members = log.members || []
        if (!members.length) continue
        const share = (Number(log.totalCost) || 0) / members.length
        for (const m of members) {
            const row = totals[m.customerId]
                || (totals[m.customerId] = { customerId: m.customerId, name: m.name, revenue: 0 })
            row.name = m.name        // freshest account name wins
            row.revenue += share
        }
    }
    const sorted = Object.values(totals)
        .map((r) => ({ ...r, revenue: Math.round(r.revenue) }))
        .sort((a, b) => b.revenue - a.revenue)
        .slice(0, 5)
    const max = sorted[0]?.revenue || 1
    return sorted.map((p) => ({ ...p, widthPct: Math.round((p.revenue / max) * 100) }))
})


/** Whether the log's filters are narrowing what's shown here. */
const filtered = computed(() => activeFilterCount.value > 0)

usePageBackground('#0f172a')

const insightsLoaded = ref(false)
const insightsLoading = ref(false)
async function loadInsights() {
    insightsLoading.value = true
    // Let the "Crunching…" state actually paint before the (synchronous) fetch
    // + chart recompute blocks the thread — otherwise the spinner never shows.
    await nextTick()
    await new Promise((r) => requestAnimationFrame(() => r()))
    try {
        await loadLedger({ force: true })
        insightsLoaded.value = true
        await nextTick()               // hand the frame to the heavy first render
    } finally {
        insightsLoading.value = false
    }
}
// No auto-load and no background re-aggregation — the manager presses Load
// (and can press it again to refresh) so a year of data never spins the fans.

</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.4s ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>