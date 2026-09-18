// Branch context shared across the app. The selected branch id is persisted so
// authFetch can attach it as the X-Branch header (see Auth.js). Switching a
// branch reloads so every view refetches under the new scope.
import { ref, computed } from 'vue'
import { API_URL, authFetch } from '@/Auth.js'

const KEY = 'baize_branch'

export const branches = ref([])
export const canCombine = ref(false)
export const currentBranchId = ref(localStorage.getItem(KEY) ? Number(localStorage.getItem(KEY)) : null)
export const currentBranch = computed(() => branches.value.find((b) => b.id === currentBranchId.value) || null)
export const multiBranch = computed(() => branches.value.length > 1)
// Add-on modules licensed for the CURRENTLY SELECTED branch (per-branch gating).
// Falls back to an empty set until branches load.
export const currentFeatures = computed(() => currentBranch.value?.features || [])
export function branchHasFeature(key) { return currentFeatures.value.includes(key) }

export async function loadBranches() {
    try {
        const r = await authFetch(`${API_URL}/branches`)
        if (!r.ok) return
        const d = await r.json()
        branches.value = d.branches || []
        canCombine.value = !!d.canCombine
        // Adopt the server's selected branch if we don't have a valid one yet.
        if (!currentBranchId.value || !branches.value.some((b) => b.id === currentBranchId.value)) {
            setBranch(d.selected ?? branches.value[0]?.id ?? null, false)
        }
    } catch { /* ignore — single-branch installs just have one */ }
}

export function setBranch(id, reload = true) {
    currentBranchId.value = id
    if (id == null) localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, String(id))
    if (reload) window.location.reload()   // simplest correct refetch under the new scope
}

export async function createBranch(name) {
    const r = await authFetch(`${API_URL}/branches`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
    })
    if (!r.ok) {
        const e = await r.json().catch(() => ({}))
        throw new Error(e.message || 'Could not create the branch.')
    }
    await loadBranches()
    return r.json()
}