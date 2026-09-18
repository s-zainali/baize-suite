<template>
    <div class="bg-slate-900 p-6 pt-0 text-slate-100 h-[100dvh] flex flex-col">

        <Header :is-bills="true" :refreshing="refreshing" @activate-modal="$event === 'refresh' ? (load(true), loadCanteen(true)) : null"/>

        <div class="space-y-6 flex-1 overflow-y-scroll">
            <!-- Only the counters this person works. Showing a section they
                 can't use and filling it with a permission error is just noise
                 on a screen they'll read all shift. -->
            <div v-if="canFloor" class="h-full">
                <p v-if="loading" class="py-24 text-center text-xs font-bold text-slate-600">Loading bills…</p>

                <p v-else-if="loadError"
                    class="mx-auto max-w-md rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-center text-xs font-bold text-rose-400">
                    {{ loadError }}
                </p>

                <div v-else
                    class="border rounded-[3rem] p-6 bg-border-slate-800/40 border-slate-700 shadow-md bg-slate-950/30 h-full flex flex-col">
                    <div class="flex justify-between items-center ml-2 mr-2 pb-6 border-b border-slate-600">
                        <h2 class="text-2xl font-bold text-slate-200 truncate tracking-widest">Active Game Bills</h2>
                        <div class="flex shrink-0 items-center gap-3 text-xs font-bold">
                            <span v-if="bills.length" class="text-slate-400">
                                {{ bills.length }} open · Rs {{ outstanding.toLocaleString('en-PK') }}
                            </span>
                            <RouterLink v-if="onAccount" to="/dashboard"
                                class="rounded-lg border border-amber-600/40 bg-amber-500/10 px-2.5 py-1 text-amber-400">
                                Rs {{ onAccount.toLocaleString('en-PK') }} on account
                            </RouterLink>
                        </div>
                    </div>

                    <div v-if="!bills.length" class=" text-center flex-1 flex flex-col justify-center items-center">
                        <span class="mb-3 block text-3xl opacity-40">🧾</span>
                        <p class="text-sm font-bold text-slate-300">No open bills</p>
                    </div>

                    <div v-else ref="scrollContainer" class="mt-6 overflow-x-auto bills-scroll h-full">
                        <div class="flex items-start gap-2">
                            <article v-for="bill in bills" :key="bill.logId"
                                class="w-[21rem] shrink-0 zoom-85 border-2 border-slate-700 bg-slate-800 rounded-b-4xl rounded-t-xl pt-2">
                                <BillingReceipt :receipt="bill" :embedded="true" @settle="settle(bill, $event)"
                                    @split="saveSplit(bill, $event)" @close="close(bill)" />
                                <div class="text-center mt-4 mb-2 uppercase font-black tracking-widest">
                                    {{ bill.lounge }}
                                </div>
                                <div class="text-center mb-4 uppercase font-black tracking-widest">
                                    {{ bill.tableType }} {{ bill.tableId }}
                                </div>
                            </article>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="canCanteen" class="h-full">
                <p v-if="loadingCanteen" class="py-24 text-center text-xs font-bold text-slate-600">Loading Canteen
                    bills…</p>

                <p v-else-if="canteenLoadError"
                    class="mx-auto max-w-md rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-center text-xs font-bold text-rose-400">
                    {{ canteenLoadError }}
                </p>

                <div v-else
                    class="border rounded-[3rem] p-6 bg-border-slate-800/40 border-slate-700 shadow-md bg-slate-950/30 h-full flex flex-col">
                    <div class="flex justify-between items-center ml-2 mr-2 pb-6 border-b border-slate-600">
                        <h2 class="text-2xl font-bold text-slate-200 truncate tracking-widest">Active Canteen Bills</h2>
                        <div class="flex shrink-0 items-center gap-3 text-xs font-bold">
                            <span v-if="canteenBills.length" class="text-slate-400">
                                {{ canteenBills.length }} open · Rs {{ canteenOutstanding.toLocaleString('en-PK') }}
                            </span>
                        </div>
                    </div>

                    <div v-if="!canteenBills.length"
                        class=" text-center flex-1 flex flex-col justify-center items-center">
                        <span class="mb-3 block text-3xl opacity-40">🧾</span>
                        <p class="text-sm font-bold text-slate-300">No open bills</p>
                    </div>

                    <div v-else class="mt-6 overflow-x-auto bills-scroll">
                        <div class="flex items-start gap-5">
                            <article v-for="order in canteenBills" :key="order.id" class="w-[21rem] shrink-0 zoom-85 border-2 border-slate-700 rounded-b-4xl rounded-t-xl pt-2">
                                <BillingReceipt variant="canteen" :receipt="canteenReceipt(order)" :embedded="true"
                                    @settle="settleCanteen(order, $event)" @close="closeCanteen(order)" />
                                <div class="text-center mt-4 mb-2 uppercase font-black tracking-widest">
                                    {{ canteenReceipt(order).receiptId }}
                                </div>
                            </article>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { authFetch, API_URL, canFloor, canCanteen } from '@/Auth.js'
import { usePageBackground } from '@/composables/usePageBackground.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import BillingReceipt from '@/components/BillingReceipt.vue'
import Header from '@/components/Header.vue'

usePageBackground('#0f172a')


const bills = ref([])
const canteenBills = ref([])
const outstanding = ref(0)
const canteenOutstanding = ref(0)
const onAccount = ref(0)
const loading = ref(true)
const refreshing = ref(false)
const loadingCanteen = ref(true)
const refreshingCanteen = ref(false)
const loadError = ref('')
const canteenLoadError = ref('')

const scrollContainer = ref(null)

onMounted(() => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
})
/** Totals across the sections this person can actually see. */
const openCount = computed(
    () => (canFloor.value ? bills.value.length : 0)
        + (canCanteen.value ? canteenBills.value.length : 0),
)
const visibleOutstanding = computed(
    () => (canFloor.value ? outstanding.value : 0)
        + (canCanteen.value ? canteenOutstanding.value : 0),
)

async function load(manual = false) {
    // Skip the request entirely rather than collecting a 403 every poll.
    if (!canFloor.value) { loading.value = false; return }
    if (manual) refreshing.value = true
    try {
        const res = await authFetch(`${API_URL}/bills/active`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not load the bills')
        bills.value = data.bills || []
        outstanding.value = data.outstanding || 0
        onAccount.value = data.onAccount || 0
        loadError.value = ''
    } catch (err) {
        loadError.value = err.message
    } finally {
        loading.value = false
        refreshing.value = false
    }
}

async function loadCanteen(manual = false) {
    if (!canCanteen.value) { loadingCanteen.value = false; return }
    if (manual) refreshingCanteen.value = true
    try {
        const res = await authFetch(`${API_URL}/canteen/orders/active`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not load the bills')
        canteenBills.value = data.orders || []
        canteenOutstanding.value = data.outstanding || 0
        canteenLoadError.value = ''
    } catch (err) {
        canteenLoadError.value = err.message
    } finally {
        loadingCanteen.value = false
        refreshingCanteen.value = false
    }
}

// 1.5s was two requests a second per open tab, each re-issuing pay links.
useAutoRefresh(load, 1200)
useAutoRefresh(loadCanteen, 1200)
onUnmounted(() => { bills.value = [] })

function replace(bill, patch) {
    bills.value = bills.value.map((b) => (b.logId === bill.logId ? { ...b, ...patch } : b))
}

async function settle(bill, { status, name, method, done }) {
    try {
        const res = await authFetch(`${API_URL}/bills/${bill.logId}/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, name, method }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not update the bill')
        done?.(data)
        // Settling does NOT remove the card. The cashier is still looking at it,
        // and a bill vanishing mid-transaction is how you lose track of what you
        // just took money for. It stays until they close it.
        replace(bill, {
            paymentStatus: data.paymentStatus,
            paymentMethod: data.paymentMethod,
            khataName: data.khataName,
        })
        if (data.paymentStatus === 'paid') {
            outstanding.value = Math.max(0, outstanding.value - bill.totalCost)
        }
    } catch (err) {
        done?.({ error: err.message })
    }
}

/**
 * Close the bill for good — recorded on the server, not just hidden here.
 *
 * The server refuses unless it has been settled, so a bill nobody has dealt
 * with can't be made to vanish from every screen at once.
 */
async function close(bill) {
    try {
        const res = await authFetch(`${API_URL}/bills/${bill.logId}/close`, { method: 'POST' })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not close that bill')
        bills.value = bills.value.filter((b) => b.logId !== bill.logId)
    } catch (err) {
        loadError.value = err.message
    }
}

/** Shape a canteen order into what BillingReceipt renders. */
function canteenReceipt(order) {
    return {
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
        orderId: order.id,
        payUrl: order.payUrl || '',
        paymentStatus: order.paymentStatus,
        paymentMethod: order.paymentMethod,
        khataName: order.khataName,
        // A counter sale has no named guest, so there is no account to charge.
        isWalkIn: true,
        segments: [],
    }
}

async function settleCanteen(order, { status, method, done }) {
    try {
        const res = await authFetch(`${API_URL}/canteen/orders/${order.id}/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, method }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not update that order')
        canteenBills.value = canteenBills.value.map((o) =>
            o.id === order.id
                ? { ...o, paymentStatus: data.paymentStatus, paymentMethod: data.paymentMethod }
                : o,
        )
        if (data.paymentStatus === 'paid') {
            canteenOutstanding.value = Math.max(0, canteenOutstanding.value - order.total)
        }
        done?.(data)
    } catch (err) {
        done?.({ error: err.message })
    }
}

async function closeCanteen(order) {
    try {
        const res = await authFetch(`${API_URL}/canteen/orders/${order.id}/close`, { method: 'POST' })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not close that order')
        canteenBills.value = canteenBills.value.filter((o) => o.id !== order.id)
    } catch (err) {
        canteenLoadError.value = err.message
    }
}

async function saveSplit(bill, { splitCount, done }) {
    try {
        await authFetch(`${API_URL}/bills/${bill.logId}/split`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ splitCount }),
        })
        replace(bill, { splitCount })
    } catch (err) {
        console.error('Could not save the split', err)
    } finally {
        done?.()
    }
}
</script>

<style scoped>
.bills-scroll::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

.bills-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.bills-scroll::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 4px;
}

.bills-scroll {
    scrollbar-width: thin;
    scrollbar-color: #334155 transparent;
}
</style>