<template>
    <div
        class="relative min-h-screen overflow-clip bg-slate-900 text-white selection:bg-emerald-500/30 selection:text-emerald-300">

        <div
            class="sm:hidden mt-4 sticky top-0 z-100 flex flex-1 flex-col items-center justify-center gap-2 bg-gradient-to-r from-transparent via-slate-800/80 to-transparent  backdrop-blur-md sm:order-2 sm:col-span-1">
            <div class="h-[1px] w-full rounded-full bg-gradient-to-r from-transparent via-slate-700 to-transparent">
            </div>
            <div class="flex items-center gap-4">
                <img src="/baize_logo.png" class="h-8" alt="">
                <img src="/baize_logo_text.png" class="h-8 py-1 object-contain" alt="Baize Logo" />
            </div>
            <div class="h-[1px] w-full rounded-full bg-gradient-to-r from-transparent via-slate-700 to-transparent">
            </div>
        </div>
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
            <nav class="mb-4 grid grid-cols-1 sm:flex gap-2 border-b border-slate-800/80 pb-3">
                <button @click="activeTab = 'dashboard'"
                    :class="activeTab === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                    class="flex items-center gap-2 rounded-xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    Dashboard
                </button>
                <button @click="activeTab = 'clubs'"
                    :class="activeTab === 'clubs' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                    class="flex items-center gap-2 rounded-xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Explore Clubs
                </button>
                <button @click="activeTab = 'friends'"
                    :class="activeTab === 'friends' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-400 border-slate-700/60 hover:text-slate-200'"
                    class="flex items-center gap-2 rounded-xl border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer">
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Friends
                </button>
            </nav>

            <!-- TAB 1: MAIN DASHBOARD VIEW -->
            <main v-if="activeTab === 'dashboard'" class="flex-1 space-y-4">
                <!-- Summary strip -->
                <section class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                    <div v-for="stat in stats" :key="stat.label"
                        class="group relative overflow-hidden rounded-2xl border border-slate-700 bg-slate-800 shadow-[] p-4 backdrop-blur-xl transition-all duration-300 hover:border-slate-700/80 hover:bg-slate-700/80"
                        :class="stat.label === 'Owed' ? 'col-span-2 sm:col-span-1' : ''">
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

                        <button @click="activeTab = 'clubs'"
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
                                <div class="group flex w-full items-center gap-4 rounded-2xl border px-4 py-3 text-left transition-all"
                                    :class="khata.bills.some(b => b.ref === game.receiptId) ?
                                        'border-amber-700/60 bg-amber-500/10 hover:border-amber-600 hover:bg-amber-500/15' :
                                        'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'"
                                    :title="`View bill for ${typeLabel(game.tableType)} #${game.tableNumber}`">
                                    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border"
                                        :style="{ borderColor: `${typeColor(game.tableType)}40`, backgroundColor: `${typeColor(game.tableType)}14` }">
                                        <span class="h-2.5 w-2.5 rounded-full"
                                            :style="{ backgroundColor: typeColor(game.tableType) }" />
                                    </span>

                                    <div class="min-w-0 flex-1">
                                        <p class="text-[9px] font-black uppercase tracking-wider"
                                            :style="{ color: typeColor(game.tableType) }">
                                            {{ typeLabel(game.tableType) }} #{{ game.tableNumber }}
                                        </p>
                                        <p class="mt-0.5 truncate text-xs font-bold text-slate-200">
                                            {{ playedLabel(game) }}
                                        </p>
                                    </div>

                                    <div class="shrink-0 text-right">
                                        <p class="font-mono text-xs font-bold text-slate-300">{{
                                            durationLabel(game.minutes) }}</p>
                                        <p class="font-mono text-[10px] text-slate-400">Rs {{ game.cost }}</p>
                                    </div>

                                    <button type="button" @click="openReceipt(game)"
                                        class="cursor-pointer shrink-0 rounded-lg border px-2.5 py-1 text-[8px] font-black uppercase tracking-widest transition-all"
                                        :class="khata.bills.some(b => b.ref === game.receiptId) ? 'border-amber-600/80 text-amber-400 hover:border-amber-400 hover:bg-amber-500/20' : 'border-slate-700 text-slate-400 hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-400'">
                                        Bill
                                    </button>
                                </div>
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
                            @select-club="selectClub(club)" />
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
            <PoweredByZain :forCustomer="true" />

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

            <BillingReceipt v-else-if="receipt" :receipt="receipt" :read-only="true" @close="closeReceipt" />
        </div>
    </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { typeLabel, typeColor, formatPhoneDisplay, qrMatrix, qrSvgPath, BookingItem, PoweredByZain, BillingReceipt, useAutoRefresh } from '@baize/ui'
import { customer, signOut, apiGet, apiPost, apiDelete } from '../auth.js'
import { fetchClubs, cancelBooking } from '../api.js'
import ClubCard from '@/components/ClubCard.vue'

const router = useRouter()

// Navigation tab state
const activeTab = ref('dashboard') // 'dashboard' | 'clubs'

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

function playedLabel(game) {
    if (!game.playedAt) return game.date || ''
    const when = new Date(game.playedAt)
    const time = when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    const sameDay = (a, b) => a.toDateString() === b.toDateString()
    if (sameDay(when, today)) return `Today, ${time}`
    if (sameDay(when, yesterday)) return `Yesterday, ${time}`
    return `${when.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}, ${time}`
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

const stats = computed(() => [
    {
        label: 'Upcoming',
        value: upcoming.value.length,
        hint: upcoming.value.length === 1 ? 'reservation' : 'reservations',
        tone: 'text-emerald-400',
        accent: 'via-emerald-500/60',
    },
    {
        label: 'Games Played',
        value: summary.value.gamesPlayed,
        hint: summary.value.gamesPlayed === 1 ? 'session so far' : 'sessions so far',
        tone: 'text-sky-400',
        accent: 'via-sky-500/60',
    },
    {
        label: 'Time Played',
        value: totalPlayed.value,
        hint: 'across all stations',
        tone: 'text-violet-400',
        accent: 'via-violet-500/60',
    },
    {
        label: 'Favourite',
        value: favourite.value.label,
        hint: favourite.value.hint,
        tone: 'text-amber-400',
        accent: 'via-amber-500/60',
        color: favourite.value.color,
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
function inviteFriend(friend) { activeTab.value = 'clubs' }
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
            isFavourite: Boolean(c.favourite)
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
        receipt.value = data.receipt
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

useAutoRefresh(fetchState, 15000)
</script>