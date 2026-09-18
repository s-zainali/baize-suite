import { ref, computed } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

/**
 * License + branding, shared app-wide (same module-store pattern as useSettings).
 *
 * Two backends are involved:
 *   • the app's own API (API_URL) — reads local license status and stores an
 *     activated token. These run BEFORE staff login (the club gate), so they're
 *     public and use plain fetch.
 *   • the license server (VITE_LICENSE_SERVER_URL) — the club's account: register,
 *     login, enrol this device, list issued licenses.
 *
 * Online activation orchestrates both: sign in to the account, enrol this
 * machine, pull the club's token, and hand it to the app to store & verify.
 */

// The license server's base URL. In dev it defaults to the local server
// (docker-compose maps it to :8090); in production set VITE_LICENSE_SERVER_URL.
const LICENSE_SERVER = (import.meta.env.VITE_LICENSE_SERVER_URL
    || (import.meta.env.DEV ? 'http://localhost:8090' : ''))
const CLUB_TOKEN_KEY = 'baize_club_token'

const branding = ref({ clubName: null, logoUrl: null })
const status = ref(null)   // { activated, valid, enforced, clubName, expiresAt, daysLeft, ... }
const account = ref(null)  // license-server account once signed in: { club, devices, licenses }
const _clubToken0 = localStorage.getItem('baize_club_token') || ''
const isClubLoggedIn = ref(!!_clubToken0)  // reactive mirror of the stored club session

export const clubName = computed(() => branding.value.clubName || 'Baize')
export const clubLogo = computed(() => branding.value.logoUrl || null)
export const licenseServerConfigured = !!LICENSE_SERVER

// Gate the app only when the server actually enforces licensing and it's invalid.
// In dev (ENFORCE_LICENSE off) this stays false, so the app is never gated.
export const needsActivation = computed(() =>
    !!status.value && status.value.enforced && !status.value.valid)

// Off on cloud/Render builds (DEVICE_BINDING=off) — then activation skips the
// device-enrolment dance entirely.
export const deviceBinding = computed(() => status.value?.deviceBinding !== false)

// Licensed add-on modules (base features are always available).
export const entitlements = computed(() => status.value?.entitlements || [])
export function hasFeature(key) { return entitlements.value.includes(key) }

// ── app API (public; run before staff login) ────────────────────────────────

export async function loadBranding() {
    try {
        const r = await fetch(`${API_URL}/branding`)
        if (r.ok) branding.value = await r.json()
    } catch { /* offline — keep defaults */ }
    return branding.value
}

export const clubBranches = ref([])

/** List the signed-in club's branches (each carries its own signed token). */
export async function loadClubBranches() {
    if (!LICENSE_SERVER) return []
    const r = await fetch(`${LICENSE_SERVER}/api/club/branches`, {
        headers: { Authorization: `Bearer ${_clubToken()}` },
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.error || 'Could not load your branches.')
    clubBranches.value = d.branches || []
    return clubBranches.value
}

/** Activate a chosen branch's licence on THIS install. The signed branch token
 *  is the authorisation, so this works at the pre-login gate. */
export async function activateBranch(branch) {
    if (!branch || !branch.token) {
        throw new Error("This branch has no licence yet — mint it in the admin portal first.")
    }
    const res = await fetch(`${API_URL}/license/branch/activate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: branch.token, name: branch.name }),
    })
    const d = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(d.error || 'Activation failed.')
    await loadLicense()               // refresh /api/license → the gate lifts
    return d
}

/** Re-pull fresh signed tokens for the branches THIS install has activated and
 *  re-store them, so feature changes made in the admin AFTER activation (e.g.
 *  enabling PC or Automated Payments) actually take effect. Online + club-session
 *  only; offline it's a no-op and the stored tokens keep working. */
export async function syncBranchLicenses() {
    if (!LICENSE_SERVER || !_clubToken()) return false
    let server
    try { server = await loadClubBranches() } catch { return false }
    const byUid = Object.fromEntries((server || []).map((b) => [b.uid, b]))
    let local = []
    try {
        const r = await authFetch(`${API_URL}/branches`)
        if (r.ok) local = (await r.json()).branches || []
    } catch { return false }
    let changed = false
    for (const lb of local) {
        const sb = byUid[lb.uid]
        if (!sb || !sb.token) continue
        try {
            const res = await fetch(`${API_URL}/license/branch/activate`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: sb.token, name: sb.name }),
            })
            if (res.ok) changed = true
        } catch { /* offline — keep the stored token */ }
    }
    if (changed) await loadLicense()
    return changed
}

/** Activate EVERY branch the club has onto THIS install — the online / shared-URL
 *  model: one install holds all branch licences, and each browser picks its own
 *  branch from the sidebar (X-Branch is per-browser, so branches run in parallel). */
export async function activateAllBranches() {
    let list = clubBranches.value
    if (!list.length) { try { list = await loadClubBranches() } catch { return 0 } }
    let n = 0
    for (const b of list) {
        if (!b.token || b.status !== 'active') continue
        try {
            const res = await fetch(`${API_URL}/license/branch/activate`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: b.token, name: b.name }),
            })
            if (res.ok) n++
        } catch { /* keep going */ }
    }
    await loadLicense()
    return n
}


export async function loadLicense() {
    try {
        const r = await fetch(`${API_URL}/license`)
        if (r.ok) status.value = await r.json()
    } catch { /* offline */ }
    return status.value
}

export async function fetchDeviceId() {
    const r = await fetch(`${API_URL}/license/device-id`)
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.error || "Couldn't read this device's ID.")
    return d.fingerprint
}

async function _apply(res) {
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.error || 'Activation failed.')
    status.value = data
    await loadBranding()
    return data
}

/** Offline path: activate from an uploaded .key file. */
export async function activateToken(tokenFile) {
    const fd = new FormData()
    fd.append('token', tokenFile)
    return _apply(await fetch(`${API_URL}/license/activate`, { method: 'POST', body: fd }))
}

/** Activate from a raw token string (used by the online account flow). */
export async function activateTokenString(tokenStr) {
    const fd = new FormData()
    fd.append('token', new Blob([tokenStr], { type: 'text/plain' }), 'license.key')
    return _apply(await fetch(`${API_URL}/license/activate`, { method: 'POST', body: fd }))
}

// ── license-server account (the club login/register) ─────────────────────────

function _clubToken() { return localStorage.getItem(CLUB_TOKEN_KEY) || '' }
export function clubLoggedIn() { return !!_clubToken() }
export function clubLogout() { localStorage.removeItem(CLUB_TOKEN_KEY); account.value = null; isClubLoggedIn.value = false }

// Deactivate the stored license on the backend, clear the local session, and
// refresh status so the activation gate (sign-in) reappears. Owner-only server-side.
export async function deactivateLicense() {
    const r = await authFetch(`${API_URL}/license/deactivate`, { method: 'POST' })
    if (!r.ok) throw new Error('Could not deactivate the license.')
    clubLogout()
    await loadLicense()
    return true
}

async function _clubPost(path, body) {
    if (!LICENSE_SERVER) throw new Error("Online activation isn't configured on this build.")
    const r = await fetch(`${LICENSE_SERVER}${path}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.error || 'Request failed.')
    return d
}

export async function clubRegister(form) {
    const d = await _clubPost('/api/register', form)
    localStorage.setItem(CLUB_TOKEN_KEY, d.token)
    isClubLoggedIn.value = true
    return d
}

export async function clubLogin(form) {
    const d = await _clubPost('/api/login', form)
    localStorage.setItem(CLUB_TOKEN_KEY, d.token)
    isClubLoggedIn.value = true
    return d
}

async function clubMe() {
    const r = await fetch(`${LICENSE_SERVER}/api/me`, {
        headers: { Authorization: `Bearer ${_clubToken()}` },
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) {
        if (r.status === 401) clubLogout()   // stale/expired session — reset the gate
        throw new Error(d.error || 'Your session expired — sign in again.')
    }
    return d
}

/** Refresh the signed-in club's profile + licenses into `account`. */
export async function loadAccount() {
    account.value = await clubMe()
    return account.value
}

async function enrollDevice(fingerprint) {
    // Best-effort: registers this machine on the account so a device-bound
    // license can be issued for it. A failure here shouldn't block activation.
    try {
        await fetch(`${LICENSE_SERVER}/api/devices`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${_clubToken()}` },
            body: JSON.stringify({ fingerprint }),
        })
    } catch { /* ignore */ }
}

/** Register this machine on the account (best-effort; only meaningful when the
 *  install uses device binding). */
export async function enrollThisDevice() {
    try {
        const fp = await fetchDeviceId()
        await enrollDevice(fp)
    } catch { /* non-fatal */ }
}

/** Apply the account's active license to this install. Returns true if it
 *  activated, false if there's nothing usable yet (no license, or one that
 *  isn't for this device). Throws only on a session/network error, so the UI
 *  can keep waiting instead of dead-ending. */
export async function tryActivate() {
    const me = await clubMe()                     // throws (401) if signed out
    account.value = me
    const lic = (me.licenses || []).find((l) => l.status === 'active' && l.token)
    if (!lic) return false
    try { await activateTokenString(lic.token); return true }
    catch { return false }                        // e.g. bound to another device — keep waiting
}

/** One-shot: enrol this device (when bound), then attempt activation. */
export async function activateViaAccount() {
    if (deviceBinding.value) await enrollThisDevice()
    return tryActivate()
}

// ── owner-only, post-activation ──────────────────────────────────────────────

export async function uploadLogo(file) {
    const fd = new FormData()
    fd.append('logo', file)
    const res = await authFetch(`${API_URL}/license/logo`, { method: 'POST', body: fd })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.error || 'Upload failed.')
    branding.value = { ...branding.value, logoUrl: data.logoUrl }
    return data
}

// ── heartbeat (frontend side): re-poll /api/license so a server-side revoke /
// suspend / renewal surfaces mid-session. The actual server beat happens in the
// backend (throttled); this just keeps the frontend's status fresh.
const HEARTBEAT_MS = Number(import.meta.env.VITE_LICENSE_HEARTBEAT_MS) || 300000  // 5 min
let _hbTimer = null

export const refreshLicense = loadLicense

export function startHeartbeat() {
    stopHeartbeat()
    _hbTimer = setInterval(loadLicense, HEARTBEAT_MS)
    window.addEventListener('focus', loadLicense)
    window.addEventListener('online', loadLicense)
}

export function stopHeartbeat() {
    if (_hbTimer) { clearInterval(_hbTimer); _hbTimer = null }
    window.removeEventListener('focus', loadLicense)
    window.removeEventListener('online', loadLicense)
}

export { branding, status, account, isClubLoggedIn }