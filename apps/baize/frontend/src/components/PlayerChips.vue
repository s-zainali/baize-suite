<template>
    <div class="flex gap-4 flex-col absolute top-0 left-0 w-full h-full z-100 flex-wrap gap-1 rounded-lg bg-slate-950/70 p-2 pt-4 backdrop-blur-xs shadow-md chips-scroll"
        :class="wrapperClass">
        <span class="text-sm font-black tracking-widest text-center text-slate-200 uppercase">Players</span>
        <div class="flex flex-col items-center gap-2">
            <div v-for="(player, i) in players" :key="player.name + i"
                class="group flex justify-between gap-2 h-auto w-full items-center rounded-lg border bg-slate-800 px-2 py-1.5 text-xs font-bold text-white/90"
                :class="player.customerId ? 'border-amber-600' : 'border-slate-700'">
                <div class="flex items-center gap-1.5 min-w-0 flex-1">
                    <span title="Linked account" class=" w-2 h-2 rounded-xs shrink-0 self-center" :class="player.customerId? 'bg-amber-500' : 'bg-emerald-500'"></span>
                    <span class="break-all whitespace-normal flex-1">{{ player.name }}</span>
                </div>
                <button v-if="removable" type="button" @click.stop="emit('remove', i)"
                    :aria-label="`Remove ${player.name}`"
                    class="cursor-pointer text-white/40 hover:text-red-500 shrink-0 self-center">✕</button>
            </div>
        </div>
        <button class="absolute top-1 right-2 cursor-pointer hover:text-rose-400 transition duration-300 ease-in-out" title="Close" @click="emit('close')" >✕</button>
    </div>
</template>

<script setup>
/**
 * The roster, as chips.
 *
 * One component so every station shows players the same way — the cards had
 * drifted into three different treatments, and each fix to one left the others
 * behind. The list is capped and scrolls: cards are fixed-height boxes, so a
 * fifth player has to scroll rather than push the card's own content out.
 */
defineProps({
    players: { type: Array, default: () => [] },
    /** Off during a live session: removing from a running tab should be deliberate. */
    removable: { type: Boolean, default: true },
    /** Spacing, which differs between sitting under an input and inside a screen. */
    wrapperClass: { type: String, default: '' },
})

const emit = defineEmits(['remove', 'close'])
</script>

<style scoped>
.chips-scroll::-webkit-scrollbar {
    width: 4px;
}

.chips-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.chips-scroll::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 2px;
}

.chips-scroll {
    scrollbar-width: thin;
    scrollbar-color: #334155 transparent;
}
</style>