<template>
    <div class="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm md:pl-[var(--modal-inset,1rem)]"
        @click.self="close">
        <div class="w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-900 p-5">

            <div class="mb-4 flex items-start justify-between gap-3">
                <div>
                    <h2 class="text-lg font-black text-white">Link Player</h2>
                </div>
                <button @click="close" class="cursor-pointer p-1 text-lg text-slate-500 hover:text-rose-400">✕</button>
            </div>
            <p v-if="full" class="mb-3 rounded-xl border border-amber-600/40 bg-amber-500/10 px-3 py-2 text-[10px] font-bold text-amber-400">
                This table is full — up to {{ max }} players.
            </p>

            <div class="grid grid-cols-2 gap-4">
                <div class="flex flex-col gap-4">
                    <h2 class="font-bold text-sm text-slate-200">Member</h2>
                    <PhoneField v-model="phone" id="cust-phone" />
                    <button @click="search" :disabled="searching || phone.length !== 10 || full"
                        class="shrink-0 cursor-pointer rounded-xl bg-emerald-800 py-2 w-full text-xs font-black uppercase tracking-widest text-slate-200 transition-colors hover:bg-emerald-700 disabled:opacity-40 disabled:bg-slate-800">
                        {{ searching ? '…' : 'Find' }}
                    </button>
                    <p v-if="error" class="mt-2 text-[10px] font-bold text-rose-400">{{ error }}</p>
                    <!-- Confirm before adding. The counter should see who they matched,
                    not have a stranger silently attached to the tab. -->
                    <div v-if="found" class="mt-4 rounded-2xl border border-emerald-600/40 bg-emerald-500/5 p-4">
                        <p class="text-[9px] font-black uppercase tracking-widest text-emerald-500">Account found</p>
                        <p class="mt-1 text-sm font-black text-white">{{ found.name }}</p>
                        <p class="font-mono text-[10px] text-slate-500">{{ found.phone }}</p>

                        <button @click="confirm"
                            class="mt-3 w-full cursor-pointer rounded-xl bg-emerald-600 py-2.5 text-[10px] font-black uppercase tracking-widest text-white hover:bg-emerald-500">
                            Add to Table
                        </button>
                    </div>
                </div>
                <div class="flex flex-col gap-4">
                    <h2 class="font-bold text-sm text-slate-200">Non-Member</h2>
                    <TextField :form="playerForm" :type="'text'" :label="'Player name'" :placeholder="'Full Name'"
                        :field="'playerName'" />
                    <button @click="add" :disabled="!playerForm.playerName.trim() || full"
                        class="shrink-0 cursor-pointer rounded-xl bg-emerald-800 py-2 w-full text-xs font-black uppercase tracking-widest text-slate-200 transition-colors hover:bg-emerald-700 disabled:opacity-40 disabled:bg-slate-800">
                        Add
                    </button>
                </div>
            </div>
            <div v-if="modelValue.length > 0" class="mt-4 flex flex-col gap-4">
                <h2 class="font-bold text-sm text-slate-200">Linked Players</h2>
                <div v-for="(player, i) in modelValue" :key="(player.customerId || player.name) + '-' + i"
                    class="w-full flex justify-between p-2 rounded-xl bg-slate-800 border border-slate-800 gap-4">
                    <div class="w-full flex items-center justify-between">
                        <span class="font-black pl-4 text-sm">{{ player.name }}</span>
                        <span class="px-3 py-1 rounded-lg text-xs tracking-widest uppercase font-bold"
                            :class="player.customerId ? 'bg-amber-700' : 'bg-emerald-700'">{{ player.customerId ?
                            'Member' : 'Guest' }}</span>
                    </div>
                    <button @click="remove(i)" :aria-label="`Remove ${player.name}`"
                        class="hover:text-rose-500 cursor-pointer aspect-square">✕</button>
                </div>
                <button @click="close"
                    class="shrink-0 cursor-pointer rounded-xl bg-emerald-800 py-2 w-full text-xs font-black uppercase tracking-widest text-slate-200 transition-colors hover:bg-emerald-700">
                    Finish and close
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
/**
 * Attach a real customer account to a station's player list.
 *
 * Deliberately a lookup and a confirmation rather than a live-search list:
 * staff typing a partial number should not be shown a roll of the club's
 * customers, and an exact-match-then-confirm flow can't attach the wrong
 * person to somebody's bill.
 */
import { ref, computed } from 'vue'
import PhoneField from '../Fields/PhoneField.vue'
import { authFetch, API_URL } from '@/Auth.js'
import TextField from '../Fields/TextField.vue'

const props = defineProps({
    modelValue: { type: Array, default: () => [] },
    max: { type: Number, default: 8 }
})

const emit = defineEmits(['linked', 'update:modelValue', 'close-modal'])

const phone = ref('')
const playerForm = ref({ playerName: '' })
const found = ref(null)
const error = ref('')
const searching = ref(false)

async function search() {
    if (searching.value) return
    searching.value = true
    error.value = ''
    found.value = null
    try {
        const res = await authFetch(
            `${API_URL}/customers/lookup?phone=${encodeURIComponent(phone.value.trim())}`,
        )
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Could not look that number up')
        found.value = data.customer
    } catch (err) {
        error.value = err.message
    } finally {
        searching.value = false
    }
}

const full = computed(() => props.modelValue.length >= props.max)

/** Already on this table — by account if linked, otherwise by name. */
function isDuplicate(player) {
    return props.modelValue.some((p) => (
        player.customerId
            ? p.customerId === player.customerId
            : !p.customerId && p.name.toLowerCase() === player.name.toLowerCase()
    ))
}

function offer(player) {
    if (full.value) return (error.value = `Up to ${props.max} players`)
    if (isDuplicate(player)) return (error.value = `${player.name} is already on this table`)
    error.value = ''
    emit('linked', player)
    return true
}

function add() {
    const name = playerForm.value.playerName.trim()
    if (!name) return
    if (offer({ name, customerId: null })) playerForm.value.playerName = ''
}

function confirm() {
    if (offer({ name: found.value.name, customerId: found.value.id })) {
        found.value = null
        phone.value = ''
    }
}

/** Take someone back off the list without leaving the dialog. */
function remove(index) {
    emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
}

function close() {
    emit('close-modal')
}
</script>