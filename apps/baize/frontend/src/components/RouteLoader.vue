<template>
    <div class="flex min-h-[60dvh] flex-col items-center justify-center gap-5 p-6">
        <div class="relative h-14 w-14">
            <span class="absolute inset-0 rounded-full border-2 border-slate-800" />
            <span
                class="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-emerald-500" />
            <span class="absolute inset-0 flex items-center justify-center text-lg">{{ icon }}</span>
        </div>
        <div class="text-center">
            <p class="text-[11px] font-black uppercase tracking-widest text-slate-300">{{ label }}</p>
            <p class="mt-1 text-[10px] text-slate-600">{{ hint }}</p>
        </div>
    </div>
</template>

<script setup>
/**
 * Shown while a lazily-loaded page downloads.
 *
 * The canteen carries a lot of artwork, so on a slow counter tablet there is a
 * real gap between the tap and the page appearing. Without this the screen
 * simply sits blank and staff tap again.
 */
defineProps({
    icon: { type: String, default: '⏳' },
    label: { type: String, default: 'Loading' },
    hint: { type: String, default: 'One moment…' },
})
</script>