<template>
    <AdminShell>
      <!-- Stat strip -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        <div v-for="s in statCards" :key="s.label" class="bg-slate-900/60 border border-slate-800/80 rounded-2xl px-4 py-3.5">
          <p class="text-2xl font-black" :class="s.color">{{ s.value }}</p>
          <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">{{ s.label }}</p>
        </div>
      </div>
  
      <!-- Venues (full width — dashboard is read-only; mint from a venue's page) -->
      <div class="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 sm:p-8 backdrop-blur-md shadow-2xl pb-8">
        <div class="flex flex-wrap gap-4 justify-between items-center mb-6 pb-4 border-b border-slate-800/60">
          <div>
            <h2 class="text-lg font-black text-white uppercase tracking-wider">Registered Venues</h2>
            <p class="text-xs text-slate-400 mt-0.5">Open a venue to view detail, manage devices and mint licenses.</p>
          </div>
          <input v-model="search" @input="debouncedFetch" placeholder="Search name, email, ID, city…"
            class="bg-slate-950 border border-slate-800 focus:border-emerald-600 rounded-xl px-4 py-2 text-xs font-bold text-white outline-none w-64 placeholder:text-slate-600 placeholder:font-normal">
        </div>
  
        <div v-if="loading" class="flex flex-col items-center justify-center py-20 text-slate-500 font-mono text-sm gap-3">
          <div class="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Loading venues…</span>
        </div>
        <div v-else-if="!clubs.length" class="flex flex-col items-center justify-center text-center py-20 text-slate-500 bg-slate-950/40 border-2 border-dashed border-slate-800/80 rounded-3xl">
          <span class="text-4xl mb-3 opacity-40">📡</span>
          <p class="text-sm font-bold text-slate-300">No venues found</p>
          <p class="text-xs text-slate-500 mt-1">{{ search ? 'Try a different search.' : 'Venues appear here once they register.' }}</p>
        </div>
  
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <router-link v-for="club in clubs" :key="club.uuid" :to="`/club/${club.uuid}`"
            class="group bg-slate-900 border-2 border-slate-800/90 hover:border-emerald-600/70 rounded-3xl p-5 transition-all flex flex-col justify-between">
            <div>
              <div class="flex justify-between items-start gap-2 mb-3">
                <span class="text-[10px] font-mono font-bold text-slate-400 uppercase bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">{{ club.city || 'Global' }}</span>
                <div class="flex flex-wrap gap-1.5 justify-end">
                  <StatusPill v-if="!club.isActive" status="suspended" label="Suspended" />
                  <StatusPill :status="club.plan" />
                  <StatusPill :status="club.licenseStatus" :label="licLabel(club.licenseStatus)" />
                </div>
              </div>
              <h3 class="font-black text-base tracking-tight text-white group-hover:text-emerald-400 transition-colors mb-1">{{ club.clubName }}</h3>
              <p class="text-xs font-bold text-slate-300 truncate">{{ club.email }}</p>
              <p class="text-[11px] text-slate-400 mt-0.5">{{ club.ownerName || 'No contact' }} · {{ club.licenseCount }} license(s) · {{ club.deviceCount }} device(s)</p>
            </div>
            <div class="pt-3.5 mt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
              <span class="text-slate-500 truncate max-w-[150px]">{{ club.uuid }}</span>
              <span class="font-bold text-slate-400 group-hover:text-emerald-400">Details →</span>
            </div>
          </router-link>
        </div>
      </div>
    </AdminShell>
  </template>
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useAdmin } from '@/stores/admin.js'
  import { useToast } from '@/composables/useToast.js'
  import AdminShell from '@/components/AdminShell.vue'
  import StatusPill from '@/components/ui/StatusPill.vue'
  
  const admin = useAdmin()
  const toast = useToast()
  
  const clubs = ref([])
  const stats = ref({})
  const loading = ref(false)
  const search = ref('')
  
  const statCards = computed(() => [
    { label: 'Venues', value: stats.value.clubs ?? '—', color: 'text-white' },
    { label: 'Active', value: stats.value.activeLicenses ?? '—', color: 'text-emerald-400' },
    { label: 'Expiring', value: stats.value.expiringSoon ?? '—', color: 'text-amber-400' },
    { label: 'Expired', value: stats.value.expiredLicenses ?? '—', color: 'text-slate-300' },
    { label: 'Revoked', value: stats.value.revokedLicenses ?? '—', color: 'text-rose-400' },
    { label: 'Devices', value: stats.value.devices ?? '—', color: 'text-indigo-300' },
  ])
  
  const licLabel = (s) => ({ active: 'Active', expired: 'Expired', revoked: 'Revoked' }[s] || 'No license')
  
  let timer
  function debouncedFetch() { clearTimeout(timer); timer = setTimeout(fetchClubs, 300) }
  async function fetchClubs() {
    loading.value = true
    try { clubs.value = (await admin.clubs({ q: search.value, perPage: 100 })).items }
    catch (e) { toast.error(e.message) } finally { loading.value = false }
  }
  async function fetchStats() { try { stats.value = await admin.stats() } catch (e) { toast.error(e.message) } }
  
  onMounted(() => { fetchStats(); fetchClubs() })
  </script>