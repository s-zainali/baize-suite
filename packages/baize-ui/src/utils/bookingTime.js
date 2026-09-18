// Booking time rules, kept out of the component so they can be reasoned about
// (and tested) on their own.
//
// The slot grid is 30 minutes, and a booking must last at least one slot — so
// the earliest valid end is always start + 30 min.

export const SLOT_MINUTES = 30
export const MIN_DURATION_MINUTES = 30
export const MAX_DURATION_MINUTES = 500

const pad = (n) => String(n).padStart(2, '0')

/** 'HH:MM' -> minutes since midnight. */
export function toMinutes(hhmm) {
    if (!hhmm) return null
    const [h, m] = hhmm.split(':').map(Number)
    if (Number.isNaN(h) || Number.isNaN(m)) return null
    return h * 60 + m
}

/** Minutes since midnight -> 'HH:MM'. Returns null once it runs past midnight. */
export function toHHMM(minutes) {
    if (minutes === null || minutes < 0 || minutes >= 24 * 60) return null
    return `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`
}

/** 'YYYY-MM-DD' for a Date, in local time (never UTC — bookings are local). */
export function toISODate(date) {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Round up to the next slot boundary. 14:01 -> 14:30, 14:30 -> 14:30. */
export function ceilToSlot(minutes) {
    return Math.ceil(minutes / SLOT_MINUTES) * SLOT_MINUTES
}

/**
 * Earliest start time selectable on a given date.
 * Today is limited to the next slot boundary; future dates open from midnight.
 */
export function earliestStart(dateISO, now = new Date()) {
    if (dateISO !== toISODate(now)) return '00:00'
    return toHHMM(ceilToSlot(now.getHours() * 60 + now.getMinutes()))
}

/**
 * Latest start time selectable — late enough slots are unusable because the
 * minimum booking would spill past midnight.
 */
export function latestStart() {
    return toHHMM(24 * 60 - MIN_DURATION_MINUTES)
}

/** Earliest end time for a given start: one full slot later. */
export function earliestEnd(startTime) {
    const start = toMinutes(startTime)
    if (start === null) return null
    return toHHMM(start + MIN_DURATION_MINUTES)
}

export function latestEnd(startTime) {
    const start = toMinutes(startTime)
    if (start === null) return null
    return toHHMM(start + MAX_DURATION_MINUTES)
}

/** 'HH:MM' -> '9:00 AM'. */
export function formatTime12(hhmm) {
    const minutes = toMinutes(hhmm)
    if (minutes === null) return ''
    const h24 = Math.floor(minutes / 60)
    const period = h24 >= 12 ? 'PM' : 'AM'
    const h12 = h24 % 12 === 0 ? 12 : h24 % 12
    return `${h12}:${pad(minutes % 60)} ${period}`
}

/** Human duration between two 'HH:MM' values, e.g. '1h 30m'. */
export function formatDuration(startTime, endTime) {
    const start = toMinutes(startTime)
    const end = toMinutes(endTime)
    if (start === null || end === null || end <= start) return ''
    const total = end - start
    const h = Math.floor(total / 60)
    const m = total % 60
    if (h && m) return `${h}h ${m}m`
    return h ? `${h}h` : `${m}m`
}

/**
 * Why this start/end pair isn't bookable, or '' when it is fine.
 * Mirrors the server-side checks so the button disables before a round trip.
 */
export function validateRange(dateISO, startTime, endTime, now = new Date()) {
    const start = toMinutes(startTime)
    const end = toMinutes(endTime)
    if (start === null || end === null) return 'Pick a start and end time'

    if (dateISO === toISODate(now)) {
        const nowMinutes = now.getHours() * 60 + now.getMinutes()
        if (start < nowMinutes) return 'Start time is in the past'
    } else if (dateISO < toISODate(now)) {
        return 'That date has already passed'
    }

    if (end <= start) return 'End time must be after the start time'
    if (end - start < MIN_DURATION_MINUTES) {
        return `Minimum booking is ${MIN_DURATION_MINUTES} minutes`
    }
    return ''
}

/**
 * Do two half-open intervals [aStart, aEnd) and [bStart, bEnd) overlap?
 * Half-open means a booking ending at 4:00 doesn't clash with one starting then.
 */
export function overlaps(aStart, aEnd, bStart, bEnd) {
    return aStart < bEnd && bStart < aEnd
}