<template>
    <div
        class="group relative flex h-64 flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-900 shadow-xl transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-400/40 hover:shadow-2xl hover:shadow-emerald-500/10">

        <!-- logo poster background (~50% opacity) with a scrim for legibility -->
        <div class="pointer-events-none absolute inset-0">
            <img v-if="logoSrc && !logoFailed" :src="logoSrc" alt=""
                class="h-full w-full object-cover translate-x-25 opacity-50 transition-transform duration-700 ease-out group-hover:scale-105"
                @error="logoFailed = true" />
            <div v-else class="absolute inset-0 flex items-center justify-center">
                <span class="select-none text-[9rem] font-black leading-none text-white/[0.04]">{{ initial }}</span>
            </div>
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/75 to-slate-950/25"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/0 to-emerald-500/0 transition-colors duration-300 group-hover:from-emerald-500/5"></div>
        </div>

        <!-- top: branch count + favourite -->
        <div class="relative flex items-start justify-between p-4">
            <span
                class="rounded-full border border-white/15 bg-black/40 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-white/90 backdrop-blur-md">
                {{ club.branchesCount }} {{ club.branchesCount === 1 ? 'Branch' : 'Branches' }}
            </span>
            <button type="button" @click="$emit('toggle-favourite')"
                :title="club.isFavourite ? 'Remove from favourites' : 'Add to favourites'"
                class="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border backdrop-blur-md transition-colors"
                :class="club.isFavourite
                    ? 'border-amber-400/40 bg-amber-400/20 text-amber-300'
                    : 'border-white/15 bg-black/40 text-slate-400 hover:border-white/30 hover:text-slate-200'">
                <svg viewBox="0 0 24 24" class="h-4 w-4"
                    :fill="club.isFavourite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                    <path d="M12 17.3l-6.2 3.7 1.6-7.1L2 9.2l7.2-.6L12 2l2.8 6.6 7.2.6-5.4 4.7 1.6 7.1z"
                        stroke-linejoin="round" />
                </svg>
            </button>
        </div>

        <!-- bottom: identity + actions -->
        <div class="relative mt-auto p-4">
            <div class="flex items-end gap-3">
                <div
                    class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden">
                    <img v-if="logoSrc && !logoFailed" :src="logoSrc" alt="" class="h-full w-full object-cover" />
                    <span v-else class="text-xl font-black text-emerald-400">{{ initial }}</span>
                </div>
                <div class="min-w-0 pb-0.5">
                    <h3 class="truncate text-xl font-black leading-tight text-white">{{ club.name }}</h3>
                    <p class="mt-1 flex items-center gap-1 truncate text-xs font-medium text-slate-300">
                        <svg class="h-3 w-3 shrink-0 text-emerald-400" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2">
                            <path d="M12 21s-6-5.686-6-10a6 6 0 1112 0c0 4.314-6 10-6 10z" stroke-linecap="round"
                                stroke-linejoin="round" />
                            <circle cx="12" cy="11" r="2" />
                        </svg>
                        <span class="truncate">{{ club.location }}</span>
                    </p>
                </div>
            </div>

            <div class="mt-4 flex gap-2">
                <button type="button" @click="$emit('view-club')"
                    class="flex-1 cursor-pointer rounded-xl border border-white/20 bg-white/10 py-2.5 text-[10px] font-black uppercase tracking-wider text-white backdrop-blur-md transition-all hover:bg-white/20">
                    View Arena
                </button>
                <button type="button" @click="$emit('select-club')"
                    class="flex-1 cursor-pointer rounded-xl bg-emerald-500 py-2.5 text-[10px] font-black uppercase tracking-wider text-slate-950 shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-400">
                    Create Booking
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ club: { type: Object, default: () => ({}) } })
defineEmits(['select-club', 'view-club', 'toggle-favourite'])
const logoFailed = ref(false)
const logoSrc = computed(() => props.club?.logoUrl || null)
const initial = computed(() => (props.club?.name || 'C').charAt(0).toUpperCase())
</script>