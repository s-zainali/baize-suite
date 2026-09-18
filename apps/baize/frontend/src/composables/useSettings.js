import { reactive } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'

/**
 * Global (per-install) UI preferences, mirrored from the backend so a choice
 * like "show bills on checkout" or "pin the summary strip" survives a refresh
 * or a fresh session instead of resetting to its default every time.
 *
 * The values are shared across the app: any component can read the reactive
 * `settings` map, seed a local ref from `settingValue()` on mount, and persist
 * a change with `setSetting()`. The backend (/api/settings) owns the allowlist
 * of valid keys; the DEFAULTS here only cover the gap before the first load.
 */

const settings = reactive({})

const DEFAULTS = {
    dashboard_show_bills: true,   // pop the table receipt on checkout
    canteen_show_bills: true,     // pop the canteen receipt on checkout
    summary_sticky: false,        // pin the dashboard summary strip to the top
}

/** Pull the current values from the server. Cheap; call it on page mount. */
export async function loadSettings() {
    try {
        const res = await authFetch(`${API_URL}/settings`)
        if (res.ok) {
            const data = await res.json()
            Object.assign(settings, DEFAULTS, data.settings || {})
        }
    } catch {
        // Offline or not yet loaded — callers still get defaults via settingValue.
    }
    return settings
}

/** Current value of a setting, falling back to its default if unseen. */
export function settingValue(name, fallback) {
    if (name in settings) return settings[name]
    if (name in DEFAULTS) return DEFAULTS[name]
    return fallback ?? false
}

/** Persist a setting. Updates the local mirror immediately, then writes through. */
export async function setSetting(name, value) {
    settings[name] = value   // optimistic: the UI reflects the change at once
    try {
        await authFetch(`${API_URL}/settings/${name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value }),
        })
    } catch {
        // Left optimistic; the next loadSettings() re-syncs with the server.
    }
}

export { settings }