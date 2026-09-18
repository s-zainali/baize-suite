<template>
    <div class="pointer-events-auto w-full space-y-2">

        <button type="button" @click.stop="emit('link')" :title="full ? `Up to ${max} players` : 'Add or link a player'"
            aria-label="Add or link a player" :disabled="full"
            class="group flex h-[26px] w-full shrink-0 cursor-pointer items-center justify-center gap-1 rounded-md border border-white/15 bg-white/5 text-[10px] font-bold leading-none text-white/70 backdrop-blur-sm transition-all hover:border-slate-400/50 hover:bg-white/10 hover:text-slate-200 disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-transparent disabled:text-white/30">
            <span class="text-xs leading-none transition-transform group-hover:scale-110">+</span>
            {{ players.length ? 'Add Another' : 'Add Player' }}
        </button>
        <p v-if="notice" class="text-center text-[8px] font-bold text-amber-300/80">{{ notice }}</p>
    </div>
</template>

<script setup>
import PlayerChips from './PlayerChips.vue'
/**
 * Who is playing on this station.
 *
 * Replaces the single name field. Typing a name and pressing enter — or simply
 * moving on — adds it to the list, so the common case of four friends on one
 * table stops being four separate guesses at the counter.
 *
 * The list lives here until the session starts; nothing is persisted for an
 * idle table, exactly as the single name behaved before.
 */
import { ref, computed, watch } from 'vue'

const props = defineProps({
    modelValue: { type: Array, default: () => [] },
    max: { type: Number, default: 8 },
    /**
     * Draw the roster here. Cards with a display of their own — the PS5
     * screen — turn this off and show the names there instead, because the
     * space under the button is barely one line tall.
     */
    chips: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'link'])

const notice = ref('')

const players = computed(() => props.modelValue || [])

const full = computed(() => players.value.length >= props.max)

// Full is worth saying out loud; a silently disabled button reads as broken.
watch(full, (isFull) => {
    if (!isFull) return
    notice.value = `Up to ${props.max} players`
    setTimeout(() => { notice.value = '' }, 2200)
})
</script>