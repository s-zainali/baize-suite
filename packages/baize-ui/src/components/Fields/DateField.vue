<template>
    <div ref="root" class="relative">
        <button type="button" @click="open = !open"
            class="w-full flex items-center justify-between bg-slate-950/60 rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors cursor-pointer"
            :class="open ? 'border-slate-600' : 'border-slate-800 hover:border-slate-700'">
            <span :class="modelValue ? 'font-bold text-white' : 'text-slate-600'">
                {{ modelValue ? formatDisplay(modelValue) : placeholder }}
            </span>
            <svg class="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
        </button>

        <CalendarPanel v-if="open" :selected="modelValue" :min="min" @select="pick" @clear="pick('')" />
    </div>
</template>

<script setup>
import { ref, reactive, computed, h, defineComponent, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
    modelValue: { type: String, default: '' },   // 'YYYY-MM-DD'
    placeholder: { type: String, default: 'Select date' },
    min: { type: String, default: '' },          // earliest selectable 'YYYY-MM-DD'
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const root = ref(null)

const pad = n => String(n).padStart(2, '0')
const toISO = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`

function formatDisplay(iso) {
    const [y, m, d] = iso.split('-').map(Number)
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return `${d} ${months[m - 1]} ${y}`
}

function pick(iso) {
    emit('update:modelValue', iso)
    open.value = false
}

const CalendarPanel = defineComponent({
    props: {
        selected: { type: String, default: '' },
        min: { type: String, default: '' },
    },
    emits: ['select', 'clear'],
    setup(panelProps, { emit }) {
        const today = new Date()
        const init = panelProps.selected
            ? { y: Number(panelProps.selected.slice(0, 4)), m: Number(panelProps.selected.slice(5, 7)) - 1 }
            : { y: today.getFullYear(), m: today.getMonth() }
        const view = reactive(init)

        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December']
        const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
        const todayISO = toISO(today.getFullYear(), today.getMonth(), today.getDate())

        const days = computed(() => {
            const first = new Date(view.y, view.m, 1)
            const start = new Date(view.y, view.m, 1 - first.getDay())
            return Array.from({ length: 42 }, (_, i) => {
                const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i)
                return {
                    label: d.getDate(),
                    iso: toISO(d.getFullYear(), d.getMonth(), d.getDate()),
                    inMonth: d.getMonth() === view.m,
                    disabled: !!panelProps.min && toISO(d.getFullYear(), d.getMonth(), d.getDate()) < panelProps.min,
                }
            })
        })

        const nav = (delta) => {
            const d = new Date(view.y, view.m + delta, 1)
            view.y = d.getFullYear()
            view.m = d.getMonth()
        }

        return () => h('div', {
            class: 'absolute left-0 top-full mt-2 z-20 w-60 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-slate-950/80 p-3'
        }, [
            h('div', { class: 'flex items-center justify-between mb-2' }, [
                h('button', {
                    type: 'button',
                    class: 'w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer text-sm',
                    onClick: () => nav(-1)
                }, '‹'),
                h('span', { class: 'text-xs font-black text-white' }, `${monthNames[view.m]} ${view.y}`),
                h('button', {
                    type: 'button',
                    class: 'w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer text-sm',
                    onClick: () => nav(1)
                }, '›'),
            ]),
            h('div', { class: 'grid grid-cols-7 mb-1' }, weekdays.map(w =>
                h('span', {
                    class: 'text-center text-[9px] font-black uppercase tracking-wider text-slate-500 py-1',
                    key: w
                }, w)
            )),
            h('div', { class: 'grid grid-cols-7 gap-0.5' }, days.value.map(d =>
                h('button', {
                    type: 'button',
                    key: d.iso,
                    disabled: d.disabled,
                    class: [
                        'h-7 rounded-lg text-[11px] font-bold transition-colors',
                        d.disabled
                            ? 'text-slate-800 cursor-not-allowed'
                            : d.iso === panelProps.selected
                                ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/40 cursor-pointer'
                                : d.iso === todayISO
                                    ? 'text-indigo-400 hover:bg-slate-800 cursor-pointer'
                                    : d.inMonth
                                        ? 'text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer'
                                        : 'text-slate-700 hover:bg-slate-800/50 cursor-pointer'
                    ],
                    onClick: () => { if (!d.disabled) emit('select', d.iso) }
                }, d.label)
            )),
            h('div', { class: 'flex justify-between items-center mt-2 pt-2 border-t border-slate-800' }, [
                h('button', {
                    type: 'button',
                    class: 'text-[10px] font-bold text-slate-500 hover:text-red-400 transition-colors cursor-pointer',
                    onClick: () => emit('clear')
                }, 'Clear'),
                h('button', {
                    type: 'button',
                    class: 'text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer',
                    onClick: () => emit('select', todayISO)
                }, 'Today'),
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