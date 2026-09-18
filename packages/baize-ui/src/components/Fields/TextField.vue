<template>
    <div
        class="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 transition-all hover:border-slate-700 focus-within:border-slate-600">
        <label :for="props.id" class="block text-xs font-bold text-slate-300 tracking-wide mb-3">{{props.label}}</label>
        <input :id="props.id" v-model="props.form[props.field]" :type=props.type :placeholder="props.placeholder"
            class="w-full bg-slate-900 rounded-xl border border-slate-800 px-3 py-2.5 text-sm font-bold text-white placeholder:text-slate-600 placeholder:font-normal outline-none focus:border-slate-600 transition-colors" />
    </div>
</template>

<script setup>
const props = defineProps({form: Object, label: String, field:String, id:String, placeholder: String, type:String})
</script>