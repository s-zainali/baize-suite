import { reactive, computed } from 'vue'

/**
 * Shared table-type registry: labels, colours, badges and which renderer a type
 * uses — all data-driven from the backend, so nothing is hardcoded twice.
 *
 * This module has NO auth/network coupling. Each app injects HOW to fetch its
 * types (with its own base URL + headers) via `configureTableTypes`, and each
 * app maps renderer names to ITS OWN components (the club app → interactive
 * cards; the customer app → the read-only TableVisual). Only the metadata is
 * shared here.
 */
const types = reactive([])
let loaded = false
let _fetchTypes = null   // () => Promise<Array>, provided by the host app

export function configureTableTypes({ fetchTypes }) {
    _fetchTypes = fetchTypes
}

export async function loadTableTypes(force = false) {
    if ((loaded && !force) || !_fetchTypes) return types
    try {
        const data = await _fetchTypes()
        if (Array.isArray(data)) {
            types.splice(0, types.length, ...data)
            if (data.length) loaded = true
        }
    } catch { /* offline — keep what we have */ }
    return types
}

export const metaByKey = computed(() => Object.fromEntries(types.map((t) => [t.key, t])))
export const typeLabel = (k) => metaByKey.value[k]?.label || k
export const typeColor = (k) => metaByKey.value[k]?.color || '#818cf8'
export const typeBadge = (k) => metaByKey.value[k]?.badge || '?'
export const rendererFor = (k) => metaByKey.value[k]?.renderer || 'pool'

export const entitledTypes = computed(() => types.filter((t) => t.entitled !== false))
export const typeEntitled = (k) => metaByKey.value[k]?.entitled !== false
export const tableTypeOptions = computed(() => entitledTypes.value.map((t) => ({ value: t.key, label: t.label })))

export { types }