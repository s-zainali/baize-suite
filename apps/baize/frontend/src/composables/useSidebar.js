import { ref, computed, watch } from 'vue'

/**
 * Sidebar state, shared by the sidebar itself and the page shell that has to
 * make room for it.
 *
 * Collapsed state is remembered: on a counter tablet the staff will collapse it
 * once and expect it to stay that way through every shift.
 */
const STORE_KEY = 'ls_sidebar_collapsed'

export const collapsed = ref(localStorage.getItem(STORE_KEY) === '1')

watch(collapsed, (value) => {
    localStorage.setItem(STORE_KEY, value ? '1' : '0')
})

export const toggleSidebar = () => { collapsed.value = !collapsed.value }

/** Open state of the mobile drawer — separate, because it isn't remembered. */
export const drawerOpen = ref(false)

/**
 * Left padding the page content needs so it isn't hidden under the sidebar.
 * Only applies from `md` up; below that the sidebar is an overlay drawer.
 */
export const contentOffset = computed(() =>
    collapsed.value ? 'md:pl-15' : 'md:pl-60',
)

/**
 * The sidebar's width, published as a CSS variable.
 *
 * Modals are centred with flexbox inside a full-screen overlay, which means
 * "centre of the viewport" — visibly off to the left of the space the user is
 * actually looking at. They pad by this instead. A variable rather than an
 * import so a modal needs no wiring: they are scattered across pages and
 * several are third-party-shaped dialogs that shouldn't know the app's layout.
 */
const SIDEBAR_WIDTH = { expanded: '15rem', collapsed: '4.5rem' }

// The sidebar width plus a gutter, precomputed.
//
// This exists so a stylesheet never has to write calc(). In a Tailwind
// arbitrary value, `calc(var(--sidebar-w)+1rem)` is INVALID CSS — calc
// requires whitespace around the operator — and the browser silently drops
// the whole declaration. Doing the arithmetic here keeps the class a plain
// var() lookup that cannot be malformed.
const MODAL_INSET = { expanded: '16rem', collapsed: '5.5rem' }

function publishWidth(isCollapsed) {
    if (typeof document === 'undefined') return
    const key = isCollapsed ? 'collapsed' : 'expanded'
    const root = document.documentElement.style
    root.setProperty('--sidebar-w', SIDEBAR_WIDTH[key])
    root.setProperty('--modal-inset', MODAL_INSET[key])
}

publishWidth(collapsed.value)
watch(collapsed, publishWidth)
