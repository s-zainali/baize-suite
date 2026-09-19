<template>
    <div class="relative min-h-screen overflow-hidden bg-slate-950 text-white pb-6">

        <!-- ── ambient background ─────────────────────────────────────────
             Felt green and chalk blue, at very low opacity. It should read as
             atmosphere from a pool hall, never as decoration competing with the
             form. -->
        <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
            <!-- Table felt: a fine weave, not a gradient wash -->
            <div class="absolute inset-0"
                style="background-image:radial-gradient(circle at 1px 1px, rgba(148,163,184,0.16) 1px, transparent 0);background-size:22px 22px" />

            <!-- Chalk grid, drawn faintly across the whole field -->
            <div class="absolute inset-0"
                style="background-image:linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px),linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px);background-size:88px 88px" />

            <!-- Racked triangle, top right. Geometry is derived so the frame
                 encloses every ball rather than cutting through them. -->
            <svg class="absolute -right-20 -top-12 h-80 w-80 rotate-[14deg]" viewBox="0 0 200 145" fill="none">
                <g opacity="0.5">
                    <circle v-for="ball in rack" :key="ball.n" :cx="ball.x" :cy="ball.y" r="11"
                        :fill="ball.color" />
                    <!-- Stripes get a white band across the middle -->
                    <path v-for="ball in stripedRack" :key="`s${ball.n}`"
                        :d="`M${ball.x - 11} ${ball.y} a11 11 0 0 1 22 0 Z`" fill="#f8fafc" opacity="0.85"
                        :transform="`rotate(90 ${ball.x} ${ball.y})`" />
                    <circle v-for="ball in rack" :key="`o${ball.n}`" :cx="ball.x" :cy="ball.y" r="11"
                        fill="none" stroke="#0f172a" stroke-opacity="0.5" stroke-width="0.8" />
                </g>
                <!-- Wooden rack frame -->
                <path d="M100 2 L174.7 131.4 L25.3 131.4 Z" fill="none" stroke="#a16207" stroke-opacity="0.75"
                    stroke-width="4" stroke-linejoin="round" />
                <path d="M100 2 L174.7 131.4 L25.3 131.4 Z" fill="none" stroke="#78350f" stroke-opacity="0.5"
                    stroke-width="1" stroke-linejoin="round" />
            </svg>

            <!-- Cue and cue ball, bottom left, aimed across the page -->
            <svg class="absolute -bottom-24 -left-24 h-[30rem] w-[30rem]" viewBox="0 0 400 400" fill="none">
                <!-- butt -> shaft -> ferrule, thinning towards the tip -->
                <path d="M18 372 L262 134" stroke="#78350f" stroke-opacity="0.8" stroke-width="6.5"
                    stroke-linecap="round" />
                <path d="M120 272.5 L262 134" stroke="#a16207" stroke-opacity="0.8" stroke-width="5"
                    stroke-linecap="round" />
                <path d="M262 134 L286.3 110.3" stroke="#e7e5e4" stroke-opacity="0.85" stroke-width="4.5"
                    stroke-linecap="round" />
                <path d="M286.3 110.3 L292.7 104.0" stroke="#38bdf8" stroke-opacity="0.9" stroke-width="4.5"
                    stroke-linecap="round" />
                <!-- cue ball -->
                <circle cx="340.7" cy="57.2" r="20" fill="#f8fafc" fill-opacity="0.85" />
                <circle cx="340.7" cy="57.2" r="20" fill="none" stroke="#0f172a" stroke-opacity="0.35"
                    stroke-width="1" />
                <ellipse cx="333.7" cy="49.2" rx="6" ry="4" fill="#ffffff" opacity="0.7"
                    transform="rotate(-28 333.7 49.2)" />
            </svg>

            <!-- Corner pockets -->
            <svg class="absolute left-0 top-0 h-32 w-32 text-slate-500" viewBox="0 0 100 100" fill="none">
                <path d="M0 46 A46 46 0 0 0 46 0" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.4" />
                <path d="M0 62 A62 62 0 0 0 62 0" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.1" />
            </svg>
            <svg class="absolute bottom-0 right-0 h-32 w-32 rotate-180 text-slate-500" viewBox="0 0 100 100"
                fill="none">
                <path d="M0 46 A46 46 0 0 0 46 0" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.4" />
                <path d="M0 62 A62 62 0 0 0 62 0" stroke="currentColor" stroke-opacity="0.3" stroke-width="1.1" />
            </svg>

            <!-- Cushion sights down each rail -->
            <div class="absolute inset-y-0 left-3 hidden w-1 flex-col justify-around sm:flex">
                <span v-for="i in 9" :key="`l${i}`" class="block h-1.5 w-1.5 rotate-45 bg-slate-500/60" />
            </div>
            <div class="absolute inset-y-0 right-3 hidden w-1 flex-col justify-around sm:flex">
                <span v-for="i in 9" :key="`r${i}`" class="block h-1.5 w-1.5 rotate-45 bg-slate-500/60" />
            </div>

            <!-- Vignette, so the card always sits on the darkest part of the felt -->
            <div class="absolute inset-0"
                style="background:radial-gradient(ellipse 62% 48% at 50% 45%, rgba(2,6,23,0.86) 0%, rgba(2,6,23,0.42) 55%, rgba(2,6,23,0) 100%)" />
            <div class="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-slate-950/80 to-transparent" />
        </div>

        <!-- ── content ───────────────────────────────────────────────────── -->
        <div class="relative flex min-h-screen items-center justify-center p-4 py-8">
            <div class="w-full max-w-[380px]">

                <!-- Brand -->
                <div class="mb-7 text-center">
                    <div class="flex items-center justify-center flex-col gap-2">
                        <img src="/baize_logo.png" class="h-20" alt="">
                        <img src="/baize_logo_text.png" class="w-25" alt="">
                    </div>
                    <p class="mt-1 text-xs text-slate-500">{{ subtitle }}</p>
                </div>

                <!-- Card. Fixed max height with an internal scroll region, so a
                     long form never pushes the action button off screen. -->
                <div class="relative rounded-3xl border border-slate-800 bg-slate-900/80 shadow-2xl shadow-emerald-950/20 backdrop-blur-xl">
                    <div class="pointer-events-none absolute inset-x-8 -top-px h-px bg-gradient-to-r from-transparent via-emerald-400/50 to-transparent" />

                    <!-- ── pinned head ── -->
                    <div class="px-6 pt-6">
                        <div v-if="isEntryMode"
                            class="flex gap-1 rounded-2xl border border-slate-800 bg-slate-950/60 p-1">
                            <button v-for="tab in ['signin', 'signup']" :key="tab" type="button" @click="switchMode(tab)"
                                class="flex-1 cursor-pointer rounded-xl py-2 text-[10px] font-black uppercase tracking-widest transition-all duration-200"
                                :class="mode === tab
                                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/40'
                                    : 'text-slate-500 hover:text-slate-300'">
                                {{ tab === 'signin' ? 'Sign In' : 'Sign Up' }}
                            </button>
                        </div>

                        <div v-else-if="mode !== 'done'">
                            <button type="button" @click="switchMode(previousStep)"
                                class="group flex cursor-pointer items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 transition-colors hover:text-slate-300">
                                <span class="text-sm leading-none transition-transform group-hover:-translate-x-0.5">‹</span>
                                Back
                            </button>
                            <h2 class="mt-4 text-lg font-black">{{ stepTitle }}</h2>
                            <p class="mt-1 text-[11px] leading-snug text-slate-500">{{ stepBlurb }}</p>

                            <!-- Three-step progress through the reset flow -->
                            <div class="mt-4 flex gap-1.5">
                                <span v-for="(step, i) in resetSteps" :key="step"
                                    class="h-0.5 flex-1 rounded-full transition-colors duration-300"
                                    :class="i <= resetStepIndex ? 'bg-emerald-500' : 'bg-slate-800'" />
                            </div>
                        </div>
                    </div>

                    <!-- ── scrolling body ── -->
                    <div class="relative">
                        <!-- Fades hint at content beyond the fold, and disappear
                             at the ends so they never look like a stuck gradient. -->
                        <div class="pointer-events-none absolute inset-x-0 top-0 z-10 h-6 bg-gradient-to-b from-slate-900 to-transparent transition-opacity duration-200"
                            :class="atTop ? 'opacity-0' : 'opacity-100'" />
                        <div class="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-8 bg-gradient-to-t from-slate-900 to-transparent transition-opacity duration-200"
                            :class="atBottom ? 'opacity-0' : 'opacity-100'" />

                        <div ref="scroller" @scroll.passive="updateScrollEdges"
                            class="max-h-[46vh] min-h-[180px] overflow-y-auto overscroll-contain px-6 py-5
                                   [scrollbar-color:theme(colors.slate.700)_transparent] [scrollbar-width:thin]
                                   [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-700/70
                                   [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">

                            <Transition :name="transitionName" mode="out-in">
                                <div :key="mode" class="space-y-4">

                                    <!-- ─── SIGN IN ─── -->
                                    <template v-if="mode === 'signin'">
                                        <PhoneField v-model="form.phone" id="cust-signin-phone"
                                            :error="errors.phone" :touched="touched.phone" />
                                        <PasswordField :form="form" field="password" label="Password"
                                            id="cust-signin-password" placeholder="••••••••"
                                            :error="{ condition: false, message: '' }" @keyup.enter="submitSignIn" />
                                        <button type="button" @click="switchMode('forgot')"
                                            class="cursor-pointer px-0.5 text-[10px] font-bold text-emerald-500 transition-colors hover:text-emerald-400">
                                            Forgot your password?
                                        </button>
                                    </template>

                                    <!-- ─── SIGN UP ─── -->
                                    <template v-else-if="mode === 'signup'">
                                        <PhoneField v-model="form.phone" id="cust-phone" :error="errors.phone"
                                            :touched="touched.phone" />
                                        <p class="-mt-2 px-1 text-[10px] leading-snug text-slate-600">
                                            This is your account name — you'll sign in and get booking
                                            confirmations with it.
                                        </p>

                                        <div>
                                            <TextField :form="form" field="email" label="Email" id="cust-email"
                                                placeholder="you@example.com" type="email" />
                                            <FieldError :message="touched.email ? errors.email : ''" />
                                            <p class="mt-1.5 px-1 text-[10px] leading-snug text-slate-600">
                                                Verification codes and receipts are sent here.
                                            </p>
                                        </div>

                                        <div>
                                            <TextField :form="form" field="name" label="Full Name" id="cust-name"
                                                placeholder="Your name" type="text" />
                                                <FieldError :message="touched.name ? errors.name : ''" />
                                        </div>

                                        <div>
                                            <PasswordField :form="form" field="password" label="Password"
                                                id="cust-password" placeholder="At least 8 characters"
                                                :error="fieldError('password')" />
                                            <PasswordStrength v-if="form.password" :password="form.password" />
                                        </div>

                                        <PasswordField :form="form" field="confirm" label="Confirm Password"
                                            id="cust-confirm" placeholder="Repeat your password"
                                            :error="fieldError('confirm')" @keyup.enter="submitSignUp" />

                                    </template>

                                    <!-- ─── FORGOT: which number ─── -->
                                    <template v-else-if="mode === 'forgot'">
                                        <PhoneField v-model="form.phone" id="cust-forgot-phone" :error="errors.phone"
                                            :touched="touched.phone" />
                                    </template>

                                    <!-- ─── FORGOT: the code ─── -->
                                    <template v-else-if="mode === 'verify'">
                                        <div class="flex justify-between gap-1.5" @paste="onCodePaste">
                                            <input v-for="(digit, i) in codeDigits" :key="i"
                                                :ref="el => codeInputs[i] = el" v-model="codeDigits[i]" type="text"
                                                inputmode="numeric" maxlength="1" autocomplete="one-time-code"
                                                :aria-label="`Digit ${i + 1}`" @input="onCodeInput(i)"
                                                @keydown.backspace="onCodeBackspace(i)" @keyup.enter="submitVerify"
                                                class="aspect-square w-full rounded-xl border bg-slate-950/60 text-center font-mono text-lg font-black text-white outline-none transition-all duration-150"
                                                :class="touched.code && errors.code
                                                    ? 'border-rose-700 focus:border-rose-500'
                                                    : digit
                                                        ? 'border-emerald-600/60 bg-emerald-950/20'
                                                        : 'border-slate-800 hover:border-slate-700 focus:border-emerald-600'" />
                                        </div>
                                        <FieldError :message="touched.code ? errors.code : ''" />

                                        <button type="button" @click="resendCode" :disabled="resendIn > 0 || loading"
                                            class="w-full cursor-pointer text-[10px] font-bold text-slate-500 transition-colors hover:text-slate-300 disabled:cursor-not-allowed disabled:text-slate-700">
                                            {{ resendIn > 0 ? `Resend code in ${resendIn}s` : 'Resend code' }}
                                        </button>
                                    </template>

                                    <!-- ─── FORGOT: new password ─── -->
                                    <template v-else-if="mode === 'reset'">
                                        <div>
                                            <PasswordField :form="form" field="password" label="New Password"
                                                id="cust-new-password" placeholder="At least 8 characters"
                                                :error="fieldError('password')" />
                                            <PasswordStrength v-if="form.password" :password="form.password" />
                                        </div>
                                        <PasswordField :form="form" field="confirm" label="Confirm Password"
                                            id="cust-new-confirm" placeholder="Repeat your password"
                                            :error="fieldError('confirm')" @keyup.enter="submitReset" />
                                    </template>

                                    <!-- ─── DONE ─── -->
                                    <template v-else-if="mode === 'done'">
                                        <div class="space-y-4 py-6 text-center">
                                            <div class="relative mx-auto flex h-14 w-14 items-center justify-center">
                                                <span class="absolute -inset-2 rounded-full border border-emerald-500/20" />
                                                <span
                                                    class="relative flex h-14 w-14 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/15 text-xl text-emerald-400">✓</span>
                                            </div>
                                            <div>
                                                <h2 class="text-lg font-black">{{ doneTitle }}</h2>
                                                <p class="mx-auto mt-1.5 max-w-[16rem] text-[11px] leading-snug text-slate-500">
                                                    {{ doneMessage }}
                                                </p>
                                            </div>
                                        </div>
                                    </template>
                                </div>
                            </Transition>
                        </div>
                    </div>

                    <!-- ── pinned action ── -->
                    <div class="space-y-3 border-t border-slate-800/70 px-6 pb-6 pt-4">
                        <FormAlert :error="serverError" :success="successMessage" />

                        <button @click="primaryAction" :disabled="loading"
                            class="group relative w-full cursor-pointer overflow-hidden rounded-xl bg-emerald-600 py-3.5 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-emerald-900/30 transition-all duration-200 hover:bg-emerald-500 active:scale-[0.985] disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500 disabled:shadow-none">
                            <span class="flex items-center justify-center gap-2">
                                <span v-if="loading"
                                    class="h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-slate-400" />
                                {{ primaryLabel }}
                            </span>
                        </button>

                        <p v-if="mode === 'signup'" class="text-center text-[9px] leading-snug text-slate-600">
                            By creating an account you agree to receive booking confirmations by email.
                        </p>
                    </div>
                </div>

                <p class="mt-6 text-center font-mono text-[10px] text-slate-700">
                    {{ APP_NAME }}
                </p>
            </div>
        </div>
        <PoweredByZain :for-customer="true"/>
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {TextField} from '@baize/ui'
import {PasswordField} from '@baize/ui'
import {PhoneField} from '@baize/ui'
import { isValidPhone, maskPhone } from '@baize/ui'
import {PoweredByZain} from '@baize/ui'
import {TableVisual} from '@baize/ui'
import * as customerApi from '../api.js'

const router = useRouter()
const clubName = ref('')

const APP_NAME = 'Baize'

// ── small presentational helpers, local to this page ───────────────────────
const FieldError = (props) =>
    props.message ? h('p', { class: 'mt-1.5 px-1 text-[10px] font-bold text-rose-400' }, props.message) : null
FieldError.props = { message: String }

const FormAlert = (props) => {
    if (props.error) {
        return h('p', {
            class: 'rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-[10px] font-bold text-rose-400',
            role: 'alert',
        }, props.error)
    }
    if (props.success) {
        return h('p', {
            class: 'rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-bold text-emerald-400',
            role: 'status',
        }, props.success)
    }
    return null
}
FormAlert.props = { error: String, success: String }

const PasswordStrength = (props) => {
    const rules = passwordRules(props.password)
    const met = rules.filter((r) => r.ok).length
    const tone = ['bg-rose-500', 'bg-rose-500', 'bg-amber-500', 'bg-emerald-500'][met] || 'bg-slate-700'
    const label = ['Too weak', 'Too weak', 'Getting there', 'Strong'][met] || ''
    const missing = rules.filter((r) => !r.ok).map((r) => r.label).join(', ')
    return h('div', { class: 'mt-2 px-1' }, [
        h('div', { class: 'mb-1.5 flex gap-1' }, rules.map((r, i) =>
            h('span', {
                key: i,
                class: ['h-1 flex-1 rounded-full transition-colors duration-300', r.ok ? tone : 'bg-slate-800'],
            }))),
        h('p', { class: 'text-[9px] font-bold text-slate-500' }, [
            h('span', { class: met === 3 ? 'text-emerald-400' : 'text-slate-400' }, label),
            missing ? ` · needs ${missing}` : '',
        ]),
    ])
}
PasswordStrength.props = { password: String }

// ── state ──────────────────────────────────────────────────────────────────
// Fifteen balls racked in a triangle. Positions are generated, and the frame
// path in the template was derived from these extents so it surrounds the balls
// instead of slicing through them.
const BALL_R = 11
const BALL_SPACING = 2 * BALL_R + 1.5
const ROW_SPACING = (BALL_SPACING * Math.sqrt(3)) / 2

// Standard pool colours: 1-8 solid, 9-15 striped in the same order.
const BALL_COLOURS = [
    '#facc15', '#2563eb', '#dc2626', '#7c3aed', '#ea580c', '#16a34a', '#7f1d1d', '#0f172a',
    '#facc15', '#2563eb', '#dc2626', '#7c3aed', '#ea580c', '#16a34a', '#7f1d1d',
]

const rack = (() => {
    const balls = []
    for (let row = 0; row < 5; row++) {
        for (let col = 0; col <= row; col++) {
            const n = balls.length + 1
            balls.push({
                n,
                x: 100 + (col - row / 2) * BALL_SPACING,
                y: 34 + row * ROW_SPACING,
                color: BALL_COLOURS[n - 1],
            })
        }
    }
    return balls
})()

const stripedRack = rack.filter((ball) => ball.n > 8)

const mode = ref('signin')   // signin | signup | forgot | verify | reset | done
const loading = ref(false)
const serverError = ref('')
const successMessage = ref('')
const doneTitle = ref('')
const doneMessage = ref('')

const form = reactive({ name: '', phone: '', email: '', password: '', confirm: '' })
const touched = reactive({ name: false, phone: false, email: false, password: false, confirm: false, code: false })

const codeDigits = ref(['', '', '', '', '', ''])
const codeInputs = ref([])
const enteredCode = computed(() => codeDigits.value.join(''))

const resetToken = ref('')
const resendIn = ref(0)
let resendTimer = null

const isEntryMode = computed(() => mode.value === 'signin' || mode.value === 'signup')

const subtitle = computed(() => ({
    signin: 'Welcome back',
    signup: 'Book a table in seconds',
    forgot: 'Let\'s get you back in',
    verify: 'Check your messages',
    reset: 'Choose a new password',
    done: '',
}[mode.value] || ''))

const stepTitle = computed(() => ({
    forgot: 'Reset Password',
    verify: 'Enter Code',
    reset: 'New Password',
}[mode.value] || ''))

const stepBlurb = computed(() => ({
    forgot: 'Enter your number and we\'ll email a 6-digit code to the address on your account.',
    // Careful not to confirm the account exists, or this becomes a way to test
    // which numbers are registered.
    verify: `If ${maskPhone(form.phone)} is registered, a code is on its way to its email address.`,
    reset: 'Pick something you haven\'t used here before.',
}[mode.value] || ''))

const resetSteps = ['forgot', 'verify', 'reset']
const resetStepIndex = computed(() => resetSteps.indexOf(mode.value))
const previousStep = computed(() => ({ forgot: 'signin', verify: 'forgot', reset: 'verify' }[mode.value] || 'signin'))

const primaryLabel = computed(() => {
    if (loading.value) {
        return { signin: 'Signing in…', signup: 'Creating account…', forgot: 'Sending…', verify: 'Checking…', reset: 'Saving…' }[mode.value] || 'Working…'
    }
    return { signin: 'Sign In', signup: 'Create Account', forgot: 'Send Code', verify: 'Verify Code', reset: 'Change Password', done: 'Go to Sign In' }[mode.value]
})

// ── scroll affordances ─────────────────────────────────────────────────────
const scroller = ref(null)
const atTop = ref(true)
const atBottom = ref(true)

function updateScrollEdges() {
    const el = scroller.value
    if (!el) return
    atTop.value = el.scrollTop <= 2
    // A form that doesn't overflow should show no fades at all
    atBottom.value = el.scrollTop + el.clientHeight >= el.scrollHeight - 2
}
onMounted(updateScrollEdges)
watch(mode, () => nextTick(() => {
    scroller.value?.scrollTo({ top: 0 })
    updateScrollEdges()
}))

// Slide forward through the reset flow, back when retreating
const transitionName = ref('slide-fwd')
watch(mode, (next, previous) => {
    const order = ['signin', 'signup', 'forgot', 'verify', 'reset', 'done']
    transitionName.value = order.indexOf(next) >= order.indexOf(previous) ? 'slide-fwd' : 'slide-back'
})

// ── validation ─────────────────────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

function passwordRules(password = '') {
    return [
        { ok: password.length >= 8, label: '8+ characters' },
        { ok: /[A-Za-z]/.test(password), label: 'a letter' },
        { ok: /\d/.test(password), label: 'a number' },
    ]
}

const errors = computed(() => {
    const e = {}
    const needsPhone = ['signin', 'signup', 'forgot'].includes(mode.value)
    const needsPassword = ['signup', 'reset'].includes(mode.value)

    if (needsPhone) {
        if (!form.phone) e.phone = 'Please enter your phone number'
        else if (!isValidPhone(form.phone)) e.phone = 'Enter a valid mobile, e.g. 300 1234567'
    }

    if (mode.value === 'signup') {
        if (!form.name.trim()) e.name = 'Please enter your name'
        // Required, not optional: one-time codes are delivered by email, so an
        // account without one can never be recovered.
        if (!form.email.trim()) e.email = 'Please enter your email'
        else if (!EMAIL_RE.test(form.email.trim())) e.email = 'That doesn\'t look like an email address'
    }

    if (needsPassword) {
        const unmet = passwordRules(form.password).filter((r) => !r.ok)
        if (!form.password) e.password = 'Please choose a password'
        else if (unmet.length) e.password = `Needs ${unmet.map((r) => r.label).join(', ')}`
        if (!form.confirm) e.confirm = 'Please repeat your password'
        else if (form.confirm !== form.password) e.confirm = 'Passwords don\'t match'
    }

    if (mode.value === 'verify' && enteredCode.value.length < 6) e.code = 'Enter all six digits'
    return e
})

const fieldError = (field) => ({
    condition: !!(touched[field] && errors.value[field]),
    message: errors.value[field] || '',
})

function markAllTouched() {
    for (const key of Object.keys(touched)) touched[key] = true
}

function switchMode(next) {
    mode.value = next
    serverError.value = ''
    successMessage.value = ''
    for (const key of Object.keys(touched)) touched[key] = false
    // Passwords never survive a mode change. The phone number does, so the reset
    // flow doesn't make people retype the thing they just entered.
    form.password = ''
    form.confirm = ''
    if (isEntryMode.value) codeDigits.value = ['', '', '', '', '', '']
}

// Clear a stale server error as soon as the user starts fixing things
watch(() => [form.phone, form.password, form.name, form.confirm, form.email], () => {
    serverError.value = ''
})

// ── verification code input ────────────────────────────────────────────────
function onCodeInput(index) {
    touched.code = true
    codeDigits.value[index] = codeDigits.value[index].replace(/\D/g, '').slice(-1)
    if (codeDigits.value[index] && index < 5) codeInputs.value[index + 1]?.focus()
}

function onCodeBackspace(index) {
    // Backspace in an empty box steps back, which is what people expect
    if (!codeDigits.value[index] && index > 0) codeInputs.value[index - 1]?.focus()
}

function onCodePaste(event) {
    const pasted = (event.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    if (!pasted) return
    event.preventDefault()
    codeDigits.value = Array.from({ length: 6 }, (_, i) => pasted[i] || '')
    touched.code = true
    nextTick(() => codeInputs.value[Math.min(pasted.length, 5)]?.focus())
}

function startResendCooldown(seconds = 45) {
    resendIn.value = seconds
    clearInterval(resendTimer)
    resendTimer = setInterval(() => {
        resendIn.value -= 1
        if (resendIn.value <= 0) clearInterval(resendTimer)
    }, 1000)
}
onUnmounted(() => clearInterval(resendTimer))

// ── submission ─────────────────────────────────────────────────────────────
async function run(action) {
    loading.value = true
    serverError.value = ''
    try {
        await action()
    } catch (err) {
        serverError.value = err.message || 'Something went wrong. Please try again.'
        if (err.field) touched[err.field] = true
    } finally {
        loading.value = false
    }
}

function primaryAction() {
    if (loading.value) return
    ({
        signin: submitSignIn,
        signup: submitSignUp,
        forgot: submitForgot,
        verify: submitVerify,
        reset: submitReset,
        done: () => switchMode('signin'),
    })[mode.value]?.()
}

function submitSignIn() {
    touched.phone = true
    if (!form.phone || !form.password) {
        serverError.value = 'Enter your number and password'
        return
    }
    run(async () => {
        await customerApi.signIn({ phone: form.phone, password: form.password })
        router.push('/home')
    })
}

function submitSignUp() {
    markAllTouched()
    if (Object.keys(errors.value).length) return
    run(async () => {
        await customerApi.signUp({
            name: form.name, phone: form.phone, email: form.email, password: form.password,
        })
        router.push('/home')
    })
}

function submitForgot() {
    touched.phone = true
    if (errors.value.phone) return
    run(async () => {
        await customerApi.requestReset({ phone: form.phone })
        // Advance regardless — saying whether the account exists would leak
        // which numbers are registered.
        mode.value = 'verify'
        touched.code = false
        startResendCooldown()
        nextTick(() => codeInputs.value[0]?.focus())
    })
}

function resendCode() {
    if (resendIn.value > 0 || loading.value) return
    run(async () => {
        await customerApi.requestReset({ phone: form.phone })
        codeDigits.value = ['', '', '', '', '', '']
        touched.code = false
        successMessage.value = 'A new code is on its way.'
        startResendCooldown()
        nextTick(() => codeInputs.value[0]?.focus())
    })
}

function submitVerify() {
    touched.code = true
    if (enteredCode.value.length < 6) return
    run(async () => {
        const { resetToken: token } = await customerApi.verifyCode({
            phone: form.phone, code: enteredCode.value,
        })
        resetToken.value = token
        successMessage.value = ''
        mode.value = 'reset'
        touched.password = false
        touched.confirm = false
        form.password = ''
        form.confirm = ''
    })
}

function submitReset() {
    touched.password = true
    touched.confirm = true
    if (errors.value.password || errors.value.confirm) return
    run(async () => {
        await customerApi.resetPassword({ resetToken: resetToken.value, password: form.password })
        resetToken.value = ''
        doneTitle.value = 'Password changed'
        doneMessage.value = 'Use your new password to sign in.'
        mode.value = 'done'
    })
}
</script>

<style scoped>
.slide-fwd-enter-active,
.slide-fwd-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
    transition: opacity 0.18s ease, transform 0.18s ease;
}

.slide-fwd-enter-from { opacity: 0; transform: translateX(12px); }
.slide-fwd-leave-to   { opacity: 0; transform: translateX(-12px); }
.slide-back-enter-from { opacity: 0; transform: translateX(-12px); }
.slide-back-leave-to   { opacity: 0; transform: translateX(12px); }

/* Motion here is decorative; anyone who has asked for less shouldn't get it. */
@media (prefers-reduced-motion: reduce) {
    .slide-fwd-enter-active,
    .slide-fwd-leave-active,
    .slide-back-enter-active,
    .slide-back-leave-active {
        transition: opacity 0.12s ease;
    }
    .slide-fwd-enter-from,
    .slide-fwd-leave-to,
    .slide-back-enter-from,
    .slide-back-leave-to { transform: none; }
}
</style>