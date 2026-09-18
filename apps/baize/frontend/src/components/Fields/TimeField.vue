<template>
    <div ref="root" class="relative">
        <button type="button" @click="open = !open"
            class="w-full flex items-center justify-between bg-slate-950/60 rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors cursor-pointer"
            :class="open ? 'border-slate-600' : 'border-slate-800 hover:border-slate-700'">
            <span :class="modelValue ? 'font-bold text-white' : 'text-slate-600'">
                {{ modelValue ? formatTime(modelValue) : placeholder }}
            </span>
            <svg class="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        </button>

        <TimePanel v-if="open" :selected="modelValue" :min="min" :max="max" @select="pick" @clear="pick('')" />
    </div>
</template>

<script setup>
import { ref, h, defineComponent, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
    modelValue: { type: String, default: '' },   // 'HH:MM' 24h
    placeholder: { type: String, default: 'Select time' },
    // Slots outside [min, max] are shown greyed out and can't be picked.
    min: { type: String, default: '' },          // earliest selectable 'HH:MM'
    max: { type: String, default: '' },          // latest selectable 'HH:MM'
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const root = ref(null)

const pad = n => String(n).padStart(2, '0')

function formatTime(hhmm) {
    const [hs, ms] = hhmm.split(':').map(Number)
    const period = hs >= 12 ? 'PM' : 'AM'
    const h12 = hs % 12 === 0 ? 12 : hs % 12
    return `${h12}:${pad(ms)} ${period}`
}

function pick(t) {
    emit('update:modelValue', t)
    open.value = false
}

const TimePanel = defineComponent({
    props: {
        selected: { type: String, default: '' },
        min: { type: String, default: '' },
        max: { type: String, default: '' },
    },
    emits: ['select', 'clear'],
    setup(panelProps, { emit }) {
        const options = []
        for (let hr = 0; hr < 24; hr++) {
            for (const min of [0, 30]) {
                options.push(`${pad(hr)}:${pad(min)}`)
            }
        }

        const isDisabled = (t) =>
            (!!panelProps.min && t < panelProps.min) || (!!panelProps.max && t > panelProps.max)

        const listEl = ref(null)

        onMounted(async () => {
            await nextTick()
            // Land on the current pick, else the first slot the user can actually
            // choose — scrolling to noon is useless when noon is disabled.
            const target = listEl.value?.querySelector('[data-active="true"]')
                || listEl.value?.querySelector('[data-first-enabled="true"]')
                || listEl.value?.querySelector('[data-noon="true"]')
            target?.scrollIntoView({ block: 'center' })
        })

        const firstEnabled = () => options.find(t => !isDisabled(t))

        return () => h('div', {
            class: 'absolute left-0 right-0 top-full mt-2 z-20 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-slate-950/80 overflow-hidden'
        }, [
            h('div', {
                ref: listEl,
                class: 'max-h-44 overflow-y-auto p-1 lounge-time-scroll'
            }, options.map(t => {
                const disabled = isDisabled(t)
                return h('button', {
                    type: 'button',
                    key: t,
                    disabled,
                    'data-active': t === panelProps.selected ? 'true' : 'false',
                    'data-noon': t === '12:00' ? 'true' : 'false',
                    'data-first-enabled': t === firstEnabled() ? 'true' : 'false',
                    class: [
                        'w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs text-left font-mono transition-colors',
                        disabled
                            ? 'text-slate-700 line-through cursor-not-allowed'
                            : t === panelProps.selected
                                ? 'bg-emerald-600/15 text-emerald-400 font-bold cursor-pointer'
                                : 'text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer'
                    ],
                    onClick: () => { if (!disabled) emit('select', t) }
                }, formatTime(t))
            })),
            h('div', { class: 'flex justify-end px-3 py-1.5 border-t border-slate-800' }, [
                h('button', {
                    type: 'button',
                    class: 'text-[10px] font-bold text-slate-500 hover:text-red-400 transition-colors cursor-pointer',
                    onClick: () => emit('clear')
                }, 'Clear'),
            ]),
        ])
    }
})

function handleClickOutside(e) {
    if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
.lounge-time-scroll::-webkit-scrollbar {
    width: 6px;
}

.lounge-time-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.lounge-time-scroll::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 3px;
}

.lounge-time-scroll::-webkit-scrollbar-thumb:hover {
    background: #475569;
}
</style>