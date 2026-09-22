// Customer session store — separate from src/Auth.js in every respect.
//
// Different storage keys, different token, different API base. A staff token
// and a customer token can never be mistaken for one another because nothing
// reads both: this file is not imported by the staff bundle, and src/Auth.js is
// not imported by this one.

import { reactive, computed } from 'vue'

export const CUSTOMER_API = import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api/customer`
    : '/api/customer'

// Deliberately NOT 'ls_token'. Sharing that key would let a stale staff session
// masquerade as a customer one (and vice versa) on a shared browser.
const TOKEN_KEY = 'ls_customer_token'
const PROFILE_KEY = 'ls_customer_profile'

function readProfile() {
    try {
        return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null')
    } catch {
        return null
    }
}

export const customer = reactive({
    token: localStorage.getItem(TOKEN_KEY) || '',
    profile: readProfile(),
})

export const isSignedIn = computed(() => !!customer.token)

export function setSession(token, profile) {
    customer.token = token
    customer.profile = profile
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}

export function signOut({ redirect = true } = {}) {
    customer.token = ''
    customer.profile = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(PROFILE_KEY)
    if (redirect) window.location.href = '/'
}

/**
 * POST helper that always yields a readable error.
 *
 * Calling .json() on an HTML error page throws a parse error that says nothing
 * useful, which is how a missing endpoint ends up looking like a dead button.
 */
export async function apiPost(path, body, { auth = false } = {}) {
    const headers = { 'Content-Type': 'application/json' }
    if (auth && customer.token) headers.Authorization = `Bearer ${customer.token}`

    const res = await fetch(`${CUSTOMER_API}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body || {}),
    })

    const text = await res.text()
    let data = {}
    try {
        data = text ? JSON.parse(text) : {}
    } catch {
        throw Object.assign(
            new Error(
                res.status === 404
                    ? `Endpoint ${path} not found — is the backend running the customer blueprint?`
                    : `Server returned ${res.status}`,
            ),
            { status: res.status },
        )
    }

    if (!res.ok) {
        throw Object.assign(new Error(data.error || `Request failed (${res.status})`), {
            status: res.status,
            field: data.field || '',
        })
    }
    return data
}

/**
 * Authenticated GET against the customer API.
 *
 * Every customer endpoint requires a token, so there's no branch here — the
 * earlier version tried to special-case a couple of paths, referenced the staff
 * `auth.token`, and returned nothing from either branch.
 */
export async function apiGet(path) {
    const res = await fetch(`${CUSTOMER_API}${path}`, {
        headers: customer.token ? { Authorization: `Bearer ${customer.token}` } : {},
    })
    if (res.status === 401) {
        signOut({ redirect: false })
        throw new Error('Session expired')
    }
    const text = await res.text()
    let data = {}
    try {
        data = text ? JSON.parse(text) : {}
    } catch {
        throw new Error(
            res.status === 404
                ? `Endpoint ${path} not found — is the backend running the customer blueprint?`
                : `Server returned ${res.status}`,
        )
    }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
    return data
}

export async function apiDelete(path) {
    const res = await fetch(`${CUSTOMER_API}${path}`, {
        method: 'DELETE',
        headers: customer.token ? { Authorization: `Bearer ${customer.token}` } : {},
    })
    if (res.status === 401) {
        signOut({ redirect: false })
        throw new Error('Session expired')
    }
    if (!res.ok) throw new Error(`Request failed (${res.status})`)
}