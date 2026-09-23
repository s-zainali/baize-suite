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

        <div class=" relative flex flex-grow flex-wrap items-center justify-end gap-2">
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
            <button class="cursor-pointer" @click="showSettings = !showSettings">
                <svg fill="#CBD5E1" viewBox="0 0 24 24" height="25px" width="25px" xmlns="http://www.w3.org/2000/svg" id="settings"
                    class="icon glyph" stroke="#CBD5E1">
                    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
                    <g id="SVGRepo_iconCarrier">
                        <path
                            d="M20.89,9.78h-.65a1.16,1.16,0,0,1-1-.74V9a1.13,1.13,0,0,1,.22-1.26l.46-.46a1.13,1.13,0,0,0,0-1.58L18.29,4.14a1.13,1.13,0,0,0-1.58,0l-.46.46A1.13,1.13,0,0,1,15,4.82h0a1.16,1.16,0,0,1-.74-1V3.11A1.11,1.11,0,0,0,13.11,2H10.89A1.11,1.11,0,0,0,9.78,3.11v.65a1.16,1.16,0,0,1-.74,1H9A1.13,1.13,0,0,1,7.75,4.6l-.46-.46a1.13,1.13,0,0,0-1.58,0L4.14,5.71a1.13,1.13,0,0,0,0,1.58l.46.46A1.13,1.13,0,0,1,4.82,9V9a1.16,1.16,0,0,1-1,.74H3.11A1.11,1.11,0,0,0,2,10.89v2.22a1.11,1.11,0,0,0,1.11,1.11h.65a1.16,1.16,0,0,1,1,.74v0a1.13,1.13,0,0,1-.22,1.26l-.46.46a1.13,1.13,0,0,0,0,1.58l1.57,1.57a1.13,1.13,0,0,0,1.58,0l.46-.46A1.13,1.13,0,0,1,9,19.18H9a1.16,1.16,0,0,1,.74,1v.65A1.11,1.11,0,0,0,10.89,22h2.22a1.11,1.11,0,0,0,1.11-1.11v-.65a1.16,1.16,0,0,1,.74-1h0a1.13,1.13,0,0,1,1.26.22l.46.46a1.13,1.13,0,0,0,1.58,0l1.57-1.57a1.13,1.13,0,0,0,0-1.58l-.46-.46A1.13,1.13,0,0,1,19.18,15v0a1.16,1.16,0,0,1,1-.74h.65A1.11,1.11,0,0,0,22,13.11V10.89A1.11,1.11,0,0,0,20.89,9.78ZM12,16a4,4,0,1,1,4-4A4,4,0,0,1,12,16Z">
                        </path>
                    </g>
                </svg>
            </button>
            <div v-if="showSettings" class="absolute z-100 shadow-xl top-10 bg-slate-800 border border-slate-700 p-4 rounded-2xl flex flex-col gap-2">
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
                <div v-if="isDashboard" class="flex justify-end items-center gap-2">
                    <span class="text-xs uppercase font-bold text-slate-400">
                        Small Stations
                    </span>

                    <!-- Toggle Button Track -->
                    <button type="button" role="switch" :aria-checked="showBills" @click="emit('toggle-station-size')"
                        class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-lg flex px-0.5  items-center transition-colors duration-300 ease-in-out  focus:outline-none"
                        :class="!smallStations ? 'bg-rose-600/70 hover:bg-rose-600' : 'bg-emerald-800 hover:bg-emerald-600'">
                        <!-- Sliding Knob -->
                        <span
                            class="pointer-events-none inline-block h-4 w-4 transform rounded-md bg-slate-100 shadow-md transition duration-300 ease-in-out"
                            :class="smallStations ? 'translate-x-5' : 'translate-x-0'" />
                    </button>
                </div>
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
import { computed, ref } from 'vue'
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
    smallStations: { type: Boolean, default: false },
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    lowStock: { type: Array, default: () => [] },
    refreshing: { type: Boolean, default: false },
})

import { canFloor } from '@/Auth.js'

const emit = defineEmits(['activate-modal', 'toggle-bills', 'toggle-station-size'])

const page = computed(() => {
    if (props.title) return { title: props.title, icon: '' }
    if (props.isCanteen) return { title: 'Canteen', icon: '/snack.png' }
    if (props.isBills) return { title: 'Active Bills', icon: '' }
    if (props.isLogs) return { title: 'Activity Log', icon: '' }
    if (props.isInsights) return { title: 'Analytics', icon: '' }
    if (props.isOverview) return { title: 'Overview', icon: '' }
    return { title: 'Dashboard', icon: '/billiards.png' }
})

const showSettings = ref(false)
</script>