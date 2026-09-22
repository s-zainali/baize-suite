// src/auth.js — auth store + fetch wrapper
import { reactive, computed } from 'vue'

export const API_URL = import.meta.env.VITE_API_URL || '/api'

export const auth = reactive({
    token: localStorage.getItem('ls_token') || '',
    role: localStorage.getItem('ls_role') || '',
    username: localStorage.getItem('ls_user') || '',
    // Which counters this person may work. Granted per user by an owner, not
    // implied by their role — except for managers and owners, who cover both.
    capabilities: (localStorage.getItem('ls_caps') || '').split(',').filter(Boolean),
})

export const isLoggedIn = computed(() => !!auth.token)
export const canManage = computed(() => ['manager', 'owner'].includes(auth.role))
export const isOwner = computed(() => auth.role === 'owner')

/**
 * Area of responsibility, mirroring the server.
 *
 * Managers and owners cover everything by rank; a receptionist has whatever an
 * owner granted them. The server is what actually enforces this — the copy
 * here only decides what to show.
 */
const FULL_ACCESS_ROLES = ['manager', 'owner']

/** Human-readable role names. */
const ROLE_LABELS = {
    receptionist: 'Receptionist',
    manager: 'Manager',
    owner: 'Owner',
}

export const CAPABILITY_LABELS = {
    floor: 'Dashboard',
    canteen: 'Canteen',
}
export const ALL_CAPABILITIES = ['floor', 'canteen']
export const capabilityLabel = (area) => CAPABILITY_LABELS[area] || area
export const roleLabel = (role) => ROLE_LABELS[role] || role || ''

export const can = (area) =>
    FULL_ACCESS_ROLES.includes(auth.role) || auth.capabilities.includes(area)
export const canFloor = computed(() => can('floor'))
export const canCanteen = computed(() => can('canteen'))

/** Where this role belongs when they sign in or hit a page they can't open. */
export const homeRoute = computed(() => {
    if (auth.role === 'owner') return '/overview'
    if (!can('floor') && can('canteen')) return '/canteen'
    return '/dashboard'
})

export async function login(username, password) {
    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Login failed')
    auth.token = data.token
    auth.role = data.role
    auth.username = data.username
    auth.capabilities = data.capabilities || []
    localStorage.setItem('ls_token', data.token)
    localStorage.setItem('ls_role', data.role)
    localStorage.setItem('ls_user', data.username)
    localStorage.setItem('ls_caps', auth.capabilities.join(','))
}

export function logout() {
    auth.token = ''
    auth.role = ''
    auth.username = ''
    auth.capabilities = []
    localStorage.removeItem('ls_token')
    localStorage.removeItem('ls_role')
    localStorage.removeItem('ls_user')
    localStorage.removeItem('ls_caps')
    window.location.href = '/login'
}

// Drop-in replacement for authFetch() on API calls: attaches the token,
// and boots the user to /login when the shift token expires (401).
export async function authFetch(url, options = {}) {
    const branchId = localStorage.getItem('baize_branch')
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${auth.token}`,
            // Tells the backend which branch this request targets (scoping). A
            // reconciliation "All branches" view clears it so the server combines.
            ...(branchId ? { 'X-Branch': branchId } : {}),
        },
    })
    if (res.status === 401) {
        logout()
        throw new Error('Session expired')
    }
    return res
}