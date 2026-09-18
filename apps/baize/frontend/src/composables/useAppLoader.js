import { ref } from 'vue'
import { authFetch, API_URL, canFloor, canCanteen, canManage } from '@/Auth.js'
import { loadSettings } from './useSettings.js'
import { loadTableTypes } from './useTableTypes.js'
import * as canteenApi from '@/canteen/api.js'

/**
 * One-time boot for the signed-in staff app.
 *
 * The whole point of the loader is that the app is butter-smooth *after* it —
 * so we spend the initial wait warming everything a page could need, then reveal
 * the app in one go. Three kinds of work happen here:
 *
 *   1. Data — settings, floor state, the canteen menu, and the ledger, pulled
 *      into their shared stores so pages render from memory instead of a cold
 *      fetch. (KeepAlive in App.vue then keeps them mounted, so revisiting a
 *      page is instant.)
 *   2. Code — the lazily-split route chunks (logs, insights, active bills) are
 *      fetched now, so the first visit doesn't stall on a download.
 *   3. Artwork — every menu image is decoded up front, so nothing pops in.
 *
 * Same module-scope reactive "store" pattern as useSettings / useLedger — no
 * extra dependency. Nothing here may throw: a broken image, an offline endpoint
 * or one the current role can't reach must still let boot finish.
 */

const progress = ref(0)      // 0-100
const ready = ref(false)     // true once the app may be shown
const label = ref('Starting up')
let started = false

function collectImageUrls(node, out) {
    if (!node || typeof node !== 'object') return
    if (Array.isArray(node)) {
        for (const v of node) collectImageUrls(v, out)
        return
    }
    for (const [k, v] of Object.entries(node)) {
        if ((k === 'imgUrl' || k === 'img_url') && typeof v === 'string' && v) {
            out.add(v.startsWith('http') ? v : `${API_URL}${v}`)
        } else if (v && typeof v === 'object') {
            collectImageUrls(v, out)
        }
    }
}

function preloadImage(url) {
    return new Promise((resolve) => {
        const img = new Image()
        img.onload = img.onerror = () => resolve()   // never reject - a 404 mustn't wedge boot
        img.decoding = 'async'                        // decode off the main thread where supported
        img.src = url
        if (img.decode) img.decode().then(resolve).catch(() => resolve())
    })
}

async function warm(path) {
    try {
        const res = await authFetch(`${API_URL}${path}`)
        return res.ok ? await res.json() : null
    } catch {
        return null
    }
}

/** Fetch the code-split route bundles now so first navigation is instant. */
function prefetchRoutes() {
    return Promise.allSettled([
        import('@/pages/LogsPage.vue'),
        import('@/pages/InsightsPage.vue'),
        import('@/pages/ActiveBillsPage.vue'),
    ])
}

export async function boot() {
    if (started) return
    started = true
    ready.value = false
    progress.value = 0
    label.value = 'Starting up'

    // Captured so its artwork can be preloaded after the data phase.
    let menu = null

    // Only the work this role can actually use - a canteen-only till has no
    // floor state to fetch, a receptionist has no ledger, and so on. Skipping
    // them avoids pointless 403s and a slower boot.
    const tasks = [
        { label: 'Preparing', run: () => (document.fonts ? document.fonts.ready : Promise.resolve()) },
        { label: 'Loading settings', run: () => loadSettings() },
    ]
    if (canFloor.value) tasks.push({ label: 'Loading the floor', run: () => warm('/state') })
    if (canFloor.value) tasks.push({ label: 'Loading stations', run: () => loadTableTypes() })  // station type registry — pages render from this
    if (canCanteen.value) tasks.push({ label: 'Loading the canteen', run: async () => { menu = await canteenApi.fetchMenu() } })
    tasks.push({ label: 'Preparing pages', run: () => prefetchRoutes() })

    // Data + code fill 0 -> 55%; artwork takes 55 -> 98%; then a beat at 100%.
    const span = 55
    for (let i = 0; i < tasks.length; i++) {
        label.value = tasks[i].label
        try { await tasks[i].run() } catch { /* resilient: keep going */ }
        progress.value = Math.round(((i + 1) / tasks.length) * span)
    }

    label.value = 'Loading artwork'
    const urls = new Set()
    collectImageUrls(menu, urls)
    const list = [...urls]
    if (list.length) {
        let done = 0
        await Promise.all(list.map((u) => preloadImage(u).then(() => {
            done += 1
            progress.value = Math.min(98, Math.round(span + (done / list.length) * (98 - span)))
        })))
    } else {
        progress.value = 98
    }

    label.value = 'Ready'
    progress.value = 100
    await new Promise((r) => setTimeout(r, 320))   // let the ring visibly finish
    ready.value = true
}

export function resetLoader() {
    started = false
    ready.value = false
    progress.value = 0
    label.value = 'Starting up'
}

export { progress, ready, label }