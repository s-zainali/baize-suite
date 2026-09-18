// Pakistani mobile numbers, treated as the customer's identity.
//
// People type these six different ways — 0300 1234567, +92 300 1234567,
// 03001234567, 92-300-1234567 — and all of them mean the same account. Every
// one is reduced to a single canonical form before it reaches storage, because
// "uniquely identifiable" only holds if 0300-1234567 and +923001234567 can't
// become two separate customers.
//
// The input field shows a fixed +92 affix, so the value the user edits is the
// ten-digit national number (3XXXXXXXXX) and nothing else.

/**
 * Strip country and trunk prefixes, keeping every remaining digit.
 * Validation uses this: an over-long number has to FAIL, not get trimmed into a
 * valid one, or a fat-fingered extra digit silently becomes someone else's
 * account.
 */
function rawNational(input) {
    let digits = String(input ?? '').replace(/\D/g, '')
    if (digits.startsWith('0092')) digits = digits.slice(4)
    else if (digits.startsWith('92') && digits.length > 10) digits = digits.slice(2)
    // A trunk prefix only means something in front of a real number, so strip it
    // rather than letting '0300…' become an eleven-digit national number.
    if (digits.startsWith('0')) digits = digits.replace(/^0+/, '')
    return digits
}

/**
 * The bare national number for display, e.g. '3001234567'.
 * Truncates, because this runs on every keystroke and the field caps at ten.
 */
export const nationalDigits = (input) => rawNational(input).slice(0, 10)

/** Canonical storage form '+923001234567', or null when it isn't a valid mobile. */
export function normalisePhone(input) {
    const national = rawNational(input)
    if (!/^3\d{9}$/.test(national)) return null
    return `+92${national}`
}

export const isValidPhone = (input) => normalisePhone(input) !== null

/** Grouped for the affixed input: '300 1234567'. */
export function formatPhoneInput(input) {
    const national = nationalDigits(input)
    if (national.length <= 3) return national
    return `${national.slice(0, 3)} ${national.slice(3)}`
}

/** Full local spelling for reading back to the user: '0300-1234567'. */
export function formatPhoneDisplay(input) {
    const national = nationalDigits(input)
    if (!national) return ''
    if (national.length <= 3) return `0${national}`
    return `0${national.slice(0, 3)}-${national.slice(3)}`
}

/** Partially hidden, for confirmation screens: '0300-****567'. */
export function maskPhone(input) {
    const national = nationalDigits(input)
    if (national.length !== 10) return String(input ?? '')
    return `0${national.slice(0, 3)}-****${national.slice(7)}`
}

/** Digits still needed, for inline progress hints. */
export const phoneDigitsRemaining = (input) => Math.max(0, 10 - nationalDigits(input).length)