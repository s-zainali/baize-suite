<template>
    <header class="left-0 z-50 -mr-6 -ml-6 mb-6 flex flex-row flex-wrap items-center justify-between gap-4 p-6 pb-4"
        :class="isOverview ? 'bg-neutral-950' : 'bg-slate-900'">

        <div class="flex min-w-0 items-center gap-3">
            <!-- Opens the nav drawer. Mobile only — on desktop the sidebar is
                 always there, so a button to reveal it would do nothing. -->
            <button @click="drawerOpen = true" aria-label="Open menu"
                class="flex h-9 w-9 shrink-0 cursor-pointer flex-col items-center justify-center gap-[3px] rounded-xl border border-slate-700 bg-slate-800 text-slate-300 md:hidden">
                <span class="block h-[2px] w-4 rounded bg-current" />
                <span class="block h-[2px] w-4 rounded bg-current" />
                <span class="block h-[2px] w-4 rounded bg-current" />
            </button>

            <img v-if="page.icon" :src="page.icon" alt="" class="hidden h-9 shrink-0 sm:inline" />
            <div class="min-w-0">
                <h1 class="truncate text-3xl font-black tracking-tight text-white">{{ page.title }}</h1>
                <p v-if="subtitle" class="mt-0.5 truncate text-xs text-slate-500">{{ subtitle }}</p>
            </div>
        </div>

        <div class="flex flex-grow flex-wrap items-center justify-end gap-2">
            <!-- Page-specific controls: a tab switch, a filter button, a clock. -->
            <SyncIndicator />
            <slot name="controls" />

            <button v-if="isBills" @click="emit('activate-modal', 'refresh')" :disabled="refreshing"
                class="cursor-pointer rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 transition-all hover:bg-slate-700 hover:text-white disabled:opacity-50">
                {{ refreshing ? 'Refreshing…' : 'Refresh' }}
            </button>


            <button v-if="isCanteen && lowStock.length" @click="emit('activate-modal', 'lowStock')"
                class="cursor-pointer rounded-xl border border-amber-600/40 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-400 transition-all hover:bg-amber-500/20">
                Low Stock ⚠ {{ lowStock.length }}
            </button>
            <button v-if="isDashboard && canFloor" @click="emit('activate-modal', 'khata')"
                class="cursor-pointer rounded-xl border border-amber-600/40 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-400 transition-all hover:bg-amber-500/20">
                Khata Book
            </button>
            <div v-if="isCanteen || isDashboard" class="flex justify-end items-center gap-2">
                <!-- Label Text -->
                <span class="text-xs uppercase font-bold text-slate-400">
                    View Active Bills
                </span>

                <!-- Toggle Button Track -->
                <button type="button" role="switch" :aria-checked="showBills" @click="emit('toggle-bills')"
                    class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg flex px-0.5  items-center transition-colors duration-300 ease-in-out  focus:outline-none"
                    :class="!showBills ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                    <!-- Sliding Knob -->
                    <span
                        class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                        :class="showBills ? 'translate-x-5' : 'translate-x-0'" />
                </button>
            </div>
        </div>
    </header>
</template>

<script setup>
/**
 * The page bar: what you're looking at, and the controls for it.
 *
 * Navigation moved to Sidebar.vue when the destination list outgrew a single
 * row. This keeps the same props the pages already pass, so nothing had to
 * change on their side — the buttons simply live in the sidebar now.
 */
import { computed } from 'vue'
import { drawerOpen } from '@/composables/useSidebar.js'
import SyncIndicator from './SyncIndicator.vue'

const props = defineProps({
    // Which page is wearing the bar. Kept from the previous header so existing
    // pages need no edit.
    isDashboard: { type: Boolean, default: false },
    isCanteen: { type: Boolean, default: false },
    isBills: { type: Boolean, default: false },
    isLogs: { type: Boolean, default: false },
    isInsights: { type: Boolean, default: false },
    isOverview: { type: Boolean, default: false },
    /** Overrides the derived title, for a page that isn't in the list. */
    showBills: { type: Boolean, default: true },
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    lowStock: { type: Array, default: () => [] },
    refreshing: { type: Boolean, default: false },
})

import { canFloor } from '@/Auth.js'

const emit = defineEmits(['activate-modal', 'toggle-bills'])

const page = computed(() => {
    if (props.title) return { title: props.title, icon: '' }
    if (props.isCanteen) return { title: 'Canteen', icon: '/snack.png' }
    if (props.isBills) return { title: 'Active Bills', icon: '' }
    if (props.isLogs) return { title: 'Activity Log', icon: '' }
    if (props.isInsights) return { title: 'Analytics', icon: '' }
    if (props.isOverview) return { title: 'Overview', icon: '' }
    return { title: 'Dashboard', icon: '/billiards.png' }
})
</script>