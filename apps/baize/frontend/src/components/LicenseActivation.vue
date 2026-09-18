<template>
    <div class="min-h-[100dvh] z-[90] grid lg:grid-cols-[46%_1fr] bg-slate-950 font-sans text-zinc-100 overflow-hidden">

        <!-- ── LEFT: Felt brand panel ── -->
        <div class="baize-felt relative hidden lg:flex flex-col justify-between p-14 overflow-hidden">
            <!-- Billiards graphics, matched to the customer login -->
            <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
                <!-- felt weave -->
                <div class="absolute inset-0"
                    style="background-image:radial-gradient(circle at 1px 1px, rgba(255,255,255,0.10) 1px, transparent 0);background-size:22px 22px;opacity:.45"></div>
                <!-- Racked triangle, top right -->
                <svg class="absolute -right-16 -top-10 h-72 w-72 rotate-[14deg] opacity-80" viewBox="0 0 200 145" fill="none">
                    <g opacity="0.85">
                        <circle v-for="ball in rack" :key="ball.n" :cx="ball.x" :cy="ball.y" r="11" :fill="ball.color" />
                        <path v-for="ball in stripedRack" :key="`s${ball.n}`"
                            :d="`M${ball.x - 11} ${ball.y} a11 11 0 0 1 22 0 Z`" fill="#f8fafc" opacity="0.85"
                            :transform="`rotate(90 ${ball.x} ${ball.y})`" />
                        <circle v-for="ball in rack" :key="`o${ball.n}`" :cx="ball.x" :cy="ball.y" r="11"
                            fill="none" stroke="#04140e" stroke-opacity="0.55" stroke-width="0.8" />
                    </g>
                    <path d="M100 2 L174.7 131.4 L25.3 131.4 Z" fill="none" stroke="#d1a054" stroke-opacity="0.7"
                        stroke-width="4" stroke-linejoin="round" />
                    <path d="M100 2 L174.7 131.4 L25.3 131.4 Z" fill="none" stroke="#78350f" stroke-opacity="0.5"
                        stroke-width="1" stroke-linejoin="round" />
                </svg>
                <!-- Cue and cue ball, bottom left, aimed across the panel -->
                <svg class="absolute -bottom-28 -left-28 h-[34rem] w-[34rem] opacity-90" viewBox="0 0 400 400" fill="none">
                    <path d="M18 372 L262 134" stroke="#5c3210" stroke-opacity="0.9" stroke-width="6.5" stroke-linecap="round" />
                    <path d="M120 272.5 L262 134" stroke="#c08a3e" stroke-opacity="0.9" stroke-width="5" stroke-linecap="round" />
                    <path d="M262 134 L286.3 110.3" stroke="#e7e5e4" stroke-opacity="0.9" stroke-width="4.5" stroke-linecap="round" />
                    <path d="M286.3 110.3 L292.7 104.0" stroke="#34d399" stroke-opacity="0.95" stroke-width="4.5" stroke-linecap="round" />
                    <circle cx="340.7" cy="57.2" r="20" fill="#f8fafc" fill-opacity="0.92" />
                    <circle cx="340.7" cy="57.2" r="20" fill="none" stroke="#04140e" stroke-opacity="0.4" stroke-width="1" />
                    <ellipse cx="333.7" cy="49.2" rx="6" ry="4" fill="#ffffff" opacity="0.8" transform="rotate(-28 333.7 49.2)" />
                </svg>
                <!-- Corner pockets -->
                <svg class="absolute left-0 top-0 h-28 w-28 text-emerald-200/40" viewBox="0 0 100 100" fill="none">
                    <path d="M0 46 A46 46 0 0 0 46 0" stroke="currentColor" stroke-width="1.4" />
                    <path d="M0 62 A62 62 0 0 0 62 0" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.1" />
                </svg>
                <svg class="absolute bottom-0 right-0 h-28 w-28 rotate-180 text-emerald-200/40" viewBox="0 0 100 100" fill="none">
                    <path d="M0 46 A46 46 0 0 0 46 0" stroke="currentColor" stroke-width="1.4" />
                    <path d="M0 62 A62 62 0 0 0 62 0" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.1" />
                </svg>
                <!-- Cushion sights down each rail -->
                <div class="absolute inset-y-0 left-3 flex w-1 flex-col justify-around">
                    <span v-for="i in 9" :key="`l${i}`" class="block h-1.5 w-1.5 rotate-45 bg-emerald-200/25"></span>
                </div>
                <div class="absolute inset-y-0 right-3 flex w-1 flex-col justify-around">
                    <span v-for="i in 9" :key="`r${i}`" class="block h-1.5 w-1.5 rotate-45 bg-emerald-200/25"></span>
                </div>
                <!-- Vignette keeps the copy readable over the graphics -->
                <div class="absolute inset-0"
                    style="background:radial-gradient(ellipse 78% 62% at 42% 48%, rgba(2,15,10,0.78) 0%, rgba(2,15,10,0.30) 58%, transparent 100%)"></div>
            </div>

            <div class="relative z-10 flex items-center gap-3">
                <img src="/baize_logo.png" alt="Baize" class="h-10 drop-shadow-lg" />
                <img src="/baize_logo_text.png" alt="Baize" class="h-5 opacity-95" />
            </div>

            <div class="relative z-10 max-w-md">
                <p class="text-[11px] font-bold uppercase tracking-[0.4em] text-emerald-300/70 mb-5">Club Operating System</p>
                <h2 class="text-[2.6rem] leading-[1.1] font-black tracking-tight text-white">
                    The table's set.<br />
                    <span class="text-emerald-300">Rack 'em up.</span>
                </h2>
                <p class="mt-5 text-[15px] text-emerald-100/60 leading-relaxed max-w-sm">
                    Tables, bookings, canteen and khata — one panel, licensed to your venue.
                </p>
                <ul class="mt-9 space-y-3.5">
                    <li v-for="f in features" :key="f" class="flex items-center gap-3.5 text-sm text-emerald-50/85">
                        <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-400/15 border border-emerald-300/25 text-emerald-300 text-[11px]">✓</span>
                        {{ f }}
                    </li>
                </ul>
            </div>

            <div class="relative z-10 flex items-center gap-2.5 text-xs text-emerald-100/45">
                <span class="relative flex h-2 w-2">
                    <span class="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60 animate-ping"></span>
                    <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-400"></span>
                </span>
                Secure activation · cryptographically licensed
            </div>
        </div>

        <!-- ── RIGHT: Form panel ── -->
        <div class="relative flex items-center justify-center p-6 sm:p-12 overflow-y-auto">
            <div class="pointer-events-none absolute inset-0 opacity-60"
                style="background: radial-gradient(80% 50% at 50% 0%, rgba(16,185,129,0.06), transparent 70%)"></div>

            <div class="w-full max-w-md my-auto relative z-10 animate-rise">
                <!-- Mobile brand -->
                <div class="lg:hidden flex flex-col items-center gap-3 mb-10">
                    <img src="/baize_logo.png" alt="Baize" class="h-11" />
                    <span class="text-[10px] font-bold uppercase tracking-[0.35em] text-emerald-500/80">Club Portal</span>
                </div>

                <!-- Step indicator -->
                <div v-if="view !== 'keyfile'" class="flex items-center gap-3 mb-9">
                    <div class="flex items-center gap-2.5">
                        <span class="grid place-items-center h-6 w-6 rounded-full text-[11px] font-bold transition-colors"
                            :class="view === 'activate' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-500 text-slate-950'">
                            {{ view === 'activate' ? '✓' : '1' }}
                        </span>
                        <span class="text-xs font-semibold" :class="view === 'activate' ? 'text-zinc-500' : 'text-white'">Account</span>
                    </div>
                    <div class="flex-1 h-px bg-gradient-to-r from-slate-700 to-slate-800"></div>
                    <div class="flex items-center gap-2.5">
                        <span class="grid place-items-center h-6 w-6 rounded-full text-[11px] font-bold border transition-colors"
                            :class="view === 'activate' ? 'bg-emerald-500 text-slate-950 border-emerald-500' : 'bg-slate-900 text-zinc-500 border-slate-700'">2</span>
                        <span class="text-xs font-semibold" :class="view === 'activate' ? 'text-white' : 'text-zinc-500'">Branch</span>
                    </div>
                </div>

                <!-- Header -->
                <div class="mb-8">
                    <div class="flex items-center justify-between mb-1.5">
                        <h1 class="text-[1.7rem] font-black text-white tracking-tight">{{ headers[view].title }}</h1>
                        <button v-if="view === 'activate'" @click="signOut"
                            class="text-xs font-semibold text-zinc-500 hover:text-rose-400 transition-colors cursor-pointer">Sign out</button>
                    </div>
                    <p class="text-sm text-zinc-400">{{ headers[view].sub }}</p>
                </div>

                <!-- ── SIGN IN ── -->
                <div v-if="view === 'signin'" class="space-y-5">
                    <TextField :form="acct" :field="'email'" :label="'Email'" :placeholder="'you@email.com'" :type="'text'" />
                    <PasswordField :form="acct" :field="'password'" :label="'Password'" :placeholder="'••••••••'"
                        :error="{ condition: false, message: '' }" @keyup.enter="submit(doSignin)" />
                    <button @click="submit(doSignin)" :disabled="busy || !acct.email || !acct.password" :class="btn">
                        <span class="btn-sheen"></span>{{ busy ? 'Signing in…' : 'Sign In' }}
                    </button>
                </div>

                <!-- ── REGISTER ── -->
                <div v-else-if="view === 'register'" class="space-y-4">
                    <TextField :form="acct" :field="'clubName'" :label="'Club Name'" :placeholder="'e.g. B Snooker Lounge'" :type="'text'" />
                    <div class="grid grid-cols-2 gap-4">
                        <TextField :form="acct" :field="'ownerName'" :label="'Owner'" :placeholder="'Full name'" :type="'text'" />
                        <PhoneField v-model="acct.phone" id="club-phone" :label="'Phone'" />
                    </div>
                    <TextField :form="acct" :field="'email'" :label="'Email'" :placeholder="'you@email.com'" :type="'text'" />
                    <div class="grid grid-cols-2 gap-4">
                        <TextField :form="acct" :field="'city'" :label="'City'" :placeholder="'Islamabad'" :type="'text'" />
                        <TextField :form="acct" :field="'country'" :label="'Country'" :placeholder="'Pakistan'" :type="'text'" />
                    </div>
                    <PasswordField :form="acct" :field="'password'" :label="'Password'" :placeholder="'at least 8 characters'"
                        :error="{ condition: false, message: '' }" />
                    <button @click="submit(doRegister)" :disabled="busy || !acct.clubName || !acct.email || !acct.password" :class="btn">
                        <span class="btn-sheen"></span>{{ busy ? 'Creating Account…' : 'Create Account' }}
                    </button>
                </div>

                <!-- ── SELECT BRANCH ── -->
                <div v-else-if="view === 'activate'" class="space-y-4">
                    <!-- Account context -->
                    <div class="flex items-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                        <div class="h-11 w-11 shrink-0 rounded-xl bg-gradient-to-br from-emerald-500/20 to-slate-800 border border-emerald-500/20 grid place-items-center text-emerald-300 font-black">
                            {{ (account?.club?.clubName || 'C').charAt(0).toUpperCase() }}
                        </div>
                        <div class="min-w-0">
                            <p class="text-sm font-bold text-zinc-100 truncate">{{ account?.club?.clubName || 'Your club' }}</p>
                            <p class="text-xs text-zinc-500 truncate">{{ account?.club?.email }}</p>
                        </div>
                    </div>

                    <p class="text-xs text-zinc-400">Choose the branch this device runs. It activates that branch's licence on this install — you can switch branches later from the sidebar.</p>

                    <!-- Loading -->
                    <div v-if="branchesLoading" class="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm">
                        <span class="h-4 w-4 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin"></span>
                        <span class="text-zinc-300 text-xs">Loading your branches…</span>
                    </div>

                    <!-- No branches -->
                    <div v-else-if="!clubBranches.length" class="rounded-2xl border border-amber-500/20 bg-amber-500/[0.05] p-4 text-sm">
                        <p class="font-bold text-amber-300 mb-1">No branches yet</p>
                        <p class="text-zinc-400 text-xs">Your provider needs to register a branch for this account. Once they do, it appears here.</p>
                        <button @click="submit(reloadBranches)" class="mt-3 text-xs font-semibold text-emerald-400 hover:text-emerald-300 cursor-pointer">Refresh</button>
                    </div>

                    <!-- Branch list -->
                    <div v-else class="space-y-2">
                        <button v-if="clubBranches.length > 1" @click="submit(activateAll)" :disabled="busy"
                            class="w-full rounded-2xl border border-emerald-500/40 bg-emerald-500/[0.06] hover:bg-emerald-500/[0.12] p-3 text-left text-sm font-bold text-emerald-300 transition-colors disabled:opacity-50 cursor-pointer">
                            Activate all {{ clubBranches.length }} branches here
                            <span class="block text-[11px] font-normal text-emerald-400/70 mt-0.5">Shared / online install: run every branch, each device picks its own from the sidebar.</span>
                        </button>
                        <p v-if="clubBranches.length > 1" class="text-[11px] text-zinc-500 pt-1">…or activate a single branch this device runs:</p>
                        <button v-for="bch in clubBranches" :key="bch.uid" @click="submit(() => pickBranch(bch))"
                            :disabled="busy || !bch.token || bch.status !== 'active'"
                            class="w-full text-left rounded-2xl border p-4 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                            :class="bch.token && bch.status === 'active' ? 'border-slate-800 bg-slate-900/60 hover:border-emerald-500/40' : 'border-slate-800 bg-slate-900/40'">
                            <div class="flex items-center justify-between gap-3">
                                <div class="min-w-0">
                                    <p class="text-sm font-bold text-zinc-100 truncate">{{ bch.name }}</p>
                                    <p class="text-xs text-zinc-500 truncate">{{ bch.address || '—' }}</p>
                                </div>
                                <span class="shrink-0 px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider"
                                    :class="bch.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-zinc-500 border border-slate-700'">
                                    {{ bch.status }}
                                </span>
                            </div>
                            <div v-if="(bch.features || []).length" class="flex flex-wrap gap-1.5 mt-2">
                                <span v-for="f in bch.features" :key="f" class="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide bg-slate-800 text-zinc-400">{{ f }}</span>
                            </div>
                            <p v-if="!bch.token" class="text-[11px] text-amber-400/80 mt-2">No licence minted for this branch yet.</p>
                        </button>
                        <button @click="submit(reloadBranches)" class="w-full text-xs font-semibold text-zinc-500 hover:text-zinc-300 py-1 cursor-pointer">Refresh branches</button>
                    </div>
                </div>

                <!-- ── KEY FILE (offline) ── -->
                <div v-else class="space-y-4">
                    <div class="relative group flex flex-col items-center justify-center p-9 bg-slate-900/40 border border-dashed border-slate-700 rounded-2xl hover:border-emerald-500/40 hover:bg-slate-900/60 transition-colors cursor-pointer" @click="pickFile">
                        <div v-if="selectedFile" class="flex flex-col items-center gap-3">
                            <div class="h-14 w-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 grid place-items-center text-emerald-400">
                                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            </div>
                            <span class="text-zinc-200 font-medium text-sm truncate max-w-[220px]">{{ selectedFile.name }}</span>
                        </div>
                        <div v-else class="flex flex-col items-center gap-3 text-zinc-500">
                            <div class="h-14 w-14 rounded-full bg-slate-800/60 grid place-items-center group-hover:text-emerald-400 transition-colors">
                                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
                            </div>
                            <div class="text-center">
                                <span class="text-sm font-semibold text-zinc-300 block">Click to upload license key</span>
                                <span class="text-xs text-zinc-500 block mt-1">.key files only</span>
                            </div>
                        </div>
                        <input ref="fileInput" type="file" class="hidden" accept=".key" @change="onFileSelect" />
                    </div>
                    <button @click="submit(() => activateToken(selectedFile))" :disabled="busy || !selectedFile" :class="btn">
                        <span class="btn-sheen"></span>{{ busy ? 'Activating…' : 'Activate offline' }}
                    </button>
                </div>

                <!-- Error -->
                <transition name="fade">
                    <div v-if="error" class="mt-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-2.5">
                        <span class="text-rose-400 text-sm">⚠</span>
                        <p class="text-xs font-semibold text-rose-300">{{ error }}</p>
                    </div>
                </transition>

                <!-- Footer nav -->
                <div class="mt-8 pt-6 border-t border-slate-800/70 text-center text-xs text-zinc-500 space-y-2">
                    <p v-if="view === 'signin'">New here?
                        <span @click="go('register')" class="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer ml-1">Register your club</span>
                    </p>
                    <p v-else-if="view === 'register'">Already registered?
                        <span @click="go('signin')" class="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer ml-1">Sign in</span>
                    </p>
                    <p v-if="view === 'signin' || view === 'register'">Have a local key?
                        <span @click="go('keyfile')" class="font-semibold text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer ml-1">Activate offline</span>
                    </p>
                    <p v-if="view === 'keyfile'">
                        <span @click="go('signin')" class="font-semibold text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer">← Back to sign in</span>
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import {
    status, account, activateToken, fetchDeviceId, deviceBinding,
    clubLogin, clubRegister, clubLoggedIn, clubLogout, loadAccount,
    activateViaAccount, tryActivate, isClubLoggedIn,
    clubBranches, loadClubBranches, activateBranch, activateAllBranches,
} from '@/composables/useLicense.js'
import TextField from './Fields/TextField.vue'
import PasswordField from './Fields/PasswordField.vue'
import PhoneField from './Fields/PhoneField.vue'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'

const btn = 'btn-primary group relative w-full py-3.5 rounded-xl text-sm font-bold tracking-wide text-white overflow-hidden bg-gradient-to-b from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 shadow-lg shadow-emerald-900/40 disabled:shadow-none transition-all active:scale-[.99] cursor-pointer'
const features = ['Live tables & sessions', 'Canteen POS & stock', 'Khata / credit ledger', 'Bookings & waiting queue']

// Racked triangle + cue graphics, matched to the customer login page.
const BALL_R = 11
const BALL_SPACING = 2 * BALL_R + 1.5
const ROW_SPACING = (BALL_SPACING * Math.sqrt(3)) / 2
const BALL_COLOURS = [
    '#facc15', '#2563eb', '#dc2626', '#7c3aed', '#ea580c', '#16a34a', '#7f1d1d', '#0f172a',
    '#facc15', '#2563eb', '#dc2626', '#7c3aed', '#ea580c', '#16a34a', '#7f1d1d',
]
const rack = (() => {
    const balls = []
    for (let row = 0; row < 5; row++) {
        for (let col = 0; col <= row; col++) {
            const n = balls.length + 1
            balls.push({ n, x: 100 + (col - row / 2) * BALL_SPACING, y: 34 + row * ROW_SPACING, color: BALL_COLOURS[n - 1] })
        }
    }
    return balls
})()
const stripedRack = rack.filter((b) => b.n > 8)

const view = ref(isClubLoggedIn.value ? 'activate' : 'signin')
const branchesLoading = ref(false)

async function reloadBranches() {
    branchesLoading.value = true
    try { await loadClubBranches() }
    finally { branchesLoading.value = false }
}
async function activateAll() { await activateAllBranches() }
async function pickBranch(bch) {
    await activateBranch(bch)     // stores the branch licence → the gate lifts
}
const acct = ref({ clubName: '', email: '', password: '', ownerName: '', phone: '', city: '', country: '' })
const busy = ref(false)
const error = ref('')
const pending = ref(false)
let pollTimer = null

const headers = {
    signin: { title: 'Welcome back', sub: 'Sign in to your club account to continue.' },
    register: { title: 'Register your club', sub: 'Create your club account — takes a minute.' },
    activate: { title: 'Activate this install', sub: 'One step from going live.' },
    keyfile: { title: 'Offline activation', sub: 'Upload the license key we provided.' },
}

const activeLicense = computed(() => (account.value?.licenses || []).find((l) => l.status === 'active') || null)
// What to tell the operator on the gate when there's no ready license — driven
// by the app's real license state, so an expired/revoked install says so
// instead of a misleading "No active license".
const GATE_STATE = {
    expired:   { label: 'License expired', tone: 'text-rose-300', dot: 'bg-rose-400' },
    grace:     { label: 'Expired — grace period', tone: 'text-amber-300', dot: 'bg-amber-400' },
    revoked:   { label: 'License revoked', tone: 'text-rose-300', dot: 'bg-rose-400' },
    suspended: { label: 'Account suspended', tone: 'text-rose-300', dot: 'bg-rose-400' },
    invalid:   { label: 'License invalid', tone: 'text-rose-300', dot: 'bg-rose-400' },
    unlicensed:{ label: 'No license yet', tone: 'text-amber-300', dot: 'bg-amber-400' },
}
const gate = computed(() => {
    const st = status.value?.state
    const base = GATE_STATE[st]
        || { label: status.value?.valid ? 'Awaiting license' : 'No active license', tone: 'text-amber-300', dot: 'bg-amber-400' }
    // 'invalid' covers clock-rollback AND tamper — surface the actual reason so a
    // clock issue reads as "system clock was set back", not a scary generic label.
    if (st === 'invalid' && status.value?.reason) return { ...base, label: status.value.reason }
    return base
})
const registeredDevices = computed(() => (account.value?.devices || []).map((d) => d.fingerprint))
const isDeviceRegistered = computed(() => !!deviceId.value && registeredDevices.value.includes(deviceId.value))

function go(v) { error.value = ''; view.value = v }

onMounted(async () => {
    if (isClubLoggedIn.value) {
        // A transient failure (cold server, flaky network) must NOT log the user
        // out — clubMe() already clears the token on a real 401. Keep the session.
        try { await loadAccount() } catch { /* transient — keep session */ }
        // Resolve the view from the REAL state after loading, not a stale snapshot.
        view.value = isClubLoggedIn.value ? 'activate' : 'signin'
        if (view.value === 'activate') reloadBranches()
        if (isClubLoggedIn.value && deviceBinding.value) { try { deviceId.value = await fetchDeviceId() } catch { /* ignore */ } }
    }
})

// Keep the view honest with the session. If it's lost anywhere (a real 401
// clears the token) fall back to sign-in instead of stranding a broken
// 'activate' screen that only a refresh could fix. When it returns, move on.
watch(isClubLoggedIn, (loggedIn) => {
    if (!loggedIn) {
        stopPending()
        if (view.value === 'activate' || view.value === 'keyfile') view.value = 'signin'
    } else if (view.value === 'signin' || view.value === 'register') {
        view.value = 'activate'
        reloadBranches()          // fetch this club's branches for the picker
    }
})
onBeforeUnmount(stopPending)

async function doSignin() {
    await clubLogin({ email: acct.value.email, password: acct.value.password })
    await loadAccount()
    view.value = 'activate'
    if (deviceBinding.value) { try { deviceId.value = await fetchDeviceId() } catch { /* ignore */ } }
}

async function doRegister() {
    await clubRegister({ ...acct.value, phone: acct.value.phone ? `+92${acct.value.phone}` : '' })
    await loadAccount()
    view.value = 'activate'
    if (deviceBinding.value) { try { deviceId.value = await fetchDeviceId() } catch { /* ignore */ } }
}

async function doActivate() {
    const ok = await activateViaAccount()
    if (ok) return
    await loadAccount().catch(() => {})
    startPending()
}

function startPending() {
    pending.value = true
    if (pollTimer) return
    pollTimer = setInterval(async () => {
        // A blip must not boot the user — keep polling; a real 401 is handled
        // centrally (clubMe clears the token, and the watcher resets the view).
        try { if (await tryActivate()) stopPending() }
        catch { /* transient — keep polling */ }
    }, 8000)
}

function stopPending() {
    pending.value = false
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function checkNow() { if (!(await tryActivate())) { /* still pending */ } }

function signOut() {
    stopPending()
    clubLogout()
    deviceId.value = ''
    showDeviceId.value = false
    view.value = 'signin'
}

const deviceId = ref('')
const showDeviceId = ref(false)
const loadingId = ref(false)
const copied = ref(false)

async function copyId() {
    if (!deviceId.value) return
    try { await navigator.clipboard.writeText(deviceId.value) } catch { /* non-HTTPS */ }
    copied.value = true
    setTimeout(() => { copied.value = false }, 1500)
}

const fileInput = ref(null)
const selectedFile = ref(null)
const pickFile = () => fileInput.value?.click()
function onFileSelect(e) { selectedFile.value = e.target.files?.[0] || null }

function fmtDate(iso) {
    if (!iso) return '—'
    const d = new Date(iso)
    return isNaN(d) ? iso : d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })
}

// Poll the account only while logged in and not yet licensed — so a signed-out
// gate isn't hammering /me, and a live install isn't thrashing state.
useAutoRefresh(() => (isClubLoggedIn.value && !status.value?.valid ? loadAccount() : undefined), 4000)

async function submit(fn) {
    busy.value = true
    error.value = ''
    try { await fn() }
    catch (e) { error.value = e.message }
    finally { busy.value = false }
}
</script>

<style scoped>
/* Felt table lighting — layered radials, no cheap blur blobs */
.baize-felt {
    background:
        radial-gradient(115% 75% at 50% -12%, rgba(16, 185, 129, 0.22), transparent 58%),
        radial-gradient(90% 60% at 82% 112%, rgba(5, 150, 105, 0.14), transparent 60%),
        linear-gradient(160deg, #073024 0%, #04211a 46%, #020a08 100%);
}
/* Button sheen sweep on hover */
.btn-sheen {
    position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
    background: linear-gradient(110deg, transparent 30%, rgba(255, 255, 255, 0.28) 50%, transparent 70%);
    transform: translateX(-120%); transition: transform 0.7s ease;
}
.btn-primary:hover:not(:disabled) .btn-sheen { transform: translateX(120%); }

.animate-rise { animation: rise 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
@keyframes rise { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>