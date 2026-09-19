<template>
    <div class="min-h-screen bg-slate-950 text-white">
        <div class="mx-auto max-w-6xl px-4 sm:px-6 py-6 space-y-8">
            <!-- Header -->
            <header class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <img src="/baize_logo_text.png" class="h-6" alt="Baize" onerror="this.style.display='none'" />
                </div>
                <div class="flex items-center gap-3">
                    <div class="text-right hidden sm:block">
                        <p class="text-[10px] font-black uppercase tracking-widest text-emerald-500">Signed in</p>
                        <p class="text-sm font-black">{{ fullName }}</p>
                    </div>
                    <button @click="signOut()"
                        class="rounded-xl border border-slate-800 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:border-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors cursor-pointer">
                        Sign out
                    </button>
                </div>
            </header>

            <!-- ── FIND CLUBS (hero) ── -->
            <section class="rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-900 to-slate-950 p-6 sm:p-8">
                <h1 class="text-2xl sm:text-3xl font-black tracking-tight">Find your club</h1>
                <p class="text-sm text-slate-400 mt-1">Search a venue, pick a branch, book a table.</p>

                <!-- search -->
                <div class="mt-5 relative">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">⌕</span>
                    <input v-model="query" type="search" placeholder="Search clubs by name or city…"
                        class="w-full rounded-2xl border border-slate-700 bg-slate-950 pl-10 pr-4 py-3.5 text-sm font-semibold text-white outline-none focus:border-emerald-500 transition-colors" />
                </div>

                <!-- tabs -->
                <div class="mt-4 flex gap-2">
                    <button v-for="t in tabs" :key="t.key" @click="tab = t.key"
                        class="rounded-xl px-4 py-2 text-[11px] font-black uppercase tracking-widest transition-colors cursor-pointer"
                        :class="tab === t.key ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'">
                        {{ t.label }}<span v-if="t.key === 'fav' && favUids.size" class="ml-1 opacity-70">{{ favUids.size }}</span>
                    </button>
                </div>

                <!-- clubs grid -->
                <div v-if="loadingClubs" class="py-12 text-center text-sm font-bold text-slate-600">Finding clubs…</div>
                <div v-else-if="!visibleClubs.length" class="py-12 text-center">
                    <p class="text-sm font-bold text-slate-400">{{ tab === 'fav' ? 'No favourites yet' : 'No clubs found' }}</p>
                    <p class="text-xs text-slate-500 mt-1">{{ tab === 'fav' ? 'Star a club to keep it here.' : 'Try a different search.' }}</p>
                </div>
                <div v-else class="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div v-for="club in visibleClubs" :key="club.uid"
                        class="group rounded-2xl border border-slate-800 bg-slate-900/60 p-5 hover:border-emerald-500/40 transition-colors">
                        <div class="flex items-start justify-between gap-3">
                            <div class="min-w-0">
                                <p class="text-base font-black text-white truncate">{{ club.name }}</p>
                                <p class="text-[11px] text-slate-500 truncate">{{ club.city || '—' }} · {{ club.branches }} branch{{ club.branches === 1 ? '' : 'es' }}</p>
                            </div>
                            <button @click="toggleFav(club)" :title="isFav(club) ? 'Unfavourite' : 'Favourite'"
                                class="shrink-0 text-lg leading-none cursor-pointer transition-transform active:scale-90"
                                :class="isFav(club) ? 'text-amber-400' : 'text-slate-600 hover:text-slate-400'">
                                {{ isFav(club) ? '★' : '☆' }}
                            </button>
                        </div>
                        <button @click="openClub(club)"
                            class="mt-4 w-full rounded-xl bg-emerald-600 py-2.5 text-[10px] font-black uppercase tracking-widest text-white hover:bg-emerald-500 transition-colors cursor-pointer">
                            View &amp; book
                        </button>
                    </div>
                </div>
            </section>

            <!-- ── YOUR BOOKINGS ── -->
            <section class="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
                <div class="flex items-baseline justify-between">
                    <h2 class="text-lg font-black tracking-tight">Your bookings</h2>
                    <span v-if="upcoming.length" class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-emerald-400">
                        {{ upcoming.length }} upcoming
                    </span>
                </div>
                <div v-if="loadingBookings" class="py-8 text-center text-xs font-bold text-slate-600">Loading…</div>
                <div v-else-if="!upcoming.length" class="mt-4 rounded-2xl border border-dashed border-slate-700 py-8 text-center">
                    <p class="text-xs font-bold text-slate-400">Nothing booked yet</p>
                    <p class="text-[11px] text-slate-500 mt-1">Find a club above and reserve a table.</p>
                </div>
                <ul v-else class="mt-4 space-y-2">
                    <li v-for="b in upcoming" :key="b.id"
                        class="flex items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-950/50 px-4 py-3">
                        <div class="min-w-0">
                            <p class="text-[9px] font-black uppercase tracking-widest" :style="{ color: typeColor(b.tableType) }">
                                {{ typeLabel(b.tableType) }} #{{ b.tableNumber ?? '' }}
                            </p>
                            <p class="text-xs font-bold text-slate-200 mt-0.5">{{ whenLabel(b) }}</p>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                            <span v-if="b.status === 'active'" class="rounded-md bg-emerald-500/15 px-2 py-1 text-[9px] font-black uppercase text-emerald-400">Playing</span>
                            <span class="font-mono text-[11px] text-slate-500">{{ b.code }}</span>
                            <button @click="cancel(b.id)" class="rounded-lg border border-slate-700 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-slate-400 hover:border-rose-500/50 hover:text-rose-300 cursor-pointer">Cancel</button>
                        </div>
                    </li>
                </ul>
            </section>

            <!-- ── ACCOUNT ── -->
            <section class="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
                <h2 class="mb-3 text-[9px] font-black uppercase tracking-widest text-slate-500">Account</h2>
                <dl class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div class="flex items-center justify-between rounded-xl bg-slate-950/50 border border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Name</dt>
                        <dd class="truncate pl-3 text-xs font-bold">{{ fullName }}</dd>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-slate-950/50 border border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Phone</dt>
                        <dd class="font-mono text-xs font-bold">{{ displayPhone }}</dd>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-slate-950/50 border border-slate-800 px-4 py-3">
                        <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Email</dt>
                        <dd class="truncate pl-3 text-xs font-bold">{{ customer.profile?.email || '—' }}</dd>
                    </div>
                </dl>
            </section>

            <PoweredByZain :forCustomer="true" />
        </div>
    </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { customer, signOut, apiGet, apiPost, apiDelete } from '../auth.js'
import { typeLabel, typeColor, formatPhoneDisplay, PoweredByZain } from '@baize/ui'

const router = useRouter()
const fullName = computed(() => (customer.profile?.name || 'Guest').trim())
const displayPhone = computed(() => formatPhoneDisplay(customer.profile?.phone || ''))

// ── clubs ──
const clubs = ref([])
const favUids = ref(new Set())
const loadingClubs = ref(true)
const query = ref('')
const tab = ref('all')
const tabs = [{ key: 'all', label: 'All' }, { key: 'near', label: 'Near you' }, { key: 'fav', label: 'Favourites' }]

const isFav = (club) => favUids.value.has(club.uid)
const matches = (club) => {
    const q = query.value.trim().toLowerCase()
    return !q || `${club.name} ${club.city || ''}`.toLowerCase().includes(q)
}
const visibleClubs = computed(() => {
    let list = clubs.value.filter(matches)
    if (tab.value === 'fav') list = list.filter(isFav)
    return list
})

async function loadClubs() {
    loadingClubs.value = true
    try {
        const [all, fav] = await Promise.allSettled([apiGet('/clubs'), apiGet('/clubs/favourites')])
        if (all.status === 'fulfilled') clubs.value = all.value.clubs || []
        if (fav.status === 'fulfilled') favUids.value = new Set((fav.value.clubs || []).map(c => c.uid))
    } finally { loadingClubs.value = false }
}

async function toggleFav(club) {
    const on = isFav(club)
    // optimistic
    const next = new Set(favUids.value)
    on ? next.delete(club.uid) : next.add(club.uid)
    favUids.value = next
    try {
        on ? await apiDelete(`/clubs/${club.uid}/favourite`) : await apiPost(`/clubs/${club.uid}/favourite`, {}, { auth: true })
    } catch { loadClubs() }   // revert from server on failure
}

function openClub(club) {
    router.push({ path: '/booking', query: { club: club.uid } })
}

// ── bookings ──
const bookings = ref([])
const loadingBookings = ref(true)
const upcoming = computed(() =>
    [...bookings.value]
        .filter(b => b.status === 'active' || new Date(b.endTime) > new Date())
        .sort((a, b) => (a.status !== b.status ? (a.status === 'active' ? -1 : 1) : new Date(a.startTime) - new Date(b.startTime))))

function whenLabel(b) {
    const d = new Date(b.startTime)
    const time = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    return `${d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}, ${time}`
}
async function loadBookings() {
    loadingBookings.value = true
    try { const d = await apiGet('/bookings'); bookings.value = d.bookings || [] }
    catch { /* ignore */ } finally { loadingBookings.value = false }
}
async function cancel(id) {
    try { await apiDelete(`/bookings/${id}`); bookings.value = bookings.value.filter(b => b.id !== id) } catch {}
}

onMounted(() => { loadClubs(); loadBookings() })
</script>