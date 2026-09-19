<template>
    <!-- Only meaningful when this install actually syncs (hybrid). Hidden on local-only. -->
    <div v-if="status && status.syncing" class="flex items-center gap-2" :title="tip">
        <span class="relative flex h-2.5 w-2.5">
            <span v-if="state === 'ok'" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60"></span>
            <span class="relative inline-flex h-2.5 w-2.5 rounded-full" :class="dotClass"></span>
        </span>
        <span class="text-[10px] font-black uppercase tracking-widest" :class="textClass">{{ label }}</span>
        <span v-if="backlog" class="rounded-full bg-slate-700/60 px-1.5 py-0.5 text-[9px] font-bold text-slate-300">{{ backlog }}</span>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSyncStatus } from '@/composables/useSyncStatus.js'

const { status } = useSyncStatus()

const backlog = computed(() => {
    const p = status.value?.pending || {}
    return Object.values(p).reduce((a, b) => a + b, 0) || 0
})
const state = computed(() => {
    if (!status.value) return 'ok'
    if (!status.value.online) return 'off'
    return backlog.value ? 'busy' : 'ok'
})
const label = computed(() => ({ ok: 'Synced', busy: 'Syncing', off: 'Offline' }[state.value]))
const dotClass = computed(() => ({ ok: 'bg-emerald-400', busy: 'bg-amber-400', off: 'bg-rose-500' }[state.value]))
const textClass = computed(() => ({ ok: 'text-emerald-400', busy: 'text-amber-400', off: 'text-rose-400' }[state.value]))
const tip = computed(() => {
    const s = status.value
    if (!s) return ''
    if (!s.online) return `Offline — ${s.consecutiveFailures} failed attempt(s). ${s.lastError || ''}`.trim()
    if (backlog.value) return `${backlog.value} change(s) waiting to sync`
    return `Up to date${s.lastPushAt ? ` · last push ${new Date(s.lastPushAt).toLocaleTimeString()}` : ''}`
})
</script>