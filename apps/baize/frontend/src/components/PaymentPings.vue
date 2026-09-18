<template>
    <div class="pointer-events-none fixed bottom-5 right-5 z-[80] flex w-72 flex-col gap-2">
        <TransitionGroup name="ping">
            <div v-for="ping in visible" :key="ping.token"
                class="pointer-events-auto overflow-hidden rounded-2xl border border-emerald-500/40 bg-slate-900 shadow-2xl shadow-emerald-950/40">
                <div class="flex items-start gap-3 p-4">
                    <span
                        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/15 text-emerald-400">
                        ✓
                    </span>
                    <div class="min-w-0 flex-1">
                        <p class="text-[9px] font-black uppercase tracking-widest text-emerald-500">
                            Payment Received
                        </p>
                        <p class="mt-0.5 truncate text-sm font-black text-white">
                            {{ ping.paidBy || 'Guest' }}
                        </p>
                        <p class="font-mono text-[10px] text-slate-500">
                            {{ methodLabel(ping.method) }}{{ ping.reference ? ` · ${ping.reference}` : '' }}
                        </p>
                    </div>
                    <div class="shrink-0 text-right">
                        <p class="font-mono text-sm font-black text-emerald-400">Rs {{ ping.amount }}</p>
                        <button @click="dismiss(ping.token)"
                            class="mt-1 cursor-pointer text-[9px] font-bold text-slate-600 hover:text-slate-400">
                            Dismiss
                        </button>
                    </div>
                </div>
                <!-- Drains so it's obvious the card will go on its own -->
                <div class="h-0.5 bg-emerald-500/70 ping-drain" />
            </div>
        </TransitionGroup>
    </div>
</template>

<script setup>
/**
 * Announces payments made by scanning a receipt QR.
 *
 * The server marks each payment seen when it hands it over, so a payment pings
 * once even with the dashboard and the canteen both polling.
 */
import { ref, onUnmounted } from 'vue'
import { authFetch, API_URL } from '@/Auth.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'

const props = defineProps({
    /** How long a card stays before fading, in ms. */
    dwell: { type: Number, default: 5000 },
})
const emit = defineEmits(['received'])

const visible = ref([])
const timers = new Map()

const METHODS = { easypaisa: 'EasyPaisa', jazzcash: 'JazzCash' }
const methodLabel = (id) => METHODS[id] || 'Paid'

function dismiss(token) {
    visible.value = visible.value.filter((p) => p.token !== token)
    clearTimeout(timers.get(token))
    timers.delete(token)
}

async function poll() {
    try {
        const res = await authFetch(`${API_URL}/payments/recent`)
        if (!res.ok) return
        const data = await res.json()
        for (const payment of data.payments || []) {
            if (visible.value.some((p) => p.token === payment.token)) continue
            visible.value.unshift(payment)
            timers.set(payment.token, setTimeout(() => dismiss(payment.token), props.dwell))
            emit('received', payment)
        }
    } catch {
        // A missed poll is harmless: the payment stays unseen and arrives next time.
    }
}

useAutoRefresh(poll, 5000)
onUnmounted(() => {
    for (const timer of timers.values()) clearTimeout(timer)
    timers.clear()
})
</script>

<style scoped>
.ping-enter-active,
.ping-leave-active { transition: all 0.25s ease; }
.ping-enter-from { opacity: 0; transform: translateX(1rem); }
.ping-leave-to { opacity: 0; transform: translateX(1rem); }

.ping-drain { animation: drain 5s linear forwards; transform-origin: left; }
@keyframes drain { from { transform: scaleX(1); } to { transform: scaleX(0); } }

@media (prefers-reduced-motion: reduce) {
    .ping-drain { animation: none; }
    .ping-enter-from, .ping-leave-to { transform: none; }
}
</style>