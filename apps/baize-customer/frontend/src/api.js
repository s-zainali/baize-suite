// api.js
import { apiGet, apiPost, apiDelete, setSession } from './auth.js'

export async function signUp({ name, phone, email, password }) {
    const data = await apiPost('/register', { name, phone, email, password })
    setSession(data.token, data.profile)
    return data
}

export async function signIn({ phone, password }) {
    const data = await apiPost('/login', { phone, password })
    setSession(data.token, data.profile)
    return data
}

/** Always resolves — the server answers identically whether or not the
 *  account exists, and the UI must not behave differently either. */
export const requestReset = ({ phone }) => apiPost('/password/forgot', { phone })

export const verifyCode = ({ phone, code }) => apiPost('/password/verify', { phone, code })

export const resetPassword = ({ resetToken, password }) =>
    apiPost('/password/reset', { resetToken, password })

// ── NEW: Club Discovery & Booking Central Endpoints ──
export const fetchClubs = ({ query = '', near = '' } = {}) => 
    apiGet(`/clubs?query=${encodeURIComponent(query)}&near=${encodeURIComponent(near)}`)

export const fetchAvailability = ({ date, clubUid, branchUid }) => {
    if (!clubUid) throw new Error('clubUid is required')
    
    let path = `/clubs/${encodeURIComponent(clubUid)}/availability?date=${date}`
    if (branchUid) {
        path += `&branch=${encodeURIComponent(branchUid)}`
    }
    
    return apiGet(path)
}

export const createBooking = ({ tableUid, startTime, endTime }) =>
    apiPost('/bookings', { tableUid, startTime, endTime })

export const cancelBooking = (bookingId) =>
    apiDelete(`/bookings/${bookingId}`)