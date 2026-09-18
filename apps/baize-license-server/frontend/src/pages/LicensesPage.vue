<template>
    <AdminShell>
      <div class="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl mb-16">
        <div class="flex flex-wrap gap-4 justify-between items-center mb-6 pb-4 border-b border-slate-800/60">
          <div>
            <h2 class="text-lg font-black text-white uppercase tracking-wider">All Licenses</h2>
            <p class="text-xs text-slate-400 mt-0.5">{{ meta.total ?? 0 }} total · every token issued across all venues.</p>
          </div>
          <div class="flex gap-2">
            <select v-model="status" @change="fetchLicenses" class="bg-slate-950 border border-slate-800 focus:border-emerald-600 rounded-xl px-3 py-2 text-xs font-bold text-white outline-none">
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="expired">Expired</option>
              <option value="revoked">Revoked</option>
            </select>
            <input v-model="search" @input="debounced" placeholder="Search venue / code…"
              class="bg-slate-950 border border-slate-800 focus:border-emerald-600 rounded-xl px-4 py-2 text-xs font-bold text-white outline-none w-52 placeholder:text-slate-600 placeholder:font-normal">
          </div>
        </div>
  
        <div v-if="loading" class="py-16 text-center text-slate-500 font-mono text-sm">Loading…</div>
        <div v-else-if="!rows.length" class="py-16 text-center text-slate-500">No licenses match.</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-800/60">
                <th class="py-3 pr-4 font-bold">Venue</th>
                <th class="py-3 px-4 font-bold">Status</th>
                <th class="py-3 px-4 font-bold">Binding</th>
                <th class="py-3 px-4 font-bold">Expires</th>
                <th class="py-3 px-4 font-bold">Code</th>
                <th class="py-3 pl-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in rows" :key="l.id" class="border-b border-slate-800/40 hover:bg-slate-900/40">
                <td class="py-3 pr-4">
                  <router-link :to="`/club/${l.clubUuid}`" class="font-bold text-white hover:text-emerald-400">{{ l.clubName }}</router-link>
                  <p class="text-[10px] font-mono text-slate-500">{{ l.clubUuid }}</p>
                </td>
                <td class="py-3 px-4"><StatusPill :status="l.status" /></td>
                <td class="py-3 px-4 text-xs text-slate-400">{{ l.deviceBound ? `${l.deviceCount} device(s)` : 'Unbound' }}</td>
                <td class="py-3 px-4 text-xs text-slate-300">{{ fmtDate(l.expiresAt) }}<span v-if="l.status==='active'" class="text-slate-500"> · {{ l.daysLeft }}d</span></td>
                <td class="py-3 px-4 font-mono text-xs text-slate-400">{{ l.activationCode }}</td>
                <td class="py-3 pl-4">
                  <div class="flex gap-1.5 justify-end">
                    <button @click="copy(l.activationCode, 'Code')" class="px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">Code</button>
                    <button @click="askRenew(l)" class="px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">Renew</button>
                    <button v-if="l.status !== 'revoked'" @click="askRevoke(l)" class="px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-rose-950/70 border border-rose-900 text-rose-300 hover:bg-rose-900/60 cursor-pointer">Revoke</button>
                    <button v-else @click="doUnrevoke(l)" class="px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-emerald-950/70 border border-emerald-800 text-emerald-300 hover:bg-emerald-900/60 cursor-pointer">Restore</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
  
        <div v-if="meta.pages > 1" class="flex justify-center items-center gap-3 mt-6 text-xs font-bold text-slate-400">
          <button @click="go(page - 1)" :disabled="page <= 1" class="px-3 py-1.5 rounded-lg bg-slate-800 disabled:opacity-40 cursor-pointer">Prev</button>
          <span>Page {{ meta.page }} / {{ meta.pages }}</span>
          <button @click="go(page + 1)" :disabled="page >= meta.pages" class="px-3 py-1.5 rounded-lg bg-slate-800 disabled:opacity-40 cursor-pointer">Next</button>
        </div>
      </div>
  
      <ConfirmModal :open="!!revokeTarget" title="Revoke license?" danger confirm-label="Revoke" :busy="busy"
        :message="`This immediately stops ${revokeTarget?.clubName}'s license from activating online. You can restore it later.`"
        @confirm="doRevoke" @cancel="revokeTarget = null" />
      <RenewModal :open="!!renewTarget" :busy="busy" @confirm="doRenew" @cancel="renewTarget = null" />
    </AdminShell>
  </template>
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useAdmin } from '@/stores/admin.js'
  import { useToast } from '@/composables/useToast.js'
  import { copy, fmtDate } from '@/composables/actions.js'
  import AdminShell from '@/components/AdminShell.vue'
  import StatusPill from '@/components/ui/StatusPill.vue'
  import ConfirmModal from '@/components/ui/ConfirmModal.vue'
  import RenewModal from '@/components/ui/RenewModal.vue'
  
  const admin = useAdmin(); const toast = useToast()
  const rows = ref([]); const meta = ref({}); const loading = ref(false)
  const status = ref(''); const search = ref(''); const page = ref(1)
  const revokeTarget = ref(null); const renewTarget = ref(null); const busy = ref(false)
  
  async function fetchLicenses() {
    loading.value = true
    try {
      const data = await admin.licenses({ status: status.value, q: search.value, page: page.value, perPage: 25 })
      rows.value = data.items; meta.value = { total: data.total, page: data.page, pages: data.pages }
    } catch (e) { toast.error(e.message) } finally { loading.value = false }
  }
  let timer; function debounced() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchLicenses() }, 300) }
  function go(p) { page.value = p; fetchLicenses() }
  
  function askRevoke(l) { revokeTarget.value = l }
  function askRenew(l) { renewTarget.value = l }
  async function doRevoke() {
    busy.value = true
    try { await admin.revoke(revokeTarget.value.id); toast.success('License revoked.'); revokeTarget.value = null; fetchLicenses() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  async function doUnrevoke(l) {
    try { await admin.unrevoke(l.id); toast.success('License restored.'); fetchLicenses() } catch (e) { toast.error(e.message) }
  }
  async function doRenew(days) {
    busy.value = true
    try { await admin.renew(renewTarget.value.id, days); toast.success('License renewed.'); renewTarget.value = null; fetchLicenses() }
    catch (e) { toast.error(e.message) } finally { busy.value = false }
  }
  onMounted(fetchLicenses)
  </script>