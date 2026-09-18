import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API = import.meta.env.VITE_API_URL || ''
const KEY = 'admin_token'

/**
 * Admin session + a thin typed client for the vendor API. The session is a
 * short-lived JWT (from /api/admin/login) — the master token is never stored.
 * Every call carries the Bearer token; a 401 logs out and surfaces a message.
 */
export const useAdmin = defineStore('admin', () => {
  const token = ref(localStorage.getItem(KEY) || '')
  const isAuthed = computed(() => !!token.value)

  function setToken(t) {
    token.value = t || ''
    if (t) localStorage.setItem(KEY, t)
    else localStorage.removeItem(KEY)
  }
  function logout() { setToken('') }

  async function api(path, { method = 'GET', body } = {}) {
    const res = await fetch(`${API}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
    if (res.status === 401) { logout(); throw new Error('Session expired — please sign in again.') }
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
    return data
  }

  async function login(masterToken) {
    const res = await fetch(`${API}/api/admin/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: masterToken }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.error || 'Login failed.')
    setToken(data.token)
    return data
  }

  const qs = (params) => {
    const p = new URLSearchParams(Object.entries(params || {}).filter(([, v]) => v !== '' && v != null))
    const s = p.toString()
    return s ? `?${s}` : ''
  }

  return {
    token, isAuthed, setToken, logout, login,
    stats: () => api('/api/admin/stats'),
    clubs: (params) => api(`/api/admin/clubs${qs(params)}`),
    club: (uuid) => api(`/api/admin/clubs/${uuid}`),
    editClub: (uuid, body) => api(`/api/admin/clubs/${uuid}`, { method: 'PATCH', body }),
    issue: (body) => api('/api/admin/issue', { method: 'POST', body }),
    licenses: (params) => api(`/api/admin/licenses${qs(params)}`),
    revoke: (id) => api(`/api/admin/licenses/${id}/revoke`, { method: 'POST' }),
    unrevoke: (id) => api(`/api/admin/licenses/${id}/unrevoke`, { method: 'POST' }),
    renew: (id, days) => api(`/api/admin/licenses/${id}/renew`, { method: 'POST', body: { days } }),
    addDevice: (body) => api('/api/admin/devices', { method: 'POST', body }),
    removeDevice: (id) => api(`/api/admin/devices/${id}`, { method: 'DELETE' }),
    events: (params) => api(`/api/admin/events${qs(params)}`),
    branches: (uuid) => api(`/api/admin/clubs/${uuid}/branches`),
    registerBranch: (uuid, body) => api(`/api/admin/clubs/${uuid}/branches`, { method: 'POST', body }),
    updateBranch: (id, body) => api(`/api/admin/branches/${id}`, { method: 'PATCH', body }),
    mintBranch: (id, body) => api(`/api/admin/branches/${id}/mint`, { method: 'POST', body }),
    revokeBranch: (id, unrevoke = false) => api(`/api/admin/branches/${id}/revoke`, { method: 'POST', body: { unrevoke } }),
  }
})