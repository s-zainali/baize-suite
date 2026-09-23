<template>
    <div class="max-w-6xl mx-auto px-4 py-10 space-y-6 animate-fadeIn">

        <!-- Hero header -->
        <header class="rounded-3xl border border-slate-700 bg-slate-800 p-8 shadow-2xl">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div class="space-y-3">
                    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest" :class="meta.chip">
                        <span class="w-1.5 h-1.5 rounded-full" :class="meta.dot"></span> License &amp; Identity Control
                    </div>
                    <h1 class="text-3xl md:text-4xl font-black tracking-tight text-white">Membership &amp; Branding</h1>
                    <p class="text-sm text-slate-400 max-w-xl">Your club's operational license, device binding, per-branch entitlements, and white-label identity.</p>
                </div>
                <button v-if="s.activated" @click="showLogout = true"
                    class="shrink-0 inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/60 px-5 py-3 text-xs font-bold text-slate-300 hover:border-rose-500/60 hover:bg-rose-500/10 hover:text-rose-300 transition-colors cursor-pointer active:scale-95">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                    Log out
                </button>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-slate-950/50 p-6 rounded-4xl border border-slate-800">
            <!-- License identity -->
            <section class="lg:col-span-8 space-y-6">
                <!-- Status banner -->
                <div class="rounded-2xl border p-6" :class="meta.banner">
                    <div class="flex items-start justify-between gap-4">
                        <div class="flex items-center gap-4">
                            <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl shrink-0" :class="meta.iconBg">{{ meta.icon }}</div>
                            <div>
                                <p class="text-xl font-black" :class="meta.text">{{ meta.label }}</p>
                                <p class="text-xs text-slate-300/80 mt-0.5 max-w-md leading-relaxed">{{ meta.message }}</p>
                            </div>
                        </div>
                        <span class="shrink-0 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border" :class="meta.pill">{{ meta.badge }}</span>
                    </div>
                    <div v-if="s.state === 'grace' && s.graceHoursLeft != null" class="mt-4 pt-4 border-t border-white/10 flex items-center gap-2 text-xs font-bold text-amber-300">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        Locks in ~{{ s.graceHoursLeft }} hour{{ s.graceHoursLeft === 1 ? '' : 's' }} unless renewed.
                    </div>
                </div>

                <!-- Detail tiles -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                        <div class="flex items-center gap-2 text-slate-500 mb-3"><span class="text-base">🏢</span><span class="text-[10px] font-black uppercase tracking-widest">Club</span></div>
                        <p class="text-base font-black text-white truncate">{{ s.clubName || 'Uninitialized' }}</p>
                        <p class="text-[10px] font-mono text-slate-500 truncate">{{ s.clubUid || '—' }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                        <div class="flex items-center gap-2 text-slate-500 mb-3"><span class="text-base">⏳</span><span class="text-[10px] font-black uppercase tracking-widest">Validity</span></div>
                        <p class="text-base font-black text-white">{{ fmtDateTime(s.expiresAt) }}</p>
                        <p class="text-[11px]" :class="validityHint.class">{{ validityHint.text }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                        <div class="flex items-center gap-2 text-slate-500 mb-3"><span class="text-base">🔗</span><span class="text-[10px] font-black uppercase tracking-widest">Binding</span></div>
                        <p class="text-base font-black text-white">{{ s.deviceBinding ? 'Device-locked' : 'Unbound' }}</p>
                        <p class="text-[11px] text-slate-500">{{ s.deviceBinding ? 'Tied to this machine' : 'Runs on any machine' }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                        <div class="flex items-center gap-2 text-slate-500 mb-3"><span class="text-base">📡</span><span class="text-[10px] font-black uppercase tracking-widest">Last check-in</span></div>
                        <p class="text-base font-black text-white">{{ s.lastServerCheck ? fmtDateTime(s.lastServerCheck) : 'Never' }}</p>
                        <p class="text-[11px] text-slate-500">{{ s.lastServerCheck ? 'Heartbeat with the license server' : 'Offline / not yet contacted' }}</p>
                    </div>
                </div>

                <div class="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                    <p class="text-xs text-slate-400 leading-relaxed">{{ meta.action }}</p>
                </div>
            </section>

            <!-- Branding -->
            <aside class="lg:col-span-4">
                <div class="rounded-2xl border border-slate-800 bg-slate-950/50 p-6 shadow-2xl h-full flex flex-col">
                    <h2 class="text-[11px] font-black uppercase tracking-widest text-slate-300 mb-5 flex items-center justify-between">
                        <span>Club Branding</span><span class="text-[9px] text-slate-500 font-bold">Asset Manager</span>
                    </h2>
                    <div class="flex flex-col items-center justify-center p-8 bg-slate-950/60 border-2 border-dashed border-slate-700 rounded-2xl relative group transition-colors hover:border-slate-600">
                        <div v-if="preview" class="w-28 h-28 relative flex items-center justify-center p-2 rounded-2xl bg-slate-800 border border-slate-700">
                            <img :src="resolveLogoSrc(preview)" alt="Club Logo" class="max-h-24 max-w-24 object-contain" />
                        </div>
                        <div v-else class="w-28 h-28 flex flex-col items-center justify-center text-slate-600 gap-2">
                            <div class="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500 group-hover:text-slate-400 transition-colors">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                            </div>
                            <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">No Logo Set</span>
                        </div>
                        <button type="button" @click="pickFile" class="absolute inset-0 bg-slate-950/90 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1.5 cursor-pointer">
                            <div class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-pool-felt-400 mb-1">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                            </div>
                            <span class="text-xs font-black text-white uppercase tracking-wider">{{ preview ? 'Change Logo' : 'Upload Logo' }}</span>
                            <span class="text-[10px] text-slate-400 font-medium">PNG, JPG, SVG up to 5MB</span>
                        </button>
                    </div>
                    <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelect" />
                    <div class="flex items-center justify-between mt-4 px-1">
                        <button v-if="preview" type="button" @click="clearImage" class="text-[11px] font-bold text-rose-400 hover:text-rose-300 transition-colors cursor-pointer flex items-center gap-1"><span>✕</span> Remove image</button>
                        <span v-else class="text-[11px] text-slate-500">Recommended: 512×512px</span>
                    </div>
                    <button @click="handleSave" :disabled="saving || !selectedFile"
                        class="mt-auto pt-0 w-full  mt-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-[0.98] disabled:bg-slate-900 disabled:text-slate-600 disabled:cursor-not-allowed text-xs font-black tracking-widest text-white uppercase transition-colors cursor-pointer flex items-center justify-center gap-2 h-10">
                        <svg v-if="saving" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                        <span>
                            {{ saving ? 'Uploading…' : 'Save Changes' }}
                        </span>
                    </button>
                </div>
            </aside>
        </div>

        <!-- Branches -->
        <section v-if="s.activated" class="rounded-2xl border border-slate-800 bg-slate-950/50 p-8 shadow-2xl">
            <div class="flex items-center justify-between gap-4 mb-1">
                <h2 class="text-lg font-black text-white">Branches</h2>
                <span class="px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold text-slate-400 bg-slate-950 border border-slate-800">{{ branches.length }} / {{ s.branchLimit || 1 }} used</span>
            </div>
            <p class="text-xs text-slate-400 mb-6 max-w-2xl">Each branch runs on its own license with its own feature set. Register a branch by activating the token your provider issued for it — branches are never created here freely.</p>

            <div v-if="branches.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                <div v-for="b in branches" :key="b.id" class="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                    <div class="flex items-center justify-between gap-3 mb-2.5">
                        <p class="text-sm font-black text-white truncate flex items-center gap-2">
                            {{ b.name }}
                            <span v-if="b.isDefault" class="text-[8px] font-black uppercase tracking-widest text-pool-felt-400 bg-pool-felt-500/10 border border-pool-felt-500/20 px-1.5 py-0.5 rounded">Main</span>
                        </p>
                        <span class="text-[9px] font-mono text-slate-600 shrink-0">{{ b.uid }}</span>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                        <span v-for="f in (b.features || [])" :key="f"
                            class="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wide bg-pool-felt-500/10 text-pool-felt-300 border border-pool-felt-500/20">{{ f }}</span>
                        <span v-if="!(b.features || []).length" class="text-[10px] text-slate-500">Base only (pool, snooker, private rooms)</span>
                    </div>
                </div>
            </div>
            <p v-else class="text-xs text-slate-500 mb-6">No branches registered yet.</p>

            <div class="rounded-2xl border border-slate-800 bg-slate-950/50 p-5">
                <label class="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Activate a branch license</label>
                <textarea v-model="branchToken" rows="3" placeholder="Paste the branch license token here…"
                    class="w-full bg-slate-950 border border-slate-700 focus:border-pool-felt-500 rounded-xl p-3 text-[11px] font-mono text-slate-200 outline-none resize-none"></textarea>
                <div class="flex items-center gap-3 mt-3">
                    <input v-model="branchName" placeholder="Branch name (optional)"
                        class="flex-1 bg-slate-950 border border-slate-700 focus:border-pool-felt-500 rounded-xl px-3 py-2.5 text-xs font-bold text-white outline-none">
                    <button @click="activateBranch" :disabled="branchBusy || !branchToken.trim()"
                        class="px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest bg-pool-felt-600 hover:bg-pool-felt-500 disabled:bg-slate-800 disabled:text-slate-500 text-white cursor-pointer active:scale-95">
                        {{ branchBusy ? 'Activating…' : 'Activate' }}
                    </button>
                </div>
                <p v-if="branchMsg" class="mt-2 text-[11px] font-bold" :class="branchOk ? 'text-pool-felt-400' : 'text-rose-400'">{{ branchMsg }}</p>
            </div>
        </section>

        <!-- Log out confirm (themed) -->
        <transition enter-active-class="transition duration-150" enter-from-class="opacity-0" leave-active-class="transition duration-150" leave-to-class="opacity-0">
            <div v-if="showLogout" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md" @click.self="showLogout = false">
                <div class="bg-slate-900 border border-slate-800 w-full max-w-sm rounded-2xl p-6 shadow-2xl">
                    <div class="flex items-center gap-3 mb-3">
                        <div class="w-10 h-10 rounded-2xl bg-slate-800 flex items-center justify-center text-lg">↩</div>
                        <h2 class="text-lg font-black text-white">Log out?</h2>
                    </div>
                    <p class="text-xs text-slate-400 mb-6 leading-relaxed">
                        You'll be signed out and returned to the sign-in screen. Sign back in to resume — your data stays exactly as it is.
                    </p>
                    <div class="flex gap-3">
                        <button @click="showLogout = false" class="flex-1 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">Cancel</button>
                        <button @click="confirmLogout" :disabled="loggingOut" class="flex-1 py-2.5 rounded-xl text-xs font-black bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-60 cursor-pointer">{{ loggingOut ? 'Logging out…' : 'Log out' }}</button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { status, loadBranding, clubLogout, clubLoggedIn, deactivateLicense, loadLicense } from '@/composables/useLicense';
import { usePageBackground } from '@/composables/usePageBackground';
import { API_URL, authFetch } from '@/Auth';
import { branches, loadBranches } from '@/composables/useBranch.js';
import { onMounted } from 'vue';

// license status object (reactive ref → read .value in script, auto-unwrap in template)
const s = computed(() => status.value || {})

const branchToken = ref('')
const branchName = ref('')
const branchBusy = ref(false)
const branchMsg = ref('')
const branchOk = ref(false)

onMounted(loadBranches)

async function activateBranch() {
    branchBusy.value = true; branchMsg.value = ''
    try {
        const res = await authFetch(API_URL + '/license/branch/activate', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: branchToken.value.trim(), name: branchName.value.trim() || undefined }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(data.error || 'Could not activate that branch token.')
        branchOk.value = true
        branchMsg.value = `Activated: ${data.branch?.name || 'branch'}${(data.branch?.features || []).length ? ' (' + data.branch.features.join(', ') + ')' : ''}`
        branchToken.value = ''; branchName.value = ''
        await loadBranches()
        await loadLicense()   // pick up the new branch's entitlements in place — no logout needed
    } catch (e) {
        branchOk.value = false; branchMsg.value = e.message
    } finally { branchBusy.value = false }
}

// Per-state presentation. `valid` still gates the app elsewhere; this is display.
const STATES = {
    active:    { label: 'Active', badge: 'Active', icon: '✓', message: 'Your license is active and verified.',
                 action: 'Nothing to do — your club is fully licensed.' },
    expiring:  { label: 'Expiring soon', badge: 'Expiring', icon: '⏳', message: 'Your license lapses shortly. Renew to avoid interruption.',
                 action: 'Contact your provider to renew before it expires.' },
    grace:     { label: 'Expired — grace period', badge: 'Grace', icon: '⚠', message: 'Your license has expired but the app is still running on a short grace period.',
                 action: 'Renew with your provider now — the app locks when the grace period ends.' },
    expired:   { label: 'Expired', badge: 'Expired', icon: '⛔', message: 'Your license has expired and the app is locked.',
                 action: 'Contact your provider to renew and restore access.' },
    revoked:   { label: 'Revoked', badge: 'Revoked', icon: '⛔', message: 'This license has been revoked and the app is disabled.',
                 action: 'This device has been remotely disabled. Contact your provider.' },
    suspended: { label: 'Account suspended', badge: 'Suspended', icon: '⛔', message: 'Your club account is suspended.',
                 action: 'Your account is on hold. Contact your provider to reactivate.' },
    invalid:   { label: 'Invalid license', badge: 'Invalid', icon: '⛔', message: s.value?.reason || 'This license could not be verified.',
                 action: 'Re-activate with a valid license, or contact your provider.' },
    unlicensed:{ label: 'Not activated', badge: 'None', icon: '○', message: 'No license is activated on this install.',
                 action: 'Activate a license to begin.' },
}
const THEME = {
    ok:    { chip: 'bg-pool-felt-500/10 border border-pool-felt-500/25 text-pool-felt-300', dot: 'bg-pool-felt-400',
             banner: 'bg-pool-felt-500/5 border-pool-felt-500/25', text: 'text-pool-felt-300', iconBg: 'bg-pool-felt-500/15 text-pool-felt-300',
             pill: 'bg-pool-felt-500/10 text-pool-felt-300 border-pool-felt-500/25' },
    warn:  { chip: 'bg-amber-500/10 border border-amber-500/20 text-amber-400', dot: 'bg-amber-400',
             banner: 'bg-amber-500/5 border-amber-500/25', text: 'text-amber-300', iconBg: 'bg-amber-500/15 text-amber-300',
             pill: 'bg-amber-500/10 text-amber-300 border-amber-500/25' },
    bad:   { chip: 'bg-rose-500/10 border border-rose-500/20 text-rose-400', dot: 'bg-rose-400',
             banner: 'bg-rose-500/5 border-rose-500/25', text: 'text-rose-300', iconBg: 'bg-rose-500/15 text-rose-300',
             pill: 'bg-rose-500/10 text-rose-300 border-rose-500/25' },
    idle:  { chip: 'bg-slate-500/10 border border-slate-600/40 text-slate-400', dot: 'bg-slate-400',
             banner: 'bg-slate-900 border-slate-700', text: 'text-slate-200', iconBg: 'bg-slate-700 text-slate-300',
             pill: 'bg-slate-800 text-slate-300 border-slate-600' },
}
const THEME_FOR = { active: 'ok', expiring: 'warn', grace: 'warn', expired: 'bad', revoked: 'bad', suspended: 'bad', invalid: 'bad', unlicensed: 'idle' }

const meta = computed(() => {
    const state = s.value.state || (s.value.activated ? (s.value.valid ? 'active' : 'invalid') : 'unlicensed')
    return { ...STATES[state] || STATES.invalid, ...THEME[THEME_FOR[state] || 'bad'] }
})

const validityHint = computed(() => {
    const st = s.value.state
    if (st === 'grace') return { text: `Grace: ~${s.value.graceHoursLeft ?? 0}h left`, class: 'text-amber-400 font-bold' }
    if (st === 'expired') return { text: 'Expired', class: 'text-rose-400 font-bold' }
    if (st === 'revoked' || st === 'suspended') return { text: 'License disabled', class: 'text-rose-400 font-bold' }
    const dl = s.value.daysLeft
    if (dl == null) return { text: '—', class: 'text-slate-500' }
    // dl can be 0 while the license is still valid (expires later today) — that's
    // "expires today", NOT expired. Only state === 'expired' means expired.
    if (dl <= 0) return { text: 'Expires today', class: 'text-amber-400 font-bold' }
    return { text: `${dl} day${dl === 1 ? '' : 's'} remaining`, class: dl <= 7 ? 'text-amber-400 font-bold' : 'text-pool-felt-400 font-bold' }
})

function fmtDate(iso) { if (!iso) return '—'; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' }) }
function fmtDateTime(iso) { if (!iso) return '—'; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString([], { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }

const showLogout = ref(false)
const loggingOut = ref(false)
async function confirmLogout() {
    loggingOut.value = true
    try { await deactivateLicense() }        // clears the session + returns to the sign-in screen
    catch (e) { console.error(e) }
    finally { loggingOut.value = false; showLogout.value = false }
}

// ── branding upload ──
const fileInput = ref(null)
const selectedFile = ref(null)
const localPreview = ref(null)
const saving = ref(false)
const preview = computed(() => localPreview.value || s.value.logoUrl || '')
const pickFile = () => fileInput.value?.click()

function resolveLogoSrc(url) {
    if (!url) return ''
    if (url.startsWith('blob:') || url.startsWith('http')) return url
    return API_URL + url
}
function onFileSelect(event) {
    const file = event.target.files?.[0]
    if (!file) return
    revoke(); selectedFile.value = file; localPreview.value = URL.createObjectURL(file)
}
async function handleSave() {
    if (!selectedFile.value) return
    saving.value = true
    try {
        const fd = new FormData(); fd.append('logo', selectedFile.value)
        const res = await authFetch(API_URL + '/license/logo', { method: 'POST', body: fd })
        if (res && res.ok) {
            const data = await res.json()
            if (data.logoUrl && status.value) status.value.logoUrl = data.logoUrl
            revoke(); selectedFile.value = null; localPreview.value = null
        }
    } catch (err) { console.error('Failed to upload logo:', err) }
    finally { saving.value = false; loadBranding() }
}
function clearImage() {
    revoke(); selectedFile.value = null; localPreview.value = null
    if (status.value) status.value.logoUrl = ''
    if (fileInput.value) fileInput.value.value = ''
}
function revoke() { if (localPreview.value) URL.revokeObjectURL(localPreview.value) }

usePageBackground('#0f172a')
</script>