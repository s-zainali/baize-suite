<template>
    <div class="relative" ref="root">
        <button @click="open = !open"
            class="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-2.5 py-1.5 transition-colors hover:border-slate-700">
            <span
                class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-black uppercase text-white">
                {{ initials }}
            </span>
            <span class="max-w-[90px] truncate text-xs font-bold text-slate-200">{{ firstName }}</span>
        </button>

        <div v-if="open"
            class="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
            <div class="border-b border-slate-800 px-4 py-3">
                <p class="truncate text-sm font-bold text-white">{{ customer.profile?.name }}</p>
                <p class="truncate font-mono text-[10px] text-slate-500">{{ displayPhone }}</p>
            </div>
            <RouterLink to="/home" @click="open = false"
                class="block px-4 py-2.5 text-xs font-bold text-slate-300 transition-colors hover:bg-slate-800">
                My Bookings
            </RouterLink>
            <RouterLink to="/booking" @click="open = false"
                class="block px-4 py-2.5 text-xs font-bold text-slate-300 transition-colors hover:bg-slate-800">
                Book a Table
            </RouterLink>
            <button @click="signOut()"
                class="w-full cursor-pointer px-4 py-2.5 text-left text-xs font-bold text-rose-400 transition-colors hover:bg-slate-800">
                Sign Out
            </button>
        </div>
    </div>
</template>

<script setup>
// A customer-only menu. The staff UserMenu shows role badges and imports the
// staff auth store — pulling it in here would put `ls_token`, logout-to-/staff
// and the word "receptionist" into the guest bundle.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { customer, signOut } from '../auth.js'
import { formatPhoneDisplay } from '@/utils/phone.js'

const open = ref(false)
const root = ref(null)

const firstName = computed(() => (customer.profile?.name || 'Guest').trim().split(' ')[0])
const initials = computed(() => (customer.profile?.name || 'G').trim().slice(0, 2))
const displayPhone = computed(() => formatPhoneDisplay(customer.profile?.phone || ''))

const onClickOutside = (event) => {
    if (root.value && !root.value.contains(event.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))
</script>