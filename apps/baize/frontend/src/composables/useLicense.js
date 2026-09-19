import { ref, computed } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

const LICENSE_SERVER = (import.meta.env.VITE_LICENSE_SERVER_URL
    || (import.meta.env.DEV ? 'http://localhost:8090' : ''))
const CLUB_TOKEN_KEY = 'baize_club_token'
const SELECTED_BRANCH_KEY = 'baize_selected_branch'

const branding = ref({ clubName: null, logoUrl: null })
export const status = ref(null)   // exported so reactivity is top-level root
const account = ref(null)
const isClubLoggedIn = ref(!!localStorage.getItem(CLUB_TOKEN_KEY))

export const clubName = computed(() => branding.value.clubName || 'Baize')
export const clubLogo = computed(() => branding.value.logoUrl || null)
export const licenseServerConfigured = !!LICENSE_SERVER

export const needsActivation = computed(() =>
    !!status.value && status.value.enforced && !status.value.valid)

export const deviceBinding = computed(() => status.value?.deviceBinding !== false)

// ── FIX 1: Direct reactive reader for entitlements ────────────────────────────
export const entitlements = computed(() => {
    if (!status.value) return []
    return Array.isArray(status.value.entitlements) ? status.value.entitlements : []
})

// ── FIX 2: Check status.value directly so function calls outside templates don't hit cold computed caches
export function hasFeature(key) {
    if (!status.value || !Array.isArray(status.value.entitlements)) return false
    return status.value.entitlements.includes(key)
}

function _getActiveBranchUid(overrideUid = null) {
    if (overrideUid) return overrideUid
    return localStorage.getItem(SELECTED_BRANCH_KEY) || localStorage.getItem('selected_branch_uid') || ''
}

export async function loadBranding() {
    try {
        const r = await fetch(`${API_URL}/branding`)
        if (r.ok) branding.value = await r.json()
    } catch { /* offline */ }
    return branding.value
}

export const clubBranches = ref([])

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
    await loadLicense(branch.uid)
    return d
}

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
        } catch { /* offline */ }
    }
    if (changed) await loadLicense()
    return changed
}

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

// ── FIX 3: Force brand-new object reference assignment to break Vue stale cache ──
export async function loadLicense(branchUid = null) {
    try {
        const activeBranch = _getActiveBranchUid(branchUid)
        const headers = {}
        if (activeBranch) {
            headers['X-Branch-UID'] = activeBranch
        }

        const r = await fetch(`${API_URL}/license`, { headers })
        if (r.ok) {
            const newStatus = await r.json()
            // Re-assign a fresh object reference so Vue triggers ALL downstream watchers
            status.value = { ...newStatus }
        }
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
    status.value = { ...data }
    await loadBranding()
    return data
}

export async function activateToken(tokenFile) {
    const fd = new FormData()
    fd.append('token', tokenFile)
    return _apply(await fetch(`${API_URL}/license/activate`, { method: 'POST', body: fd }))
}

export async function activateTokenString(tokenStr) {
    const fd = new FormData()
    fd.append('token', new Blob([tokenStr], { type: 'text/plain' }), 'license.key')
    return _apply(await fetch(`${API_URL}/license/activate`, { method: 'POST', body: fd }))
}

function _clubToken() { return localStorage.getItem(CLUB_TOKEN_KEY) || '' }
export function clubLoggedIn() { return !!_clubToken() }
export function clubLogout() {
    localStorage.removeItem(CLUB_TOKEN_KEY)
    account.value = null
    isClubLoggedIn.value = false
}

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
        if (r.status === 401) clubLogout()
        throw new Error(d.error || 'Your session expired — sign in again.')
    }
    return d
}

export async function loadAccount() {
    account.value = await clubMe()
    return account.value
}

async function enrollDevice(fingerprint) {
    try {
        await fetch(`${LICENSE_SERVER}/api/devices`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${_clubToken()}` },
            body: JSON.stringify({ fingerprint }),
        })
    } catch { /* ignore */ }
}

export async function enrollThisDevice() {
    try {
        const fp = await fetchDeviceId()
        await enrollDevice(fp)
    } catch { /* non-fatal */ }
}

export async function tryActivate() {
    const me = await clubMe()
    account.value = me
    const lic = (me.licenses || []).find((l) => l.status === 'active' && l.token)
    if (!lic) return false
    try { await activateTokenString(lic.token); return true }
    catch { return false }
}

export async function activateViaAccount() {
    if (deviceBinding.value) await enrollThisDevice()
    return tryActivate()
}

export async function uploadLogo(file) {
    const fd = new FormData()
    fd.append('logo', file)
    const res = await authFetch(`${API_URL}/license/logo`, { method: 'POST', body: fd })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.error || 'Upload failed.')
    branding.value = { ...branding.value, logoUrl: data.logoUrl }
    return data
}

const HEARTBEAT_MS = Number(import.meta.env.VITE_LICENSE_HEARTBEAT_MS) || 300000
let _hbTimer = null

export const refreshLicense = loadLicense

export function startHeartbeat() {
    stopHeartbeat()
    _hbTimer = setInterval(() => loadLicense(), HEARTBEAT_MS)
    window.addEventListener('focus', () => loadLicense())
    window.addEventListener('online', () => loadLicense())
}

export function stopHeartbeat() {
    if (_hbTimer) { clearInterval(_hbTimer); _hbTimer = null }
    window.removeEventListener('focus', () => loadLicense())
    window.removeEventListener('online', () => loadLicense())
}

export { branding, account, isClubLoggedIn }