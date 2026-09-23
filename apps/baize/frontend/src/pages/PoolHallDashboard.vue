<template>
    <div class="bg-slate-900 p-6 pt-0 text-slate-100 relative flex flex-col">

        <ServerOfflineModal v-if="serverOffline" @attempt-connection="attemptConnection" />
        <div v-else :class="[
            activeModal !== 'none'
                ? 'pointer-events-none transition-all duration-300'
                : 'transition-all duration-300',
        ]" class="flex-1">
            <Header @activate-modal="handleActivateModal($event)" @toggle-bills="toggleBills('dashboard')"
                @toggle-station-size="toggleStationSize()" :show-bills="showBills" :small-stations="smallStations"
                :isOwner="isOwner" :isDashboard="true" />

            <SummaryStrip :table-types="tableTypes" :table-summary="tableSummary" />

            <BookingsComponent :bookings="bookings" @refresh="attemptConnection"
                @start-from-booking="startSessionWaiting($event, bookings, 'bookings')" />

            <QueueComponent :queue="waitingQueue" :tableSummary="tableSummary" @remove-guest="removeFromQueue($event)"
                @add-guest="activeModal = 'addToQueue'"
                @start-from-queue="startSessionWaiting($event, waitingQueue, 'queue')" />

            <div class="space-y-6">
                <!-- Empty state: no lounges yet -->
                <div v-if="lounges.length === 0 && !addingLounge"
                    class="flex flex-col items-center justify-center text-center py-10 text-slate-500">
                    <span class="text-4xl mb-3">🛋️</span>
                    <p class="text-sm font-bold text-slate-400">No lounges yet</p>
                    <p class="text-xs text-slate-600 mt-1">Create your first lounge below to start adding tables.</p>
                </div>

                <TableGrid v-for="lounge in lounges" :key="lounge.id" :lounge="lounge" :rates="rates"
                    :tableLounge="tablesForLounge(lounge.uid)" :canManage="canManage" :bookings="bookings"
                    :small-stations="smallStations" @update-status="handleTableUpdate($event)"
                    @open-receipt="showBills ? activeReceipt = $event : ''"
                    @transfer-table="handleTransferTable($event)" @remove-table="removeTable($event)"
                    @rename-lounge="renameLounge($event)" @remove-lounge="removeLounge($event)" />

                <!-- Add lounge -->
                <div v-if="canManage">
                    <button v-if="!addingLounge" @click="addingLounge = true"
                        class="w-full border-2 border-dashed border-slate-800 hover:border-slate-600 rounded-[3rem] p-6 text-slate-500 hover:text-slate-300 font-bold text-sm transition-all cursor-pointer">
                        + Add Lounge
                    </button>
                    <div v-else
                        class="w-full border-2 border-dashed border-slate-700 rounded-[3rem] p-6 flex items-center justify-center gap-3">
                        <input v-model.trim="newLoungeName" @keyup.enter="createLounge"
                            @keyup.esc="addingLounge = false" placeholder="Lounge name (e.g. Non-Smoking, PS5 Zone)"
                            maxlength="60"
                            class="w-72 bg-slate-950/60 border border-slate-700 focus:border-slate-500 rounded-xl px-4 py-2.5 text-sm font-bold text-white outline-none transition-colors placeholder:text-slate-600 placeholder:font-normal" />
                        <button @click="createLounge"
                            class="px-4 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white transition-all cursor-pointer">
                            Create
                        </button>
                        <button @click="addingLounge = false; newLoungeName = ''"
                            class="px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 hover:text-white transition-all cursor-pointer">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>

    </div>
    <AddTableModal v-if="activeModal === 'addTable'" :rates="rates" :lounges="lounges" :tableTypes="tableTypes"
        :existing-names="existingStationNames" @confirm-creation="createNewTable($event)"
        @close-modal="activeModal = 'none'" />

    <ConfirmDeleteModal v-if="activeModal === 'confirmDelete'" :uid="tableToRemove" @confirmRemove="confirmRemove()"
        @closeModal="activeModal = 'none'" />

    <RatesModal v-if="activeModal === 'rates'" :rates="rates" @save-configuration="saveGlobalRates($event)"
        @close-modal="activeModal = 'none'" />

    <KhataModal v-if="activeModal === 'khata'" @close-modal="activeModal = 'none'" @settled="refreshBillStatus()" />

    <TransferTableModal v-if="activeModal === 'transferTable'" :from_uid="fromTableUid" :tableLounge="tableLounge"
        :rates="rates" :bookings="bookings" @transfer-table="transferTable($event)"
        @close-modal="activeModal = 'none'" />

    <StartFromQueueModal v-if="activeModal === 'startFromQueue'" :from_uid="fromTableUid" :newGuest="newGuest"
        :tableLounge="tableLounge" :rates="rates" :bookings="bookings"
        @start-session="newGuest.tableId = $event; startSession('queue')" @close-modal="activeModal = 'none'" />
    <!-- One receipt for the whole floor, rather than a copy inside each
         station card. -->
    <BillingReceipt v-if="activeReceipt" :receipt="activeReceipt" :dismissable="true" @dismiss="activeReceipt = null"
        @close="closeBill" @settle="settleBill" @split="saveSplit" />

    <PaymentPings @received="onPaymentReceived" />

    <AddToQueueModal v-if="activeModal === 'addToQueue'" :lounges="lounges" :rates="rates"
        @close-modal="activeModal = 'none'" :table-lounge="tableLounge" @enqueue="enQueue($event)" />


    <div v-if="tableError"
        class="fixed flex gap-3 z-100 bottom-10 left-1/2 border-2 border-rose-500 font-black rounded-lg px-3 py-1 uppercase bg-rose-500/80 transition duration-500 ease-in-out">
        <span class="text-white">target table busy</span>
        <button @click="tableError = false" class="font-black text-white cursor-pointer">✕</button>
    </div>
</template>

<script setup>
import { usePageBackground } from '@/composables/usePageBackground.js'
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue'
import { types as tableTypes } from '@/composables/useTableTypes.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import PaymentPings from '../components/PaymentPings.vue'
import BillingReceipt from '../components/BillingReceipt.vue'
import ConfirmDeleteModal from '../components/Modals/ConfirmDeleteModal.vue'
import AddTableModal from '../components/Modals/AddTableModal.vue'
import KhataModal from '../components/Modals/KhataModal.vue'
import ServerOfflineModal from '../components/Modals/ServerOfflineModal.vue'
import TransferTableModal from '../components/Modals/TransferTableModal.vue'
import StartFromQueueModal from '../components/Modals/StartFromQueueModal.vue'
import AddToQueueModal from '@/components/Modals/AddToQueueModal.vue'
import RatesModal from '../components/Modals/RatesModal.vue'
import Header from '../components/Header.vue'
import TableGrid from '../components/TableGrid.vue'
import QueueComponent from '../components/QueueComponent.vue'
import SummaryStrip from '../components/SummaryStrip.vue'
import BookingsComponent from '../components/BookingsComponent.vue'
import { authFetch, API_URL } from '@/Auth.js'
import { loadSettings, settingValue, setSetting } from '@/composables/useSettings.js'
import { canManage, canFloor, isOwner, auth, logout } from '@/Auth.js'
import { onModalRequest } from '@/composables/useModals.js'
import { componentFor } from '@/composables/useTableTypes.js'


// const API_URL = import.meta.env.VITE_API_URL

const rates = reactive({})   // was reactive({snooker: 8, ...})

const activeModal = ref('none')
const tableLounge = ref([])
const lounges = ref([])
const addingLounge = ref(false)
const newLoungeName = ref('')
const historicalLogs = ref([])
const logsGrossTotal = ref(0)
const tableError = ref(false)
const serverOffline = ref(false)
const showBills = ref(true)
const tableToRemove = ref(null)
const bookings = ref([])
let fromTable = ref(null)
let fromTableUid = ref(null)
const newGuest = ref({ name: '', tableType: '', id: 0, tableId: '' })
const smallStations = ref(false)

const existingStationNames = computed(() =>
    lounges.value.flatMap((l) => (l.tables || []).map((t) => t.id ?? t.tableId)),
)

onModalRequest('rates', () => { activeModal.value = 'rates' })
onModalRequest('addTable', () => { activeModal.value = 'addTable' })

const toggleBills = (context) => {
    showBills.value = !showBills.value
    setSetting('dashboard_show_bills', showBills.value)
}
const toggleStationSize = (context) => {
    smallStations.value = !smallStations.value
    setSetting('small_stations', smallStations.value)
}


const tableSummary = computed(() => {
    const summary = {}
    tableTypes.forEach((t) => {
        const tables = tableLounge.value.filter((item) => item.type === t.id)
        const queueCount = waitingQueue.value.filter((guest) => guest.tableType === t.id).length
        summary[t.id] = {
            queueCount: queueCount,
            total: tables.length,
            occupied: tables.filter((item) => item.isActive).length,
            resumable: tables.filter((item) => item.resumable).length,
            free: tables.length - tables.filter((item) => item.isActive || item.resumable).length,
        }
    })
    return summary
})

const waitingQueue = ref([])

/**
 * Fold fresh server state into the tables we already have.
 *
 * A roster typed on an IDLE table exists only in the browser — it isn't sent
 * until the session starts. Replacing the array wholesale therefore threw away
 * whatever the cashier was midway through typing, which is why players
 * vanished on every poll.
 *
 * Once a table is running, the server is authoritative: its roster was saved
 * with the session, and keeping a stale local copy would show the wrong names
 * after a transfer or a resume.
 */
// A start/stop is applied optimistically on click; the next poll can still be
// carrying the OLD state for a beat, which would flip the card back until the
// following poll. We hold the optimistic value until the server agrees.
const pendingToggles = new Map()   // uid -> { active, at }
const PENDING_TTL = 15000

const mergeTables = (incoming) => {
    const localMap = new Map(tableLounge.value.map((t) => [t.uid, t]))

    return incoming.map((table) => {
        const existing = localMap.get(table.uid)
        if (!existing) return table   // brand-new table from the server

        // Drafts live only in the browser until the session starts, so an idle
        // table keeps whatever the cashier is midway through typing.
        const idle = !table.isActive
        const draftName = existing.bookingName
        const draftPlayers = existing.players

        // Honour a just-clicked start/stop until the server confirms it.
        const pending = pendingToggles.get(table.uid)
        let holdActive = null
        if (pending) {
            if (Date.now() - pending.at > PENDING_TTL || table.isActive === pending.active) {
                pendingToggles.delete(table.uid)          // confirmed or expired
            } else {
                holdActive = pending.active               // server still stale → hold
            }
        }

        // Mutate in place so Vue keeps the element (no phantom enter/leave).
        Object.assign(existing, table)

        if (idle) {
            if (draftName && !table.bookingName) existing.bookingName = draftName
            if (draftPlayers?.length && !table.players?.length) existing.players = draftPlayers
        }
        if (holdActive !== null) {
            existing.isActive = holdActive
            if (!holdActive) existing.startTime = null
        }
        return existing
    })
}

const attemptConnection = async () => {
    try {
        const res = await authFetch(`${API_URL}/state`)
        const data = await res.json()
        waitingQueue.value = data.queue
        tableLounge.value = mergeTables(data.tables)
        tableLounge.value = tableLounge.value.filter(table => table.entitled)
        lounges.value = data.lounges || []
        bookings.value = data.bookings
        Object.keys(data.rates).forEach(type => {
            rates[type] = { ...data.rates[type] }
        })
        serverOffline.value = false
    } catch (err) {
        serverOffline.value = true
    }
}

// The dashboard used to load state once and never again, so a booking made by
// a guest online (or by another tablet) never appeared until someone refreshed.
// 10s: fast enough that another tablet's change shows up without anyone
// thinking to refresh, slow enough to be invisible. The draft roster survives
// it now, so there's no reason to cripple the interval.
useAutoRefresh(attemptConnection, 10000)

// Restore the persisted "show bills" preference (backend-backed).
onMounted(async () => {
    await loadSettings()
    showBills.value = settingValue('dashboard_show_bills', true)
    smallStations.value = settingValue('small_stations', false)
})

const randomInt = (min, max) => {
    min = Math.ceil(min)
    max = Math.floor(max)
    return Math.floor(Math.random() * (max - min + 1)) + min
}

const enQueue = async (item) => {
    let id = randomInt(0, 1000)
    while (waitingQueue.value.find(guest => guest.id == id)) {
        id = randomInt(0, 1000)
    }
    item.id = id
    const res = await authFetch(`${API_URL}/queue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guestName: item.guestName, tableType: item.tableType, uid: item.id }),
    })
    if (res.ok) {
        // Show the callable number right away; the next state poll would carry
        // it too, but this avoids a flash of a numberless row.
        const data = await res.json().catch(() => ({}))
        item.number = data.number
        waitingQueue.value.push(item)
    }
}

const deQueue = () => {
    waitingQueue.value.pop()
}

const startSessionWaiting = async (id, waitingList, startFrom) => {
    let index = waitingList.findIndex(item => item.id == id)
    newGuest.value = { name: waitingList[index].guestName, tableType: waitingList[index].tableType, id: waitingList[index].id, tableId: '' }

    if (startFrom === "queue") {
        activeModal.value = 'startFromQueue'
    }
    else {
        if (checkifActive(waitingList[index].tableUid)) {
            tableError.value = true
            return
        }
        newGuest.value.tableId = waitingList[index].tableUid
        startSession('booking', id)
    }
}

const checkifActive = (tableUid) => {
    return tableLounge.value.filter((table) => table.uid === tableUid)[0].isActive
}

const startSession = async (from, id = '') => {
    const payload = {
        uid: newGuest.value.tableId,
        isActive: true,
        bookingName: newGuest.value.name
    }
    const res = await authFetch(`${API_URL}/tables/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
    if (from === 'booking') {
        await authFetch(`${API_URL}/bookings/${id}`, { method: 'POST' })
        attemptConnection()
    }
    const data = await res.json()
    handleTableUpdate({
        uid: newGuest.value.tableId,
        isActive: true,
        bookingName: newGuest.value.name,
        startTime: data.startTime,
        priorSeconds: 0,
        resumable: false,
    })
    if (res.ok) {
        if (from === 'queue') {
            removeFromQueue(newGuest.value.id)
        }
        activeModal.value = 'none'
        newGuest.value = { name: '', tableType: '', id: 0, tableId: '' }
    }
}

const removeFromQueue = async (id) => {
    let index = waitingQueue.value.findIndex(guest => guest.id == id)
    waitingQueue.value.splice(index, 1)
    await authFetch(`${API_URL}/queue/${id}`, { method: 'DELETE' })
}


const createNewTable = async ({ type, loungeUid, tableId }) => {
    const typeKey = type
    const payload = { type: typeKey, id: tableId, loungeUid }
    try {
        await authFetch(`${API_URL}/tables`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        tableLounge.value.push({ ...payload, isActive: false, bookingName: '', startTime: null })
        activeModal.value = 'none'
    } catch (err) {
        serverOffline.value = true
    }
}

// ---------- LOUNGES ----------
const tablesForLounge = (loungeUid) =>
    tableLounge.value.filter((t) => t.loungeUid === loungeUid)

const createLounge = async () => {
    const name = newLoungeName.value.trim() || `Lounge ${lounges.value.length + 1}`
    try {
        const res = await authFetch(`${API_URL}/lounges`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        })
        const data = await res.json()
        lounges.value.push({ id: data.id, name: data.name })
        addingLounge.value = false
        newLoungeName.value = ''
    } catch (err) {
        serverOffline.value = true
    }
}

const renameLounge = async ({ id, name }) => {
    const lounge = lounges.value.find((l) => l.id === id)
    if (!lounge) return
    const previous = lounge.name
    lounge.name = name // optimistic
    try {
        const res = await authFetch(`${API_URL}/lounges/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        })
        if (!res.ok) lounge.name = previous
    } catch (err) {
        lounge.name = previous
        serverOffline.value = true
    }
}

const removeLounge = async (id) => {
    // Legacy client-side default lounge (id: null) never existed in the DB —
    // just drop it locally instead of calling DELETE /lounges/null.
    if (id == null) {
        lounges.value = lounges.value.filter((l) => l.id != null)
        return
    }
    try {
        const res = await authFetch(`${API_URL}/lounges/${id}`, { method: 'DELETE' })
        if (res.ok) {
            lounges.value = lounges.value.filter((l) => l.id !== id)
        }
    } catch (err) {
        serverOffline.value = true
    }
}

const handleActivateModal = (modal) => {
    if (modal === 'logs') return openLogsModal()
    // Can't add a table with no lounge to put it in — open the lounge creator instead
    if (modal === 'addTable' && lounges.value.length === 0) {
        addingLounge.value = true
        return
    }
    activeModal.value = modal
}

const removeTable = (uid) => {
    tableToRemove.value = uid
    activeModal.value = 'confirmDelete'
}

const confirmRemove = async () => {
    if (!tableToRemove.value) return

    try {
        await authFetch(`${API_URL}/tables/${tableToRemove.value}`, { method: 'DELETE' })
        tableLounge.value = tableLounge.value.filter((t) => t.uid !== tableToRemove.value)
        activeModal.value = 'none'
        tableToRemove.value = null
    } catch (err) {
        serverOffline.value = true
        activeModal.value = 'none'
    }
}

const handleTableUpdate = async ({ uid, isActive, bookingName, players, startTime, priorSeconds, resumable, pendingTotal }) => {
    const match = tableLounge.value.find((t) => t.uid === uid)
    if (!match) return
    pendingToggles.set(uid, { active: isActive, at: Date.now() })   // guard against a stale poll
    match.isActive = isActive
    match.startTime = isActive ? startTime : null
    if (bookingName !== undefined) match.bookingName = bookingName
    // Carried through so the card keeps its chips between the click and the
    // next poll; without it the roster blinked away the moment play started.
    if (players !== undefined) match.players = players
    // Session fields drive the cumulative timer and the Resume button
    if (priorSeconds !== undefined) match.priorSeconds = priorSeconds
    if (resumable !== undefined) match.resumable = resumable
    if (pendingTotal !== undefined) match.pendingTotal = pendingTotal
}

const handleTransferTable = async ({ from_uid, fromTableNumber }) => {
    fromTable = fromTableNumber
    fromTableUid = from_uid
    activeModal.value = "transferTable"
}

const transferTable = async ({ from_uid, to_uid, allowActive }) => {
    // Snapshot both tabs before any update: on a swap the destination's roster
    // and name move onto the source station.
    const from_table = tableLounge.value.find((t) => t.uid === from_uid)
    const to_table = tableLounge.value.find((t) => t.uid === to_uid)
    try {
        const res = await authFetch(`${API_URL}/tables/transfer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from_uid, to_uid, allowActive }),
        })
        const data = await res.json()
        if (!res.ok) {
            console.error('Transfer failed:', data.error)
            activeModal.value = 'none'
            return
        }
        // The from-tab lands on the destination. The server opened a fresh
        // segment there at ITS rate and reports the time banked so far, so the
        // timer carries on unbroken.
        handleTableUpdate({
            uid: to_uid,
            isActive: true,
            bookingName: from_table?.bookingName,
            // Carry the roster across (a copy, so clearing the source can't empty it too).
            players: [...(from_table?.players || [])],
            startTime: data.startTime,
            priorSeconds: data.priorSeconds,
            resumable: false,
            pendingTotal: 0,
        })
        if (data.swapped && data.swappedWith) {
            // Swap: the destination's tab lands on the source station, which
            // stays active with its own continued session.
            handleTableUpdate({
                uid: from_uid,
                isActive: true,
                bookingName: to_table?.bookingName,
                players: [...(to_table?.players || [])],
                startTime: data.swappedWith.startTime,
                priorSeconds: data.swappedWith.priorSeconds,
                resumable: false,
                pendingTotal: 0,
            })
        } else {
            // Plain transfer: the source goes idle. Clear the roster explicitly
            // or mergeTables treats the lingering names as an unsaved draft.
            handleTableUpdate({
                uid: from_uid, isActive: false, bookingName: '',
                players: [],
                startTime: null, priorSeconds: 0, resumable: false, pendingTotal: 0,
            })
        }
    } catch (err) {
        serverOffline.value = true
    }
    activeModal.value = 'none'
}

const saveGlobalRates = async (payload) => {
    try {
        await authFetch(`${API_URL}/rates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        // update the component's reactive `rates`, one new object per key
        Object.keys(payload).forEach(type => {
            rates[type] = { ...payload[type] }
        })
        activeModal.value = 'none'
    } catch (err) {
        serverOffline.value = true
    }
}

const canteenOrders = ref([])

// ── the open bill ─────────────────────────────────────────────────────────
const activeReceipt = ref(null)

/** Mark the open bill paid, or leave it on account. */
async function settleBill({ status, name, method, done }) {
    const logId = activeReceipt.value?.logId
    if (!logId) { done?.({ error: 'This bill has no ledger entry to settle' }); return }
    try {
        const res = await authFetch(`${API_URL}/bills/${logId}/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, name, method }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not update the bill')
        done?.(data)
    } catch (err) {
        done?.({ error: err.message })
    }
}

/** Close the bill on the server, then take it off the screen. */
async function closeBill() {
    const logId = activeReceipt.value?.logId
    if (!logId) { activeReceipt.value = null; return }
    try {
        await authFetch(`${API_URL}/bills/${logId}/close`, { method: 'POST' })
    } catch (err) {
        console.error('Could not close the bill', err)
    } finally {
        activeReceipt.value = null
    }
}

/** Remember how many ways the bill was split. */
async function saveSplit({ splitCount, done }) {
    const logId = activeReceipt.value?.logId
    if (!logId) { done?.(); return }
    try {
        await authFetch(`${API_URL}/bills/${logId}/split`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ splitCount }),
        })
    } catch (err) {
        console.error('Could not save the split', err)
    } finally {
        done?.()
    }
}

/**
 * While an unpaid bill is on screen, watch it for payment.
 *
 * Polling the bill itself rather than the notification feed: notifications are
 * consumed by whichever screen reads them first, so a receipt relying on those
 * would stay 'unpaid' whenever the canteen till happened to poll first.
 */
let billWatch = null

function stopBillWatch() {
    if (billWatch) clearInterval(billWatch)
    billWatch = null
}

async function refreshBillStatus() {
    const open = activeReceipt.value
    if (!open?.logId || open.paymentStatus === 'paid') { stopBillWatch(); return }
    try {
        const res = await authFetch(`${API_URL}/bills/${open.logId}`)
        if (!res.ok) return
        const data = await res.json()
        if (data.paymentStatus !== open.paymentStatus || data.paymentMethod !== open.paymentMethod) {
            activeReceipt.value = {
                ...open,
                paymentStatus: data.paymentStatus,
                paymentMethod: data.paymentMethod,
                khataName: data.khataName,
            }
        }
    } catch {
        // A missed poll is harmless; the next one picks it up.
    }
}

watch(() => activeReceipt.value?.logId, (logId) => {
    stopBillWatch()
    if (logId) billWatch = setInterval(refreshBillStatus, 2000)
}, { immediate: true })

onUnmounted(stopBillWatch)

/**
 * A payment can land while the bill is on screen. Reflect it there and then,
 * the same way a station card reflects its own status, so the cashier isn't
 * looking at a stale 'unpaid' receipt after the guest has already paid.
 */
function onPaymentReceived(payment) {
    attemptConnection()
    const open = activeReceipt.value
    if (!open) return
    const matches = (payment.logId && payment.logId === open.logId)
        || (payment.billGroup && payment.billGroup === open.billGroup)
    if (matches) {
        activeReceipt.value = {
            ...open,
            paymentStatus: 'paid',
            paymentMethod: payment.method,
        }
    } else {
        // Not obviously ours — ask the bill directly rather than guess.
        refreshBillStatus()
    }
}

const openLogsModal = async () => {
    try {
        // Both ledgers load together so the switch is instant either way.
        const [logsRes, canteenRes] = await Promise.allSettled([
            authFetch(`${API_URL}/logs`).then((r) => r.json()),
            authFetch(`${API_URL}/canteen/orders`).then((r) => r.json()),
        ])
        if (logsRes.status === 'fulfilled') {
            historicalLogs.value = logsRes.value.logs
            logsGrossTotal.value = logsRes.value.grossTotal
        }
        canteenOrders.value = canteenRes.status === 'fulfilled' ? canteenRes.value.orders : []
        activeModal.value = 'logs'
    } catch (err) {
        serverOffline.value = true
    }
}


usePageBackground('#0f172a')
</script>