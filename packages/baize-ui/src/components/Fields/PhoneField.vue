<template>
    <div class="rounded-2xl border bg-slate-950/40 p-4 transition-all duration-200"
        :class="showError
            ? 'border-rose-800/70 hover:border-rose-700 focus-within:border-rose-600'
            : 'border-slate-800 hover:border-slate-700 focus-within:border-emerald-600/60'">

        <div class="mb-3 flex items-center justify-between">
            <label :for="id" class="text-xs font-bold tracking-wide text-slate-300">{{ label }}</label>
            <span v-if="remaining > 0 && focused" class="font-mono text-[9px] font-bold text-slate-600">
                {{ remaining }} more
            </span>
            <span v-else-if="valid" class="text-[9px] font-black uppercase tracking-widest text-emerald-500">✓</span>
        </div>

        <div class="flex items-stretch gap-2">
            <!-- Every customer is Pakistani here, so the country code is furniture,
                 not a decision. Fixing it removes a whole class of typo. -->
            <span
                class="flex select-none items-center rounded-xl border border-slate-800 bg-slate-900/80 px-2.5 font-mono text-sm font-bold text-slate-400">
                +92
            </span>
            <input :id="id" ref="input" :value="display" type="tel" inputmode="numeric" autocomplete="tel-national"
                placeholder="300 1234567" :aria-invalid="showError" @input="onInput" @focus="focused = true"
                @blur="focused = false"
                class="w-full rounded-xl border border-slate-800 bg-slate-900 px-3 py-2.5 font-mono text-sm font-bold tracking-wide text-white outline-none transition-colors placeholder:font-normal placeholder:tracking-normal placeholder:text-slate-600 focus:border-slate-600" />
        </div>

        <p v-if="showError" class="mt-2 px-0.5 text-[10px] font-bold text-rose-400">{{ error }}</p>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatPhoneInput, nationalDigits, isValidPhone, phoneDigitsRemaining } from '../../utils/phone.js'

const props = defineProps({
    modelValue: { type: String, default: '' },   // always the bare national digits
    label: { type: String, default: 'Phone Number' },
    id: { type: String, default: 'phone' },
    error: { type: String, default: '' },
    touched: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const focused = ref(false)
const input = ref(null)

const display = computed(() => formatPhoneInput(props.modelValue))
const valid = computed(() => isValidPhone(props.modelValue))
const remaining = computed(() => phoneDigitsRemaining(props.modelValue))
const showError = computed(() => props.touched && !!props.error)

function onInput(event) {
    // Store digits only; the spaces are presentation. Pasting '+92 300…' or
    // '0300…' lands on the same value as typing it.
    const digits = nationalDigits(event.target.value)
    emit('update:modelValue', digits)
    // The value prop won't change if the digits didn't, so a rejected keystroke
    // would leave the stray character on screen. Put the field back in step.
    event.target.value = formatPhoneInput(digits)
}

defineExpose({ focus: () => input.value?.focus() })
</script>