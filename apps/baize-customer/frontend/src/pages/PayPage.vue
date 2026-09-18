<template>
    <div class="flex min-h-[100dvh] items-center justify-center bg-slate-950 p-4 text-slate-100">
        <div class="w-full max-w-sm">

            <div class="mb-6 text-center">
                <h1 class="text-2xl font-black tracking-tight">Baize</h1>
                <p class="mt-1 text-xs text-slate-500">Secure payment</p>
            </div>

            <div class="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
                <p v-if="loading" class="py-12 text-center text-xs font-bold text-slate-500">Loading…</p>

                <div v-else-if="error" class="py-8 text-center">
                    <div
                        class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-rose-500/40 bg-rose-500/10 text-xl text-rose-400">
                        !
                    </div>
                    <p class="text-sm font-bold text-rose-400">{{ error }}</p>
                    <p class="mt-2 text-[11px] text-slate-500">Ask the counter for a fresh code.</p>
                </div>

                <!-- Already settled: say so plainly rather than inviting a second payment -->
                <div v-else-if="payment.status === 'paid'" class="py-6 text-center">
                    <div
                        class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/15 text-2xl text-emerald-400">
                        ✓
                    </div>
                    <h2 class="text-lg font-black">Payment Received</h2>
                    <p class="mt-1 font-mono text-3xl font-black text-emerald-400">Rs {{ payment.amount }}</p>
                    <p class="mt-2 text-[11px] text-slate-500">
                        {{ payment.reference ? `Ref ${payment.reference} · ` : '' }}{{ methodLabel }}
                    </p>
                    <p class="mt-4 text-[10px] leading-relaxed text-slate-600">
                        Show this screen at the counter. The till has already been notified.
                    </p>
                </div>

                <div v-else>
                    <div class="border-b border-dashed border-slate-800 pb-5 text-center">
                        <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">
                            {{ kindLabel }}
                        </span>
                        <p class="mt-2 font-mono text-4xl font-black text-white">Rs {{ payment.amount }}</p>
                        <p v-if="payment.reference" class="mt-1 font-mono text-[10px] text-slate-500">
                            Ref {{ payment.reference }}
                        </p>
                        <p v-if="payment.payerName" class="mt-0.5 text-[11px] font-bold text-slate-400">
                            {{ payment.payerName }}
                        </p>
                    </div>

                    <div class="mt-5">
                        <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-slate-500">
                            Pay with
                        </label>
                        <div class="grid grid-cols-2 gap-2">
                            <button v-for="option in methods" :key="option.id" @click="method = option.id"
                                class="cursor-pointer rounded-2xl border px-3 py-4 text-center transition-all"
                                :class="method === option.id
                                    ? 'border-emerald-500/60 bg-emerald-600/15'
                                    : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'">
                                <span class="block text-xl">{{ option.emoji }}</span>
                                <span class="mt-1 block text-[11px] font-black"
                                    :class="method === option.id ? 'text-emerald-300' : 'text-slate-400'">
                                    {{ option.label }}
                                </span>
                            </button>
                        </div>
                    </div>

                    <div class="mt-4">
                        <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-slate-500">
                            Your name
                        </label>
                        <input v-model="paidBy" type="text" placeholder="So the counter knows who paid"
                            class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2.5 text-sm font-bold text-white outline-none transition-colors placeholder:text-xs placeholder:font-normal placeholder:text-slate-600 focus:border-slate-600" />
                    </div>

                    <p v-if="payError"
                        class="mt-3 rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-[10px] font-bold text-rose-400">
                        {{ payError }}
                    </p>

                    <button @click="pay" :disabled="paying"
                        class="mt-5 w-full cursor-pointer rounded-xl bg-emerald-600 py-3.5 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-emerald-950/30 transition-all hover:bg-emerald-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500">
                        {{ paying ? 'Confirming…' : `Pay Rs ${payment.amount}` }}
                    </button>

                    <p class="mt-3 text-center text-[9px] leading-relaxed text-amber-600">
                        DEMO — no money moves. Confirming marks the bill paid and notifies the counter.
                    </p>
                </div>
            </div>

            <p class="mt-6 text-center font-mono text-[10px] text-slate-700">Baize</p>
        </div>
    </div>
</template>

<script setup>
/**
 * Opened by scanning the QR on a receipt. Deliberately public — no sign-in,
 * because the person holding the code is standing at the counter with the bill.
 * The endpoint only exposes an amount and a reference for the same reason.
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CUSTOMER_API } from '../auth.js'

const route = useRoute()
const token = route.params.token

// The pay endpoints sit outside the customer blueprint, so build from its root.
const API_ROOT = CUSTOMER_API.replace(/\/customer$/, '')

const payment = ref({ amount: 0, status: 'pending', reference: '', payerName: '' })
const loading = ref(true)
const error = ref('')
const payError = ref('')
const paying = ref(false)
const method = ref('easypaisa')
const paidBy = ref('')

const methods = [
    { id: 'easypaisa', label: 'EasyPaisa', emoji: '📱' },
    { id: 'jazzcash', label: 'JazzCash', emoji: '📲' },
]
const methodLabel = computed(() =>
    methods.find((m) => m.id === payment.value.method)?.label || 'Paid',
)
const kindLabel = computed(() => ({
    session: 'Table Bill',
    canteen: 'Canteen Order',
    account: 'Account Balance',
}[payment.value.kind] || 'Amount Due'))

async function load() {
    try {
        const res = await fetch(`${API_ROOT}/pay/${token}`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'That payment link is not valid')
        payment.value = data.payment
        paidBy.value = data.payment.payerName || ''
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
}

async function pay() {
    if (paying.value) return
    paying.value = true
    payError.value = ''
    try {
        const res = await fetch(`${API_ROOT}/pay/${token}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method: method.value, paidBy: paidBy.value }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not confirm that payment')
        payment.value = data.payment
    } catch (err) {
        payError.value = err.message
    } finally {
        paying.value = false
    }
}

onMounted(load)
</script>