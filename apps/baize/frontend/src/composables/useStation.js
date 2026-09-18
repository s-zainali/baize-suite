// Shared session logic for the station cards (PoolTable, PlayStation, Foosball).
//
// All three had the same ~90 lines of timer + start/stop code copy-pasted, which
// is how they drifted apart. Billing now lives on the server, so this is mostly
// about keeping the card in step with the tab it's showing.

import { ref, computed, watch, onUnmounted } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

export function useStation(props, emit) {
    const timeElapsed = ref(0) // total across the whole tab, not just this stretch
    const receiptData = ref(null)
    const busy = ref(false)
    const error = ref('')
    let timerInterval = null
    let errorTimer = null

    function fail(message) {
        console.error(message)
        error.value = message
        clearTimeout(errorTimer)
        errorTimer = setTimeout(() => (error.value = ''), 6000)
    }
    
    // Returns the number of minutes until an upcoming booking starts (within the next hour), or null
    const bookedIn = computed(() => {
        return () => {
            const now = new Date()
            const oneAndHalfHourLater = new Date(now.getTime() + 60 * 90 * 1000)
    
            const booking = (props.bookings || []).find(booking => {
                if (booking.tableUid !== props.table.uid) {
                    return false
                }
                const start = new Date(booking.startTime)            
                // Checks if the booking hasn't started yet and falls within the 1-hour window
                return start > now && start <= oneAndHalfHourLater
            })
            // console.log(props.bookings)
    
            if (!booking) return null
    
            const start = new Date(booking.startTime)
            return Math.round((start - now) / (1000 * 60))
        }
    })

    /**
     * POST and always come back with something readable.
     *
     * A missing route returns an HTML 404, and calling .json() on that throws a
     * parse error that says nothing useful — which is how a stale backend ends
     * up looking like a dead button.
     */
    /** The joined roster, matching what the server stores as the session name. */
    const rosterLabel = () =>
        (props.table.players || []).map((p) => p.name).filter(Boolean).join(', ')

    async function post(path) {
        const res = await authFetch(`${API_URL}${path}`, { method: 'POST' })
        const body = await res.text()
        let data = {}
        try {
            data = body ? JSON.parse(body) : {}
        } catch {
            throw new Error(
                res.status === 404
                    ? `Endpoint ${path} not found (HTTP 404) — is the backend running the new index.py?`
                    : `Server returned ${res.status} (not JSON)`,
            )
        }
        if (!res.ok) throw new Error(data.error || `Request failed (HTTP ${res.status})`)
        return data
    }

    const banked = () => props.table.priorSeconds || 0

    /** A paused tab is still sitting on this station, waiting to be resumed or settled. */
    const canResume = computed(() => !props.table.isActive && !!props.table.resumable)

    /** Bill accrued so far on a paused tab, shown on the card. */
    const pendingTotal = computed(() => props.table.pendingTotal || 0)

    function stopTicker() {
        if (timerInterval) clearInterval(timerInterval)
        timerInterval = null
    }

    function tick() {
        const since = props.table.startTime
            ? Math.floor((Date.now() - new Date(props.table.startTime)) / 1000)
            : 0
        timeElapsed.value = banked() + Math.max(0, since)
    }

    function startTicker() {
        stopTicker()
        tick()
        timerInterval = setInterval(tick, 1000)
    }

    // One source of truth for the clock: re-sync whenever the tab changes shape.
    watch(
        () => [props.table.startTime, props.table.priorSeconds, props.table.isActive],
        () => {
            if (props.table.isActive && props.table.startTime) startTicker()
            else {
                stopTicker()
                // Paused tabs keep showing the time banked so far
                timeElapsed.value = canResume.value ? banked() : 0
            }
        },
        { immediate: true },
    )

    onUnmounted(stopTicker)

    const formattedTime = computed(() => {
        const total = timeElapsed.value
        const h = Math.floor(total / 3600)
        const m = Math.floor((total % 3600) / 60)
        const s = total % 60
        if (h > 0) {
            return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
        }
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    })

    async function startSession() {
        if (busy.value) return
        busy.value = true
        error.value = ''
        try {
            const res = await authFetch(`${API_URL}/tables/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: props.table.uid,
                    isActive: true,
                    bookingName: props.table.bookingName,
                    players: props.table.players || [],
                }),
            })
            const data = await res.json()
            emit('update-status', {
                uid: props.table.uid,
                isActive: true,
                // The roster replaced the single name field, so bookingName is
                // empty locally until the next poll — which is why a started
                // table read "Walk-in Guest" despite having players. Build the
                // label from what was actually sent.
                bookingName: rosterLabel() || props.table.bookingName,
                players: props.table.players || [],
                startTime: data.startTime,
                priorSeconds: 0,
                resumable: false,
                pendingTotal: 0,
            })
        } catch (err) {
            fail(`Couldn't start session: ${err.message}`)
        } finally {
            busy.value = false
        }
    }

    /** Pause. Bills nothing and logs nothing — the tab stays open. */
    async function stopSession() {
        if (busy.value) return
        busy.value = true
        error.value = ''
        try {
            const data = await post(`/tables/${props.table.uid}/stop`)
            emit('update-status', {
                uid: props.table.uid,
                isActive: false,
                startTime: null,
                // name is kept so the paused card can show whose tab it is
                bookingName: rosterLabel() || props.table.bookingName,
                players: props.table.players || [],
                priorSeconds: data.invoice ? secondsOf(data.invoice) : 0,
                resumable: true,
                pendingTotal: data.invoice ? data.invoice.totalCost : 0,
            })
        } catch (err) {
            fail(`Couldn't pause: ${err.message}`)
        } finally {
            busy.value = false
        }
    }

    /** Settle the tab: prints the receipt, writes the ledger row, frees the station. */
    async function endSession() {
        if (busy.value) return
        busy.value = true
        error.value = ''
        try {
            const data = await post(`/tables/${props.table.uid}/end`)
            // A no-op end (nothing was running) returns no invoice; don't open
            // an empty receipt the user then has to dismiss.
            // The receipt is rendered once, by the dashboard. Emitting it keeps
            // one copy of that markup instead of three identical ones.
            receiptData.value = data.invoice || null
            if (receiptData.value) emit('open-receipt', receiptData.value)
            emit('update-status', {
                uid: props.table.uid,
                isActive: false,
                bookingName: '',
                // Cleared explicitly. Without this the roster stayed on the
                // card: the dashboard preserves a local roster on an idle
                // table (so a half-typed one survives polling), and a table
                // that has just ended looks exactly like that — idle, with the
                // server reporting no players.
                players: [],
                startTime: null,
                priorSeconds: 0,
                resumable: false,
                pendingTotal: 0,
            })
        } catch (err) {
            fail(`Couldn't end session: ${err.message}`)
        } finally {
            busy.value = false
        }
    }

    function secondsOf(invoice) {
        return (invoice.segments || []).reduce((sum, s) => sum + (s.seconds || 0), 0)
    }

    async function resumeSession() {
        if (busy.value) return
        busy.value = true
        error.value = ''
        try {
            const data = await post(`/tables/${props.table.uid}/resume`)
            receiptData.value = null
            emit('update-status', {
                uid: props.table.uid,
                isActive: true,
                bookingName: data.bookingName,
                startTime: data.startTime,
                priorSeconds: data.priorSeconds,
                resumable: false,
                pendingTotal: 0,
            })
        } catch (err) {
            fail(`Couldn't resume: ${err.message}`)
        } finally {
            busy.value = false
        }
    }

    const toggleTimer = () => (props.table.isActive ? stopSession() : startSession())

    const closeReceipt = () => {
        receiptData.value = null
    }

    /**
     * Mark the just-issued bill paid, or leave it on the guest's khata.
     * The receipt component emits this rather than calling the API itself,
     * because it is shared with the customer bundle.
     */
    async function settleBill({ status, name, method, done }) {
        const logId = receiptData.value?.logId
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

    /** Persist how many ways the just-issued bill was split. */
    async function saveSplit({ splitCount, done }) {
        const logId = receiptData.value?.logId
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

    return {
        timeElapsed,
        formattedTime,
        receiptData,
        busy,
        canResume,
        pendingTotal,
        error,
        bookedIn,
        toggleTimer,
        startSession,
        stopSession,
        resumeSession,
        endSession,
        closeReceipt,
        settleBill,
        saveSplit,
    }
}