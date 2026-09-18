<template>
    <div class="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="flex max-h-[85dvh] w-full max-w-2xl flex-col rounded-3xl border border-slate-800 bg-slate-900 p-6">

            <div class="mb-5 flex shrink-0 items-start justify-between gap-4">
                <div>
                    <h2 class="text-xl font-black text-white">Khata Book</h2>
                    <p class="mt-1 text-xs text-slate-400">Tables and canteen in one place. Settle a single bill, or the whole account.</p>
                </div>
                <div class="text-right">
                    <span class="block text-[10px] font-black uppercase tracking-widest text-slate-500">Outstanding</span>
                    <span class="font-mono text-2xl font-black"
                        :class="outstanding ? 'text-amber-400' : 'text-slate-600'">
                        Rs {{ formatRs(outstanding) }}
                    </span>
                </div>
            </div>

            <p v-if="loading" class="py-16 text-center text-xs font-bold text-slate-500">Loading…</p>

            <div v-else-if="!people.length"
                class="rounded-2xl border border-dashed border-slate-800 py-16 text-center">
                <p class="text-sm font-bold text-slate-300">Nothing on credit</p>
                <p class="mt-1 text-xs text-slate-500">Every bill has been settled.</p>
            </div>

            <div v-else class="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1 khata-scroll">
                <div v-for="person in people" :key="person.name"
                    class="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                    <div class="flex items-center justify-between gap-3">
                        <div class="min-w-0">
                            <p class="truncate text-sm font-black text-white">{{ person.name }}</p>
                            <p class="font-mono text-[10px] text-slate-500">
                                {{ person.bills.length }} unpaid bill{{ person.bills.length === 1 ? '' : 's' }}
                            </p>
                        </div>
                        <div class="flex shrink-0 items-center gap-3">
                            <span class="font-mono text-lg font-black text-amber-400">Rs {{ formatRs(person.total) }}</span>
                            <button @click="expanded === person.name ? expanded = null : expanded = person.name"
                                class="cursor-pointer rounded-lg border border-slate-800 px-2 py-1 text-[9px] font-black uppercase tracking-widest text-slate-400 hover:border-slate-700 hover:text-slate-200">
                                {{ expanded === person.name ? 'Hide' : 'Bills' }}
                            </button>
                            <button @click="confirming = person"
                                class="cursor-pointer rounded-lg bg-emerald-600 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-white hover:bg-emerald-500">
                                Settle
                            </button>
                        </div>
                    </div>

                    <ul v-if="expanded === person.name" class="mt-3 space-y-1.5 border-t border-slate-800 pt-3">
                        <li v-for="bill in person.bills" :key="`${bill.kind}-${bill.id}`"
                            class="rounded-xl bg-slate-950/40 px-3 py-2">
                            <div class="flex items-center justify-between gap-3">
                                <span class="flex min-w-0 items-center gap-2 font-mono text-[11px]">
                                    <span class="shrink-0 rounded px-1.5 py-0.5 text-[8px] font-black uppercase tracking-widest"
                                        :class="bill.kind === 'canteen'
                                            ? 'bg-amber-500/10 text-amber-400'
                                            : 'bg-sky-500/10 text-sky-400'">
                                        {{ bill.kind === 'canteen' ? 'Canteen' : 'Table' }}
                                    </span>
                                    <span class="truncate text-slate-300">{{ bill.label }}</span>
                                    <span class="shrink-0 text-slate-600">#{{ bill.ref }}</span>
                                </span>
                                <div class="flex shrink-0 items-center gap-2">
                                    <span class="font-mono text-[11px] font-bold text-slate-200">
                                        Rs {{ formatRs(bill.total) }}
                                    </span>
                                    <button v-if="bill.payUrl" @click="toggleQr(bill)"
                                        :title="`Show a QR for this ${bill.kind === 'canteen' ? 'order' : 'bill'}`"
                                        class="cursor-pointer rounded-lg border px-2 py-1 text-[9px] font-black uppercase tracking-widest transition-colors"
                                        :class="qrFor === billKey(bill)
                                            ? 'border-emerald-600/50 bg-emerald-600/15 text-emerald-300'
                                            : 'border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'">
                                        QR
                                    </button>
                                    <button @click="settleBill(person, bill)" :disabled="settling"
                                        class="cursor-pointer rounded-lg border border-slate-800 px-2 py-1 text-[9px] font-black uppercase tracking-widest text-slate-400 transition-colors hover:border-emerald-600/50 hover:text-emerald-400 disabled:opacity-40">
                                        Paid
                                    </button>
                                </div>
                            </div>

                            <!-- Scanning this settles THIS bill only. -->
                            <div v-if="qrFor === billKey(bill)"
                                class="mt-2 flex items-center gap-3 border-t border-slate-800 pt-2">
                                <svg :viewBox="qrViewBox(bill.payUrl)" class="h-24 w-24 shrink-0 rounded-lg bg-white p-1"
                                    shape-rendering="crispEdges" role="img" aria-label="Scan to pay this bill">
                                    <path :d="qrPath(bill.payUrl)" fill="#0f172a" />
                                </svg>
                                <p class="text-[10px] leading-relaxed text-slate-500">
                                    Guest scans to pay <span class="font-bold text-slate-300">Rs {{ formatRs(bill.total) }}</span>
                                    for this {{ bill.kind === 'canteen' ? 'order' : 'table bill' }}.
                                    It settles on its own once paid — no need to mark it here.
                                </p>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>

            <p v-if="error"
                class="mt-3 shrink-0 rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-[10px] font-bold text-rose-400">
                {{ error }}
            </p>

            <button @click="emit('close-modal')"
                class="mt-5 shrink-0 cursor-pointer rounded-xl bg-slate-800 py-2.5 text-[10px] font-black uppercase tracking-widest text-slate-200 hover:bg-slate-700">
                Close
            </button>
        </div>

        <!-- Taking money is worth one confirmation: settling can't be undone
             from here, and the amounts are real. -->
        <div v-if="confirming"
            class="fixed inset-0 z-70 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm md:pl-[var(--modal-inset,1rem)]"
            @click.self="confirming = null">
            <div class="w-full max-w-xs rounded-3xl border border-slate-800 bg-slate-900 p-6 text-center">
                <h3 class="text-lg font-black text-white">Settle Khata</h3>
                <p class="mt-1 text-[11px] text-slate-400">
                    Mark everything owed by <span class="font-bold text-white">{{ confirming.name }}</span> as paid?
                </p>
                <p class="mt-4 font-mono text-3xl font-black text-emerald-400">
                    Rs {{ formatRs(confirming.total) }}
                </p>
                <p class="mt-1 text-[10px] text-slate-600">
                    {{ confirming.bills.length }} bill{{ confirming.bills.length === 1 ? '' : 's' }}
                </p>
                <div class="mt-6 flex gap-2">
                    <button @click="confirming = null"
                        class="flex-1 cursor-pointer rounded-xl bg-slate-800 py-2.5 text-[10px] font-black uppercase tracking-widest text-slate-300">
                        Cancel
                    </button>
                    <button @click="settle(confirming)" :disabled="settling"
                        class="flex-1 cursor-pointer rounded-xl bg-emerald-600 py-2.5 text-[10px] font-black uppercase tracking-widest text-white hover:bg-emerald-500 disabled:bg-slate-800">
                        {{ settling ? 'Settling…' : 'Mark Paid' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'
import { qrMatrix, qrSvgPath } from '@/utils/qr.js'

const emit = defineEmits(['close-modal', 'settled'])

const people = ref([])
const outstanding = ref(0)
const loading = ref(true)
const error = ref('')
const expanded = ref(null)
const confirming = ref(null)
const settling = ref(false)

const formatRs = (n) => Number(n || 0).toLocaleString('en-PK')

// ── per-bill QR ───────────────────────────────────────────────────────────
const qrFor = ref(null)
const QR_QUIET = 4
const billKey = (bill) => `${bill.kind}-${bill.id}`
const toggleQr = (bill) => {
    qrFor.value = qrFor.value === billKey(bill) ? null : billKey(bill)
}

// Cached: re-encoding on every render would rebuild the matrix each frame.
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

/** Cashier takes cash for one bill without clearing the whole account. */
async function settleBill(person, bill) {
    if (settling.value) return
    settling.value = true
    error.value = ''
    try {
        const body = bill.kind === 'canteen' ? { orderIds: [bill.id] } : { sessionIds: [bill.id] }
        const res = await authFetch(`${API_URL}/khata/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not settle that bill')
        qrFor.value = null
        await load()
        emit('settled', data)
    } catch (err) {
        error.value = err.message
    } finally {
        settling.value = false
    }
}

async function load() {
    error.value = ''
    try {
        const res = await authFetch(`${API_URL}/khata`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not load the khata book')
        people.value = data.people || []
        outstanding.value = data.outstanding || 0
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
}

async function settle(person) {
    if (settling.value) return
    settling.value = true
    error.value = ''
    try {
        const res = await authFetch(`${API_URL}/khata/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: person.name }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not settle that khata')
        confirming.value = null
        await load()
        emit('settled', data)
    } catch (err) {
        error.value = err.message
        confirming.value = null
    } finally {
        settling.value = false
    }
}

onMounted(load)
</script>

<style scoped>
.khata-scroll::-webkit-scrollbar { width: 6px; }
.khata-scroll::-webkit-scrollbar-track { background: transparent; }
.khata-scroll::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
.khata-scroll { scrollbar-width: thin; scrollbar-color: #334155 transparent; }
</style>