<template>
    <div>
        <span v-if="label" class="mb-1.5 block text-[9px] font-bold tracking-widest uppercase"
            :class="accentText">{{ label }}</span>

        <div class="flex items-center justify-between overflow-hidden rounded-xl border bg-slate-900 transition-colors"
            :class="[accentBorder, disabled ? 'opacity-50' : '']">
            <button type="button" @click="step(-1)" :disabled="disabled || atMin"
                :aria-label="`Decrease ${label || 'value'}`"
                class="flex h-9 w-8 shrink-0 cursor-pointer items-center justify-center text-slate-400 transition-colors hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:text-slate-700 disabled:hover:bg-transparent">
                −
            </button>

            <!-- Typing beats stepping for a jump from 60 to 450, so the middle
                 is an input rather than a label.

                 The suffix is positioned OUT of the layout rather than sitting
                 beside the number. Reserving width for it — and for a matching
                 spacer to keep the number centred — cost 48px, which a narrow
                 rates column doesn't have to spare, and the digits were clipped
                 to make room. Now the input owns the whole middle and centres
                 in it; symmetric padding keeps the text clear of the suffix,
                 so it stays centred whether a suffix is shown or not. -->
            <div class="relative min-w-0 flex-1">
                <input ref="input" :value="display" @input="onInput" @blur="onBlur" @keydown.up.prevent="step(1)"
                    @keydown.down.prevent="step(-1)" :disabled="disabled" :placeholder="placeholder" inputmode="numeric"
                    class="w-full min-w-0 bg-transparent px-4 text-center text-sm font-black tabular-nums text-white outline-none placeholder:font-normal placeholder:text-slate-600 disabled:cursor-not-allowed" />
                <span v-if="suffix && !isEmpty" aria-hidden="true"
                    class="pointer-events-none absolute inset-y-0 right-1 flex items-center text-[10px] font-normal text-slate-500">
                    {{ suffix }}
                </span>
            </div>

            <button type="button" @click="step(1)" :disabled="disabled || atMax"
                :aria-label="`Increase ${label || 'value'}`"
                class="flex h-9 w-8 shrink-0 cursor-pointer items-center justify-center text-slate-400 transition-colors hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:text-slate-700 disabled:hover:bg-transparent">
                +
            </button>
        </div>

        <p v-if="hint" class="mt-1 px-0.5 text-[9px] leading-snug text-slate-600">{{ hint }}</p>
        <p v-if="error" class="mt-1 px-0.5 text-[10px] font-bold text-rose-400">{{ error }}</p>
    </div>
</template>

<script setup>
/**
 * Number input with +/- steppers.
 *
 * Two behaviours worth knowing:
 *  - `nullable` lets the field be genuinely empty, which canteen stock needs to
 *    mean "made to order, never runs out". Without it, clearing the box would
 *    silently become 0 and take the item off the menu.
 *  - The value is emitted as a NUMBER (or null), never a string, so callers
 *    don't have to remember to coerce it before sending it to the API.
 */
import { ref, computed } from 'vue'

const props = defineProps({
    modelValue: { type: [Number, String], default: 0 },
    label: { type: String, default: '' },
    suffix: { type: String, default: '' },        // e.g. 'Rs'
    placeholder: { type: String, default: '' },
    min: { type: Number, default: 0 },
    max: { type: Number, default: Number.MAX_SAFE_INTEGER },
    stepBy: { type: Number, default: 1 },
    disabled: { type: Boolean, default: false },
    hint: { type: String, default: '' },
    error: { type: String, default: '' },
    /** Allow an empty value (emits null) rather than forcing a number. */
    nullable: { type: Boolean, default: false },
    /** 'slate' | 'emerald' | 'amber' | 'indigo' — tints the border and label. */
    accent: { type: String, default: 'slate' },
})

const emit = defineEmits(['update:modelValue'])
const input = ref(null)

const ACCENTS = {
    slate: { border: 'border-slate-700', text: 'text-slate-500' },
    emerald: { border: 'border-emerald-500/20', text: 'text-emerald-500' },
    amber: { border: 'border-amber-500/20', text: 'text-amber-500' },
    indigo: { border: 'border-indigo-500/20', text: 'text-indigo-400' },
}
const accentBorder = computed(() => (ACCENTS[props.accent] || ACCENTS.slate).border)
const accentText = computed(() => (ACCENTS[props.accent] || ACCENTS.slate).text)

const isEmpty = computed(() => props.modelValue === '' || props.modelValue === null || props.modelValue === undefined)
const numeric = computed(() => (isEmpty.value ? null : Number(props.modelValue) || 0))
const display = computed(() => (isEmpty.value ? '' : String(numeric.value)))

const atMin = computed(() => !isEmpty.value && numeric.value <= props.min)
const atMax = computed(() => !isEmpty.value && numeric.value >= props.max)

const clamp = (n) => Math.min(Math.max(n, props.min), props.max)

function step(direction) {
    if (props.disabled) return
    // Stepping an empty nullable field starts from the floor rather than NaN
    const base = isEmpty.value ? props.min : numeric.value
    emit('update:modelValue', clamp(base + direction * props.stepBy))
}

function onInput(event) {
    const raw = event.target.value.replace(/[^\d]/g, '')
    if (raw === '') {
        // Keep the box empty while typing; coerce on blur so backspacing to
        // clear the field doesn't fight the user by snapping back to 0.
        emit('update:modelValue', props.nullable ? null : '')
        return
    }
    emit('update:modelValue', clamp(Number(raw)))
    event.target.value = String(clamp(Number(raw)))
}

function onBlur() {
    if (isEmpty.value && !props.nullable) emit('update:modelValue', props.min)
}

defineExpose({ focus: () => input.value?.focus() })
</script>