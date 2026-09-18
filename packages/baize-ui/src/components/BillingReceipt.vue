<template>
    <div
        :class="embedded
        ? 'flex justify-center'
        : 'fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-4 bg-slate-950/80 backdrop-blur-xs transition-all pointer-events-auto md:pl-[var(--modal-inset,1rem)]'">
        <!-- The paper stays one continuous sheet; when it outgrows the screen the
         OVERLAY scrolls it, so nothing inside the receipt gets its own bar. -->
        <div id="printable-receipt"
            class="bg-white text-slate-900 w-full max-w-xs shadow-2xl rounded-xs font-mono text-xs p-5 relative tracking-tight border-t-8 border-slate-400 select-none my-auto">
            <div class="text-center space-y-1 mb-4">
                <h3 class="text-base font-black tracking-widest uppercase">{{ title }}</h3>
                <div class="flex flex-col items-center justify-center gap-2">
                    <img :src="`${API_URL}${branding['logoUrl']}`" class="w-20" alt="">
                    <p class="text-[15px] text-slate-500 leading-none uppercase mb-2">{{ branding['clubName'] }}</p>
                </div>
                <p class="text-[10px] text-slate-400 leading-none font-sans">{{ receipt.date }}</p>
            </div>

            <div class="space-y-2 border-b border-dashed border-slate-300 pb-3 mb-3 uppercase">
                <div v-if="isSession" class="flex justify-between">
                    <span class="text-slate-500">STATION:</span>
                    <span class="font-bold uppercase">{{ receipt.tableType }} #{{ receipt.tableId }}</span>
                </div>
                <div v-else class="flex justify-between">
                    <span class="text-slate-500">SERVED TO:</span>
                    <span class="font-bold uppercase truncate max-w-[150px]">{{ receipt.player }}</span>
                </div>
                <div v-if="receipt.lounge" class="flex justify-between">
                    <span class="text-slate-500">LOUNGE:</span>
                    <span class="font-bold uppercase truncate max-w-[150px]">{{ receipt.lounge }}</span>
                </div>
                <div v-if="isSession" class="flex justify-between">
                    <span class="text-slate-500">PLAYER:</span>
                    <span class="font-bold truncate max-w-[150px]">{{ receipt.player }}</span>
                </div>
                <div v-if="receipt.servedBy" class="flex justify-between">
                    <span class="text-slate-500">CASHIER:</span>
                    <span class="font-bold truncate max-w-[150px]">{{ receipt.servedBy }}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">RECEIPT:</span>
                    <span class="font-bold text-indigo-600">#{{ receipt.receiptId }}</span>
                </div>
            </div>

            <!-- Line items: what was actually bought (canteen sales) -->
            <div v-if="!isSession" class="space-y-2 border-b border-dashed border-slate-400 pb-4 mb-4">
                <div v-for="(line, i) in lineItems" :key="i" class="flex justify-between">
                    <span class="truncate max-w-[150px] uppercase">
                        {{ line.name }}
                        <span v-if="line.qty > 1" class="text-slate-500 uppercase">× {{ line.qty }}</span>
                    </span>
                    <span>Rs {{ line.cost }}</span>
                </div>
                <div v-if="receipt.discountAmount" class="flex justify-between text-slate-500 text-[11px] pt-1">
                    <span>Discount ({{ receipt.discountPercent }}%)</span>
                    <span>− Rs {{ receipt.discountAmount }}</span>
                </div>

            </div>

            <div v-if="isSession" class="space-y-2 border-b border-dashed border-slate-400 pb-4 mb-4 uppercase">
                <div class="flex justify-between">
                    <span>Duration Played</span><span>{{ receipt.elapsed }}</span>
                </div>
                <div class="flex justify-between">
                    <span>Billable Minutes</span><span>{{ receipt.billableMins }} min</span>
                </div>
                <div v-if="!isMixed" class="flex justify-between text-slate-500 text-[11px]">
                    <span>Base Unit Rate</span><span class="normal-case">Rs {{ receipt.rate }}/min</span>
                </div>
                <div v-else class="text-slate-500 text-[10px] leading-snug pt-0.5">
                    Charged per station — see breakdown below.
                </div>
                <!-- Without this you can read minutes and rate but never the figure
               they produce, which is the one people actually check. -->
                <div class="flex justify-between font-bold pt-1.5 border-t border-slate-200">
                    <span>Table Time Total</span><span class="normal-case">Rs {{ playTotal }}</span>
                </div>
            </div>

            <!-- Per-station breakdown: only worth showing once a tab has moved -->
            <div v-if="isSession && isMixed" class="border-b border-dashed border-slate-300 pb-3 mb-3">
                <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                    Session Breakdown
                </p>
                <div class="space-y-1">
                    <div v-for="(seg, i) in billedSegments" :key="i" class="flex justify-between text-[10px]">
                        <span class="truncate">
                            <span class="uppercase font-bold">{{ seg.tableType }} #{{ seg.tableId }}</span>
                            <span class="text-slate-500"> · {{ seg.billableMins }}m × {{ seg.rate }}</span>
                        </span>
                        <span class="font-bold">Rs {{ seg.cost }}</span>
                    </div>
                </div>
            </div>

            <div v-if="splitCount > 1" class="my-4 border-y border-dashed border-slate-300 py-2">
                <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                    Itemized Charges
                </p>
                <div class="space-y-0.5">
                    <div v-for="item in splitItems" :key="item.id" class="flex justify-between text-[10px] font-mono">
                        <span class="uppercase">Split #{{ item.id }}</span>
                        <span>Rs {{ item.amount }}</span>
                    </div>
                </div>
            </div>

            <!-- Canteen charges put on this tab -->
            <div v-if="canteenItems.length" class="border-b border-dashed border-slate-400 pb-3 mb-3">
                <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                    Canteen
                </p>
                <div class="space-y-1">
                    <div v-for="(line, i) in canteenItems" :key="i" class="flex justify-between text-[10px] uppercase">
                        <span class="truncate max-w-[130px]">
                            <span class="font-bold">{{ line.name }}</span>
                            <span v-if="line.qty > 1" class="text-slate-500"> × {{ line.qty }}</span>
                        </span>
                        <span class="font-bold">Rs {{ line.cost }}</span>
                    </div>
                </div>
                <div class="flex justify-between font-bold mt-1.5 pt-1.5 border-t border-slate-200">
                    <span>Canteen Total</span><span>Rs {{ receipt.canteenTotal }}</span>
                </div>
            </div>

            <div class="flex justify-between items-center py-1 mb-4 uppercase">
                <span class="text-sm font-black tracking-wide">GRAND TOTAL:</span>
                <span class=" normal-case text-lg font-black border-b-4 double-border-bottom">Rs {{ receipt.totalCost }}</span>
            </div>

            <!-- Payment. Either it's owed and scannable, or it's settled — the
             receipt should never leave that ambiguous. -->
            <div v-if="!isPaid && !onKhata" class="border-y border-dashed border-slate-400 py-3 mb-4">
                <p class="text-center text-[10px] font-black uppercase tracking-widest text-slate-700 mb-2 normal-case">
                    Scan to Pay Rs {{ receipt.totalCost }}
                </p>
                <div class="flex justify-center">
                    <svg :viewBox="qrViewBox" class="w-32 h-32" shape-rendering="crispEdges" role="img"
                        aria-label="Scan to pay">
                        <rect :x="-qrQuietZone" :y="-qrQuietZone" :width="qrSpan" :height="qrSpan" fill="#fff" />
                        <path :d="qrPath" fill="#0f172a" />
                    </svg>
                </div>
                <p class="text-center text-[9px] text-slate-500 font-sans mt-2 leading-snug">
                    Open the camera and scan. Pay by EasyPaisa or JazzCash —
                    <span v-if="payUrl" class="font-bold text-slate-700">the counter is notified automatically.</span>
                    <span v-else class="font-bold text-slate-700">then the counter confirms and marks it paid.</span>
                </p>
                <p class="text-center text-[9px] text-slate-400 font-sans mt-1">
                    Ref {{ receipt.receiptId }}
                </p>
            </div>

            <div v-else-if="status === 'paid'" class="border-y border-dashed border-slate-400 py-3 mb-4 h-10 flex justify-center items-center">
                <img src="/paid_textured.svg" alt="PAID IN FULL" class="opacity-90 h-20 -rotate-27 ml-5 mb-5">
            </div>

            <!-- Actions.
             Kept to two tight rows: the status is carried by the buttons
             themselves (ticked when active) rather than a separate line, and
             Split sits beside Clear instead of stacking above it. -->
            <div class="mt-3 space-y-1.5 no-print">
                <!-- Settled: show HOW, not a button that would take the money twice. -->
                <div v-if="isPaid" class="flex gap-2">
                    <div class="flex-1 py-1.5 rounded text-[9px] font-bold border uppercase tracking-wider text-center
                        bg-emerald-600 text-white border-emerald-700 flex items-center justify-center gap-1.5">
                        <span>✓ Paid</span>
                        <span v-if="methodLabel" class="font-normal opacity-90">· {{ methodLabel }}</span>
                    </div>
                </div>

                <div v-else-if="showSettle" class="flex items-center gap-1.5">
                    <!-- An account bill needs a name to chase, so it isn't offered to
                 walk-ins. -->
                    <button v-if="receipt.customerId !== null && !receipt.isWalkIn " @click="settle(onKhata ? 'pending' : 'khata')" :disabled="settling"
                        class="flex-1 py-1.5 rounded text-[9px] font-bold border cursor-pointer uppercase tracking-wider disabled:opacity-50 transition-colors"
                        :class="onKhata
                            ? 'bg-amber-500 text-white border-amber-600 hover:bg-amber-600'
                            : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'">
                        {{ onKhata ? '✓ On Account' : 'On Account'}}
                    </button>
                    <!-- With the payment aggregator ON, EasyPaisa/JazzCash arrive by QR
                 and self-settle, so only Cash is marked here. With it OFF (no
                 payUrl), there's no automated reconciliation, so the cashier
                 records EasyPaisa/JazzCash manually too. -->
                    <button v-if="!onKhata" @click="settle('paid', 'cash')" :disabled="settling"
                        class="flex-1 py-1.5 rounded text-[9px] font-bold border cursor-pointer uppercase tracking-wider disabled:opacity-50 transition-colors bg-white text-slate-700 border-slate-300 hover:bg-slate-100">
                        Paid Cash
                    </button>
                </div>
                <div v-if="!isPaid && showSettle && !entitlements.includes('payments')" class="flex w-full gap-2">
                    <button v-if="!onKhata" @click="settle('paid', 'easypaisa')" :disabled="settling"
                        class="flex-1 py-1.5 rounded text-[9px] font-bold border cursor-pointer uppercase tracking-wider disabled:opacity-50 transition-colors bg-white text-slate-700 border-slate-300 hover:bg-slate-100">
                        Paid EasyPaisa
                    </button>
                    <button v-if="!onKhata" @click="settle('paid', 'jazzcash')" :disabled="settling"
                        class="flex-1 py-1.5 rounded text-[9px] font-bold border cursor-pointer uppercase tracking-wider disabled:opacity-50 transition-colors bg-white text-slate-700 border-slate-300 hover:bg-slate-100">
                        Paid JazzCash
                    </button>
                </div>

                <div class="flex items-center gap-1.5">
                    <button v-if="!readOnly && !onKhata && isSession && !isPaid" @click="isSplitModalOpen = true"
                        class="py-1.5 rounded text-[9px] font-bold bg-white text-slate-700 border border-slate-300 cursor-pointer hover:bg-slate-100 uppercase tracking-wider shrink-0 flex-1">
                        Split
                    </button>
                    <button v-if="dismissable && !isPaid && !onKhata" @click="emit('dismiss')"
                      title="Hide this bill here — the customer display keeps it"
                      class="py-1.5 px-3 rounded text-[9px] font-bold bg-rose-700 text-slate-200 border border-rose-800 cursor-pointer hover:bg-rose-600 transition duration-400 ease-in-out uppercase tracking-wider shrink-0 no-print flex-1">
                      Dismiss
                    </button>
                    <button v-if="canClose" @click="printBill()"
                        class="py-1.5 rounded text-[9px] font-bold bg-white text-slate-700 border border-slate-300 cursor-pointer hover:bg-slate-100 flex-1 uppercase tracking-wider shrink-0">
                        Print Bill 
                    </button>
                    <button v-if="canClose" @click="emit('close')" :disabled="!canClose"
                        :title="canClose ? '' : 'Mark the bill paid, or put it on account, first'"
                        class="flex-1 py-1.5 rounded text-[9px] font-bold uppercase tracking-wider transition-all"
                        :class="canClose
                            ? 'bg-slate-900 hover:bg-slate-800 text-white cursor-pointer shadow-md'
                            : 'bg-slate-200 text-slate-400 cursor-not-allowed'">
                        CLOSE
                    </button>
                    
                </div>

                <p v-if="settleError" class="text-[9px] text-rose-600 font-bold leading-snug">
                    {{ settleError }}
                </p>
                <!-- <p v-else-if="showSettle && !canClose"
            class="text-[9px] text-slate-400 leading-snug text-center">
            {{ receipt.isWalkIn ? 'Walk-in — mark paid to clear.' : 'Mark paid, or put it on account, to clear.' }}
          </p> -->
            </div>

            <!-- Splitting is a billing action, so it wears the same paper. -->
            <div v-if="isSplitModalOpen"
                class="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
                @click.self="isSplitModalOpen = false">
                <div
                    class="bg-white text-slate-900 w-full max-w-xs shadow-2xl rounded-xs font-mono text-xs p-5 relative tracking-tight border-t-8 border-slate-400 select-none my-auto">

                    <div class="text-center space-y-1 mb-4">
                        <h3 class="text-base font-black tracking-widest uppercase">Split Bill</h3>
                        <p class="text-[10px] text-slate-500 leading-none">Receipt #{{ receipt.receiptId }}</p>
                    </div>

                    <div class="space-y-1 border-b border-dashed border-slate-300 pb-3 mb-3">
                        <div class="flex justify-between">
                            <span class="text-slate-500">BILL TOTAL:</span>
                            <span class="normal-case font-bold">Rs {{ receipt.totalCost }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500">SPLIT BETWEEN:</span>
                            <span class="font-bold">{{ splitCount }} {{ splitCount === 1 ? 'person' : 'people' }}</span>
                        </div>
                    </div>

                    <div class="flex items-center justify-center gap-3 mb-4">
                        <button @click="splitCount > 1 && splitCount--"
                            class="w-9 h-9 rounded-md border border-slate-300 bg-white text-slate-700 font-bold cursor-pointer hover:bg-slate-100">
                            −
                        </button>
                        <span class="text-2xl font-black w-12 text-center tabular-nums">{{ splitCount }}</span>
                        <button @click="splitCount < 50 && splitCount++"
                            class="w-9 h-9 rounded-md border border-slate-300 bg-white text-slate-700 font-bold cursor-pointer hover:bg-slate-100">
                            +
                        </button>
                    </div>

                    <div class="border-b border-dashed border-slate-400 pb-3 mb-3">
                        <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-2">Per Person</p>
                        <div class="space-y-1 max-h-40 overflow-y-auto">
                            <div v-for="item in splitItems" :key="item.id" class="flex justify-between text-[11px]">
                                <span class="text-slate-500 uppercase">Share #{{ item.id }}</span>
                                <span class="normal-case font-bold">Rs {{ item.amount }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="flex justify-between items-center py-1 mb-4">
                        <span class="text-sm font-black tracking-wide">EACH PAYS:</span>
                        <span class="text-lg font-black border-b-4 double-border-bottom">Rs {{ perHead }}</span>
                    </div>

                    <div class="flex items-center gap-2">
                        <button @click="cancelSplit"
                            class="flex-1 py-2 rounded-md text-[10px] font-bold border border-slate-300 bg-white text-slate-700 cursor-pointer hover:bg-slate-100 uppercase tracking-wider">
                            Cancel
                        </button>
                        <button @click="applySplit" :disabled="savingSplit"
                            class="flex-1 py-2 rounded-md text-[10px] font-bold bg-slate-900 text-white cursor-pointer hover:bg-slate-800 uppercase tracking-wider disabled:opacity-50">
                            {{ savingSplit ? 'Saving…' : 'Apply Split' }}
                        </button>
                    </div>

                    <div class="absolute -bottom-2 inset-x-0 h-2 flex overflow-hidden pointer-events-none">
                        <div v-for="i in 20" :key="i" class="flex-1 aspect-square bg-white rotate-45 -translate-y-1/2">
                        </div>
                    </div>
                </div>
            </div>

            <div class="absolute -bottom-2 inset-x-0 h-2 flex overflow-hidden pointer-events-none">
                <div v-for="i in 20" :key="i"
                    class="w-4 h-4 bg-white rotate-45 transform origin-top-left -mt-2 shrink-0 border-r border-b border-slate-200">
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { qrMatrix, qrSvgPath, easypaisaPayload } from '../utils/qr.js'

loadBranding()
const PRINT_WIDTH_MM = 80
const PX_TO_MM = 0.264583

function collectStyles(doc) {
    return [...document.querySelectorAll('style, link[rel="stylesheet"]')]
        .map((tag) => doc.importNode(tag.cloneNode(true), true))
}

function waitForStyles(doc) {
    const links = [...doc.querySelectorAll('link[rel="stylesheet"]')]
    if (!links.length) return Promise.resolve()
    return Promise.all(
        links.map(
            (link) =>
                new Promise((resolve) => {
                    if (link.sheet) return resolve()
                    link.addEventListener('load', resolve, { once: true })
                    link.addEventListener('error', resolve, { once: true })
                    setTimeout(resolve, 2000)
                }),
        ),
    )
}

const printing = ref(false)

async function printBill() {
    if (printing.value) return
    const source = document.getElementById('printable-receipt')
    if (!source) return

    printing.value = true

    const iframe = document.createElement('iframe')
    iframe.setAttribute('aria-hidden', 'true')
    Object.assign(iframe.style, {
        position: 'fixed', right: '0', bottom: '0',
        width: '120mm', height: '400mm', border: '0', visibility: 'hidden',
    })
    document.body.appendChild(iframe)

    const doc = iframe.contentWindow.document
    doc.open()
    doc.write('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>')
    doc.close()

    // The PDF filename comes from the IFRAME's title, since that's what prints.
    doc.title = `invoice_${props.receipt.receiptId ?? 'receipt'}`

    collectStyles(doc).forEach((tag) => doc.head.appendChild(tag))

    const clone = doc.importNode(source, true)

    // 1. Clean up elements that shouldn't print or affect height measurement
    clone.querySelectorAll('.no-print').forEach((el) => el.remove())
    clone.querySelectorAll('.absolute').forEach((el) => el.remove())

    // 2. Remove classes that cause unpredictable margins or layout shifts
    clone.classList.remove('my-auto', 'shadow-2xl')

    // 3. Enforce strict dimensions and box model inline BEFORE measuring
    clone.style.width = `${PRINT_WIDTH_MM}mm`
    clone.style.maxWidth = `${PRINT_WIDTH_MM}mm`
    clone.style.margin = '0'
    clone.style.padding = '1.25rem'
    clone.style.position = 'static'
    clone.style.boxSizing = 'border-box'

    doc.body.appendChild(clone)

    const page = doc.createElement('style')
    doc.head.appendChild(page)

    const cleanup = () => {
        if (iframe.parentNode) iframe.parentNode.removeChild(iframe)
        printing.value = false
    }

    try {
        await waitForStyles(doc)
        if (doc.fonts?.ready) await doc.fonts.ready
        await new Promise((resolve) => requestAnimationFrame(resolve))

        // Give the browser a window to calculate the inline style layout
        await new Promise((resolve) => setTimeout(resolve, 50))

        // Measure the EXACT height of the prepared node. No fuzzy math needed.
        const heightMm = Math.max(40, Math.ceil(clone.getBoundingClientRect().height * PX_TO_MM))

        page.textContent = `
            @page {
                size: ${PRINT_WIDTH_MM}mm ${heightMm}mm;
                margin: 0;
            }

            html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: ${PRINT_WIDTH_MM}mm;
                height: ${heightMm}mm;
                background: #fff;
                color: #0f172a;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                overflow: hidden;
            }

            .no-print { display: none !important; }
        `

        await new Promise((resolve) => requestAnimationFrame(resolve))

        iframe.contentWindow.addEventListener('afterprint', cleanup, { once: true })
        iframe.contentWindow.focus()
        iframe.contentWindow.print()

        setTimeout(() => { if (printing.value) cleanup() }, 60000)
    } catch {
        cleanup()
    }
}

const props = defineProps({
    receipt: { type: Object, required: true },
    // readOnly: true when viewing from logs — hides the Split Bill button, changes close label
    readOnly: { type: Boolean, default: false },
    embedded: { type: Boolean, default: false },
    dismissable: { type: Boolean, default: false },
    branding: {type: Object, default: {clubName: null, logoUrl: null}},
    entitlements: {type: Array, default: []},
    /**
     * 'session' — a table's time-based bill (the default)
     * 'canteen' — a counter sale: itemised goods, no clock, no split
     * The chrome is deliberately identical either way; only the middle differs.
     */
    variant: { type: String, default: 'session' },
    API_URL: { type: String, default: '' }
})

// The parent performs the request: this component is shared with the customer
// bundle, so it must not import the staff auth module.
const emit = defineEmits(['close', 'dismiss', 'settle', 'split'])

const status = ref(props.receipt.paymentStatus || 'pending')
const method = ref(props.receipt.paymentMethod || '')

const METHOD_LABELS = {
    cash: 'Cash', easypaisa: 'EasyPaisa', jazzcash: 'JazzCash', account: 'Account',
}
const methodLabel = computed(() => METHOD_LABELS[method.value] || '')

// A payment can land while the bill is open — the parent updates the prop and
// the receipt follows, the same way a station card follows its own status.
watch(() => [props.receipt.paymentStatus, props.receipt.paymentMethod], ([s, m]) => {
    if (s) status.value = s
    if (m) method.value = m
})
const khataName = ref(props.receipt.khataName || '')
const settling = ref(false)
const settleError = ref('')

/**
 * A zero-cost session writes no ledger row, so there is nothing to mark paid.
 * Showing the buttons there would strand the receipt: they'd always fail, and
 * Clear & Reset would never unlock.
 */
const settleable = computed(() => props.receipt.settleable !== false)

// Raised lazily: a bill that nobody scans shouldn't leave a payment record.
/**
 * The pay link arrives WITH the bill, so the QR is correct on first paint.
 * It used to be fetched here after mount, which meant the code rendered
 * before the link existed and fell back to the offline merchant payload.
 */
const payUrl = computed(() => props.receipt.payUrl || '')

// Hidden on historical views: a bill pulled from the logs is a record, not a
// till action.
const showSettle = computed(() => !props.readOnly && settleable.value)

const isPaid = computed(() => status.value === 'paid')
const onKhata = computed(() => status.value === 'pending' && !!khataName.value)

/**
 * The station can only be cleared once the money is accounted for — either
 * taken, or written to somebody's khata. Otherwise a bill can be dismissed
 * off the screen and the takings quietly under-report.
 * Historical views always close: there's nothing to settle.
 */
const canClose = computed(() =>
    props.readOnly || !settleable.value || isPaid.value || onKhata.value,
)

/**
 * Close appears once the bill is settled; Dismiss covers the unpaid case, so
 * the two never sit side by side.
 *
 * A historical receipt has nothing left to settle, so it always closes —
 * without that exception it would be a modal with no way out.
 */
const showClose = computed(() =>
    // Settled bills close. So do receipts with nothing to settle.
    props.readOnly || !settleable.value || canClose.value
    // ...and any unpaid bill that has no Dismiss to fall back on, or the
    // receipt would be a modal with no way out.
    || !props.dismissable,
)

function settle(next, payMethod = 'cash') {
    if (settling.value) return
    settling.value = true
    settleError.value = ''
    emit('settle', {
        status: next,
        method: payMethod,
        name: props.receipt.player,
        done: (result) => {
            settling.value = false
            if (result?.error) { settleError.value = result.error; return }
            status.value = result?.paymentStatus || (next === 'paid' ? 'paid' : 'pending')
            method.value = result?.paymentMethod || (next === 'paid' ? 'cash' : '')
            khataName.value = result?.khataName || ''
        },
    })
}

const isSession = computed(() => props.variant === 'session')
const title = computed(() => (isSession.value ? 'STATION BILLING' : 'CANTEEN RECEIPT'))

/** Goods sold at the counter. Empty for a session bill. */
const lineItems = computed(() => props.receipt.lineItems || [])

/**
 * What the table time alone came to.
 * Falls back to the grand total on receipts issued before canteen charges
 * existed, where every rupee was table time.
 */
const playTotal = computed(() =>
    props.receipt.playTotal ?? props.receipt.totalCost ?? 0,
)

const isSplitModalOpen = ref(false)
const savingSplit = ref(false)
// What was saved, so Cancel can put it back rather than leaving a preview
// the guest never agreed to.
const committedSplit = ref(Number(props.receipt.splitCount) || 1)

const perHead = computed(() =>
    splitCount.value > 0 ? ((props.receipt.totalCost || 0) / splitCount.value).toFixed(2) : 0,
)

function cancelSplit() {
    splitCount.value = committedSplit.value
    isSplitModalOpen.value = false
}

function applySplit() {
    if (savingSplit.value) return
    committedSplit.value = splitCount.value
    isSplitModalOpen.value = false
    // Persist so a bill reopened from the log shows the same per-head figure.
    if (!props.receipt.logId) return
    savingSplit.value = true
    emit('split', {
        splitCount: splitCount.value,
        done: () => { savingSplit.value = false },
    })
}
// Seeded from the saved value so a reopened bill keeps its split.
const splitCount = ref(Number(props.receipt.splitCount) || 1)

// ---------- per-station breakdown ----------
// Stretches that rounded down to zero minutes (a transfer done within seconds)
// are dropped rather than printed as a confusing Rs 0 line.
const billedSegments = computed(() =>
    (props.receipt.segments || []).filter((s) => s.billableMins > 0),
)

/** Food and drink charged to this tab rather than paid at the counter. */
const canteenItems = computed(() => props.receipt.canteenItems || [])
const isMixed = computed(() => billedSegments.value.length > 1)

// ---------- payment QR ----------
const qrQuietZone = 4
/**
 * What the QR encodes.
 *
 * With a pay link (demo flow) it points at the public payment page so the
 * till gets pinged when the guest pays. Without one it falls back to the
 * EMVCo merchant payload, which is what a real EasyPaisa/JazzCash code needs
 * — that logic is deliberately left exactly as it was.
 */
const qrPayload = computed(() =>
    payUrl.value        // hosted pay page → webhook auto-reconciles (2.5% tier)
    || easypaisaPayload({   // offline merchant QR → cashier confirms manually (free tier)
        amount: props.receipt.totalCost,
        billRef: props.receipt.receiptId,
        accountNumber: '03360724333',
        merchantName: 'SYED ZAIN ALI',
        merchantCity: 'ISLAMABAD',
        provider: 'RAAST'
    }),
)
const qrMatrixData = computed(() => qrMatrix(qrPayload.value, { ecLevel: 'M' }))
const qrPath = computed(() => qrSvgPath(qrMatrixData.value))
const qrSpan = computed(() => qrMatrixData.value.length + qrQuietZone * 2)
const qrViewBox = computed(
    () => `${-qrQuietZone} ${-qrQuietZone} ${qrSpan.value} ${qrSpan.value}`,
)

const splitItems = computed(() => {
    const amountPerPerson = (props.receipt.totalCost / splitCount.value).toFixed(2)
    return Array.from({ length: splitCount.value }, (_, i) => ({
        id: i + 1,
        amount: amountPerPerson,
    }))
})
</script>

<style scoped>
/* Keep the paper illusion: a faint hairline, not a chrome scrollbar. */
.receipt-scroll::-webkit-scrollbar {
    width: 4px;
}

.receipt-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.receipt-scroll::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 2px;
}

.receipt-scroll {
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 transparent;
}

.double-border-bottom {
    border-bottom-style: double;
}
</style>