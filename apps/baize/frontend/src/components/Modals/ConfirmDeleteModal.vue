<template>
    <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('closeModal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-xs rounded-3xl p-6 shadow-2xl">
            <h2 class="text-lg font-black text-white mb-2">Remove Station?</h2>
            <p class="text-xs text-slate-400 mb-6">
                This action will permanently remove this station from the floor map and ledger view.
            </p>
            <div class="flex gap-3">
                <button @click="emit('closeModal')"
                    class="flex-1 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer">
                    Cancel
                </button>
                <button @click="emit('confirmRemove')"
                    class="flex-1 py-2 rounded-xl text-xs font-black bg-rose-600 text-white hover:bg-rose-500 cursor-pointer">
                    Remove
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
const props = defineProps({ uid: String })
const emit = defineEmits(['confirmRemove', 'closeModal']);
</script>