<template>
    <div
        class="mb-4 border border-slate-700 flex justify-between gap-2 z-40 bg-slate-800 shadow-md p-4 left-0 rounded-[1.5rem]" :class="isCol ? 'flex-col items-start' : 'flex-row items-center'">
        <h1 class="text-xl font-black tracking-tight text-white ml-2 shrink-0 w-25" :class="isCol? 'mb-2' : ''">{{ title }}</h1>

        <div
            class="flex flex-nowrap gap-4 items-center w-full justify-between min-w-0 flex-1 border-slate-600"
            :class="isCol ? 'border-none' : 'border-l pl-2'">
            <!-- items: wrap or horizontal-scroll depending on `wrap` -->
            <div class="flex gap-2 items-center min-w-0 flex-1 queue-scroll justify-start"
                :class="wrap ? 'flex-wrap' : 'overflow-x-auto'">
                <div v-if="empty" class="flex items-center h-12 justify-center ml-4">
                    <span class="text-sm font-bold text-slate-300 whitespace-nowrap">{{ emptyText }}</span>
                </div>
                <slot v-else/>
            </div>

            <!-- action button(s) on the right -->
            <div v-if="$slots.action" class="flex gap-2 shrink-0">
                <slot name="action" />
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    title: { type: String, required: true },
    empty: { type: Boolean, default: false },
    emptyText: { type: String, default: 'Nothing here yet' },
    // true = items wrap onto multiple lines (bookings); false = horizontal scroll (queue)
    wrap: { type: Boolean, default: false },
    isCol: { type: Boolean, default: false },
})
</script>

<style scoped>
.queue-scroll {
    scrollbar-width: thin;
    scrollbar-color: #334155 transparent;
}

.queue-scroll::-webkit-scrollbar {
    height: 6px;
}

.queue-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.queue-scroll::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 9999px;
}

.queue-scroll::-webkit-scrollbar-thumb:hover {
    background: #475569;
}
</style>