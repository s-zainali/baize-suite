<template>
    <AdminShell>
      <router-link to="/dashboard" class="text-xs font-bold text-slate-400 hover:text-white mb-4 inline-block">← Back to venues</router-link>
  
      <div v-if="loading" class="py-20 text-center text-slate-500 font-mono text-sm">Loading venue…</div>
      <div v-else-if="!club" class="py-20 text-center text-slate-500">Venue not found.</div>
  
      <div v-else class="space-y-6 pb-16">
        <!-- Club header -->
        <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-2xl">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0">
              <div class="flex gap-1.5 mb-2">
                <StatusPill :status="club.plan" />
                <StatusPill v-if="!club.isActive" status="suspended" label="Suspended" />
              </div>
              <h1 class="text-2xl font-black text-white tracking-tight">{{ club.clubName }}</h1>
              <p class="text-xs font-mono text-slate-500">{{ club.uuid }}</p>
            </div>
            <!-- Customer Registry -->
            <div class="transition duration-300 ease-in-out flex gap-4 items-center bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 shadow-2xl">
                <div class="flex flex-col gap-1">
                    <h2 class="text-sm font-black text-white uppercase tracking-wider text-nowrap">Customer App Visibility</h2>
                    <div class="flex gap-2 items-center">
                        <div class="relative w-2 h-2 rounded" :class="registered ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'">
                        </div>
                        <p class="text-xs" :class="registered ? 'text-emerald-500' : 'text-rose-500'">{{ registered? 'Club Active' : 'Not registered' }}</p>
                    </div>
                </div>
                <input v-if="!registered" v-model="clubPublicURL" placeholder="https://club-baize.onrender.com"
                  class="w-80 bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-lg px-3 py-2 text-sm text-slate-100 tracking-wide font-mono outline-none">
                <button @click="toggleRegistration()" :disabled="registering" class="w-30 py-3 rounded-xl text-xs font-black uppercase tracking-widest border disabled:bg-slate-800 disabled:text-slate-500 text-white cursor-pointer px-4"
                :class="registered? ' bg-rose-900 border-rose-700 hover:border-rose-600' : 'bg-emerald-800 border-emerald-600 hover:border-emerald-500'">
                    {{ registered? 'Deregister' : 'Register' }}
                  </button>
            </div>
            <div class="flex gap-2 shrink-0">
              <button @click="editing = true" class="px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-wider bg-slate-800 text-slate-200 hover:bg-slate-700 cursor-pointer">Edit</button>
              <button @click="toggleSuspend" class="px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-wider cursor-pointer"
                :class="club.isActive ? 'bg-rose-950/60 border border-rose-900 text-rose-300 hover:bg-rose-900/50' : 'bg-emerald-950/60 border border-emerald-800 text-emerald-300 hover:bg-emerald-900/50'">
                {{ club.isActive ? 'Suspend' : 'Reactivate' }}
              </button>
            </div>
          </div>
          <dl class="mt-4 pt-4 border-t border-slate-800/60 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
            <div><dt class="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Email</dt><dd class="text-slate-200 font-bold truncate">{{ club.email }}</dd></div>
            <div><dt class="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Owner</dt><dd class="text-slate-200 truncate">{{ club.ownerName || '—' }}</dd></div>
            <div><dt class="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Phone</dt><dd class="text-slate-200 truncate">{{ club.phone || '—' }}</dd></div>
            <div><dt class="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Location</dt><dd class="text-slate-200 truncate">{{ [club.city, club.country].filter(Boolean).join(', ') || '—' }}</dd></div>
            <div><dt class="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Registered</dt><dd class="text-slate-200">{{ fmtDate(club.createdAt) }}</dd></div>
          </dl>
          <p v-if="club.notes" class="mt-4 pt-4 border-t border-slate-800/60 text-xs text-slate-400 leading-relaxed">{{ club.notes }}</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Branches (primary) -->
          <div class="lg:col-span-8 space-y-6">
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-2xl">
              <h2 class="text-lg font-black text-white uppercase tracking-wider mb-1">Branches ({{ branches.length }})</h2>
              <p class="text-xs text-slate-400 mb-5">Every branch — including the club's main branch — is registered here with its own signed licence and feature set. The club activates each one from the app.</p>

              <!-- Register a branch -->
              <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4 mb-5">
                <label class="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Register a branch</label>
                <input v-model="newBranch.name" placeholder="Branch name (e.g. Main Branch, Blue Area)"
                  class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-lg px-3 py-2 text-sm text-white outline-none mb-2">
                <input v-model="newBranch.address" placeholder="Address (e.g. Plot 12, Phase 2, DHA, Islamabad)"
                  class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-lg px-3 py-2 text-sm text-white outline-none mb-3">
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  <label v-for="m in MODULE_LIST" :key="m.key" class="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-[11px] font-bold text-slate-300 cursor-pointer hover:border-slate-600">
                    <input type="checkbox" :value="m.key" v-model="newBranch.modules" class="accent-emerald-500"> {{ m.label }}
                  </label>
                </div>
                <button @click="registerBranch" :disabled="registeringBranch || !newBranch.name.trim()"
                  class="px-5 py-2 rounded-lg text-xs font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white cursor-pointer">
                  {{ registeringBranch ? 'Registering…' : 'Register Branch' }}
                </button>
              </div>

              <!-- Existing branches -->
              <div v-if="branches.length" class="space-y-3">
                <div v-for="b in branches" :key="b.id" @click="selectedId = b.id"
                  class="rounded-xl border bg-slate-950/40 p-4 cursor-pointer transition-colors"
                  :class="selectedId === b.id ? 'border-emerald-500 ring-1 ring-emerald-500/40' : 'border-slate-800 hover:border-slate-600'">
                  <div class="flex items-center justify-between gap-3 mb-3">
                    <div class="min-w-0">
                      <p class="text-sm font-black text-white truncate">{{ b.name }}</p>
                      <p class="text-[11px] text-slate-400 truncate">{{ b.address || '—' }}</p>
                      <p class="text-[10px] font-mono text-slate-500 truncate">{{ b.uid }} · exp {{ fmtDate(b.expiresAt) }}</p>
                    </div>
                    <StatusPill :status="b.status" />
                  </div>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                    <label v-for="m in MODULE_LIST" :key="m.key" class="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-[10px] font-bold text-slate-300 cursor-pointer hover:border-slate-600">
                      <input type="checkbox" :value="m.key" v-model="b._draft" class="accent-emerald-500"> {{ m.label }}
                    </label>
                  </div>
                  <div class="flex items-center gap-2 flex-wrap">
                    <button @click="saveBranchFeatures(b)" class="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-emerald-700 text-white hover:bg-emerald-600 cursor-pointer">Save features</button>
                    <button v-if="b.activationCode" @click="copy(b.activationCode, 'Code')" class="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-200 hover:bg-slate-700 cursor-pointer">Code: {{ b.activationCode }}</button>
                    <button v-if="b.token" @click="copy(b.token, 'Token')" class="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-200 hover:bg-slate-700 cursor-pointer">Copy token</button>
                    <button @click="toggleBranchRevoke(b)" class="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider cursor-pointer ml-auto"
                      :class="b.status === 'revoked' ? 'bg-emerald-600 text-white hover:bg-emerald-500' : 'bg-rose-700 text-slate-200 hover:bg-rose-600'">
                      {{ b.status === 'revoked' ? 'Unrevoke' : 'Revoke' }}
                    </button>
                  </div>
                </div>
              </div>
              <p v-else class="text-xs text-slate-500">No branches registered yet.</p>
            </div>
          </div>

          <!-- Side: account licence + devices -->
          <div class="lg:col-span-4 space-y-6">
            <!-- Branch licence (mint the SELECTED branch) -->
            <div class="rounded-2xl p-6 shadow-2xl border"
              :class="selectedBranch ? 'bg-slate-900/90 border-emerald-600/60' : 'bg-slate-900/60 border-slate-800/90'">
              <h2 class="text-base font-black text-white uppercase tracking-wider mb-1">Branch Licence</h2>
              <template v-if="selectedBranch">
                <p class="text-xs text-slate-400 mb-5">Minting <b class="text-emerald-400">{{ selectedBranch.name }}</b> — sets its expiry and binding and signs its current features into a fresh token.</p>
                <div class="space-y-4">
                  <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Duration (days)</label>
                    <input type="number" v-model.number="days" min="1" class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-sm font-bold text-white outline-none">
                  </div>
                  <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Binding</label>
                    <div class="flex rounded-xl border border-slate-800 bg-slate-950 p-1 text-[11px] font-bold h-[42px]">
                      <button type="button" @click="deviceLock = true" :class="deviceLock ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'" class="flex-1 rounded-lg cursor-pointer">Device-locked</button>
                      <button type="button" @click="deviceLock = false" :class="!deviceLock ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'" class="flex-1 rounded-lg cursor-pointer">Unbound</button>
                    </div>
                    <p v-if="deviceLock && !devices.length" class="text-[10px] text-amber-400/80">⚠ No device enrolled — a device-locked token won't activate anywhere.</p>
                  </div>
                  <button @click="mintBranchLicence" :disabled="issuing" class="w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white cursor-pointer">
                    {{ issuing ? 'Minting…' : `Mint ${selectedBranch.name}'s Licence` }}
                  </button>
                </div>
                <div v-if="selectedBranch.token" class="mt-6 pt-5 border-t border-slate-800/80">
                  <div class="flex justify-between items-center mb-2">
                    <label class="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Signed Token</label>
                    <span class="text-[10px] font-mono text-slate-400">code: <b class="text-slate-200">{{ selectedBranch.activationCode }}</b></span>
                  </div>
                  <textarea readonly rows="3" :value="selectedBranch.token" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-3 text-[10px] font-mono text-slate-300 select-all outline-none resize-none leading-relaxed"></textarea>
                  <div class="flex flex-wrap gap-2 mt-2">
                    <button @click="copy(selectedBranch.token, 'Token')" class="flex-1 py-2 rounded-lg text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">Copy</button>
                    <button @click="downloadKey(selectedBranch.token, selectedBranch.uid)" class="flex-1 py-2 rounded-lg text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">.key</button>
                    <button @click="copy(selectedBranch.activationCode, 'Code')" class="flex-1 py-2 rounded-lg text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">Code</button>
                  </div>
                </div>
              </template>
              <p v-else class="text-xs text-slate-500 py-8 text-center">Select a branch on the left to mint its licence.</p>
            </div>

            <!-- Devices -->
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-2xl">
              <h2 class="text-sm font-black text-white uppercase tracking-wider mb-4">Enrolled Devices ({{ devices.length }})</h2>
              <div v-if="!devices.length" class="text-xs text-slate-500 py-4 text-center">No devices enrolled.</div>
              <ul v-else class="space-y-2">
                <li v-for="d in devices" :key="d.id" class="flex items-center justify-between gap-3 bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2">
                  <div class="min-w-0">
                    <p class="text-[11px] font-bold text-slate-300 truncate">{{ d.label || 'Unlabelled device' }}</p>
                    <p class="text-[10px] font-mono text-slate-500 truncate">{{ d.fingerprint }}</p>
                  </div>
                  <button @click="removeDevice(d)" class="shrink-0 text-[10px] font-bold text-rose-400 hover:text-rose-300 cursor-pointer">Remove</button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit modal -->
      <div v-if="editing" class="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md" @click.self="editing = false">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl max-h-[85vh] overflow-y-auto">
          <h3 class="text-lg font-black text-white mb-5">Edit venue</h3>
          <div class="space-y-3">
            <input v-for="f in editFields" :key="f.k" v-model="editForm[f.k]" :placeholder="f.label"
              class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-sm font-bold text-white outline-none placeholder:text-slate-600 placeholder:font-normal">
            <select v-model="editForm.plan" class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-sm font-bold text-white outline-none">
              <option value="local">local</option><option value="online">online</option><option value="trial">trial</option>
            </select>
            <textarea v-model="editForm.notes" rows="3" placeholder="Internal notes" class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-sm text-white outline-none resize-none placeholder:text-slate-600"></textarea>
          </div>
          <div class="flex gap-3 justify-end mt-6">
            <button @click="editing = false" class="px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 cursor-pointer">Cancel</button>
            <button @click="saveEdit" :disabled="busy" class="px-5 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer disabled:opacity-50">{{ busy ? 'Saving…' : 'Save' }}</button>
          </div>
        </div>
      </div>
  
      <ConfirmModal :open="!!revokeTarget" title="Revoke license?" danger confirm-label="Revoke" :busy="busy"
        message="This immediately stops the license from activating online. You can restore it later."
        @confirm="doRevoke" @cancel="revokeTarget = null" />
      <ConfirmModal :open="!!deviceTarget" title="Remove device?" danger confirm-label="Remove" :busy="busy"
        message="Un-enrolls this device. Existing device-locked tokens that include it will stop matching on re-issue."
        @confirm="doRemoveDevice" @cancel="deviceTarget = null" />
      <RenewModal :open="!!renewTarget" :busy="busy" @confirm="doRenew" @cancel="renewTarget = null" />
    </AdminShell>
  </template>
  <script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { useAdmin } from '@/stores/admin.js'
  import { useToast } from '@/composables/useToast.js'
  import { copy, downloadKey, fmtDate } from '@/composables/actions.js'
  import AdminShell from '@/components/AdminShell.vue'
  import StatusPill from '@/components/ui/StatusPill.vue'
  import ConfirmModal from '@/components/ui/ConfirmModal.vue'
  import RenewModal from '@/components/ui/RenewModal.vue'
  
  const route = useRoute(); const admin = useAdmin(); const toast = useToast()
  const uuid = route.params.uuid
  const club = ref(null); const devices = ref([]); const licenses = ref([]); const loading = ref(true)
  const busy = ref(false)
  const days = ref(365)
  const branches = ref([])
  const registered = ref(false)
  const clubPublicURL = ref('')
  const newBranch = reactive({ name: '', address: '', modules: [] })
  const selectedId = ref(null)
  const selectedBranch = computed(() => branches.value.find((b) => b.id === selectedId.value) || null)
  const registeringBranch = ref(false)
  const deviceLock = ref(true)
  const issuing = ref(false)
  const issued = ref(null)
  const MODULE_LIST = [
    { key: 'playstation', label: 'PlayStation' },
    { key: 'xbox', label: 'Xbox' },
    { key: 'pc', label: 'PC' },
    { key: 'foosball', label: 'Foosball' },
    { key: 'tabletennis', label: 'Table Tennis' },
    { key: 'canteen', label: 'Canteen' },
    { key: 'insights', label: 'Insights' },
    { key: 'bookings', label: 'Bookings' },
    { key: 'payments', label: 'Automated Payments' },
  ]
  const editing = ref(false)
  const revokeTarget = ref(null); const renewTarget = ref(null); const deviceTarget = ref(null)
  const editForm = reactive({ clubName: '', ownerName: '', phone: '', address: '', city: '', country: '', plan: 'local', notes: '' })
  const editFields = [
    { k: 'clubName', label: 'Club name' }, { k: 'ownerName', label: 'Owner / contact' },
    { k: 'phone', label: 'Phone' }, { k: 'city', label: 'City' }, { k: 'country', label: 'Country' },
  ]
  
  async function loadBranches() {
    try {
      const d = await admin.branches(uuid)
      branches.value = (d.branches || []).map((b) => ({ ...b, _draft: [...(b.features || [])] }))
    } catch (e) { toast.error(e.message) }
  }
  async function registerBranch() {
    registeringBranch.value = true
    try {
      await admin.registerBranch(uuid, { name: newBranch.name.trim(), address: newBranch.address.trim(), features: newBranch.modules })
      toast.success('Branch registered.'); newBranch.name = ''; newBranch.address = ''; newBranch.modules = []; loadBranches()
    } catch (e) { toast.error(e.message) } finally { registeringBranch.value = false }
  }
  async function saveBranchFeatures(b) {
    try { await admin.updateBranch(b.id, { features: b._draft }); toast.success('Features updated.'); loadBranches() }
    catch (e) { toast.error(e.message) }
  }
  async function mintBranchLicence() {
    if (!selectedBranch.value) return
    issuing.value = true
    try {
      const body = { days: days.value }
      if (!deviceLock.value) body.devices = []     // unbound; else server binds club devices
      await admin.mintBranch(selectedId.value, body)
      toast.success(`Minted ${selectedBranch.value.name}'s licence.`); loadBranches()
    } catch (e) { toast.error(e.message) } finally { issuing.value = false }
  }
  async function toggleBranchRevoke(b) {
    try {
      await admin.revokeBranch(b.id, b.status === 'revoked')
      toast.success(b.status === 'revoked' ? 'Branch restored.' : 'Branch revoked.'); loadBranches()
    } catch (e) { toast.error(e.message) }
  }
  const registering = ref(false)
  async function toggleRegistration() {
    registering.value = true
    try {
      if (registered.value) {
        await admin.removeCustomerRegistry(uuid)
        toast.success('Club deregistered from the customer app.')
      } else {
        const url = clubPublicURL.value.trim()
        if (!url) { toast.error("Enter the club's public URL first."); return }
        await admin.createCustomerRegistry(uuid, url)
        toast.success('Club registered to the customer app.')
        clubPublicURL.value = ''
      }
      await load()   // refresh the registered flag from the server
    } catch (e) {
      toast.error(e.message)
    } finally {
      registering.value = false
    }
  }
  async function load() {
    loading.value = true
    try {
      const data = await admin.club(uuid)
      registered.value = data.registered
      club.value = data.club; devices.value = data.devices; licenses.value = data.licenses
      loadBranches()
      deviceLock.value = (data.club?.plan !== 'online')
      Object.assign(editForm, {
        clubName: data.club.clubName, ownerName: data.club.ownerName, phone: data.club.phone,
        address: data.club.address, city: data.club.city, country: data.club.country,
        plan: data.club.plan, notes: data.club.notes,
      })
    } catch (e) { toast.error(e.message); club.value = null } finally { loading.value = false }
  }
  
  async function saveEdit() {
    busy.value = true
    try { await admin.editClub(uuid, { ...editForm }); toast.success('Saved.'); editing.value = false; load() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  async function toggleSuspend() {
    try { await admin.editClub(uuid, { isActive: !club.value.isActive }); toast.success(club.value.isActive ? 'Venue suspended.' : 'Venue reactivated.'); load() }
    catch (e) { toast.error(e.message) }
  }
  function removeDevice(d) { deviceTarget.value = d }
  async function doRemoveDevice() {
    busy.value = true
    try { await admin.removeDevice(deviceTarget.value.id); toast.success('Device removed.'); deviceTarget.value = null; load() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  async function doRevoke() {
    busy.value = true
    try { await admin.revoke(revokeTarget.value.id); toast.success('License revoked.'); revokeTarget.value = null; load() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  async function doUnrevoke(l) {
    try { await admin.unrevoke(l.id); toast.success('License restored.'); load() } catch (e) { toast.error(e.message) }
  }
  async function doRenew(days) {
    busy.value = true
    try { await admin.renew(renewTarget.value.id, days); toast.success('License renewed.'); renewTarget.value = null; load() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  async function mint() {
    issuing.value = true; issued.value = null
    try {
      const body = { clubUuid: uuid, days: days.value }
      if (!deviceLock.value) body.devices = []
      const data = await admin.issue(body)
      issued.value = data.license
      toast.success('License minted.')
      load()
    } catch (e) { toast.error(e.message) } finally { issuing.value = false }
  }
  
  onMounted(load)
  </script>