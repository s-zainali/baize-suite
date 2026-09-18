<template>
    <div ref="dropdownRoot"
        class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 transition-all hover:border-slate-700"
        :class="dropdownOpen ? 'border-slate-600' : ''">
        <label class="block text-xs font-bold text-slate-300 tracking-wide mb-3">{{ props.label }}</label>

        <div class="relative">
            <!-- Trigger -->
            <button ref="trigger" type="button" @click="toggle"
                :aria-expanded="dropdownOpen" aria-haspopup="listbox"
                class="w-full flex items-center justify-between bg-slate-900 rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors cursor-pointer"
                :class="dropdownOpen ? 'border-slate-600' : 'border-slate-800 hover:border-slate-700'">
                <span class="flex gap-2 items-center min-w-0"
                    :class="selectedType ? 'font-bold text-white' : 'font-normal text-slate-600'">
                    <img v-if="icons && selectedType" :src="selectedType.imgUrl" alt="" class="w-5 shrink-0">
                    <div></div>
                    <span class="truncate">{{ selectedType ? selectedType.label : placeholder }}</span>
                </span>
                <svg class="w-4 h-4 text-slate-500 transition-transform duration-200 shrink-0"
                    :class="dropdownOpen ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                    stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            <!-- Options panel -->
            <Transition enter-active-class="transition duration-150 ease-out"
                :enter-from-class="dropUp ? 'opacity-0 translate-y-1' : 'opacity-0 -translate-y-1'"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition duration-100 ease-in" leave-from-class="opacity-100 translate-y-0"
                :leave-to-class="dropUp ? 'opacity-0 translate-y-1' : 'opacity-0 -translate-y-1'">
                <div v-if="dropdownOpen" role="listbox"
                    class="absolute left-0 right-0 z-20 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-slate-950/80 overflow-y-auto p-1 dropdown-scroll"
                    :class="dropUp ? 'bottom-full mb-2' : 'top-full mt-2'"
                    :style="{ maxHeight: panelMaxHeight }">
                    <button v-for="type in options" :key="type.value" type="button" @click="selectType(type)"
                        role="option" :aria-selected="form[field] === type.value"
                        class="w-full flex items-center justify-start gap-2 px-3 py-2.5 rounded-lg text-sm text-left transition-colors cursor-pointer"
                        :class="form[field] === type.value
                            ? 'bg-emerald-600/15 text-emerald-400 font-bold'
                            : 'text-slate-300 font-bold hover:bg-slate-800 hover:text-white'">
                        <img v-if="icons" :src="type.imgUrl" alt="" class="h-5 shrink-0">
                        <span class="truncate">{{ type.label }}</span>
                        <svg v-if="form[field] === type.value" class="w-4 h-4 ml-auto shrink-0" fill="none"
                            viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    </button>
                </div>
            </Transition>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue'

const props = defineProps({
    form: Object,
    options: { type: Array, default: () => [] },
    label: String,
    field: String,
    placeholder: String,
    icons: { type: Boolean, default: false },
    badges: { type:Object, default: null }
})

const dropdownRoot = ref(null)
const trigger = ref(null)
const dropdownOpen = ref(false)

/** Open upward when there isn't room below — near the foot of a modal. */
const dropUp = ref(false)
const panelMaxHeight = ref('16rem')

const GAP = 16          // breathing room from the viewport edge
const IDEAL = 256       // 16rem, the height we'd like if space allows

/**
 * Decide which way to open, and how tall.
 *
 * Measured each time rather than assumed: the same field sits at different
 * heights depending on the modal, and on a phone there may be no room either
 * way — in which case we take the larger side and let the list scroll.
 */
async function place() {
    await nextTick()
    const el = trigger.value
    if (!el) return

    const box = el.getBoundingClientRect()
    const below = window.innerHeight - box.bottom - GAP
    const above = box.top - GAP

    dropUp.value = below < Math.min(IDEAL, above)
    const room = dropUp.value ? above : below
    panelMaxHeight.value = `${Math.max(120, Math.min(IDEAL, room))}px`
}

function toggle() {
    dropdownOpen.value = !dropdownOpen.value
    if (dropdownOpen.value) place()
}

const selectedType = computed(() =>
    props.options.find((t) => t.value === props.form[props.field]) || null,
)

function selectType(type) {
    props.form[props.field] = type.value
    dropdownOpen.value = false
}

// ── dismissal ─────────────────────────────────────────────────────────────
// Previously the panel stayed open until something was picked, so two
// dropdowns on one form could both be open and overlap each other.
function onPointerDown(event) {
    if (dropdownOpen.value && dropdownRoot.value && !dropdownRoot.value.contains(event.target)) {
        dropdownOpen.value = false
    }
}
function onKeydown(event) {
    if (event.key === 'Escape') dropdownOpen.value = false
}
// Scrolling or resizing moves the trigger, so a measured panel would detach.
function onReflow() {
    if (dropdownOpen.value) place()
}

document.addEventListener('pointerdown', onPointerDown)
document.addEventListener('keydown', onKeydown)
window.addEventListener('resize', onReflow)
window.addEventListener('scroll', onReflow, true)

onUnmounted(() => {
    document.removeEventListener('pointerdown', onPointerDown)
    document.removeEventListener('keydown', onKeydown)
    window.removeEventListener('resize', onReflow)
    window.removeEventListener('scroll', onReflow, true)
})
</script>

<style scoped>
.dropdown-scroll::-webkit-scrollbar { width: 6px; }
.dropdown-scroll::-webkit-scrollbar-track { background: transparent; }
.dropdown-scroll::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
.dropdown-scroll { scrollbar-width: thin; scrollbar-color: #334155 transparent; }
</style>