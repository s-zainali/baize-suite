<template>
    <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md"
        @click.self="emit('close')">
        <div
            class="relative w-full max-w-sm max-h-[92vh] overflow-y-auto rounded-3xl border border-slate-700 bg-slate-900 p-7 shadow-2xl text-center">

            <!-- confirmed tick -->
            <div class="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/15">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="3"
                    stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6L9 17l-5-5" />
                </svg>
            </div>
            <h2 class="text-lg font-black text-white">Booking Confirmed</h2>
            <p class="mt-1 text-[11px] text-slate-500">Show this code at the counter to claim your table.</p>


            <!-- the code -->
            <p class="mt-5 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Booking Code</p>
            <p class="mt-1 font-mono text-4xl font-black tracking-[0.35em] text-white pl-[0.35em]">{{ code || '—' }}</p>

            <!-- details, so the screenshot is self-contained -->
            <div class="mt-5 space-y-1.5 rounded-2xl border border-slate-800 bg-slate-950/40 px-4 py-3 text-left">
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Club</span>
                    <span class="text-xs font-bold text-white">{{ club }}</span>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Branch</span>
                    <span class="text-xs font-bold text-white">{{ branch }}</span>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Lounge</span>
                    <span class="text-xs font-bold text-white">{{ lounge }}</span>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Station</span>
                    <span class="text-xs font-bold text-white">{{ typeLabel(tableType) }} #{{ tableNumber }}</span>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Date</span>
                    <span class="text-xs font-bold text-white">{{ dateLabel }}</span>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Time</span>
                    <span class="text-xs font-bold text-white">{{ timeLabel }}</span>
                </div>
            </div>

            <p class="mt-4 text-[11px] font-bold text-emerald-400">
                📸 Screenshot this screen so you don't lose your code.
            </p>

            <button @click="emit('close')"
                class="mt-5 w-full rounded-xl bg-emerald-600 py-3 text-xs font-black text-white transition-all hover:bg-emerald-500 cursor-pointer">
                DONE
            </button>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { typeLabel } from '@baize/ui'

const props = defineProps({
    code: { type: String, default: '' },
    club: { type: String, default: '' },
    branch: { type: String, default: '' },
    lounge: { type: String, default: '' },
    tableType: { type: String, default: '' },
    tableNumber: { type: [String, Number], default: '' },
    date: { type: String, default: '' },        // 'YYYY-MM-DD'
    startTime: { type: String, default: '' },    // 'HH:MM'
    endTime: { type: String, default: '' },      // 'HH:MM'
})
const emit = defineEmits(['close'])


// ── date / time display ────────────────────────────────────────────────────
const to12h = (hm) => {
    if (!hm) return ''
    const [h, m] = hm.split(':').map(Number)
    const period = h >= 12 ? 'PM' : 'AM'
    const hr = h % 12 || 12
    return `${hr}:${String(m).padStart(2, '0')} ${period}`
}
const dateLabel = computed(() => {
    if (!props.date) return ''
    const d = new Date(`${props.date}T00:00:00`)
    return isNaN(d) ? props.date
        : d.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
})
const timeLabel = computed(() => `${to12h(props.startTime)} – ${to12h(props.endTime)}`)

// ── the seal ────────────────────────────────────────────────────────────────
// A hypotrochoid (spirograph) curve — the interwoven line used on banknotes and
// certificates. Its shape is fully determined by the code, so it's the same
// every time for a real booking and effectively impossible to redraw freehand.
function fnv(s) {
    let h = 2166136261 >>> 0
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0 }
    return h >>> 0
}
function gcd(a, b) { while (b) { [a, b] = [b, a % b] } return a }

function buildLayer(code, layer) {
    const seed = fnv(`${code}::${layer}`)
    let R = 7 + (seed % 7)                    // 7..13
    const r = 3 + ((seed >>> 3) % 4)          // 3..6   (unsigned shift: never degenerate)
    const d = 3 + ((seed >>> 6) % 5)          // 3..7
    // Coprime R,r makes the curve weave R cusps over r turns instead of closing
    // in a single sparse pass — that density is what reads as a guilloché.
    let guard = 0
    while (gcd(R, r) !== 1 && guard < 12) { R++; guard++ }
    const turns = r                           // == r / gcd(R,r) once coprime
    const N = Math.round(240 * turns)
    const k = (R - r) / r

    const pts = []
    let maxr = 0.0001
    for (let i = 0; i <= N; i++) {
        const th = 2 * Math.PI * turns * i / N
        const x = (R - r) * Math.cos(th) + d * Math.cos(k * th)
        const y = (R - r) * Math.sin(th) - d * Math.sin(k * th)
        pts.push([x, y])
        const rad = Math.hypot(x, y)
        if (rad > maxr) maxr = rad
    }
    const scale = 58 / maxr                   // fit inside the 160×160 viewBox
    const path = pts
        .map(([x, y], i) => `${i ? 'L' : 'M'}${(80 + x * scale).toFixed(2)} ${(80 + y * scale).toFixed(2)}`)
        .join(' ')
    return { path, h: seed % 360 }
}

const layers = computed(() => [buildLayer(props.code || '·', 0), buildLayer(props.code || '·', 1)])
const hue = (h, alpha) => `hsla(${h}, 70%, 62%, ${alpha})`
</script>