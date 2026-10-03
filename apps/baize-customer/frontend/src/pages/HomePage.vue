<template>
    <div
        class="relative min-h-screen overflow-clip bg-slate-900 text-white selection:bg-emerald-500/30 selection:text-emerald-300">

        <StickyHeader />
        <div class="relative mx-auto flex min-h-screen flex-col p-4 sm:p-6 lg:p-8">

            <!-- Header -->
            <header class="grid grid-cols-2 items-center justify-between gap-4 pb-6 sm:grid-cols-[12rem_1fr_12rem]">
                <div class="order-2 sm:order-1">
                    <div class="flex items-center gap-2">
                        <span class="relative flex h-2 w-2">
                            <span
                                class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                            <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                        </span>
                        <p class="text-[10px] font-black uppercase tracking-widest text-emerald-500">Signed in</p>
                    </div>
                    <h1 class="truncate text-xl font-black tracking-tight text-slate-100">{{ fullName }}</h1>
                </div>

                <div
                    class=" order-1 col-span-2 hidden sm:flex flex-1 flex-col items-center justify-center gap-2 bg-gradient-to-r from-transparent via-slate-800/80 to-transparent  backdrop-blur-md sm:order-2 sm:col-span-1">
                    <div
                        class="h-[1px] w-full rounded-full bg-gradient-to-r from-transparent via-slate-700 to-transparent">
                    </div>
                    <div class="flex items-center gap-3">
                        <img src="/baize_logo_text.png" class="h-8 py-1 object-contain" alt="Baize Logo" />
                    </div>
                    <div
                        class="h-[1px] w-full rounded-full bg-gradient-to-r from-transparent via-slate-700 to-transparent">
                    </div>
                </div>

                <div class="order-3 flex items-center justify-end gap-2">

                    <button @click="signOut()"
                        class="cursor-pointer rounded-xl border border-slate-800 bg-slate-900/40 px-3.5 py-2 text-[10px] font-black uppercase tracking-widest text-slate-400 transition-all hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-300">
                        Sign Out
                    </button>
                </div>
            </header>

            <!-- View Switcher Tabs (Mobile & Quick Toggle) -->
             <div class="fixed sm:relative bottom-0 left-0 z-40 w-full sm:w-auto">
                 <nav class="sm:mb-4 bg-slate-800/50 backdrop-blur-sm rounded-4xl border border-slate-700 bottom-0 left-0 z-40 sm:relative grid grid-cols-4 sm:grid-cols-1 p-4 sm:flex gap-4 sm:border-b sm:border-slate-800/80 m-6 sm:m-0">
                     <div class="bg-slate-900 rounded-2xl">
                         <button @click="setTab('dashboard')"
                             :class="activeTab === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                             class="flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer h-full w-full">
                             <svg class="h-5 w-5" fill="currentColor" viewBox="0 -32 576 576" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M570.69,236.27,512,184.44V48a16,16,0,0,0-16-16H432a16,16,0,0,0-16,16V99.67L314.78,10.3C308.5,4.61,296.53,0,288,0s-20.46,4.61-26.74,10.3l-256,226A18.27,18.27,0,0,0,0,248.2a18.64,18.64,0,0,0,4.09,10.71L25.5,282.7a21.14,21.14,0,0,0,12,5.3,21.67,21.67,0,0,0,10.69-4.11l15.9-14V480a32,32,0,0,0,32,32H480a32,32,0,0,0,32-32V269.88l15.91,14A21.94,21.94,0,0,0,538.63,288a20.89,20.89,0,0,0,11.87-5.31l21.41-23.81A21.64,21.64,0,0,0,576,248.19,21,21,0,0,0,570.69,236.27ZM288,176a64,64,0,1,1-64,64A64,64,0,0,1,288,176ZM400,448H176a16,16,0,0,1-16-16,96,96,0,0,1,96-96h64a96,96,0,0,1,96,96A16,16,0,0,1,400,448Z"></path></g></svg>
                             <span class="hidden sm:inline">
                                 Dashboard
                             </span>
                         </button>
                     </div>
                     <div class="bg-slate-900 rounded-2xl">
                         <button @click="setTab('clubs')"
                             :class="activeTab === 'clubs' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                             class="h-full w-full flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                             <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" d="M12,2 C17.5228475,2 22,6.4771525 22,12 C22,17.5228475 17.5228475,22 12,22 C6.4771525,22 2,17.5228475 2,12 C2,6.4771525 6.4771525,2 12,2 Z M17.9842695,7.39078625 C18.1985588,6.64477525 17.4973604,5.9435768 16.7513494,6.1578661 L16.6494246,6.19284365 L9.57835679,9.02127078 L9.47282273,9.07079854 C9.30957453,9.15937167 9.17428758,9.29167162 9.08209683,9.45256344 L9.02127078,9.57835679 L6.19284365,16.6494246 L6.1578661,16.7513494 C5.9435768,17.4973604 6.64477525,18.1985588 7.39078625,17.9842695 L7.49271102,17.949292 L14.5637788,15.1208648 L14.6693129,15.0713371 C14.8325611,14.982764 14.967848,14.850464 15.0600388,14.6895722 L15.1208648,14.5637788 L17.949292,7.49271102 L17.9842695,7.39078625 Z M12,10 C13.1045695,10 14,10.8954305 14,12 C14,13.1045695 13.1045695,14 12,14 C10.8954305,14 10,13.1045695 10,12 C10,10.8954305 10.8954305,10 12,10 Z"></path> </g></svg>
                             <span class="hidden sm:inline">
                                 Explore Clubs
                             </span>
                         </button>
                     </div>
                     <div class="bg-slate-900 rounded-2xl">
                         <button @click="setTab('friends')"
                             :class="activeTab === 'friends' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                             class="h-full w-full flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                             <svg class="h-5 w-5" fill="currentColor" viewBox="0 -64 640 640" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M192 256c61.9 0 112-50.1 112-112S253.9 32 192 32 80 82.1 80 144s50.1 112 112 112zm76.8 32h-8.3c-20.8 10-43.9 16-68.5 16s-47.6-6-68.5-16h-8.3C51.6 288 0 339.6 0 403.2V432c0 26.5 21.5 48 48 48h288c26.5 0 48-21.5 48-48v-28.8c0-63.6-51.6-115.2-115.2-115.2zM480 256c53 0 96-43 96-96s-43-96-96-96-96 43-96 96 43 96 96 96zm48 32h-3.8c-13.9 4.8-28.6 8-44.2 8s-30.3-3.2-44.2-8H432c-20.4 0-39.2 5.9-55.7 15.4 24.4 26.3 39.7 61.2 39.7 99.8v38.4c0 2.2-.5 4.3-.6 6.4H592c26.5 0 48-21.5 48-48 0-61.9-50.1-112-112-112z"></path></g></svg>
                             <span class="hidden sm:inline">
                                 Friends
                             </span>
                         </button>
                     </div>
                     <div class="bg-slate-900 rounded-2xl">
                         <button @click="setTab('settings')"
                             :class="activeTab === 'settings' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                             class="h-full w-full flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                             <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M14.2788 2.15224C13.9085 2 13.439 2 12.5 2C11.561 2 11.0915 2 10.7212 2.15224C10.2274 2.35523 9.83509 2.74458 9.63056 3.23463C9.53719 3.45834 9.50065 3.7185 9.48635 4.09799C9.46534 4.65568 9.17716 5.17189 8.69017 5.45093C8.20318 5.72996 7.60864 5.71954 7.11149 5.45876C6.77318 5.2813 6.52789 5.18262 6.28599 5.15102C5.75609 5.08178 5.22018 5.22429 4.79616 5.5472C4.47814 5.78938 4.24339 6.1929 3.7739 6.99993C3.30441 7.80697 3.06967 8.21048 3.01735 8.60491C2.94758 9.1308 3.09118 9.66266 3.41655 10.0835C3.56506 10.2756 3.77377 10.437 4.0977 10.639C4.57391 10.936 4.88032 11.4419 4.88029 12C4.88026 12.5581 4.57386 13.0639 4.0977 13.3608C3.77372 13.5629 3.56497 13.7244 3.41645 13.9165C3.09108 14.3373 2.94749 14.8691 3.01725 15.395C3.06957 15.7894 3.30432 16.193 3.7738 17C4.24329 17.807 4.47804 18.2106 4.79606 18.4527C5.22008 18.7756 5.75599 18.9181 6.28589 18.8489C6.52778 18.8173 6.77305 18.7186 7.11133 18.5412C7.60852 18.2804 8.2031 18.27 8.69012 18.549C9.17714 18.8281 9.46533 19.3443 9.48635 19.9021C9.50065 20.2815 9.53719 20.5417 9.63056 20.7654C9.83509 21.2554 10.2274 21.6448 10.7212 21.8478C11.0915 22 11.561 22 12.5 22C13.439 22 13.9085 22 14.2788 21.8478C14.7726 21.6448 15.1649 21.2554 15.3694 20.7654C15.4628 20.5417 15.4994 20.2815 15.5137 19.902C15.5347 19.3443 15.8228 18.8281 16.3098 18.549C16.7968 18.2699 17.3914 18.2804 17.8886 18.5412C18.2269 18.7186 18.4721 18.8172 18.714 18.8488C19.2439 18.9181 19.7798 18.7756 20.2038 18.4527C20.5219 18.2105 20.7566 17.807 21.2261 16.9999C21.6956 16.1929 21.9303 15.7894 21.9827 15.395C22.0524 14.8691 21.9088 14.3372 21.5835 13.9164C21.4349 13.7243 21.2262 13.5628 20.9022 13.3608C20.4261 13.0639 20.1197 12.558 20.1197 11.9999C20.1197 11.4418 20.4261 10.9361 20.9022 10.6392C21.2263 10.4371 21.435 10.2757 21.5836 10.0835C21.9089 9.66273 22.0525 9.13087 21.9828 8.60497C21.9304 8.21055 21.6957 7.80703 21.2262 7C20.7567 6.19297 20.522 5.78945 20.2039 5.54727C19.7799 5.22436 19.244 5.08185 18.7141 5.15109C18.4722 5.18269 18.2269 5.28136 17.8887 5.4588C17.3915 5.71959 16.7969 5.73002 16.3099 5.45096C15.8229 5.17191 15.5347 4.65566 15.5136 4.09794C15.4993 3.71848 15.4628 3.45833 15.3694 3.23463C15.1649 2.74458 14.7726 2.35523 14.2788 2.15224ZM12.5 15C14.1695 15 15.5228 13.6569 15.5228 12C15.5228 10.3431 14.1695 9 12.5 9C10.8305 9 9.47716 10.3431 9.47716 12C9.47716 13.6569 10.8305 15 12.5 15Z" fill="currentColor"></path> </g></svg>
                             <span class="hidden sm:inline">
                                 Settings
                             </span>
                         </button>
                     </div>
                 </nav>
             </div>

            <!-- TAB 1: MAIN DASHBOARD VIEW -->
            <main v-if="activeTab === 'dashboard'" class="flex-1 space-y-4">
                <!-- Summary strip -->
                <section class="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-4">
                    <div v-for="stat in stats" :key="stat.label"
                        class="group relative overflow-hidden rounded-2xl border border-slate-700 bg-slate-800 shadow-[] p-4 backdrop-blur-xl transition-all duration-300 hover:border-slate-700/80 hover:bg-slate-700/80">
                        <span
                            class="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-current to-transparent opacity-70 transition-opacity group-hover:opacity-100"
                            :class="stat.accent" />
                        <p class="text-[9px] font-black uppercase tracking-widest text-slate-400">{{ stat.label }}</p>
                        <p class="mt-1.5 truncate text-2xl font-black leading-none tracking-tight"
                            :class="stat.color ? '' : stat.tone" :style="stat.color ? { color: stat.color } : null">
                            {{ stat.value }}
                        </p>
                        <p class="mt-1.5 text-[10px] text-slate-500 font-medium">{{ stat.hint }}</p>
                    </div>
                </section>

                <!-- Bookings & Games Grid -->
                <div class="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-5">

                    <!-- Bookings -->
                    <section
                        class="flex h-[28rem] min-h-0 flex-col rounded-3xl border border-slate-700/80 bg-slate-800 p-6 backdrop-blur-xl sm:h-[30rem] lg:col-span-2 lg:h-[34rem]">
                        <div class="flex shrink-0 items-baseline justify-between">
                            <div>
                                <h2 class="text-lg font-black tracking-tight text-slate-100">Your Bookings</h2>
                                <p class="mt-0.5 text-[10px] text-slate-400">Upcoming reservations</p>
                            </div>
                            <span v-if="upcoming.length"
                                class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-emerald-400 shadow-sm">
                                {{ activeCount ? `${activeCount} playing` : `${upcoming.length} booked` }}
                            </span>
                        </div>

                        <div
                            class="mt-5 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1 [scrollbar-color:theme(colors.slate.700)_transparent] [scrollbar-width:thin] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-700/70 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">
                            <div v-if="loading"
                                class="py-12 text-center text-[11px] font-bold text-slate-500 animate-pulse">
                                Loading bookings…
                            </div>

                            <div v-else-if="!upcoming.length"
                                class="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-600/80 py-10 text-center">
                                <p class="text-[11px] font-bold text-slate-400">Nothing booked yet</p>
                                <p class="mx-auto mt-1 max-w-[15rem] text-[10px] leading-relaxed text-slate-500">
                                    Reserve a table and it'll appear here.
                                </p>
                            </div>

                            <BookingItem v-else v-for="booking in upcoming" :key="booking.id" class="w-full"
                                :for-customer="true" :booking="booking" @cancel="cancelBookingAction(booking.id)" />
                        </div>

                        <button @click="setTab('clubs')"
                            class="mt-5 flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-3.5 text-[10px] font-black uppercase tracking-widest text-white shadow-lg shadow-emerald-950/50 transition-all hover:bg-emerald-500 active:scale-[0.99] cursor-pointer">
                            Book a Table
                            <span class="text-sm leading-none">&rsaquo;</span>
                        </button>
                    </section>

                    <!-- Games -->
                    <section
                        class="flex h-[28rem] min-h-0 flex-col rounded-3xl border border-slate-700/80 bg-slate-800 p-6 backdrop-blur-xl sm:h-[30rem] lg:h-[34rem]"
                        :class="khata.outstanding ? 'lg:col-span-2' : 'lg:col-span-3'">
                        <div class="flex shrink-0 items-baseline justify-between">
                            <div>
                                <h2 class="text-lg font-black tracking-tight text-slate-100">My Games</h2>
                                <p class="mt-0.5 text-[10px] text-slate-400">Your recent sessions</p>
                            </div>
                            <span v-if="summary.gamesPlayed"
                                class="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-sky-400">
                                {{ summary.gamesPlayed }} played
                            </span>
                        </div>

                        <div v-if="gamesLoading"
                            class="mt-5 flex min-h-0 flex-1 items-center justify-center text-[11px] font-bold text-slate-500 animate-pulse">
                            Loading sessions…
                        </div>

                        <div v-else-if="!games.length" class="mt-5 flex min-h-0 flex-1 items-center justify-center">
                            <div
                                class="w-full h-full flex flex-col justify-center items-center rounded-2xl border border-dashed border-slate-600/80 px-6 py-10 text-center">
                                <p class="text-[11px] font-bold text-slate-400">No games yet</p>
                                <p class="mx-auto mt-1 max-w-[17rem] text-[10px] leading-relaxed text-slate-500">
                                    Sessions played on a booked table will show up here once finished and billed.
                                </p>
                            </div>
                        </div>

                        <ul v-else
                            class="mt-5 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1 [scrollbar-color:theme(colors.slate.700)_transparent] [scrollbar-width:thin] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-700/70 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">
                            <li v-for="game in games" :key="game.id">
                                <LoggedGame :game="game" :khata="khata" :duration-label="durationLabel" @open-receipt="openReceipt(game)"/>
                            </li>
                        </ul>
                    </section>

                    <!-- Khata Section -->
                    <section v-if="khata.outstanding"
                        class="flex flex-col justify-between rounded-3xl border border-amber-600/40 bg-amber-500/5 p-5 backdrop-blur-xl lg:col-span-1">
                        <div>
                            <div class="flex items-start justify-between">
                                <div>
                                    <h2 class="text-[10px] font-black uppercase tracking-widest text-amber-500">Your
                                        Khata</h2>
                                    <p class="mt-1 font-mono text-3xl font-black tracking-tight text-amber-400">
                                        Rs {{ khata.outstanding }}
                                    </p>
                                    <p class="mt-1 text-[10px] font-medium text-slate-400">
                                        {{ khata.bills.length }} unpaid bill{{ khata.bills.length === 1 ? '' : 's' }} ·
                                        settle at counter
                                    </p>
                                </div>
                            </div>

                            <!-- Consolidated QR Code -->
                            <div v-if="khata.payUrl"
                                class="mt-4 flex flex-col items-center justify-center rounded-2xl border border-amber-500/20 bg-amber-950/20 p-3 text-center">
                                <svg :viewBox="qrViewBox(khata.payUrl)" class="w-32 rounded-xl bg-white p-2 shadow-md"
                                    shape-rendering="crispEdges" role="img" aria-label="Scan to pay everything owed">
                                    <path :d="qrPath(khata.payUrl)" fill="#0f172a" />
                                </svg>
                                <p class="mt-2 text-[9px] font-black uppercase tracking-wider text-amber-400">
                                    Scan to pay all Rs {{ khata.outstanding }}
                                </p>
                                <p class="mt-1 text-[9px] leading-tight text-slate-400">
                                    Clears all bills at once.
                                </p>
                            </div>

                            <ul class="mt-4 space-y-2 border-t border-amber-600/20 pt-3">
                                <li v-for="bill in khata.bills" :key="`${bill.kind}-${bill.id}`"
                                    class="rounded-xl border border-slate-800/80 bg-slate-950/50 p-2.5">
                                    <div class="flex items-center justify-between gap-2 font-mono text-[11px]">
                                        <span class="flex min-w-0 items-center gap-1.5">
                                            <span
                                                class="shrink-0 rounded px-1.5 py-0.5 text-[8px] font-black uppercase tracking-widest"
                                                :class="bill.kind === 'canteen' ? 'bg-amber-500/15 text-amber-400' : 'bg-sky-500/15 text-sky-400'">
                                                {{ bill.kind === 'canteen' ? 'Canteen' : 'Table' }}
                                            </span>
                                            <span class="truncate text-slate-300">{{ bill.label }}</span>
                                        </span>

                                        <div class="flex shrink-0 items-center gap-2">
                                            <span class="font-bold text-slate-200">Rs {{ bill.total }}</span>
                                            <button v-if="bill.payUrl" @click="toggleBill(bill)"
                                                class="cursor-pointer rounded-lg border px-2 py-1 text-[8px] font-black uppercase tracking-widest transition-all"
                                                :class="openBill === billKey(bill) ? 'border-emerald-500/50 bg-emerald-500/20 text-emerald-300' : 'border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'">
                                                Pay
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Individual Bill QR -->
                                    <div v-if="openBill === billKey(bill)"
                                        class="mt-2.5 flex items-center gap-3 border-t border-slate-800/80 pt-2.5">
                                        <svg :viewBox="qrViewBox(bill.payUrl)"
                                            class="h-20 w-20 shrink-0 rounded-lg bg-white p-1"
                                            shape-rendering="crispEdges" role="img" aria-label="Scan to pay this bill">
                                            <path :d="qrPath(bill.payUrl)" fill="#0f172a" />
                                        </svg>
                                        <p class="text-[9px] leading-relaxed text-slate-400">
                                            Pays <span class="font-bold text-slate-200">Rs {{ bill.total }}</span> for
                                            this {{ bill.kind === 'canteen' ? 'order' : 'table' }} only.
                                        </p>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </section>
                </div>

                <!-- Account -->
                <section class="mt-4 rounded-3xl border border-slate-700/80 bg-slate-800 p-5 backdrop-blur-xl">
                    <h2 class="mb-3 text-[9px] font-black uppercase tracking-widest text-slate-500">Account</h2>
                    <dl class="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                        <div
                            class="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">
                            <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Name</dt>
                            <dd class="truncate pl-3 text-xs font-bold text-slate-200">{{ fullName }}</dd>
                        </div>
                        <div
                            class="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">
                            <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Phone</dt>
                            <dd class="font-mono text-xs font-bold text-slate-200">{{ displayPhone }}</dd>
                        </div>
                        <div
                            class="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">
                            <dt class="text-[10px] font-black uppercase tracking-widest text-slate-500">Email</dt>
                            <dd class="truncate pl-3 text-xs font-bold text-slate-200">{{ customer.profile?.email || '—'
                            }}</dd>
                        </div>
                    </dl>
                </section>
            </main>

            <!-- TAB 2: EXPLORE CLUBS & SEARCH VIEW -->
            <main v-else-if="activeTab === 'clubs'" class="flex-1 space-y-6">
                <!-- Search Header Banner -->
                <section class="rounded-3xl border border-slate-700 bg-slate-800 p-6 backdrop-blur-xl">
                    <div class="max-w-2xl">
                        <h2 class="text-2xl font-black tracking-tight text-white">Find a Baize Arena</h2>
                        <p class="mt-1 text-xs text-slate-400">Discover nearby cue sports arenas, view available tables,
                            and book instant sessions.</p>
                    </div>

                    <!-- Search Input -->
                    <div class="relative mt-5 max-w-xl">
                        <input v-model="clubSearchQuery" type="text" placeholder="Search by club name, area, or city..."
                            class="w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 py-3.5 pl-11 pr-4 text-xs font-semibold text-white placeholder-slate-500 shadow-inner focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
                        <svg class="absolute left-4 top-3.5 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </section>

                <!-- Search Results or Nearby Clubs -->
                <section>
                    <div class="mb-3 flex items-center justify-between">
                        <h3 class="text-[10px] font-black uppercase tracking-widest text-slate-400">
                            {{ clubSearchQuery ? `Search Results (${allClubs.length})` : 'Clubs Directory' }}
                        </h3>
                    </div>

                    <div v-if="clubsLoading" class="py-12 text-center text-xs font-bold text-slate-500 animate-pulse">
                        Searching arena directory…
                    </div>

                    <div v-else-if="!allClubs.length"
                        class="rounded-2xl border border-dashed border-slate-800 py-12 text-center">
                        <p class="text-xs font-bold text-slate-400">No clubs found</p>
                        <p class="mt-1 text-[10px] text-slate-500">Try searching for another area, city, or club name.
                        </p>
                    </div>

                    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <ClubCard v-for="club in allClubs" :key="club.id" :club="club"
                            @select-club="selectClub(club)" @toggle-favourite="toggleFavourite(club)" />
                    </div>
                </section>
            </main>
            <!-- TAB 3: FRIENDS & EXPLORE VIEW -->
            <main v-else-if="activeTab === 'friends'" class="flex-1 space-y-6">
                <!-- Search & Find Friends Banner -->
                <section class="rounded-3xl border border-slate-700 bg-slate-800 p-6 backdrop-blur-xl">
                    <div class="max-w-2xl">
                        <h2 class="text-2xl font-black tracking-tight text-white">Find & Connect Friends</h2>
                        <p class="mt-1 text-xs text-slate-400">Search for players by username or phone number, see who
                            is active, and invite them to your next session.</p>
                    </div>

                    <!-- Search Bar -->
                    <div class="relative mt-5 max-w-xl">
                        <input v-model="friendSearchQuery" type="text" placeholder="Search friends by name or phone..."
                            class="w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 py-3.5 pl-11 pr-4 text-xs font-semibold text-white placeholder-slate-500 shadow-inner focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
                        <svg class="absolute left-4 top-3.5 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </section>

                <!-- Incoming friend requests -->
                <section v-if="incomingRequests.length"
                    class="rounded-3xl border border-emerald-500/20 bg-emerald-500/[0.04] p-5">
                    <h3 class="mb-3 text-[10px] font-black uppercase tracking-widest text-emerald-400">
                        Friend requests ({{ incomingRequests.length }})
                    </h3>
                    <div class="space-y-2">
                        <div v-for="req in incomingRequests" :key="req.requestId"
                            class="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/40 p-3">
                            <div class="flex min-w-0 items-center gap-3">
                                <div
                                    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-[11px] font-black text-emerald-400">
                                    {{ req.from.name.charAt(0) }}
                                </div>
                                <div class="min-w-0">
                                    <p class="truncate text-xs font-bold text-slate-100">{{ req.from.name }}</p>
                                    <p class="font-mono text-[10px] text-slate-400">{{ req.from.phone }}</p>
                                </div>
                            </div>
                            <div class="flex shrink-0 gap-1.5">
                                <button @click="acceptRequest(req)"
                                    class="cursor-pointer rounded-xl border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-emerald-300 hover:bg-emerald-500 hover:text-white">
                                    Accept
                                </button>
                                <button @click="declineRequest(req)"
                                    class="cursor-pointer rounded-xl border border-slate-700 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-400 hover:border-rose-500/40 hover:text-rose-300">
                                    Decline
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    <!-- Main Friends Directory / Search Results -->
                    <section class="lg:col-span-2 space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="text-[10px] font-black uppercase tracking-widest text-slate-400">
                                {{ friendSearchQuery ? `Search Results (${filteredFriends.length})`
                                    : 'Your Friends List' }}
                            </h3>
                        </div>

                        <div v-if="friendsLoading"
                            class="py-12 text-center text-xs font-bold text-slate-500 animate-pulse">
                            Searching players…
                        </div>

                        <div v-else-if="!filteredFriends.length"
                            class="rounded-3xl border border-dashed border-slate-800 bg-slate-900/20 py-12 text-center">
                            <p class="text-xs font-bold text-slate-400">No friends found</p>
                            <p class="mt-1 text-[10px] text-slate-500">Try searching for another name or phone number.
                            </p>
                        </div>

                        <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <div v-for="friend in filteredFriends" :key="friend.id"
                                class="group flex items-center justify-between rounded-2xl border border-slate-700 bg-slate-800 p-4 backdrop-blur-xl transition-all hover:border-slate-700 hover:bg-slate-800/80">
                                <div class="flex items-center gap-3">
                                    <div
                                        class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-700 bg-slate-900 font-black text-emerald-400">
                                        {{ friend.name.charAt(0) }}
                                        <span :class="friend.isOnline ? 'bg-emerald-500' : 'bg-slate-600'"
                                            class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-slate-950"></span>
                                    </div>
                                    <div class="min-w-0">
                                        <p class="truncate text-xs font-bold text-slate-100">{{ friend.name }}</p>
                                        <p class="font-mono text-[10px] text-slate-400">{{ friend.phone }}</p>
                                    </div>
                                </div>

                                <div class="flex shrink-0 items-center gap-1.5">
                                    <template v-if="friend.status === 'friend'">
                                        <button @click="inviteFriend(friend)"
                                            class="cursor-pointer rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-emerald-400 transition-all hover:bg-emerald-500 hover:text-white">
                                            Invite
                                        </button>
                                        <button @click="removeFriend(friend)" title="Remove friend"
                                            class="cursor-pointer rounded-xl border border-slate-700 px-2 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-500 hover:border-rose-500/40 hover:text-rose-300">
                                            ✕
                                        </button>
                                    </template>
                                    <button v-else-if="friend.status === 'pending_out'" disabled
                                        class="cursor-not-allowed rounded-xl border border-slate-700 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-500">
                                        Requested
                                    </button>
                                    <button v-else-if="friend.status === 'pending_in'" @click="sendRequest(friend)"
                                        class="cursor-pointer rounded-xl border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-emerald-300 hover:bg-emerald-500 hover:text-white">
                                        Accept
                                    </button>
                                    <button v-else @click="sendRequest(friend)"
                                        class="cursor-pointer rounded-xl border border-slate-700 px-3 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-300 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-400">
                                        + Add
                                    </button>
                                </div>
                            </div>
                        </div>
                    </section>

                    <!-- Explore / Suggested Friends Panel -->
                    <section
                        class="rounded-3xl border border-slate-700/80 bg-slate-800 p-6 backdrop-blur-xl h-fit space-y-4">
                        <div>
                            <h3 class="text-xs font-black uppercase tracking-widest text-slate-300">Suggested Players
                            </h3>
                            <p class="mt-0.5 text-[10px] text-slate-400">Players recently active in your arena</p>
                        </div>

                        <div class="space-y-3">
                            <div v-for="suggested in suggestedFriends" :key="suggested.id"
                                class="flex items-center justify-between rounded-2xl border border-slate-800/80 bg-slate-950/40 p-3">
                                <div class="flex items-center gap-2.5 min-w-0">
                                    <div
                                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-[11px] font-black text-slate-300">
                                        {{ suggested.name.charAt(0) }}
                                    </div>
                                    <div class="min-w-0">
                                        <p class="truncate text-[11px] font-bold text-slate-200">{{ suggested.name }}
                                        </p>
                                        <p class="text-[9px] text-slate-500">{{ suggested.mutuals }} mutual friends</p>
                                    </div>
                                </div>
                                <button @click="addFriend(suggested)"
                                    class="cursor-pointer rounded-lg border border-slate-700 px-2.5 py-1 text-[8px] font-black uppercase tracking-widest text-slate-300 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-400">
                                    + Add
                                </button>
                            </div>
                        </div>
                    </section>
                </div>
            </main>

            <!-- Footer -->
            <PoweredByZain :forCustomer="true" class="mb-25 sm:mb-0" />

        </div>

        <!-- Receipt Overlay -->
        <div v-if="receiptOpen" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4"
            :class="receipt ? '' : 'bg-slate-950/80 backdrop-blur-sm'" @click.self="closeReceipt">
            <div v-if="receiptLoading"
                class="rounded-2xl border border-slate-800 bg-slate-900 px-6 py-4 text-[11px] font-bold text-slate-400 shadow-2xl">
                Loading bill…
            </div>

            <div v-else-if="receiptError"
                class="max-w-xs rounded-2xl border border-rose-500/30 bg-slate-900 px-6 py-5 text-center shadow-2xl">
                <p class="text-[11px] font-bold text-rose-400">{{ receiptError }}</p>
                <button @click="closeReceipt"
                    class="mt-4 cursor-pointer rounded-xl bg-slate-800 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-300 hover:bg-slate-700">
                    Close
                </button>
            </div>

            <BillingReceipt v-else-if="receipt" :receipt="receipt" :branding="receipt.branding"
                :api-url="receipt.logoBase" :read-only="true" @close="closeReceipt" />
        </div>
    </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { typeLabel, typeColor, formatPhoneDisplay, qrMatrix, qrSvgPath, BookingItem, PoweredByZain, BillingReceipt, useAutoRefresh } from '@baize/ui'
import { customer, signOut, apiGet, apiPost, apiDelete } from '../auth.js'
import { fetchClubs, cancelBooking } from '../api.js'
import ClubCard from '@/components/ClubCard.vue'
import LoggedGame from '@/components/LoggedGame.vue'
import { usePageBackground } from '@baize/ui'
import StickyHeader from '@/components/StickyHeader.vue'

usePageBackground('#0f172a')

const router = useRouter()
const route = useRoute()
// tab is derived from the URL so /dashboard, /clubs, /friends are real routes
const setTab = (t) => { if (route.path !== '/' + t) router.push('/' + t) }

// Navigation tab state
const activeTab = computed(() => route.path === '/clubs' ? 'clubs' : route.path === '/friends' ? 'friends' : 'dashboard')

// Customer Profile computed
const fullName = computed(() => (customer.profile?.name || 'Guest').trim())
const displayPhone = computed(() => formatPhoneDisplay(customer.profile?.phone || ''))

// Bookings
const bookings = ref([])
const loading = ref(true)

const upcoming = computed(() =>
    [...bookings.value]
        .filter((b) => b.status === 'active' || new Date(b.endTime) > new Date())
        .sort((a, b) => {
            if (a.status !== b.status) return a.status === 'active' ? -1 : 1
            return new Date(a.startTime) - new Date(b.startTime)
        })
)

const activeCount = computed(() => upcoming.value.filter((b) => b.status === 'active').length)

// Khata & QR
const khata = ref({ outstanding: 0, bills: [], payUrl: null })
const QR_QUIET = 4
const matrices = new Map()

function matrixFor(url) {
    if (!matrices.has(url)) matrices.set(url, qrMatrix(url, { ecLevel: 'M' }))
    return matrices.get(url)
}

const qrPath = (url) => qrSvgPath(matrixFor(url))
const qrViewBox = (url) => {
    const span = matrixFor(url).length + QR_QUIET * 2
    return `${-QR_QUIET} ${-QR_QUIET} ${span} ${span}`
}

const openBill = ref(null)
const billKey = (bill) => `${bill.kind}-${bill.id}`
const toggleBill = (bill) => {
    openBill.value = openBill.value === billKey(bill) ? null : billKey(bill)
}

// Games history
const games = ref([])
const gamesLoading = ref(true)
const summary = ref({ gamesPlayed: 0, minutesPlayed: 0, favourite: null })

function durationLabel(minutes) {
    const total = Number(minutes) || 0
    const h = Math.floor(total / 60)
    const m = total % 60
    if (!h) return `${m}m`
    return m ? `${h}h ${m}m` : `${h}h`
}

// Stats computed bar
const totalPlayed = computed(() => durationLabel(summary.value.minutesPlayed))

const favourite = computed(() => {
    const fav = summary.value.favourite
    if (!fav) return { label: '—', hint: 'no games yet', color: null }
    return {
        label: typeLabel(fav.type),
        hint: `${fav.plays} ${fav.plays === 1 ? 'session' : 'sessions'}`,
        color: typeColor(fav.type),
    }
})

const topClub = computed(() => {
    const t = summary.value.topClub
    if (!t) return { label: '—', hint: 'no games yet' }
    return { label: t.name, hint: `${t.plays} ${t.plays === 1 ? 'session' : 'sessions'}` }
})

const stats = computed(() => [
    // {
    //     label: 'Upcoming',
    //     value: upcoming.value.length,
    //     hint: upcoming.value.length === 1 ? 'reservation' : 'reservations',
    //     tone: 'text-emerald-400',
    //     accent: 'via-emerald-500/60',
    // },
    {
        label: 'Games Played',
        value: summary.value.gamesPlayed,
        hint: summary.value.gamesPlayed === 1 ? 'session so far' : 'sessions so far',
        tone: 'text-sky-400',
        accent: 'via-sky-500/60',
    },
    // {
    //     label: 'Time Played',
    //     value: totalPlayed.value,
    //     hint: 'across all stations',
    //     tone: 'text-violet-400',
    //     accent: 'via-violet-500/60',
    // },
    {
        label: 'Favourite Game',
        value: favourite.value.label,
        hint: favourite.value.hint,
        tone: 'text-amber-400',
        accent: 'via-amber-500/60',
        color: favourite.value.color,
    },
    {
        label: 'Top Club',
        value: topClub.value.label,
        hint: topClub.value.hint,
        tone: 'text-rose-400',
        accent: 'via-rose-500/60',
    },
    {
        label: 'Owed',
        value: `Rs ${khata.value.outstanding}`,
        hint: `${khata.value.bills.length} unpaid`,
        tone: 'text-amber-400',
        accent: 'via-amber-500/60',
    },
])

// ── Friends (API-backed) ──
const friendSearchQuery = ref('')
const friendsLoading = ref(false)
const searching = ref(false)
const friends = ref([])
const incomingRequests = ref([])
const suggestedFriends = ref([])
const searchResults = ref([])

const filteredFriends = computed(() =>
    friendSearchQuery.value.trim().length >= 2 ? searchResults.value : friends.value)

async function loadFriends() {
    friendsLoading.value = true
    try {
        const [f, r, sug] = await Promise.allSettled([
            apiGet('/friends'), apiGet('/friends/requests'), apiGet('/friends/suggested'),
        ])
        if (f.status === 'fulfilled') friends.value = (f.value.friends || []).map(x => ({ ...x, status: 'friend' }))
        if (r.status === 'fulfilled') incomingRequests.value = r.value.requests || []
        if (sug.status === 'fulfilled') suggestedFriends.value = sug.value.suggested || []
    } finally {
        friendsLoading.value = false
    }
}

let friendSearchTimer = null
watch(friendSearchQuery, (q) => {
    clearTimeout(friendSearchTimer)
    if (q.trim().length < 2) { searchResults.value = []; return }
    searching.value = true
    friendSearchTimer = setTimeout(async () => {
        try {
            const d = await apiGet(`/friends/search?q=${encodeURIComponent(q.trim())}`)
            searchResults.value = d.results || []
        } catch { searchResults.value = [] } finally { searching.value = false }
    }, 300)
})

async function sendRequest(person) {
    try {
        const d = await apiPost('/friends/requests', { customerId: person.id }, { auth: true })
        person.status = d.status
        if (d.status === 'friend') await loadFriends()
    } catch { /* ignore */ }
}
async function acceptRequest(req) {
    try { await apiPost(`/friends/requests/${req.requestId}/accept`, {}, { auth: true }); await loadFriends() } catch { }
}
async function declineRequest(req) {
    try {
        await apiPost(`/friends/requests/${req.requestId}/decline`, {}, { auth: true })
        incomingRequests.value = incomingRequests.value.filter(r => r.requestId !== req.requestId)
    } catch { }
}
async function removeFriend(person) {
    try { await apiDelete(`/friends/${person.id}`); friends.value = friends.value.filter(f => f.id !== person.id) } catch { }
}
async function toggleFavourite(club) {
    const next = !club.isFavourite
    club.isFavourite = next                       // optimistic
    try {
        if (next) await apiPost(`/clubs/${club.id}/favourite`, {}, { auth: true })
        else await apiDelete(`/clubs/${club.id}/favourite`)
    } catch (_) {
        club.isFavourite = !next                   // revert on failure
    }
}
function inviteFriend(friend) { setTab('clubs') }
function addFriend(suggested) {
    sendRequest(suggested)
    suggestedFriends.value = suggestedFriends.value.filter(x => x.id !== suggested.id)
}

// Dynamic Club Discovery Logic
const allClubs = ref([])
const clubsLoading = ref(false)
const clubSearchQuery = ref('')

async function loadClubs() {
    clubsLoading.value = true
    try {
        const data = await fetchClubs({ query: clubSearchQuery.value })
        const rawList = data.clubs || data || []
        allClubs.value = rawList.map(c => ({
            id: c.uid || c.id,
            name: c.name,
            location: [c.address, c.city].filter(Boolean).join(', ') || 'Address on request',
            branchesCount: c.branches || 1,
            isFavourite: Boolean(c.favourite),
            logoUrl: c.logoUrl || null
        }))
    } catch (err) {
        console.error('Failed to fetch clubs directory:', err)
    } finally {
        clubsLoading.value = false
    }
}

let searchTimeout = null
watch(clubSearchQuery, () => {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
        loadClubs()
    }, 300)
})

onMounted(() => {
    loadClubs()
    loadFriends()
})

function selectClub(club) {
    if (router) {
        router.push(`/booking?clubId=${club.id}`)
    }
}

// Receipts
const receiptOpen = ref(false)
const receiptLoading = ref(false)
const receiptError = ref('')
const receipt = ref(null)

async function openReceipt(game) {
    receiptOpen.value = true
    receiptLoading.value = true
    receiptError.value = ''
    receipt.value = null
    try {
        const data = await apiGet(`/games/${game.id}/receipt`)
        console.log(data)
        receipt.value = data
    } catch (error) {
        receiptError.value = error.message || "Couldn't load that bill"
    } finally {
        receiptLoading.value = false
    }
}

function closeReceipt() {
    receiptOpen.value = false
    receipt.value = null
    receiptError.value = ''
}

// Actions & Auto-refresh
async function cancelBookingAction(bookingId) {
    try {
        await cancelBooking(bookingId)
        bookings.value = bookings.value.filter((b) => b.id !== bookingId)
    } catch (error) {
        console.error('Failed to cancel booking:', error)
    }
}

async function fetchState() {
    const [bookingsResult, gamesResult, khataResult] = await Promise.allSettled([
        apiGet('/bookings'),
        apiGet('/games?limit=50'),
        apiGet('/khata'),
    ])

    if (bookingsResult.status === 'fulfilled') {
        bookings.value = bookingsResult.value.bookings || []
    } else {
        console.error('Failed to fetch bookings:', bookingsResult.reason)
    }
    loading.value = false

    if (gamesResult.status === 'fulfilled') {
        games.value = gamesResult.value.games || []
        summary.value = gamesResult.value.summary || summary.value
    } else {
        console.error('Failed to fetch games:', gamesResult.reason)
    }
    gamesLoading.value = false

    if (khataResult.status === 'fulfilled') {
        khata.value = {
            outstanding: khataResult.value.outstanding || 0,
            payUrl: khataResult.value.payUrl || null,
            bills: khataResult.value.bills || []
        }
    }
}

useAutoRefresh(fetchState, 45000)
</script>