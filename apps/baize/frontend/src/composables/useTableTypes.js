import { API_URL } from '@/Auth'
import { reactive, computed } from 'vue'
import PoolTable from '@/components/PoolTable.vue'
import ConsoleGame from '@/components/ConsoleGame.vue'
import Foosball from '@/components/Foosball.vue'


/**
 * The one place station types live on the frontend. Loaded from the backend
 * (/api/table-types, public) — so labels, colours, badges and which card renders
 * a type all come from the database, with nothing to keep in sync by hand.
 *
 * A plain relative fetch keeps this usable by both the staff and customer
 * bundles without dragging in either app's auth.
 */

const types = reactive([])            // [{ key, id, value, label, color, renderer, badge, sortOrder }]
let loaded = false

export async function loadTableTypes(force = false) {
    if (loaded && !force) return types
    try {
        // Send the selected branch so `entitled` reflects THIS branch's licence
        // (not the primary/first branch). Without it, a branch's own features
        // — e.g. PC — never light up its station types.
        const branchId = localStorage.getItem('baize_branch')
        const r = await fetch(API_URL + '/table-types', branchId ? { headers: { 'X-Branch': branchId } } : {})
        if (r.ok) {
            const data = await r.json()
            types.splice(0, types.length, ...data)
            // Only treat it as loaded once we actually have types. A blocked
            // (pre-activation) or empty response must stay retriable, or the app
            // renders every station with the default `pool` renderer forever.
            if (data.length) loaded = true
        }
    } catch { /* offline — keep whatever we have */ }
    return types
}
loadTableTypes()   // warm on first import

export const metaByKey = computed(() => Object.fromEntries(types.map((t) => [t.key, t])))

export const typeLabel = (k) => metaByKey.value[k]?.label || k
export const typeColor = (k) => metaByKey.value[k]?.color || '#818cf8'
export const typeBadge = (k) => metaByKey.value[k]?.badge || '?'
export const rendererFor = (k) => metaByKey.value[k]?.renderer || 'pool'

export const RENDERERS = { pool: PoolTable, playstation: ConsoleGame, xbox: ConsoleGame, pc: ConsoleGame, foosball: Foosball }
export const componentFor = (type) => RENDERERS[rendererFor(type)] || PoolTable

// Only station types the club's licence entitles (base types are always
// entitled; backend sets `entitled` per type). Pickers use these so unlicensed
// stations (e.g. Xbox, PS, Foosball, PC) don't even appear.
export const entitledTypes = computed(() => types.filter((t) => t.entitled !== false))
export const typeEntitled = (k) => (metaByKey.value[k]?.entitled !== false)
export const tableTypeOptions = computed(() => entitledTypes.value.map((t) => ({ value: t.key, label: t.label })))

export { types }