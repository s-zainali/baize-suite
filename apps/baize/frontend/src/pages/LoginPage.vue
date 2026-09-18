<template>
    <div class="absolute bg-slate-950 flex items-center justify-center p-4 h-full w-full">
        <div class="w-full max-w-[75vw] sm:max-w-sm">
            <div class="text-center mb-8">
                <h1 class="text-2xl font-black text-white tracking-tight">Baize</h1>
                <p class="text-xs text-slate-500 mt-1">Sign in to start your shift</p>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-lg font-black text-white">SIGN IN</h2>
                </div>
                <div class="space-y-4">
                    <TextField :form="form" :field="'username'" :label="'Username'" :id="'login-username'"
                        :placeholder="'e.g. admin'" :type="'text'" />

                    <PasswordField :form="form" :field="'password'" :label="'Password'" :placeholder="'••••••••'"
                        :error="{ condition: false, message: '' }" @keyup.enter="submit" />

                    <p v-if="error" class="text-xs font-bold text-rose-400">{{ error }}</p>

                    <button @click="submit" :disabled="loading || !form.username || !form.password"
                        class="w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
                        {{ loading ? 'Signing in…' : 'Sign In' }}
                    </button>
                </div>
            </div>

            <p class="text-center text-[10px] text-slate-600 mt-6 font-mono">
                Sessions last 12 hours · contact the owner for an account
            </p>
        </div>
    </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../Auth'
import TextField from '../components/Fields/TextField.vue'
import PasswordField from '../components/Fields/PasswordField.vue'

const router = useRouter()
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

const form = reactive({
    username: '',
    password: ''
})

async function submit() {
    if (!form.username || !form.password || loading.value) return
    loading.value = true
    error.value = ''
    try {
        await login(form.username, form.password)
        router.push('/')
    } catch (e) {
        error.value = e.message
    } finally {
        loading.value = false
    }
}
</script>