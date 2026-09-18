<template>
    <div class="bg-slate-900 p-6 pt-0 text-slate-100">
        <div class="flex flex-col">
            <div class="mb-6 flex flex-wrap items-center justify-between gap-3 pt-6">
                <h1 class="text-2xl font-black tracking-tight text-white sm:text-3xl">Activity Log</h1>

                <div class="flex flex-wrap items-center gap-2">
                    <div class="flex gap-1 rounded-2xl border border-slate-800 bg-slate-950/60 p-1">
                        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
                            class="cursor-pointer rounded-xl px-3.5 py-1.5 text-[10px] font-black uppercase tracking-widest transition-all"
                            :class="activeTab === tab.id
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-950/40'
                                : 'text-slate-500 hover:text-slate-300'">
                            {{ tab.emoji }} {{ tab.label }}
                        </button>
                    </div>
                    <button v-if="canManage" @click="showKhata = true"
                        class="cursor-pointer rounded-xl border border-amber-600/40 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-400 transition-all hover:bg-amber-500/20">
                        Khata Book
                    </button>
                    <button v-if="isGames" @click="showFilters = true"
                        class="relative flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-700 px-4 py-2 text-xs font-bold text-slate-300 transition-all hover:border-slate-500 hover:text-white">
                        <span>⚙</span> Filters
                        <span v-if="activeFilterCount > 0"
                            class="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-500 text-[9px] font-black text-white">
                            {{ activeFilterCount }}
                        </span>
                    </button>
                    <button v-if="activeFilterCount > 0" @click="clearFilters"
                        class="cursor-pointer px-2 py-2 text-xs font-bold text-slate-500 transition-colors hover:text-red-400">
                        Clear
                    </button>
                </div>
            </div>

            <p class="-mt-2 mb-4 text-xs text-slate-400">
                {{ isGames ? 'Audit ledger of all invoicing operations.' : 'Every canteen sale, counter and tab.' }}
                <span v-if="isGames && activeFilterCount > 0" class="font-bold text-indigo-400">
                    · {{ activeFilterCount }} filter{{ activeFilterCount > 1 ? 's' : '' }} active
                </span>
            </p>

            <div v-if="isGames"
                class="max-h-[calc(100dvh-14rem)] overflow-y-auto border border-slate-700 rounded-2xl bg-slate-950/40">
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr
                            class="border-b border-slate-700 bg-slate-800 text-slate-400 font-bold tracking-wider sticky top-0 backdrop-blur-md z-10">
                            <th class="p-3">Receipt Ref</th>
                            <th class="p-3">Timestamp</th>
                            <th class="p-3">Lounge</th>
                            <th class="p-3">Station</th>
                            <th class="p-3">Player Handle</th>
                            <th class="p-3">Time Active</th>
                            <th class="p-3">Status</th>
                            <th class="p-3">Payment</th>
                            <th class="p-3 text-right">Total</th>
                            <th class="p-3 text-right">Receipt</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60 font-mono text-slate-300">
                        <tr v-if="logsRows.length === 0">
                            <td colspan="8" class="text-center p-8 text-slate-500 font-sans">
                                {{ activeFilterCount > 0 ? 'No sessions match the current filters.' : 'No settled sessions found.' }}
                            </td>
                        </tr>
                        <tr v-for="log in pagedLogs" :key="log.receiptId" class="hover:bg-slate-800/20">
                            <td class="p-3 text-indigo-400">#{{ log.receiptId }}</td>
                            <td class="p-3 text-slate-400 font-sans text-nowrap">{{ log.date }}</td>
                            <td class="p-3 text-slate-400 font-sans text-nowrap">{{ log.lounge || '—' }}</td>
                            <td class="p-3">
                                <span class="px-2 py-0.5 rounded-md text-[10px] uppercase font-sans font-black" :class="log.tableType.toLowerCase().includes('private')
                                    ? log.tableType.toLowerCase().includes('pool')
                                        ? 'bg-purple-500/10 text-purple-400'
                                        : 'bg-amber-500/10 text-amber-400'
                                    : log.tableType.toLowerCase() === 'snooker'
                                        ? 'bg-emerald-500/10 text-emerald-400'
                                        : log.tableType.toLowerCase() === 'pool'
                                            ? 'bg-sky-500/10 text-sky-400'
                                            : log.tableType.toLowerCase() === 'ps5'
                                                ? 'bg-blue-500/10 text-blue-400'
                                                : 'bg-lime-500/10 text-lime-400'
                                    ">{{ log.tableType }} #{{ log.tableId }}</span>
                            </td>
                            <td class="p-3 font-sans font-medium text-white truncate max-w-15">{{ log.player }}</td>
                            <td class="p-3">{{ log.elapsed }} ({{ log.billableMins }}m)</td>
                            <td class="p-3">
                                <span class="px-2 py-0.5 rounded-md text-[10px] uppercase font-sans font-black" :class="log.status === 'void'
                                    ? 'bg-rose-500/10 text-rose-400'
                                    : log.paymentStatus === 'paid'
                                        ? 'bg-emerald-500/10 text-emerald-400'
                                        : 'bg-amber-500/10 text-amber-400'">
                                    {{ log.status === 'void' ? 'Void'
                                        : log.paymentStatus === 'paid' ? 'Paid'
                                            : (log.khataName ? 'Khata' : 'Pending') }}
                                </span>
                            </td>
                            <td class="p-3">
                                <span class="px-2 py-0.5 rounded-md text-[10px] uppercase font-sans font-black" :class="log.paymentMethod === 'tab'
                                    ? 'bg-sky-500/10 text-sky-400'
                                    : 'bg-slate-500/10 text-slate-400'">
                                    {{ log.paymentMethod === 'tab' ? 'On Tab' : log.paymentMethod }}
                                </span>
                            </td>
                            <td class="p-3 text-right font-bold text-emerald-400 shrink-0 text-nowrap">Rs {{ formatRs(log.totalCost) }}</td>
                            <td class="p-3 text-right">
                                <button @click="viewReceipt(log)"
                                    class="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 hover:border-indigo-400/60 px-2 py-1 rounded-lg transition-all cursor-pointer">
                                    Receipt
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>


            <div v-else
                class="max-h-[calc(100dvh-14rem)] overflow-y-auto border border-slate-800 rounded-2xl bg-slate-950/40">
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr
                            class="border-b border-slate-800 bg-slate-900 text-slate-400 font-bold tracking-wider sticky top-0 backdrop-blur-md z-10">
                            <th class="p-3">Order Ref</th>
                            <th class="p-3">Timestamp</th>
                            <th class="p-3">Charged To</th>
                            <th class="p-3">Items Sold</th>
                            <th class="p-3">Payment</th>
                            <th class="p-3">Status</th>
                            <th class="p-3 text-right">Total</th>
                            <th class="p-3">Receipt</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60 font-mono text-slate-300">
                        <tr v-if="canteenOrders.length === 0">
                            <td colspan="7" class="text-center p-8 text-slate-500 font-sans">
                                No canteen sales recorded yet.
                            </td>
                        </tr>
                        <tr v-for="order in pagedCanteen" :key="order.id" class="hover:bg-slate-800/20"
                            :class="order.status === 'void' ? 'opacity-40' : ''">
                            <td class="p-3 text-indigo-400">{{ order.code }}</td>
                            <td class="p-3 text-slate-400 font-sans">{{ formatWhen(order.at) }}</td>
                            <td class="p-3 font-sans font-medium text-white">{{ order.target }}</td>
                            <td class="p-3 font-sans">
                                <div class="max-w-[260px]">
                                    <span v-if="!order.items || !order.items.length" class="text-slate-500">
                                        {{ order.itemCount }} item{{ order.itemCount === 1 ? '' : 's' }}
                                    </span>
                                    <template v-else>
                                        <span class="text-slate-200">{{ itemSummary(order) }}</span>
                                        <button v-if="order.items.length > 2"
                                            @click="expanded === order.id ? expanded = null : expanded = order.id"
                                            class="ml-1 cursor-pointer text-[10px] font-bold text-indigo-400 hover:text-indigo-300">
                                            {{ expanded === order.id ? 'less' : `+${order.items.length - 2} more` }}
                                        </button>
                                        <ul v-if="expanded === order.id" class="mt-1.5 space-y-0.5">
                                            <li v-for="(line, i) in order.items" :key="i"
                                                class="flex justify-between gap-3 font-mono text-[10px] text-slate-400">
                                                <span class="truncate">{{ line.name }} × {{ line.qty }}</span>
                                                <span>Rs {{ line.lineTotal }}</span>
                                            </li>
                                        </ul>
                                    </template>
                                </div>
                            </td>
                            <td class="p-3">
                                <span class="px-2 py-0.5 rounded-md text-[10px] uppercase font-sans font-black" :class="order.method === 'tab'
                                    ? 'bg-sky-500/10 text-sky-400'
                                    : 'bg-slate-500/10 text-slate-400'">
                                    {{ order.method === 'tab' ? 'On Tab' : order.method }}
                                </span>
                            </td>
                            <td class="p-3">
                                <span class="px-2 py-0.5 rounded-md text-[10px] uppercase font-sans font-black" :class="order.status === 'void'
                                    ? 'bg-rose-500/10 text-rose-400'
                                    : order.paymentStatus === 'paid'
                                        ? 'bg-emerald-500/10 text-emerald-400'
                                        : 'bg-amber-500/10 text-amber-400'">
                                    {{ order.status === 'void' ? 'Void'
                                        : order.paymentStatus === 'paid' ? 'Paid'
                                            : (order.khataName ? 'Khata' : 'Pending') }}
                                </span>
                            </td>
                            <td class="p-3 text-right font-bold text-emerald-400">Rs {{ order.total }}</td>
                            <td v-if="!(order.method === 'tab')" class="p-3 text-right">
                                <button @click="viewCanteenReceipt(order)"
                                    class="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 hover:border-indigo-400/60 px-2 py-1 rounded-lg transition-all cursor-pointer">
                                    Receipt
                                </button>
                            </td>
                            <td v-else class="p-3 text-right flex justify-center">
                                <div
                                    class="text-[10px] font-bold text-sky-500 bg-sky-500/10 px-2 py-1 rounded-lg transition-all cursor-default w-fit">
                                    On Tab
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div
                class="mt-4 pt-4 border-t border-slate-800 flex flex-wrap justify-between items-center gap-4 bg-slate-950/30 p-4 rounded-2xl border border-slate-800/60">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">📊</span>
                    <div>
                        <span
                            class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">
                            {{ isGames ? (activeFilterCount > 0 ? 'Filtered' : 'Total') + ' Sessions' : 'Total Orders'
                            }}
                        </span>
                        <span class="text-sm font-bold text-white font-mono mt-1 block">
                            {{ isGames ? `${logsTotal} Sessions` : `${canteenOrders.length} Orders` }}</span>
                    </div>
                </div>

                <!-- Page controls: only shown once there's more than one page. -->
                <div v-if="pageCount > 1"
                    class="order-last w-full flex items-center justify-center gap-2 sm:order-none sm:w-auto">
                    <button @click="goPage(clampedPage - 1)" :disabled="clampedPage <= 1"
                        class="cursor-pointer rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-[11px] font-bold text-slate-300 transition-all hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-40">
                        ‹ Prev
                    </button>
                    <span class="px-1 text-center font-mono text-[11px] tabular-nums text-slate-300">
                        Page {{ clampedPage }} / {{ pageCount }}
                        <span class="ml-1 hidden text-slate-500 sm:inline">· {{ rangeStart }}–{{ rangeEnd }} of {{
                            activeCount }}</span>
                    </span>
                    <button @click="goPage(clampedPage + 1)" :disabled="clampedPage >= pageCount"
                        class="cursor-pointer rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-[11px] font-bold text-slate-300 transition-all hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-40">
                        Next ›
                    </button>
                </div>

                <div class="text-right">
                    <span class="text-[10px] uppercase font-black tracking-widest text-slate-500 block leading-none">
                        {{ activeFilterCount > 0 ? 'Filtered' : 'Total' }} Revenue
                    </span>
                    <span class="text-2xl font-black text-emerald-400 font-mono mt-1 block">Rs {{
                        isGames ? formatRs(logsGross) : formatRs(canteenRevenue) }}</span>
                </div>
            </div>
        </div>

        <LogFilterModal v-if="showFilters" :filters="filters" :match-count="logsTotal"
            @close-modal="showFilters = false" @clear="clearFilters" />
    </div>
    <KhataModal v-if="showKhata" @close-modal="showKhata = false" @settled="() => { invalidateLogsCache(); refreshView({ force: true }) }" />

    <BillingReceipt v-if="viewingReceipt" :receipt="viewingReceipt" :variant="viewingReceipt.variant || 'session'"
        :read-only="true" @close="viewingReceipt = null" />
</template>

<script setup>
import BillingReceipt from '@/components/BillingReceipt.vue'
import KhataModal from '@/components/Modals/KhataModal.vue'
import { auth } from '@/Auth.js'
import LogFilterModal from '@/components/Modals/LogFilterModal.vue'
import { ref, computed, watch, onMounted } from 'vue'
import {
    canteenOrders, loading, loadError, filters, clearFilters, activeFilterCount,
    logsRows, logsTotal, logsGross, loadLogsPage, loadCanteenLedger, invalidateLogsCache,
} from '@/composables/useLedger.js'
import { usePageBackground } from '@/composables/usePageBackground.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import { useRoute, useRouter } from 'vue-router'


const formatRs = n => Math.round(n).toLocaleString('en-US')

const tabs = [
    { id: 'games', label: 'Games', emoji: '🎱' },
    { id: 'canteen', label: 'Canteen', emoji: '🍟' },
]
const route = useRoute()
const router = useRouter()

// The open ledger lives in the URL, so /logs?tab=canteen is linkable and a
// refresh doesn't bounce the canteen till back to the games ledger.
const activeTab = computed({
    get: () => (route.query.tab === 'canteen' ? 'canteen' : 'games'),
    set: (tab) => router.replace({ query: { ...route.query, tab } }),
})
const isGames = computed(() => activeTab.value === 'games')

// ── pagination ──────────────────────────────────────────────────────────
// The ledger runs to thousands of rows; putting them all in the DOM at once is
// what made this page crawl. Everything is still loaded — so the filters and
// the footer totals stay exact — but only one page is rendered at a time.
const perPage = 50
const page = ref(1)

// Games load one page at a time from the server (only the visible 50); the
// canteen ledger is small (≤500) and stays client-side.
const activeCount = computed(() => (isGames.value ? logsTotal.value : canteenOrders.value.length))
const pageCount = computed(() => Math.max(1, Math.ceil(activeCount.value / perPage)))
const clampedPage = computed(() => Math.min(Math.max(1, page.value), pageCount.value))
const pageStart = computed(() => (clampedPage.value - 1) * perPage)
const pagedLogs = computed(() => logsRows.value)   // already the server page
const pagedCanteen = computed(() => canteenOrders.value.slice(pageStart.value, pageStart.value + perPage))
const rangeStart = computed(() => (activeCount.value ? pageStart.value + 1 : 0))
const rangeEnd = computed(() => Math.min(pageStart.value + perPage, activeCount.value))

const goPage = (n) => { page.value = Math.min(Math.max(1, n), pageCount.value) }

// Jump back to page 1 when the VIEW changes — a tab switch or a filter edit —
// but never on the 20s auto-refresh, which would otherwise yank the reader
// back to the top every 20 seconds.
watch(activeTab, () => { page.value = 1 })
watch(() => JSON.stringify(filters), () => { page.value = 1 })
// If the list shrinks under the current page (a filter, or a voided row), clamp.
watch(pageCount, (pc) => { if (page.value > pc) page.value = pc })

/** Voided orders are shown but excluded from the revenue figure. */
const canteenRevenue = computed(() =>
    canteenOrders.value
        .filter((o) => o.status !== 'void')
        .reduce((sum, o) => sum + (o.total || 0), 0),
)

const formatWhen = (iso) => (iso ? new Date(iso).toLocaleString() : '—')

const expanded = ref(null)
const showKhata = ref(false)
const canManage = computed(() => ['owner', 'manager'].includes(auth.role))

/** First couple of items inline; the rest behind a "+n more" toggle. */
function itemSummary(order) {
    const lines = order.items || []
    const shown = lines.slice(0, 2).map((l) => (l.qty > 1 ? `${l.name} × ${l.qty}` : l.name))
    return shown.join(', ')
}

const viewingReceipt = ref(null)
const showFilters = ref(false)


/** Reopen a canteen sale on the same paper the till printed. */
const viewCanteenReceipt = (order) => {
    viewingReceipt.value = {
        variant: 'canteen',
        receiptId: order.code,
        date: order.at ? new Date(order.at).toLocaleString() : '',
        player: order.target,
        servedBy: order.by,
        lineItems: (order.items || []).map((i) => ({
            name: i.name, qty: i.qty, cost: i.lineTotal,
        })),
        discountPercent: order.discountPercent,
        discountAmount: order.discountAmount,
        totalCost: order.total,
        paymentStatus: order.paymentStatus,
        paymentMethod: order.paymentMethod,
        khataName: order.khataName,
        isWalkIn: true,
        segments: [],
    }
}

const viewReceipt = (log) => {
    viewingReceipt.value = {
        receiptId: log.receiptId,
        date: log.date,
        lounge: log.lounge,
        tableType: log.tableType,
        tableId: log.tableId,
        player: log.player,
        elapsed: log.elapsed,
        billableMins: log.billableMins,
        rate: log.rate,
        totalCost: log.totalCost,
        segments: log.segments || [],
        // These are why a reopened bill was losing its food lines.
        canteenItems: log.canteenItems || [],
        playTotal: log.playTotal ?? log.totalCost,
        canteenTotal: log.canteenTotal || 0,
        splitCount: log.splitCount || 1,
        paymentStatus: log.paymentStatus,
        paymentMethod: log.paymentMethod,
        khataName: log.khataName,
        logId: log.logId,
    }
}


usePageBackground('#0f172a')

async function refreshView({ force = false } = {}) {
    if (isGames.value) await loadLogsPage({ page: clampedPage.value, perPage, force })
    else await loadCanteenLedger()
}
onMounted(() => { refreshView(); if (!isGames.value) loadLogsPage({ page: 1, perPage }) })
// Games: reload the current page when the page, filters, or tab change.
watch([page, activeTab], () => refreshView())
watch(() => JSON.stringify(filters), () => { page.value = 1; if (isGames.value) loadLogsPage({ page: 1, perPage }) })
// Keep the visible page fresh without yanking the reader off it.
useAutoRefresh(() => refreshView({ force: true }), 20000)

</script>