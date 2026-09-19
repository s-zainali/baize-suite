<template>
    <div v-if="isPool || isSnooker || isPrivatePool || isPrivateSnooker"
        :style="isDisplay ? { width: '101px', height: `${isSnooker ? '190px' : '175px'}` } : {}">
        <div class="w-[202px] relative flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : ' mt-12'">

            <!-- VIP Container Indicator -->
            <div v-if="isPrivatePool || isPrivateSnooker"
                class="absolute -inset-y-4 inset-x-0 rounded-[2rem] bg-slate-950/40 border-2 border-dashed pointer-events-none z-0 transition-colors duration-500"
                :class="[
                    props.table.isActive
                        ? 'border-amber-500/80 shadow-amber-950/30'
                        : 'border-amber-800/40'
                ]">
                <!-- <div class="absolute -top-3 left-1/2 -translate-x-1/2 text-white font-black text-[8px] tracking-widest px-2 py-0.5 rounded-full uppercase shadow-md whitespace-nowrap transition-colors duration-500"
                    :class="isPrivateSnooker ? (props.table.isActive ? 'bg-amber-600' : 'bg-amber-950') : 'bg-purple-600'">
                    {{ isPrivateSnooker ? 'VIP SNOOKER' : 'VIP POOL' }} #{{ table.id }}
                </div> -->
            </div>

            <div class="flex flex-col items-center w-full relative z-10 group">
                <div class="relative w-full rounded-2xl border-[0.8rem] shadow-xl transition-all duration-500"
                    :class="[isSnooker ? 'h-[380px]' : 'h-[350px]', tableThemeClasses, isDisplay ? 'flex items-center justify-center' : '']">
                    <PoolHole v-for="pos in holePositions" :key="pos" :position="pos" />
                    <span v-if="showBookingStatus && isDisplay && table.isActive"
                        class="absolute top-20 bg-amber-400 py-0.5 px-2 rounded-lg font-black tracking-widest uppercase text-md text-slate-900/90">!
                        ACTIVE</span>
                    <div class="inset-x-0 flex flex-col items-center px-4 pointer-events-none text-center z-10"
                        :class="isDisplay ? 'gap-4 h-full items-center justify-between py-4' : 'absolute top-1.5'">
                        <div class="h-8 flex flex-col items-center justify-center">
                            <span class="flex flex-col items-center font-black uppercase tracking-[0.2em] leading-tight"
                                :class="labelColorClass, isDisplay ? 'text-xl' : 'text-[9px]'">
                                <template v-if="isPrivateSnooker">
                                    <span>Snooker</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else-if="table.type === 'privatePool'">
                                    <span>Pool</span>
                                    <span class="opacity-70 mt-0.5" :class="!isDisplay ? 'text-[8px]' : 'text-xs'">VIP
                                        Room</span>
                                </template>
                                <template v-else>
                                    <span>{{ table.type.toUpperCase() }}</span>
                                </template>
                            </span>
                        </div>

                        <span class="font-black drop-shadow-md tracking-tight leading-none"
                            :class="isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white'">
                            {{ table.id }}
                        </span>
                        <span v-if="isDisplay && !hideDisplayRate"
                            class="text-xl font-semibold tracking-wider text-slate-200">{{
                                currentRate }}
                            Rs/min</span>
                    </div>

                    <div v-if="!isDisplay"
                        class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-center z-10 w-full px-3">
                        <div class="text-2xl font-mono font-bold tracking-wider px-2 py-0.5 rounded-lg transition-all duration-200 py-1"
                            :class="timerClasses">
                            {{ formattedTime }}
                        </div>
                        <div v-if="canResume"
                            class="mt-1 text-sm font-black font-mono text-amber-300 bg-slate-950/50 rounded-md px-2 py-0.5">
                            Rs {{ pendingTotal }}
                        </div>
                    </div>
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span
                            class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒
                            LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div v-else-if="isPlaystation || isPc || isXbox" :class="isDisplay ? 'w-[101px] h-[195px]' : ''">
        <div class="w-[202px] relative flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : 'mt-12'">

            <div class="flex flex-col items-center w-full relative z-10 group">

                <!-- Station card -->
                <div class="relative w-full h-[390px] rounded-2xl border-2 shadow-xl transition-all duration-500 bg-slate-950 flex flex-col items-center px-3 pb-8 overflow-hidden"
                    :class="[
                        props.table.isActive
                            ? isPlaystation
                                ? 'border-blue-500 shadow-2xl shadow-blue-500/40'
                                : isPc
                                    ? 'border-purple-500 shadow-2xl shadow-purple-500/40'
                                    : 'border-green-700 shadow-2xl shadow-green-700/40'
                            : 'border-slate-800',
                        isDisplay ? 'gap-4 pt-4 flex justify-between items-center' : 'pt-8'
                    ]">
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span
                            class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒
                            LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>

                    <!-- Header: type label + station number -->
                    <span v-if="!isDisplay"
                        class="text-[9px] font-black uppercase tracking-[0.2em] leading-tight transition-colors duration-500 pb-2"
                        :class="props.table.isActive
                            ? (isPlaystation ? 'text-blue-300/70' : isPc ? 'text-purple-300/70' : 'text-green-600/70')
                            : 'text-slate-500'">
                        {{ headerTitle }}
                    </span>
                    <!-- TV / Monitor -->
                    <div class="w-full mt-2 mb-2 relative z-5">
                        <!-- ambient glow behind the TV when live -->
                        <div class="absolute -inset-2 rounded-xl blur-lg transition-opacity duration-500 pointer-events-none"
                            :class="[
                                props.table.isActive ? 'opacity-100' : 'opacity-0',
                                isPlaystation ? 'bg-blue-500/25' : isPc ? 'bg-purple-500/25' : 'bg-green-700/25'
                            ]"></div>

                        <div
                            class="relative w-full aspect-[16/10] rounded-lg border-[3px] bg-slate-900 overflow-hidden border-slate-700">
                            <!-- screen -->
                            <div class="absolute inset-0 flex flex-col items-center justify-center overflow-hidden px-1 transition-all duration-500 gap-1"
                                :class="props.table.isActive
                                    ? isPlaystation
                                        ? 'bg-gradient-to-br from-sky-300 via-sky-500 to-sky-300'
                                        : isPc
                                            ? 'bg-gradient-to-br from-purple-400 via-purple-600 to-purple-400'
                                            : 'bg-gradient-to-br from-emerald-400 via-emerald-600 to-emerald-400'
                                    : 'bg-slate-950'">

                                    <span class="font-black tracking-widest select-none uppercase text-center" :class="[
                                        isDisplay ? 'text-xl' : 'text-lg',
                                        (isDisplay && table.isActive)
                                            ? (isPlaystation ? 'text-slate-100' : isPc ? 'text-purple-100' : 'text-green-100')
                                            : 'text-slate-400'
                                    ]">
                                        {{ tvScreenTypeLabel }}
                                    </span>
                                    <span v-if="(selected || showBookingStatus) && isDisplay && table.isActive"
                                        class="py-0.5 px-2 rounded-lg font-black tracking-widest uppercase text-md "
                                        :class="selected ? 'bg-emerald-600 text-slate-100/90' : 'bg-amber-400 text-slate-900/90'">{{
                                            selected ? 'SELECTED' : '! ACTIVE' }}</span>
                            </div>
                            <!-- console/PC light strip -->
                            <div v-if="props.table.isActive" class="absolute bottom-0 inset-x-0 h-[2px] bg-amber-500"
                                :class="isPlaystation
                                    ? 'shadow-[0_0_8px_2px_rgba(96,165,250,0.8)]'
                                    : isPc
                                        ? 'shadow-[0_0_8px_2px_rgba(192,132,252,0.8)]'
                                        : 'shadow-[0_0_8px_2px_rgba(74,150,108,0.8)]'">
                            </div>
                            <div v-else class="absolute bottom-1 right-1.5 w-1.5 h-1.5 rounded-full bg-amber-500/70">
                            </div>
                        </div>

                        <!-- TV stand -->
                        <div class="mx-auto w-8 h-1.5 bg-slate-700"></div>
                        <div class="mx-auto w-16 h-1 bg-slate-800 rounded-full"></div>
                    </div>

                    <span class="font-black drop-shadow-md tracking-tight leading-none mt-1"
                        :class="[isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white']">
                        {{ table.id }}
                    </span>

                    <!-- Console/PC + Controller/Keyboard Shelf -->
                    <div class="flex items-end justify-center gap-3 z-5 mt-2.5">
                        <!-- HARDWARE TOWER / CONSOLE VISUALS -->
                        <!-- PC Desktop Tower -->
                        <div v-if="isPc"
                            class="relative w-5 h-12 translate-x-3 bg-slate-900 rounded-md border border-slate-700 flex flex-col justify-between p-1">
                            <div class="w-full h-1 bg-slate-800 rounded-xs flex justify-around items-center px-0.5">
                                <div class="w-1 h-[1px] transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-purple-400' : 'bg-slate-600'"></div>
                                <div class="w-1 h-[1px] transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-purple-400' : 'bg-slate-600'"></div>
                            </div>
                            <!-- Glass Panel & RGB Fans -->
                            <div
                                class="w-full flex-1 my-0.5 bg-slate-950 rounded-xs border border-slate-800/80 p-0.5 flex flex-col justify-around items-center overflow-hidden">
                                <div class="w-2.5 h-2.5 rounded-full border border-dashed transition-all duration-500"
                                    :class="props.table.isActive ? 'border-purple-400 shadow-[0_0_4px_rgba(192,132,252,0.8)]' : 'border-slate-700'">
                                </div>
                                <div class="w-2.5 h-2.5 rounded-full border border-dashed transition-all duration-500"
                                    :class="props.table.isActive ? 'border-indigo-400 shadow-[0_0_4px_rgba(129,140,248,0.8)]' : 'border-slate-700'">
                                </div>
                            </div>
                            <!-- Power Button -->
                            <div class="w-full flex justify-between items-center px-0.5">
                                <div class="w-1 h-1 rounded-full transition-all duration-500"
                                    :class="props.table.isActive ? 'bg-purple-400 shadow-[0_0_4px_rgba(192,132,252,0.9)]' : 'bg-amber-500/60'">
                                </div>
                                <div class="w-1.5 h-[1.5px] bg-slate-700 rounded-xs"></div>
                            </div>
                        </div>

                        <!-- PS5 -->
                        <div v-else-if="isPs5" class="relative w-4 h-11">
                            <div
                                class="absolute inset-y-0 left-0 w-1.5 rounded-l-md rounded-r-[2px] bg-gradient-to-b from-slate-200 to-slate-400">
                            </div>
                            <div
                                class="absolute inset-y-0 right-0 w-1.5 rounded-r-md rounded-l-[2px] bg-gradient-to-b from-slate-200 to-slate-400">
                            </div>
                            <div
                                class="absolute inset-y-[2px] left-1/2 -translate-x-1/2 w-[5px] rounded-sm bg-slate-950">
                            </div>
                            <div class="absolute top-1 left-1/2 -translate-x-1/2 w-[3px] h-3 rounded-full transition-all duration-500"
                                :class="props.table.isActive
                                    ? 'bg-blue-400 shadow-[0_0_5px_1px_rgba(96,165,250,0.9)]'
                                    : 'bg-amber-500/60'"></div>
                        </div>

                        <!-- PS4 -->
                        <div v-else-if="isPs4" class="relative w-5 h-12 flex items-center justify-center">
                            <div class="absolute -bottom-0 z-5 w-6 h-1.5 bg-slate-800 rounded-sm"></div>
                            <div
                                class="absolute inset-y-0 w-4 bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800 rounded-xs shadow-md flex items-center justify-center border border-slate-700/50">
                                <div
                                    class="absolute inset-y-1 w-1 bg-slate-950 rounded-full flex flex-col items-center justify-between py-1">
                                    <div class="w-[1.5px] h-2 bg-slate-800 rounded-full"></div>
                                    <div class="w-[1.5px] h-1.5 bg-slate-800 rounded-full"></div>
                                </div>
                            </div>
                            <div class="absolute top-1.5 left-1/2 -translate-x-1/2 w-[2px] h-2 rounded-full transition-all duration-300"
                                :class="props.table.isActive
                                    ? 'bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.9)]'
                                    : 'bg-amber-500/80'"></div>
                        </div>

                        <!-- Xbox Series X -->
                        <div v-else-if="isXboxSeriesX"
                            class="relative w-5 h-12 bg-slate-900 rounded-md border border-slate-700 flex flex-col justify-between py-1 items-center">
                            <div
                                class="w-2.5 h-2.5 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center">
                                <div class="w-1 h-1 rounded-full transition-all duration-500" :class="props.table.isActive
                                    ? 'bg-green-600 shadow-[0_0_5px_1px_rgba(74,222,128,0.9)]'
                                    : 'bg-amber-500/60'"></div>
                            </div>
                            <div class="w-3 h-1 bg-slate-950 rounded-sm"></div>
                        </div>

                        <!-- Xbox One -->
                        <div v-else-if="isXboxOne" class="relative w-5 h-12 flex items-center justify-center">
                            <div class="absolute -bottom-0 z-5 w-6 h-1.5 bg-slate-800 rounded-sm"></div>
                            <div
                                class="absolute inset-y-0 w-4.5 bg-slate-900 rounded-sm border border-slate-700 flex flex-col justify-between py-1.5 items-center overflow-hidden">
                                <div
                                    class="w-2 h-2 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center">
                                    <div class="w-1 h-1 rounded-full transition-all duration-500" :class="props.table.isActive
                                        ? 'bg-green-500 shadow-[0_0_5px_1px_rgba(74,222,128,0.9)]'
                                        : 'bg-amber-500/60'"></div>
                                </div>
                                <div class="w-3 h-[1.5px] bg-slate-950 rounded-full"></div>
                                <div class="w-3.5 flex flex-col gap-[1.5px] opacity-40">
                                    <div class="w-full h-[1px] bg-slate-600"></div>
                                    <div class="w-full h-[1px] bg-slate-600"></div>
                                    <div class="w-full h-[1px] bg-slate-600"></div>
                                </div>
                            </div>
                        </div>

                        <!-- CONTROLLER / KEYBOARD & MOUSE VISUALS -->
                        <div>
                            <!-- PC Keyboard + Mouse -->
                            <svg v-if="isPc" viewBox="0 0 64 28" class="w-20 h-9 translate-x-2">
                                <!-- Keyboard Top Cable -->
                                <!-- <path d="M 26 2 V 0" stroke="#475569" stroke-width="1" stroke-linecap="round" /> -->

                                <!-- Scaled Up Heavyweight Keyboard Chassis -->
                                <path
                                    d="M 2.5 2.5 L 18 2.5 L 20 0.8 H 30 L 32 2.5 H 50.5 L 52.5 4.5 V 25.5 L 50.5 27.5 H 2.5 L 0.5 25.5 V 4.5 Z"
                                    :fill="props.table.isActive ? '#1e293b' : '#0f172a'" stroke="#475569"
                                    stroke-width="0.8" />

                                <!-- Top Badge Accent -->
                                <rect x="23" y="1.0" width="6" height="1.2" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#475569'" />

                                <!-- Maximized Recessed Keybed Area -->
                                <rect x="1.4" y="3.3" width="49.8" height="23.4" rx="0.5"
                                    :fill="props.table.isActive ? '#090d16' : '#020617'" />

                                <!-- ================= ROW 1: FUNCTION & NUMBER ROW ================= -->
                                <rect x="2.0" y="4.0" width="2.5" height="2.5" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="4.8" y="4.0" width="10.2" height="2.5" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="15.3" y="4.0" width="10.2" height="2.5" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="25.8" y="4.0" width="10.2" height="2.5" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- Number Row -->
                                <rect x="2.0" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="4.8" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="7.6" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="10.4" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="13.2" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="16.0" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="18.8" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="21.6" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="24.4" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="27.2" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="30.0" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="32.8" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="35.6" y="7.0" width="5.0" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />

                                <!-- ================= ROW 2: QWERTY ROW (W PURPLE) ================= -->
                                <rect x="2.0" y="10.6" width="4.0" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="6.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="9.3" y="10.6" width="2.7" height="3.2" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" stroke="#1e293b"
                                    stroke-width="0.2" /> <!-- W -->
                                <rect x="12.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="15.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="18.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="21.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="24.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="27.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="30.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="33.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="36.3" y="10.6" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="39.3" y="10.6" width="2.3" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- ================= ROW 3: ASDF ROW (A, S, D PURPLE) ================= -->
                                <rect x="2.0" y="14.2" width="4.7" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="7.0" y="14.2" width="2.7" height="3.2" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" stroke="#1e293b"
                                    stroke-width="0.2" /> <!-- A -->
                                <rect x="10.0" y="14.2" width="2.7" height="3.2" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" stroke="#1e293b"
                                    stroke-width="0.2" /> <!-- S -->
                                <rect x="13.0" y="14.2" width="2.7" height="3.2" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" stroke="#1e293b"
                                    stroke-width="0.2" /> <!-- D -->
                                <rect x="16.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="19.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="22.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="25.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="28.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="31.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="34.0" y="14.2" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="37.0" y="14.2" width="4.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- ================= ROW 4: ZXCV ROW ================= -->
                                <rect x="2.0" y="17.8" width="5.7" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="8.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="11.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="14.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="17.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="20.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="23.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="26.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="29.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="32.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="35.0" y="17.8" width="2.7" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="38.0" y="17.8" width="3.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- ================= ROW 5: BOTTOM ROW & SPACEBAR ================= -->
                                <rect x="2.0" y="21.4" width="3.4" height="4.8" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="5.7" y="21.4" width="2.9" height="4.8" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="8.9" y="21.4" width="2.9" height="4.8" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="12.1" y="21.4" width="18.5" height="4.8" rx="0.4"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <!-- Spacebar -->
                                <rect x="30.9" y="21.4" width="2.9" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="34.1" y="21.4" width="2.9" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="37.3" y="21.4" width="4.3" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- ================= NAVIGATION & ARROW BLOCK ================= -->
                                <rect x="42.8" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="45.7" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="48.6" y="7.0" width="2.6" height="3.2" rx="0.3" fill="#090d16" stroke="#1e293b"
                                    stroke-width="0.2" />
                                <rect x="42.8" y="10.6" width="2.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="45.7" y="10.6" width="2.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="48.6" y="10.6" width="2.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- Arrow Keys -->
                                <rect x="45.7" y="17.8" width="2.6" height="3.2" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="42.8" y="21.4" width="2.6" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="45.7" y="21.4" width="2.6" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />
                                <rect x="48.6" y="21.4" width="2.6" height="4.8" rx="0.3" fill="#090d16"
                                    stroke="#1e293b" stroke-width="0.2" />

                                <!-- ================= PROPORTIONAL GAMING MOUSE (SCALED & SHIFTED) ================= -->
                                <!-- Cable -->
                                <!-- <path d="M 59.5 7.5 V 0" stroke="#475569" stroke-width="0.8" stroke-linecap="round" /> -->

                                <!-- Mouse Body Frame -->
                                <path
                                    d="M 59.5 7.5 C 57.2 7.5 56.3 9.5 56.3 12.8 C 56.3 15.0 57.1 17.0 56.6 19.3 C 56.1 21.2 57.2 22.5 59.5 22.5 C 61.8 22.5 62.9 21.2 62.4 19.3 C 61.9 17.0 62.7 15.0 62.7 12.8 C 62.7 9.5 61.8 7.5 59.5 7.5 Z"
                                    :fill="props.table.isActive ? '#1e293b' : '#0f172a'" stroke="#475569"
                                    stroke-width="0.7" />

                                <!-- Button Seams -->
                                <path d="M 59.5 7.5 V 13.8 M 56.5 13.5 H 62.5" stroke="#475569" stroke-width="0.4" />

                                <!-- Scroll Wheel & Panel -->
                                <rect x="58.4" y="8.8" width="2.2" height="4.2" rx="0.4"
                                    :fill="props.table.isActive ? '#090d16' : '#020617'" stroke="#475569"
                                    stroke-width="0.25" />

                                <rect x="58.7" y="9.1" width="1.6" height="2.0" rx="0.3"
                                    :fill="props.table.isActive ? '#c084fc' : '#1e293b'" />

                                <rect x="58.9" y="11.5" width="1.2" height="0.9" rx="0.2" fill="#1e293b" />

                                <!-- Dragon Emblem -->
                                <path d="M 59.5 17.2 L 58.4 18.3 L 59.5 19.4 L 60.6 18.3 Z"
                                    :fill="props.table.isActive ? '#c084fc' : '#475569'" />
                            </svg>

                            <!-- PS4 DualShock 4 Controller -->
                            <svg v-else-if="isPs4" viewBox="0 0 64 42" class="w-14 h-9">
                                <path
                                    d="M 15 6 C 10 6 7 10 6 17 L 3 29 C 2 34 5.5 37.5 9 37.5 C 12.5 37.5 14.5 32.5 17 26.5 C 19.5 21.5 23.5 20.5 32 20.5 C 40.5 20.5 44.5 21.5 47 26.5 C 49.5 32.5 51.5 37.5 55 37.5 C 58.5 37.5 62 34 61 29 L 58 17 C 57 10 54 6 49 6 C 43 6 40 10 36 10 L 28 10 C 24 10 21 6 15 6 Z"
                                    :fill="props.table.isActive ? '#f8fafc' : '#64748b'"
                                    class="transition-colors duration-500" />
                                <path d="M 12 6 C 14 4 19 4 21 6 Z M 52 6 C 50 4 45 4 43 6 Z"
                                    :fill="props.table.isActive ? '#cbd5e1' : '#334155'" />
                                <path
                                    d="M 18 22.5 C 18 19.5 22 18.5 32 18.5 C 42 18.5 46 19.5 46 22.5 C 46 26.5 42 29 32 29 C 22 29 18 26.5 18 22.5 Z"
                                    :fill="props.table.isActive ? '#0f172a' : '#020617'" />
                                <circle cx="23.5" cy="24.5" r="3.6" :fill="props.table.isActive ? '#1e293b' : '#0f172a'"
                                    stroke="#475569" stroke-width="0.5" />
                                <circle cx="40.5" cy="24.5" r="3.6" :fill="props.table.isActive ? '#1e293b' : '#0f172a'"
                                    stroke="#475569" stroke-width="0.5" />
                                <path d="M 22 9.5 L 42 9.5 L 40 17.5 L 24 17.5 Z"
                                    :fill="props.table.isActive ? '#1e293b' : '#0f172a'" rx="0.8" />
                                <path d="M 25 8 L 39 8 L 38.5 9 L 25.5 9 Z"
                                    :fill="props.table.isActive ? '#60a5fa' : '#334155'"
                                    :style="props.table.isActive ? 'filter: drop-shadow(0 0 3px rgba(96,165,250,0.9))' : ''"
                                    class="transition-all duration-500" />
                                <path
                                    d="M 10.5 13.5 H 12.5 V 15.5 H 14.5 V 17.5 H 12.5 V 19.5 H 10.5 V 17.5 H 8.5 V 15.5 H 10.5 Z"
                                    fill="#334155" class="translate-x-0.5 -translate-y-0.25" />
                                <circle cx="51" cy="12.5" r="1.2" fill="#334155" />
                                <circle cx="54" cy="15.5" r="1.2" fill="#334155" />
                                <circle cx="48" cy="15.5" r="1.2" fill="#334155" />
                                <circle cx="51" cy="18.5" r="1.2" fill="#334155" />
                            </svg>

                            <!-- PS5 DualSense Controller -->
                            <svg v-else-if="isPs5" viewBox="0 0 64 42" class="w-14 h-9">
                                <path
                                    d="M14 6 C7 6 3 13 2 24 C1 32 4 39 9 39 C14 39 16 33 18 28 L46 28 C48 33 50 39 55 39 C60 39 63 32 62 24 C61 13 57 6 50 6 L14 6 Z"
                                    :fill="props.table.isActive ? '#f8fafc' : '#64748b'"
                                    class="transition-colors duration-500" />

                                <!-- Center housing: covers both joysticks with a flat bottom flush to the main body inner arch -->
                                <path
                                    d="M 19 17 L 45 17 C 47.5 17, 47.5 28, 44.5 28 L 19.5 28 C 16.5 28, 16.5 17, 19 17 Z"
                                    :fill="props.table.isActive ? '#0f172a' : '#020617'" />

                                <circle cx="24" cy="24" r="3.8" :fill="props.table.isActive ? '#1e293b' : '#0f172a'"
                                    stroke="#475569" stroke-width="0.5" />
                                <circle cx="40" cy="24" r="3.8" :fill="props.table.isActive ? '#1e293b' : '#0f172a'"
                                    stroke="#475569" stroke-width="0.5" />
                                <path d="M22 6.5 L42 6.5 L40 17 L24 17 Z"
                                    :fill="props.table.isActive ? '#cbd5e1' : '#334155'" />
                                <path d="M20.5 7 L22.5 17 M43.5 7 L41.5 17" stroke-width="1.2" stroke-linecap="round"
                                    :stroke="props.table.isActive ? '#38bdf8' : '#334155'"
                                    :style="props.table.isActive ? 'filter: drop-shadow(0 0 3px rgba(56,189,248,0.9))' : ''"
                                    class="transition-all duration-500" />
                                <path d="M12 14 H14 V16 H16 V18 H14 V20 H12 V18 H10 V16 H12 Z" fill="#334155" />
                                <circle cx="52" cy="14" r="1.2" fill="#334155" />
                                <circle cx="55" cy="17" r="1.2" fill="#334155" />
                                <circle cx="49" cy="17" r="1.2" fill="#334155" />
                                <circle cx="52" cy="20" r="1.2" fill="#334155" />
                            </svg>

                            <!-- Xbox Controller (One & Series X) -->
                            <svg v-else viewBox="0 0 64 42" class="w-14 h-9">
                                <path
                                    d="M 16 3.5 C 20 2 25 2 32 2 C 39 2 44 2 48 3.5 L 45 5.5 C 40 4.5 35 4.5 32 4.5 C 29 4.5 24 4.5 19 5.5 Z"
                                    :fill="props.table.isActive ? '#334155' : '#0f172a'" />
                                <path
                                    d="M 17 3.5 C 11 3.5 6.5 8 5 15 L 2 31 C 0.8 36.5 3.8 40.5 7.5 40.5 C 11 40.5 14.5 35 18 30 C 22 28.8 26.5 28.5 32 28.5 C 37.5 28.5 42 28.8 46 30 C 49.5 35 53 40.5 56.5 40.5 C 60.2 40.5 63.2 36.5 62 31 L 59 15 C 57.5 8 53 3.5 47 3.5 Z"
                                    :fill="props.table.isActive ? '#f8fafc' : '#64748b'"
                                    class="transition-colors duration-500" />
                                <circle cx="32" cy="8.5" r="4.2" :fill="props.table.isActive ? '#1e293b' : '#0f172a'" />
                                <path d="M 29.4 5.2
                                    Q 32.0 8.5, 34.6 5.2
                                    L 35.5 6.1
                                    Q 32.0 8.5, 35.5 10.9
                                    L 34.6 11.8
                                    Q 32.0 8.5, 29.4 11.8
                                    L 28.5 10.9
                                    Q 32.0 8.5, 28.5 6.1 Z" :fill="props.table.isActive ? '#03ff5f' : '#94a3b8'"
                                    :style="props.table.isActive ? 'filter: drop-shadow(0 0 2.5px rgba(74,222,128,0.9))' : ''"
                                    class="transition-all duration-500" />
                                <circle cx="27" cy="14" r="0.8" fill="#334155" />
                                <circle cx="32" cy="15.5" r="0.7" fill="#334155" />
                                <circle cx="37" cy="14" r="0.8" fill="#334155" />
                                <circle cx="19" cy="14.5" r="4.2" :fill="props.table.isActive ? '#0f172a' : '#020617'"
                                    stroke="#475569" stroke-width="0.5" />
                                <circle cx="19" cy="14.5" r="3" :fill="props.table.isActive ? '#1e293b' : '#0f172a'" />
                                <circle cx="25.5" cy="22.5" r="3.8"
                                    :fill="props.table.isActive ? '#0f172a' : '#020617'" />
                                <path d="M 25.5 19.2 V 25.8 M 22.2 22.5 H 28.8" stroke="#334155" stroke-width="1.3"
                                    stroke-linecap="square" />
                                <circle cx="38.5" cy="22.5" r="4.2" :fill="props.table.isActive ? '#0f172a' : '#020617'"
                                    stroke="#475569" stroke-width="0.5" />
                                <circle cx="38.5" cy="22.5" r="3"
                                    :fill="props.table.isActive ? '#1e293b' : '#0f172a'" />
                                <circle cx="47" cy="10.8" r="1.9"
                                    :fill="props.table.isActive ? '#0f172a' : '#1e293b'" />
                                <text x="47" y="11.2" font-size="2" font-weight="bold"
                                    :fill="props.table.isActive ? '#eab308' : '#7d5f04'" text-anchor="middle"
                                    dominant-baseline="middle">Y</text>
                                <circle cx="43.8" cy="14" r="1.9"
                                    :fill="props.table.isActive ? '#0f172a' : '#1e293b'" />
                                <text x="43.8" y="14.4" font-size="2" font-weight="bold"
                                    :fill="props.table.isActive ? '#38bdf8' : '#18536e'" text-anchor="middle"
                                    dominant-baseline="middle">X</text>
                                <circle cx="50.2" cy="14" r="1.9"
                                    :fill="props.table.isActive ? '#0f172a' : '#1e293b'" />
                                <text x="50.2" y="14.4" font-size="2" font-weight="bold"
                                    :fill="props.table.isActive ? '#ef4444' : '#631c1c'" text-anchor="middle"
                                    dominant-baseline="middle">B</text>
                                <circle cx="47" cy="17.2" r="1.9"
                                    :fill="props.table.isActive ? '#0f172a' : '#1e293b'" />
                                <text x="47" y="17.6" font-size="2" font-weight="bold"
                                    :fill="props.table.isActive ? '#22c55e' : '#1c4d2e'" text-anchor="middle"
                                    dominant-baseline="middle">A</text>
                            </svg>
                        </div>
                    </div>

                    <!-- Cable setup -->
                    <div class="absolute h-33 w-10.5 left-0 z-0" :class="isDisplay ? 'top-24' : 'top-1/3'">
                        <div class="absolute rounded-bl-md top-4.75 right-2 w-2.5 border-b-2 border-l-2" :class="table.isActive
                            ? isPlaystation ? 'border-blue-500/80' : isPc ? 'border-purple-500/80' : 'border-green-600/80'
                            : 'border-slate-700', isDisplay ? hideDisplayRate ? 'h-58' : 'h-44' : 'h-26.75'">
                            <div class="bg-slate-600 absolute -bottom-1 -right-1.75 w-2 h-1.5 rounded-l-xs z-5"> </div>
                            <div class="bg-slate-600 absolute -left-1 w-1.5 h-2 rounded-b-xs z-5"
                                :class="isDisplay ? '-top-0.75' : 'top-0'">
                            </div>
                        </div>
                    </div>
                    <!-- KBM Cables -->
                    <div v-if="isPc" class="absolute  w-29.5 h-4 z-10 "
                        :class="isDisplay ? 'bottom-27.5' : 'bottom-37'">
                        <!-- Mouse Wire -->
                        <div class="border-t-1 border-r-1 rounded-tr-lg  h-4 w-18 absolute top-0 right-0"
                            :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'">
                            <div class="border-t-1 border-l-1 rounded-tl-lg absolute -top-0.25 -left-2 w-2 h-5"
                                :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'">
                                <div class="border-b-1 border-r-1 rounded-br-sm absolute top-4.75 -left-1 w-1 h-2"
                                    :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'"></div>
                            </div>
                        </div>
                        <!-- Keyboard Wire -->
                        <div class="border-t-1 border-r-1 rounded-tr-sm  h-1.25 w-7 absolute top-0.5 right-10.5"
                            :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'">
                            <div class="border-t-1 border-l-1 rounded-tl-md absolute -top-0.25 -left-2 w-2 h-5"
                                :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'">
                                <div class="border-b-1 border-r-1 rounded-br-md absolute top-4.75 -left-1.5 w-1.5 h-2"
                                    :class="table.isActive ? 'border-purple-400/80' : 'border-slate-700'"></div>
                            </div>
                        </div>
                    </div>

                    <span v-if="isDisplay && !hideDisplayRate"
                        class="text-xl font-semibold tracking-wider text-slate-200">
                        {{ currentRate }} Rs/min
                    </span>



                    <!-- Buttons -->
                    <div v-if="!isDisplay" class="w-full mt-auto text-center px-6">
                        <button v-if="props.table.isActive"
                            @click="emit('transfer-table', { from_uid: props.table.uid, fromTableNumber: props.table.id, bookingName: props.table.bookingName })"
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2"
                            :class="isPlaystation ? 'bg-blue-400 text-slate-900' : isPc ? 'bg-purple-400 text-slate-900' : 'bg-green-400 text-slate-900'">
                            Transfer
                        </button>
                        <button v-else-if="canResume" @click="resumeSession" :disabled="busy"
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 mb-2 disabled:opacity-50"
                            :class="resumeButtonClasses">
                            Resume
                        </button>

                        <button @click="mainAction" :disabled="busy"
                            class="transform rounded-lg w-full py-2 text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                            :class="props.table.isActive || canResume
                                ? 'bg-rose-500 text-white hover:bg-rose-400'
                                : isPlaystation
                                    ? 'bg-blue-500 text-white hover:bg-blue-400'
                                    : isPc
                                        ? 'bg-purple-600 text-white hover:bg-purple-500'
                                        : 'bg-green-700 text-white hover:bg-green-600'">
                            {{ mainActionLabel }}
                        </button>

                    </div>
                </div>
            </div>

        </div>
    </div>
    <div v-else-if="isFoosball" :class="isDisplay ? 'w-[101px] h-[190px]' : ''">
        <div class="w-[202px] relative  flex-none px-4" :class="isDisplay ? 'scale-50 origin-top-left' : 'mt-12'">

            <div class="flex flex-col items-center w-full relative z-10 group">
                <!-- Rate + remove row (same as PoolTable) -->
                <!-- Station card -->
                <div class="relative w-full h-[380px] rounded-2xl border-2 shadow-xl transition-all duration-500 bg-slate-950 flex flex-col items-center px-3 py-6 overflow-hidden"
                    :class="props.table.isActive
                        ? isDisplay && showBookingStatus
                            ? 'border-red-600'
                            : 'border-lime-400 shadow-2xl shadow-lime-400/40'
                        : 'border-slate-800',
                        isDisplay ? 'gap-4 items-center justify-between' : ''">

                    <!-- Header: type label + station number -->
                    <div v-if="locked"
                        class="absolute h-full w-full top-0 flex items-center justify-center z-100 text-slate-300 bg-slate-950/80 rounded-xl">
                        <span class="-rotate-12 tracking-widest font-black text-lg p-3 border-4 border-slate-600 rounded-xl flex items-center gap-2">🔒 LICENCE</span>
                    </div>
                    <div v-if="(table.isBooked || slotBooked) && !table.isActive && !table.resumable"
                        class="absolute h-full w-full flex items-center justify-center z-100 text-rose-600 bg-slate-900/70 rounded-xl top-0">
                        <span
                            class="-rotate-20 tracking-widest font-black text-2xl p-3 border-4 border-rose-700 rounded-xl">BOOKED</span>
                    </div>
                    <div class="flex flex-col gap-2 w-full items-center">
                        <span class="font-black uppercase tracking-[0.2em] leading-tight transition-colors duration-500"
                            :class="props.table.isActive && !isDisplay ? 'text-lime-300/70' : 'text-slate-500', isDisplay ? 'text-xl' : 'text-[9px]'">
                            Foosball
                        </span>
    
                        <!-- Mini pitch (contained illustration, landscape) -->
                        <div class="w-full mt-2 mb-4 relative">
                            <!-- ambient glow when live -->
                            <div v-if="!isDisplay"
                                class="absolute -inset-2 rounded-xl bg-lime-400/20 blur-lg transition-opacity duration-500 pointer-events-none"
                                :class="props.table.isActive ? 'opacity-100' : 'opacity-0'"></div>
    
                            <div class="relative w-full h-[88px] rounded-lg border-[3px] overflow-hidden transition-all duration-500"
                                :class="props.table.isActive
                                    ? isDisplay && showBookingStatus
                                        ? 'bg-red-600/20 border-red-500/50'
                                        : 'bg-gradient-to-br from-emerald-500 to-emerald-700 border-slate-700'
                                    : 'bg-gradient-to-br from-slate-900 to-slate-950 border-slate-700'">
    
                                <!-- markings -->
                                <div class="absolute inset-y-0 left-1/2 w-px bg-white/15"></div>
                                <div
                                    class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 rounded-full border border-white/15">
                                </div>
                                <!-- goals -->
                                <div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-7 bg-slate-950 rounded-r"></div>
                                <div class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-7 bg-slate-950 rounded-l"></div>
    
                                <!-- four rods, alternating teams -->
                                <div v-for="rod in rods" :key="rod.x" class="absolute inset-y-0" :style="{ left: rod.x }">
                                    <div class="absolute inset-y-0 left-0 w-[2px] -translate-x-1/2 bg-white/15"></div>
                                    <!-- figures -->
                                    <div class="absolute left-0 -translate-x-1/2 flex flex-col justify-around h-full py-2">
                                        <div v-for="n in rod.count" :key="n"
                                            class="w-2.5 h-1.5 rounded-full transition-all duration-500" :class="rod.team === 'red'
                                                ? (props.table.isActive ? 'bg-rose-400' : 'bg-slate-600')
                                                : (props.table.isActive ? 'bg-sky-400' : 'bg-slate-700')">
                                        </div>
                                    </div>
                                </div>
    
                                <!-- ball: mini football (center pentagon + rim patches, ⚽ style) -->
                                <div class="absolute top-[38%] left-[56%] -translate-x-1/2 -translate-y-1/2 transition-all duration-500"
                                    :class="props.table.isActive ? 'opacity-100 animate-pulse' : 'opacity-30'">
                                    <svg viewBox="0 0 20 20" class="w-3 h-3 drop-shadow-[0_0_3px_rgba(255,255,255,0.4)]">
                                        <defs>
                                            <clipPath id="fb-ball-clip">
                                                <circle cx="10" cy="10" r="8.4" />
                                            </clipPath>
                                        </defs>
                                        <!-- body -->
                                        <circle cx="10" cy="10" r="8.6" fill="#f8fafc" stroke="#0f172a"
                                            stroke-width="1.2" />
                                        <!-- center pentagon -->
                                        <polygon points="10,6.6 13.2,8.9 12,12.7 8,12.7 6.8,8.9" fill="#0f172a" />
                                        <!-- rim patches, clipped by the ball's edge -->
                                        <g fill="#0f172a" clip-path="url(#fb-ball-clip)">
                                            <circle cx="15.2" cy="2.9" r="2.6" />
                                            <circle cx="18.4" cy="12.7" r="2.6" />
                                            <circle cx="10" cy="18.8" r="2.6" />
                                            <circle cx="1.6" cy="12.7" r="2.6" />
                                            <circle cx="4.8" cy="2.9" r="2.6" />
                                        </g>
                                    </svg>
                                </div>
                            </div>
    
                            <!-- Handles protruding past the frame (outside the clipped pitch) -->
                            <template v-for="rod in rods" :key="'handle-' + rod.x">
                                <div class="absolute -top-1.5 -translate-x-1/2 w-[5px] h-3 rounded-full bg-slate-600 border border-slate-800 transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-slate-500' : ''" :style="{ left: rod.x }"></div>
                                <div class="absolute -bottom-1.5 -translate-x-1/2 w-[5px] h-3 rounded-full bg-slate-600 border border-slate-800 transition-colors duration-500"
                                    :class="props.table.isActive ? 'bg-slate-500' : ''" :style="{ left: rod.x }"></div>
                            </template>
                        </div>
                        
                    </div>

                    <span class="font-black drop-shadow-md tracking-tight leading-none"
                        :class="isDisplay ? 'text-6xl' : 'text-4xl', hideId ? 'text-transparent' : 'text-white'">
                        {{ table.id }}
                    </span>

                    <span v-if="isDisplay && !hideDisplayRate" class="text-xl font-semibold tracking-wider text-slate-200 mt-4">{{
                        currentRate }} Rs/min</span>

                    <!-- Scoreboard: the clock, and beneath it whoever is playing.
                         This is the card's display surface, so the names belong
                         here rather than under the button where there is no room. -->
                    <div v-if="!isDisplay"
                        class="w-full mt-2.5 rounded-lg bg-slate-900 border border-slate-800 py-1.5 px-1 flex flex-col items-center justify-center">
                        <span class="text-xl font-mono font-bold tracking-wider transition-colors duration-300" :class="props.table.isActive
                            ? 'text-lime-300 drop-shadow-[0_0_6px_rgba(163,230,53,0.5)]'
                            : 'text-slate-700'">
                            {{ formattedTime }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>

import { computed, ref } from 'vue'
import PoolHole from './PoolHole.vue'

const props = defineProps({
    locked: { type: Boolean, default: false },
    table: Object, currentRate: Number,
    loungeName: { type: String, default: '' },
    isDisplay: { type: Boolean, default: false },
    showBookingStatus: { type: Boolean, default: true },
    canManage: Boolean,
    selected: { type: Boolean, default: false },
    slotBooked: { type: Boolean, default: false },
    bookings: Object,
    hideId: { type: Boolean, default: false },
    hideDisplayRate: { type: Boolean, default: false }
})

const holePositions = [
    'top-left',
    'top-right',
    'mid-left',
    'mid-right',
    'bottom-left',
    'bottom-right',
]

const isSnooker = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('snooker'),
)
const isPool = computed(() => props.table.type && props.table.type.toLowerCase().includes('pool'))
const isFoosball = computed(() => props.table.type && props.table.type.toLowerCase() === 'foosball')
const isPrivatePool = computed(
    () => props.table.type && props.table.type.toLowerCase().includes('private'),
)
const isPrivateSnooker = computed(() => props.table.type === 'privateSnooker')

const normalizedType = computed(() => {
    const t = (props.table?.type || '').toLowerCase().trim()
    if (t === 'pc' || t === 'desktop' || t === 'computer' || t === 'rig') return 'pc'
    if (t === 'ps5' || t === 'playstation 5' || t === 'playstation5') return 'ps5'
    if (t === 'ps4' || t === 'playstation 4' || t === 'playstation4') return 'ps4'
    if (t === 'xbox_one' || t === 'xbox-one' || t === 'xbox one' || t === 'xboxone' || t === 'xbox1') return 'xbox_one'
    if (t === 'xbox_series_x' || t === 'xbox-series-x' || t === 'xbox series x' || t === 'xboxseriesx' || t === 'xbox' || t === 'xboxx') return 'xbox_series_x'
    return t
})

const isPc = computed(() => normalizedType.value === 'pc')
const isPs5 = computed(() => normalizedType.value === 'ps5')
const isPs4 = computed(() => normalizedType.value === 'ps4')
const isXboxOne = computed(() => normalizedType.value === 'xbox_one')
const isXboxSeriesX = computed(() => normalizedType.value === 'xbox_series_x')

const isPlaystation = computed(() => isPs4.value || isPs5.value || normalizedType.value.startsWith('ps'))
const isXbox = computed(() => isXboxOne.value || isXboxSeriesX.value || normalizedType.value.startsWith('xbox'))

const headerTitle = computed(() => {
    if (isPc.value) return 'Gaming PC'
    if (isPs5.value) return 'PlayStation 5'
    if (isPs4.value) return 'PlayStation 4'
    if (isXboxSeriesX.value) return 'Xbox Series X'
    if (isXboxOne.value) return 'Xbox One'
    return props.table?.type || 'Console'
})

const tvScreenTypeLabel = computed(() => {
    if (isPc.value) return 'PC'
    if (isXbox.value) return `XBOX ${props.table.type[4] === '1' ? '1' : 'X'}`
    return props.table?.type || 'PS'
})


const tableThemeClasses = computed(() => {
    if (isPrivateSnooker.value) {
        return props.table.isActive
            ? 'border-amber-500/90 bg-emerald-700 shadow-2xl '
            : 'border-amber-950 bg-emerald-900'
    }

    if (isSnooker.value)
        return props.table.isActive
            ? 'border-pool-wood-500 bg-emerald-700 shadow-2xl '
            : 'border-pool-wood-900 bg-emerald-900'

    if (isPrivatePool.value)
        return props.table.isActive
            ? 'border-amber-500/90 bg-sky-600 shadow-2xl '
            : 'border-amber-950 bg-sky-800'

    if (isPool.value)
        return props.table.isActive
            ? 'border-pool-wood-500  bg-sky-600 shadow-2xl'
            : 'border-pool-wood-900 bg-sky-800'

    return props.table.isActive
        ? 'border-purple-400 bg-sky-600 shadow-2xl shadow-purple-500/40'
        : 'border-purple-900 bg-sky-600'
})
const canopyGlowColorClass = computed(() =>
    isPrivateSnooker.value
        ? 'bg-amber-200 shadow-amber-300'
        : isSnooker.value
            ? 'bg-amber-100 shadow-sky-100'
            : isPrivatePool.value
                ? 'bg-amber-200 shadow-amber-300'
                : 'bg-amber-100 shadow-sky-100',
)

const canopyBeamColorClass = computed(() =>
    isPrivateSnooker.value
        ? 'bg-gradient-to-b from-amber-200/50 to-transparent'
        : isSnooker.value
            ? 'bg-gradient-to-b from-amber-100/50 to-transparent'
            : isPrivatePool.value
                ? 'bg-gradient-to-b from-amber-200/50 to-transparent'
                : 'bg-gradient-to-b from-amber-100/50 to-transparent',
)

const labelColorClass = computed(() =>
    isSnooker.value
        ? 'text-emerald-200/60'
        : 'text-sky-200/60',
)
const rods = [
    { x: '18%', count: 2, team: 'red' },
    { x: '39%', count: 3, team: 'blue' },
    { x: '61%', count: 3, team: 'red' },
    { x: '82%', count: 2, team: 'blue' },
]
</script>