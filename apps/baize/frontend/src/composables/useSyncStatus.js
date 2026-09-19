// Polls the local install's /sync/status so the UI can show a live health dot.
// Inert on a local-only install (nothing to sync) — it simply reports mode.
import { ref, onMounted, onUnmounted } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

export function useSyncStatus(intervalMs = 10000) {
    const status = ref(null)
    const loading = ref(true)
    let timer = null

    async function refresh() {
        try {
            const res = await authFetch(`${API_URL}/sync/status`)
            status.value = await res.json()
        } catch {
            // If even the status call fails, we're effectively offline.
            status.value = { ...(status.value || { mode: 'hybrid', syncing: true }), online: false }
        } finally {
            loading.value = false
        }
    }

    onMounted(() => { refresh(); timer = setInterval(refresh, intervalMs) })
    onUnmounted(() => timer && clearInterval(timer))
    return { status, loading, refresh }
}