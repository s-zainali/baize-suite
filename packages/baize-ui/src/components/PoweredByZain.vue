<template>
    <footer class="relative mt-8 select-none " :class="forCustomer ? '-mx-6' : 'px-6 pb-6'">
        <!-- hairline divider -->
        <div class="mx-auto max-w-sm h-px bg-gradient-to-r from-transparent via-white/15 to-transparent mb-6"></div>

        <div class="flex flex-col items-center justify-center gap-2">
            <span v-if="!forCustomer" class="text-[8px] font-black uppercase tracking-[0.4em] text-white/25">
                Powered by
            </span>

            <div class="flex items-center gap-3">
                <span class="h-px w-10 sm:w-14 bg-gradient-to-r from-transparent to-white/15"></span>
                <span class="w-1 h-1 rotate-45 bg-white/20"></span>

                <div v-if="forCustomer" class="flex items-center justify-center gap-3 shrink-0">
                    <div class="group flex relative items-center justify-center gap-2 cursor-pointer">
                        <img src="/baize_logo.png" class=" h-5 sm:h-5" alt="">
                        <img src="/baize_logo_text.png" class="h-2.5 sm:h-3" alt="">
                        <div
                        class="pointer-events-none absolute left-1/2 -translate-x-1/2 top-0 w-40 h-10 rounded-full bg-emerald-400/20 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    </div>
                    </div>
                    <div
                        class="text-[8px] text-wrap text-center h-fit font-black uppercase tracking-[0.4em] text-white/25 flex gap-1 flex-col sm:flex-row">
                        <span>Powered By</span>
                    </div>
                </div>
                <a href="https://www.linkedin.com/in/s-zain-ali/" target="_blank" rel="noopener noreferrer"
                    class="group zain-wordmark relative text-sm sm:text-xl font-black uppercase tracking-[0.3em] transition-transform duration-300 group-hover:scale-105"
                    :class="forCustomer ? '' : 'pl-[0.3em]'">
                    Zain
                    <div
                        class="pointer-events-none absolute left-1/2 -translate-x-1/2 top-0 w-40 h-10 rounded-full bg-indigo-500/20 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    </div>
                </a>

                <span class="w-1 h-1 rotate-45 bg-white/20"></span>
                <span class="h-px w-10 sm:w-14 bg-gradient-to-l from-transparent to-white/15"></span>
            </div>

            <span class="text-[9px] font-mono text-white/20 tracking-wider">
                Zain Software Solutions · {{ year }}
            </span>
        </div>

        <!-- soft ambient glow behind the wordmark, revealed on hover -->

    </footer>
</template>

<script setup>
const year = new Date().getFullYear()
const props = defineProps({ forCustomer: { type: Boolean, default: false } })
</script>

<style scoped>
.zain-wordmark {
    background: linear-gradient(110deg,
            #818cf8 0%,
            #34d399 30%,
            #38bdf8 55%,
            #c084fc 75%,
            #818cf8 100%);
    background-size: 220% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: zain-shimmer 5s linear alternate infinite;
}

.group:hover .zain-wordmark {
    animation-duration: 2.5s;
}

@keyframes zain-shimmer {
    0% {
        background-position: 0% 50%;
    }

    100% {
        background-position: -220% 50%;
    }
}
</style>