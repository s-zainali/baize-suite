<template>
    <div
        class="fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden bg-slate-950 px-6">

        <!-- Ambient glow: two slow-breathing blooms, so the screen feels alive
             rather than a static spinner on black. -->
        <div class="pointer-events-none absolute inset-0">
            <div class="blob absolute -top-24 -left-24 h-96 w-96 rounded-full bg-emerald-500/15 blur-[120px]" />
            <div class="blob absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-indigo-500/15 blur-[120px]"
                style="animation-delay: -3s" />
        </div>

        <!-- Brand -->
        <div class="relative mb-10 flex flex-col items-center gap-3">
            <img src="/baize_logo.png" class="h-15" alt="">
            <img src="/baize_logo_text.png" class="h-5" alt="">
        </div>

        <!-- Progress ring with the live percentage in the centre -->
        <div class="relative flex h-44 w-44 items-center justify-center">
            <svg viewBox="0 0 120 120" class="absolute inset-0 h-full w-full -rotate-90">
                <defs>
                    <linearGradient id="ls-grad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#34d399" />
                        <stop offset="100%" stop-color="#22d3ee" />
                    </linearGradient>
                </defs>
                <circle cx="60" cy="60" r="52" fill="none" stroke="#1e293b" stroke-width="6" />
                <circle cx="60" cy="60" r="52" fill="none" stroke="url(#ls-grad)" stroke-width="6"
                    stroke-linecap="round" :stroke-dasharray="C"
                    :stroke-dashoffset="C - (shown / 100) * C"
                    style="transition: stroke-dashoffset 0.35s ease-out" />
            </svg>
            <div class="flex flex-col items-center">
                <span class="font-mono text-5xl font-black tabular-nums leading-none text-white">{{ shown }}</span>
                <span class="mt-1 text-xs font-black text-slate-600">PERCENT</span>
            </div>
        </div>

        <!-- Current phase -->
        <p class="relative mt-8 h-4 text-[11px] font-bold uppercase tracking-widest text-slate-400">
            <span :key="label" class="phase inline-block">{{ label }}</span>
        </p>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    progress: { type: Number, default: 0 },
    label: { type: String, default: 'Loading' },
})

const C = 2 * Math.PI * 52   // ring circumference
const shown = computed(() => Math.max(0, Math.min(100, Math.round(props.progress))))
</script>

<style scoped>
.float {
    animation: ls-float 3.5s ease-in-out infinite;
}

.blob {
    animation: ls-breathe 6s ease-in-out infinite;
}

/* Re-keyed on each label change, so the phase text fades in rather than snapping */
.phase {
    animation: ls-fade 0.4s ease-out;
}

@keyframes ls-float {

    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-6px);
    }
}

@keyframes ls-breathe {

    0%,
    100% {
        opacity: 0.5;
        transform: scale(1);
    }

    50% {
        opacity: 1;
        transform: scale(1.12);
    }
}

@keyframes ls-fade {
    from {
        opacity: 0;
        transform: translateY(3px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {

    .float,
    .blob,
    .phase {
        animation: none;
    }
}
</style>