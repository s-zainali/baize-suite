<template>
    <AdminShell>
      <div class="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl mb-16">
        <h2 class="text-lg font-black text-white uppercase tracking-wider mb-6 pb-4 border-b border-slate-800/60">Audit Log</h2>
        <div v-if="loading" class="py-16 text-center text-slate-500 font-mono text-sm">Loading…</div>
        <div v-else-if="!rows.length" class="py-16 text-center text-slate-500">No activity recorded yet.</div>
        <ul v-else class="space-y-2">
          <li v-for="e in rows" :key="e.id" class="flex items-start gap-4 bg-slate-950/40 border border-slate-800/70 rounded-2xl px-4 py-3">
            <span class="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/50 border border-emerald-900/60 px-2 py-1 rounded-lg shrink-0 uppercase tracking-wider">{{ e.action }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-slate-200">{{ e.summary || e.action }}</p>
              <p class="text-[10px] font-mono text-slate-500 truncate">{{ e.targetType }}:{{ e.targetId }}<span v-if="e.meta.clubUuid"> · {{ e.meta.clubUuid }}</span></p>
            </div>
            <span class="text-[11px] text-slate-500 shrink-0">{{ fmtDateTime(e.createdAt) }}</span>
          </li>
        </ul>
        <div v-if="meta.pages > 1" class="flex justify-center items-center gap-3 mt-6 text-xs font-bold text-slate-400">
          <button @click="go(page - 1)" :disabled="page <= 1" class="px-3 py-1.5 rounded-lg bg-slate-800 disabled:opacity-40 cursor-pointer">Prev</button>
          <span>Page {{ meta.page }} / {{ meta.pages }}</span>
          <button @click="go(page + 1)" :disabled="page >= meta.pages" class="px-3 py-1.5 rounded-lg bg-slate-800 disabled:opacity-40 cursor-pointer">Next</button>
        </div>
      </div>
    </AdminShell>
  </template>
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useAdmin } from '@/stores/admin.js'
  import { useToast } from '@/composables/useToast.js'
  import { fmtDateTime } from '@/composables/actions.js'
  import AdminShell from '@/components/AdminShell.vue'
  
  const admin = useAdmin(); const toast = useToast()
  const rows = ref([]); const meta = ref({}); const loading = ref(false); const page = ref(1)
  async function fetchEvents() {
    loading.value = true
    try { const d = await admin.events({ page: page.value, perPage: 40 }); rows.value = d.items; meta.value = { page: d.page, pages: d.pages } }
    catch (e) { toast.error(e.message) } finally { loading.value = false }
  }
  function go(p) { page.value = p; fetchEvents() }
  onMounted(fetchEvents)
  </script>