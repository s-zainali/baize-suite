<template>
    <!-- The way in on mobile. It used to live in the page header; with that
         gone the drawer would have had no opener at all. Floating rather than
         per-page, so it exists on every screen without each one wiring it. -->

    <!-- Backdrop, mobile only. The drawer is an overlay there, not a column. -->
    <div v-if="drawerOpen" @click="drawerOpen = false"
        class="fixed inset-0 z-400 bg-slate-950/70 backdrop-blur-sm md:hidden" />

    <aside class="fixed top-0 left-0 z-500 flex h-[100dvh] flex-col border-r  transition-[width,transform] duration-200"
        :class="[
            collapsed ? 'w-15' : 'w-60',
            drawerOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
            isOverview ? 'border-neutral-800 bg-black' : 'border-slate-800 bg-slate-950'
        ]">

        <!-- Wordmark -->
        <div class="flex h-16 shrink-0 items-center gap-3 border-b px-4 relative"
            :class="isOverview ? 'border-neutral-800' : 'border-slate-800'">
            <img src="/baize_logo.png" alt="" class=" w-10 shrink-0" />
            <img v-if="!collapsed" src="/baize_logo_text.png" alt="" class="h-6">
        </div>

        <!-- Navigation -->
        <BranchPicker v-if="!collapsed" :isOverview="isOverview" class="mt-4 mx-4" />

        <nav class="min-h-0 flex-1 overflow-y-auto py-3 nav-scroll flex flex-col gap-2"
            :class="collapsed ? 'items-center' : ''">
            <template v-for="group in groups" :key="group.name">
                <p v-if="!collapsed && group.items.length"
                    class="px-4 pt-3 pb-1.5 text-[9px] font-black uppercase tracking-widest text-slate-600">
                    {{ group.name }}
                </p>
                <div v-else-if="group.items.length" class="mx-4 my-2 border-t"
                    :class="isOverview ? 'border-neutral-800' : 'border-slate-800'" />

                <RouterLink v-for="item in group.items" :key="item.to" :to="item.to" @click="drawerOpen = false"
                    :title="collapsed ? item.label : ''"
                    class="flex items-center gap-3 rounded-xl text-xs font-bold transition-colors p-1" :class="isActive(item)
                        ? isOverview
                            ? 'bg-neutral-800 text-neutral-200'
                            : 'bg-slate-600/30 text-slate-300'
                        : isOverview
                            ? 'text-neutral-400 hover:bg-neutral-900 hover:text-white'
                            : 'text-slate-400 hover:bg-slate-900 hover:text-white',
                        collapsed ? 'mx-0 w-fit' : 'mx-2'">
                    <span class="p-1.5 rounded-lg shrink-0 text-center text-base leading-none"
                        :class="isOverview ? 'bg-neutral-800' : 'bg-slate-800'">
                        <ColorPng :url="item.icon" :color="'#CBD5E1'" />
                    </span>
                    <span v-if="!collapsed" class="truncate text-sm">{{ item.label }}</span>
                    <span v-if="!collapsed && item.badge"
                        class="ml-auto rounded-md bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-black text-amber-400">
                        {{ item.badge }}
                    </span>
                    <!-- Collapsed, a badge has no room for a number, so it
                         becomes a dot that still says "look here". -->
                    <span v-else-if="collapsed && item.badge"
                        class="absolute ml-6 -mt-4 h-2 w-2 rounded-full bg-amber-400" />
                </RouterLink>
            </template>

            <!-- Actions that open a modal rather than navigate. -->
            <template v-if="actions.length">
                <p v-if="!collapsed"
                    class="px-4 pt-4 pb-1.5 text-[9px] font-black uppercase tracking-widest text-slate-600">
                    Manage
                </p>
                <div v-else class="mx-4 my-2 border-t"
                    :class="isOverview ? 'border-neutral-800' : 'border-slate-800'" />
                <button v-for="action in actions" :key="action.modal"
                    @click="requestModal(action.modal); drawerOpen = false" :title="collapsed ? action.label : ''"
                    class="flex w-[calc(100%-1rem)] cursor-pointer items-center gap-3 rounded-xl p-1 text-xs font-bold text-slate-400 transition-colors hover:bg-slate-900 hover:text-white"
                    :class="collapsed ? 'mx-0 w-fit' : 'mx-2'"">
                    <span class=" p-1.5 shrink-0 text-center text-base leading-none bg-slate-800 rounded-lg">
                        <ColorPng :url="action.icon" :color="'#CBD5E1'" />
                    </span>
                    <span v-if="!collapsed" class="truncate text-sm">{{ action.label }}</span>
                </button>
            </template>
        </nav>

        <!-- Primary action, pinned so it never scrolls out of reach -->
        <div v-if="addButton" class="shrink-0 px-2 pb-2">
            <button @click="requestModal(addButton.modal); drawerOpen = false" :title="collapsed ? addButton.label : ''"
                class="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-3 py-2.5 text-xs font-black tracking-wider text-white">
                <span class="text-base leading-none">+</span>
                <span v-if="!collapsed" class="truncate">{{ addButton.short }}</span>
            </button>
        </div>

        <!-- Account. The popover is fixed-position rather than absolute:
             anchored inside a 4.5rem rail it would be clipped, and opening
             downward from the bottom of the screen put it off-screen. -->
        <div class="shrink-0 border-t p-2" :class="isOverview ? 'border-neutral-800' : 'border-slate-800'">
            <div class="flex gap-1" :class="collapsed ? 'flex-col items-stretch' : 'items-center'">
                <button ref="accountButton" @click="accountOpen = !accountOpen" :aria-expanded="accountOpen"
                    aria-haspopup="menu" :title="collapsed ? auth.username : ''"
                    class="flex min-w-0 flex-1 cursor-pointer items-center gap-2.5 rounded-xl py-2 text-left transition-colors"
                    :class="[
                        (collapsed ? 'justify-center px-0' : 'px-2'),
                        (accountOpen ? isOverview ? 'bg-neutral-900' : 'bg-slate-900' : ''),
                        (isOverview ? 'hover:bg-neutral-900' : '')]">
                    <span
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600/20 text-xs font-black text-indigo-300">
                        {{ initials }}
                    </span>
                    <span v-if="!collapsed" class="min-w-0 flex-1">
                        <span class="block truncate text-xs font-bold text-white">{{ auth.username }}</span>
                        <span class="block truncate text-[10px] text-slate-500">{{ roleLabel(auth.role) }}</span>
                    </span>
                    <span v-if="!collapsed" class="shrink-0 text-[10px] text-slate-600">▾</span>
                </button>

                <button @click="toggleSidebar" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
                    class="hidden h-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-900 hover:text-white md:flex"
                    :class="collapsed ? 'w-full' : 'w-8'">
                    {{ collapsed ? '›' : '‹' }}
                </button>
            </div>
        </div>
    </aside>

    <!-- Rendered outside the rail so its width is its own, not the rail's. -->
    <Teleport to="body">
        <div v-if="accountOpen" class="fixed inset-0 z-600" @click="accountOpen = false" />
        <div v-if="accountOpen" ref="accountMenu" role="menu"
            class="fixed z-610 w-56 overflow-hidden rounded-2xl border  shadow-2xl mb-2"
            :class="isOverview ? 'border-neutral-800 bg-neutral-950' : 'border-slate-700 bg-slate-900'"
            :style="menuPosition">
            <div class="px-4 py-3 border-b" :class="isOverview ? 'border-neutral-800' : 'border-slate-800'">
                <p class="text-lg font-bold text-white truncate first-letter:uppercase">{{ auth.username }}</p>
                <span class="inline-block mt-1 text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md"
                    :class="roleBadgeClass">
                    {{ roleLabel(auth.role) }}
                </span>
            </div>

            <RouterLink v-if="canManage" :to="'/manage'" @click="accountOpen = false"
                class="block w-full cursor-pointer px-4 py-2.5 text-left text-xs font-bold text-slate-300 transition-colors  hover:text-white"
                :class="isOverview ? 'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                Manage membership
            </RouterLink>

            <button v-if="isOwner" @click="activeModal = 'manageStaff'; accountOpen = false"
                class="block w-full cursor-pointer px-4 py-2.5 text-left text-xs font-bold text-slate-300 transition-colors  hover:text-white"
                :class="isOverview ? 'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                Manage Staff
            </button>

            <button @click="signOut"
                class="block w-full cursor-pointer border-t px-4 py-2.5 text-left text-xs font-bold text-rose-400 transition-colors hover:bg-rose-500/10"
                :class="isOverview ? 'border-neutral-800 hover:bg-neutral-900/10' : 'border-slate-800 hover:bg-slate-800/10'">
                Sign Out
            </button>
        </div>
    </Teleport>
    <ManageUsersModal v-if="activeModal === 'manageStaff'" @close-modal="activeModal = 'none'" />
</template>

<script setup>
/**
 * The app's navigation.
 *
 * Split out of the header because the destination list outgrew a single row —
 * a wrapping line of nine buttons is harder to scan than a column, and gets
 * worse with every page added.
 *
 * The active page comes from the route rather than a prop, so this mounts once
 * in the shell and every page gets it without wiring anything.
 */
import { ref, computed, onUnmounted, watch, nextTick } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { auth, canCanteen, canFloor, canManage, isOwner, roleLabel, logout } from '@/Auth.js'
import { branchHasFeature, loadBranches } from '@/composables/useBranch.js'
import BranchPicker from '@/components/BranchPicker.vue'
import { onMounted } from 'vue'
onMounted(loadBranches)
import { collapsed, drawerOpen, toggleSidebar } from '@/composables/useSidebar.js'
import { requestModal } from '@/composables/useModals.js'
import ManageUsersModal from './Modals/ManageUsersModal.vue'
import ColorPng from './ColorPng.vue'

const activeModal = ref('')
const props = defineProps({
    /** Low-stock items, badged on the canteen link. */
    isOverview: { type: Boolean, default: false },
    lowStock: { type: Array, default: () => [] },
})

const route = useRoute()

const roleBadgeClass = computed(() => ({
    owner: 'bg-amber-500/10 text-amber-400',
    manager: 'bg-indigo-500/10 text-indigo-400',
    receptionist: 'bg-sky-500/10 text-sky-400',
}[auth.role] || 'bg-slate-800 text-slate-400'))

const groups = computed(() => [
    {
        name: 'Floor',
        items: [
            ...(canFloor.value ? [{ to: '/dashboard', label: 'Dashboard', icon: '/billiard.png' }] : []),
            ...(canCanteen.value && branchHasFeature('canteen') ? [{
                to: '/canteen', label: 'Canteen', icon: '/school.png',
                badge: props.lowStock.length || null,
            }] : []),
            ...(canFloor.value || canCanteen.value ? [{ to: '/active-bills', label: 'Active Bills', icon: '/bill.png' }] : []),
        ],
    },
    {
        name: 'Records',
        items: [
            ...(canManage.value ? [{ to: '/logs', label: 'Activity Log', icon: '/log.png' }] : []),
            ...(canManage.value && branchHasFeature('insights') ? [{ to: '/insights', label: 'Analytics', icon: '/dashboard.png' }] : []),
            ...(isOwner.value ? [{ to: '/overview', label: 'Overview', icon: '/eye.png' }] : []),
        ],
    },
])

const actions = computed(() => [
    // Rates configure the tables, so the button only makes sense on the floor.
    // Elsewhere it would open a dialog about a screen you aren't looking at.
    ...(canManage.value && route.path.startsWith('/dashboard')
        ? [{ modal: 'rates', label: 'Set Rates', icon: '/money-bag.png' }]
        : []),
])

/**
 * The one primary action, which depends on where you are: a station on the
 * dashboard, an item in the canteen. Nowhere else has one.
 */
const addButton = computed(() => {
    if (!canManage.value) return null
    if (route.path.startsWith('/canteen')) return { modal: 'addItem', label: 'Add Item', short: 'ADD ITEM' }
    if (route.path.startsWith('/dashboard')) return { modal: 'addTable', label: 'Add Station', short: 'ADD STATION' }
    return null
})

// ── account menu ──────────────────────────────────────────────────────────
const accountOpen = ref(false)
const accountButton = ref(null)
const menuPosition = ref({})

const initials = computed(() =>
    (auth.username || '?').trim().slice(0, 2).toUpperCase(),
)

/**
 * Position the popover against the button, opening UPWARD.
 *
 * It sits at the bottom of a full-height sidebar, so a downward menu would
 * open into the edge of the screen. Measured rather than assumed, because the
 * button moves when the rail collapses.
 */
async function placeMenu() {
    await nextTick()
    const el = accountButton.value
    if (!el) return
    const box = el.getBoundingClientRect()
    menuPosition.value = {
        left: `${Math.max(8, box.left)}px`,
        bottom: `${Math.max(8, window.innerHeight - box.top + 8)}px`,
    }
}

watch(accountOpen, (open) => { if (open) placeMenu() })
// Collapsing the rail moves the button, so a menu left open would detach.
watch(collapsed, () => { accountOpen.value = false })

function signOut() {
    accountOpen.value = false
    logout()
}

function onKeydown(event) {
    if (event.key === 'Escape') accountOpen.value = false
}
window.addEventListener('keydown', onKeydown)
window.addEventListener('resize', () => { accountOpen.value = false })
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

/** Highlight the current page. `/logs?tab=canteen` still counts as the log. */
const isActive = (item) => route.path === item.to || route.path.startsWith(item.to + '/')
</script>

<style scoped>
.nav-scroll::-webkit-scrollbar {
    width: 6px;
}

.nav-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.nav-scroll::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 3px;
}

.nav-scroll {
    scrollbar-width: thin;
    scrollbar-color: #1e293b transparent;
}
</style>