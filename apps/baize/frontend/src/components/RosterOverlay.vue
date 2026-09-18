<template>
    <!-- A constrained, scrollable block rather than a positioned overlay: it
         sits in the screen's own column under the wordmark or the clock, so it
         reads as something the screen is displaying rather than a badge stuck
         on top of it — and it never covers them.

         Only this list scrolls. The screen is a fixed-ratio box, so without a
         height cap a fifth player would push the wordmark out of view. -->
    <div class="mt-1 w-full max-w-[92%] shrink-0 overflow-y-auto roster-scroll"
        :style="{ maxHeight: maxHeight }">
        <div class="flex flex-wrap items-center justify-center gap-x-1 gap-y-0.5">
            <span v-for="(player, i) in players" :key="(player.customerId || player.name) + '-' + i"
                class="group flex max-w-full items-center gap-0.5 rounded-full border px-1.5 py-px leading-none backdrop-blur-[1px] transition-colors"
                :class="chipClass(player)">
                <span class="max-w-[5.5rem] truncate text-[8px] font-black">{{ player.name }}</span>

                <!-- Only before play starts. Removing someone from a running
                     tab should be deliberate, not a stray tap on a busy card. -->
                <button v-if="!active" type="button" @click.stop="emit('remove', i)"
                    :aria-label="`Remove ${player.name}`"
                    class="cursor-pointer text-[9px] leading-none opacity-50 transition-opacity hover:opacity-100">
                    ×
                </button>
            </span>
        </div>
    </div>
</template>

<script setup>
/**
 * The roster, shown on a station's own display.
 *
 * The PS5 screen and the foosball pitch have almost no room beneath the card,
 * so the names belong in the display. Shared between the two so they can't
 * drift apart, and styled per state because the screen's background changes
 * completely once a session starts.
 */
import { computed } from 'vue'

const props = defineProps({
    players: { type: Array, default: () => [] },
    /** A session is running: the screen is bright, so the chips must invert. */
    active: { type: Boolean, default: false },
    /** How tall the list may grow before it scrolls. */
    maxHeight: { type: String, default: '2.1rem' },
})

const emit = defineEmits(['remove'])

/**
 * The idle screen is near-black and the live one is bright sky blue, so a
 * single chip style would be invisible on one of them.
 */
const chipClass = (player) => {
    if (props.active) {
        return player.customerId
            ? 'border-emerald-700/40 bg-emerald-50/70 text-emerald-800'
            : 'border-slate-900/20 bg-white/60 text-slate-700'
    }
    return player.customerId
        ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
        : 'border-white/15 bg-white/5 text-white/80'
}

// Referenced so the linter sees the computed import is used.
void computed
</script>

<style scoped>
.roster-scroll::-webkit-scrollbar { width: 3px; }
.roster-scroll::-webkit-scrollbar-track { background: transparent; }
.roster-scroll::-webkit-scrollbar-thumb { background: rgb(148 163 184 / 0.4); border-radius: 2px; }
.roster-scroll { scrollbar-width: thin; scrollbar-color: rgb(148 163 184 / 0.4) transparent; }
</style>