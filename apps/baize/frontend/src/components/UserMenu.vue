<template>
    <div ref="menuRoot" class="relative">
        <!-- Chip trigger -->
        <button type="button" @click="open = !open"
            class="flex items-center gap-2 pl-2 pr-4 py-1.5 rounded-xl border transition-all cursor-pointer" :class="open
                ? props.isOverview
                    ? 'border-neutral-600 bg-neutral-900'
                    : 'border-slate-600 bg-slate-900'
                : props.isOverview
                    ? 'border-neutral-700 hover:border-neutral-500'
                    : 'border-slate-700 hover:border-slate-500'">
            <span
                class="w-6 h-6 mr-1 rounded-lg bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-300 uppercase">
                {{ auth.username.slice(0, 2) }}
            </span>
            <span class="text-xs font-bold text-slate-200 max-w-[90px] truncate first-letter:uppercase">{{ auth.username
                }}</span>
            <svg class="w-3 h-3 text-slate-500 transition-transform duration-200" :class="open ? 'rotate-180' : ''"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
        </button>

        <!-- Menu panel -->
        <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
            <div v-if="open"
                :class="props.isOverview ? ' bg-neutral-900 border border-neutral-700 rounded-2xl shadow-2xl shadow-neutral-950/80' : ' bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-slate-950/80'"
                class="absolute right-0 top-full mt-2 z-40 w-52 overflow-hidden">
                <!-- identity -->
                <div class="px-4 py-3 border-b" :class="isOverview ? 'border-neutral-800' : 'border-slate-800'">
                    <p class="text-lg font-bold text-white truncate first-letter:uppercase">{{ auth.username }}</p>
                    <span
                        class="inline-block mt-1 text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md"
                        :class="roleBadgeClass">
                        {{ roleLabel(auth.role) }}
                    </span>
                </div>

                <div class="p-1">
                    <button v-if="isOwner && !isOverview" type="button" @click="open = false; emit('manage-users')"
                        class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold text-slate-300  hover:text-white transition-colors cursor-pointer text-left"
                        :class="props.isOverview ? 'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                        <span class="text-sm">👥</span> Manage Users
                    </button>
                    <RouterLink v-if="isOwner && !isOverview" to="/overview"
                        class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold text-slate-300  hover:text-white transition-colors cursor-pointer text-left"
                        :class="props.isOverview ? 'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                        <span class="text-sm">📊</span> Go to Overview
                    </RouterLink>
                    <RouterLink v-if="canFloor && !isDashboard" to="/dashboard"
                        class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold text-slate-300  hover:text-white transition-colors cursor-pointer text-left"
                        :class="props.isOverview ? 'hover:bg-neutral-800' : 'hover:bg-slate-800'">
                        <span class="text-sm">🛠️</span> Go to Dashboard
                    </RouterLink>
                    <button type="button" @click="handleLogout"
                        class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer text-left">
                        <span class="text-sm">⏻</span> Log Out
                    </button>
                </div>
            </div>
        </Transition>
    </div>
</template>

<script setup>

import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { auth, isOwner, canFloor, canCanteen, logout, roleLabel } from '@/Auth'

const props = defineProps({
    isOverview: { type: Boolean, default: false },
    isDashboard: { type: Boolean, default: false }
})

const emit = defineEmits(['manage-users'])

const open = ref(false)
const menuRoot = ref(null)

const roleBadgeClass = computed(() => ({
    owner: 'bg-amber-500/10 text-amber-400',
    manager: 'bg-indigo-500/10 text-indigo-400',
    receptionist: 'bg-sky-500/10 text-sky-400',
}[auth.role] || 'bg-slate-800 text-slate-400'))

function handleLogout() {
    open.value = false
    logout()
}

function handleClickOutside(e) {
    if (menuRoot.value && !menuRoot.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>