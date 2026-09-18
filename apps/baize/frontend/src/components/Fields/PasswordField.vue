<template>
    <div
        class="bg-slate-950/40 border  rounded-2xl p-4 transition-all "
        :class="error.condition
            ?'border-rose-800 hover:border-rose-700 focus-within:border-rose-600'
            :'border-slate-800 hover:border-slate-700 focus-within:border-slate-600'">
        <div class="flex justify-between items-center mb-3">
            <label :for="props.id" class="text-xs font-bold text-slate-300 tracking-wide">{{ props.label }}</label>
            <button type="button" @click="showPassword = !showPassword"
                class="text-[9px] text-amber-500 font-bold bg-amber-500/10 px-2 py-0.5 rounded-full uppercase tracking-widest hover:bg-amber-500/20 transition-colors cursor-pointer">
                {{ showPassword ? 'Hide' : 'Show' }}
            </button>
        </div>
        <input v-model="props.form[props.field]" :type="showPassword ? 'text' : 'password'" autocomplete="new-password"
            :placeholder="props.placeholder"
            :id="props.id"
            class="w-full bg-slate-900 rounded-xl border border-slate-800 px-3 py-2.5 text-sm font-bold text-white outline-none focus:border-slate-600 transition-colors placeholder:text-slate-600 placeholder:font-normal" />
        <p v-if="error.condition"
            class='text-rose-400 text-xs font-bold'>{{props.error.message}}</p>
    </div>
</template>

<script setup>

import { ref } from 'vue';
const props = defineProps({
    form: Object,
    field: String,
    label: String,
    error: Object,
    placeholder: String,
    id: String
})

const showPassword = ref(false)
</script>