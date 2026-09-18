import { ref, reactive, computed } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

/**
 * The ledger, shared by the Logs and Insights pages.
 *
 * As modals these two received their data as props from the dashboard. As
 * separate routes they have no common parent to pass anything down, so the
 * state lives here at module scope instead. That also means navigating from
 * Logs to Insights carries the active filters across — which is the behaviour
 * the Analytics button had when it was nested inside the log modal.
 */

// ── raw ledger ────────────────────────────────────────────────────────────
export const historicalLogs = ref([])
export const canteenOrders = ref([])
export const logsGrossTotal = ref(0)
export const loading = ref(true)
export const loadError = ref('')

// ── paginated logs (the Logs page loads only the visible 50, server-side) ──
export const logsRows = ref([])       // current page rows
export const logsTotal = ref(0)       // total rows across the filtered set
export const logsGross = ref(0)       // gross Rs across the filtered set
export const logsLoading = ref(false)
const _logsCache = new Map()          // qs -> { rows, total, gross } (stays in memory)

function _logsQS(page, perPage) {
    const p = new URLSearchParams({ page: String(page), perPage: String(perPage) })
    for (const [k, v] of Object.entries(filters)) {
        if (v !== '' && v !== null && v !== undefined) p.set(k, String(v))
    }
    return p.toString()
}

/** Fetch one page of logs (cached). force=true bypasses + refreshes the cache. */
export async function loadLogsPage({ page = 1, perPage = 50, force = false } = {}) {
    const qs = _logsQS(page, perPage)
    if (!force && _logsCache.has(qs)) {
        const c = _logsCache.get(qs)
        logsRows.value = c.rows; logsTotal.value = c.total; logsGross.value = c.gross
        return
    }
    logsLoading.value = true
    try {
        const r = await authFetch(`${API_URL}/logs?${qs}`)
        const d = await r.json()
        logsRows.value = d.logs || []
        logsTotal.value = d.total ?? logsRows.value.length
        logsGross.value = d.grossTotal ?? 0
        _logsCache.set(qs, { rows: logsRows.value, total: logsTotal.value, gross: logsGross.value })
        loadError.value = ''
    } catch { loadError.value = 'Could not load the activity log' }
    finally { logsLoading.value = false }
}

/** Drop the page cache — call after a settle/void so figures refresh. */
export function invalidateLogsCache() { _logsCache.clear() }

/** Canteen ledger only (≤500 rows), without pulling the full games log. */
export async function loadCanteenLedger() {
    try {
        const r = await authFetch(`${API_URL}/canteen/orders`)
        const d = await r.json()
        if (d?.orders) canteenOrders.value = d.orders
    } catch { /* floor-only accounts 403 here; ignore */ }
}

let lastFetch = 0

/** Pull both ledgers. Cached briefly so moving between the two pages is instant. */
export async function loadLedger({ force = false } = {}) {
    if (!force && Date.now() - lastFetch < 3000) return
    lastFetch = Date.now()

    const [logsResult, canteenResult] = await Promise.allSettled([
        authFetch(`${API_URL}/logs`).then((r) => r.json()),
        authFetch(`${API_URL}/canteen/orders`).then((r) => r.json()),
    ])

    if (logsResult.status === 'fulfilled' && logsResult.value?.logs) {
        historicalLogs.value = logsResult.value.logs
        logsGrossTotal.value = logsResult.value.grossTotal
            ?? logsResult.value.logs.reduce((s, l) => s + (Number(l.totalCost) || 0), 0)
        loadError.value = ''
    } else if (logsResult.status === 'rejected') {
        loadError.value = 'Could not load the activity log'
    }

    // The canteen ledger is optional: a floor-only account gets a 403 here and
    // should still see the games log rather than an error page.
    if (canteenResult.status === 'fulfilled' && canteenResult.value?.orders) {
        canteenOrders.value = canteenResult.value.orders
    }

    loading.value = false
}

// ── filters ───────────────────────────────────────────────────────────────
export const defaultFilters = () => ({
    receiptId: '',
    player: '',
    tableType: '',
    tableId: '',
    dateFrom: '',   // 'YYYY-MM-DD'
    dateTo: '',     // 'YYYY-MM-DD'
    timeFrom: '',   // 'HH:MM' 24h
    timeTo: '',     // 'HH:MM' 24h
    minCost: null,
    maxCost: null,
})

export const filters = reactive(defaultFilters())

export const clearFilters = () => Object.assign(filters, defaultFilters())

export const activeFilterCount = computed(() =>
    Object.entries(filters).filter(([, v]) => v !== '' && v !== null && v !== undefined).length,
)

// date_string is stored as a locale string like "7/7/2026, 3:45:12 PM"
const parseLogDate = (dateString) => {
    const d = new Date(dateString)
    return isNaN(d.getTime()) ? null : d
}

const toMinutes = (hhmm) => {
    const [hs, ms] = hhmm.split(':').map(Number)
    return hs * 60 + ms
}

export const filteredLogs = computed(() =>
    (historicalLogs.value || []).filter((log) => {
        if (filters.receiptId && !String(log.receiptId).toLowerCase().includes(filters.receiptId.toLowerCase())) return false
        if (filters.player && !String(log.player).toLowerCase().includes(filters.player.toLowerCase())) return false
        if (filters.tableType && log.tableType !== filters.tableType) return false
        if (filters.tableId && String(log.tableId) !== String(filters.tableId)) return false
        if (typeof filters.minCost === 'number' && log.totalCost < filters.minCost) return false
        if (typeof filters.maxCost === 'number' && log.totalCost > filters.maxCost) return false

        // --- date range ---
        if (filters.dateFrom || filters.dateTo) {
            const logDate = parseLogDate(log.date)
            if (!logDate) return false

            if (filters.dateFrom) {
                const from = new Date(filters.dateFrom + 'T00:00:00')
                // no "to" date → treat "from" as an exact-day filter
                const end = filters.dateTo
                    ? new Date(filters.dateTo + 'T23:59:59.999')
                    : new Date(filters.dateFrom + 'T23:59:59.999')
                if (logDate < from || logDate > end) return false
            } else {
                // only "to" set → everything up to that date
                const end = new Date(filters.dateTo + 'T23:59:59.999')
                if (logDate > end) return false
            }
        }

        // --- time-of-day range (supports overnight wrap, e.g. 10 PM → 2 AM) ---
        if (filters.timeFrom || filters.timeTo) {
            const logDate = parseLogDate(log.date)
            if (!logDate) return false
            const t = logDate.getHours() * 60 + logDate.getMinutes()
            const fromT = filters.timeFrom ? toMinutes(filters.timeFrom) : null
            const toT = filters.timeTo ? toMinutes(filters.timeTo) : null

            if (fromT !== null && toT !== null) {
                if (fromT <= toT) {
                    if (t < fromT || t > toT) return false
                } else {
                    // wraps past midnight: match late-night OR early-morning
                    if (t < fromT && t > toT) return false
                }
            } else if (fromT !== null) {
                if (t < fromT) return false
            } else if (t > toT) {
                return false
            }
        }

        return true
    }),
)

export const filteredTotal = computed(() =>
    filteredLogs.value.reduce((sum, log) => sum + (Number(log.totalCost) || 0), 0),
)