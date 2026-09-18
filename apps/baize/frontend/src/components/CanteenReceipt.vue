<template>
    <div class="bg-slate-900 p-6 pt-0 text-slate-100 relative flex flex-col">

        <!-- Header: same shell as the dashboard's — sticky, full-bleed over the
             page padding, same shadow, same title scale and button treatment. -->
        <header
            class="mb-6 pb-6 flex flex-row flex-wrap justify-between items-start lg:items-center gap-4 sticky top-0 z-50 bg-slate-950 shadow-[0px_0px_1rem_0px_#020617] pt-6 left-0 -mr-6 pr-6 -ml-6 pl-6">
            <div>
                <h1 class="text-3xl font-black tracking-tight text-white text-nowrap">
                    <img class="inline h-[5vh] mr-4" src="/snack.png" alt="">Canteen
                </h1>
            </div>
            <div class="flex gap-2 items-center flex-grow justify-end flex-wrap sm:flex-nowrap">
                <RouterLink to="/active-bills"
                    class="bg-slate-800 hover:bg-slate-700 hover:text-white transition-all text-slate-300 px-4 py-2 rounded-xl text-xs font-bold border border-slate-700 cursor-pointer">
                    Active Bills 🧾
                </RouterLink>
                <RouterLink to="/dashboard"
                    class="bg-slate-800 hover:bg-slate-700 hover:text-white transition-all text-slate-300 px-4 py-2 rounded-xl text-xs font-bold border border-slate-700 cursor-pointer">
                    Dashboard 🎱
                </RouterLink>
                <div
                    class="bg-slate-800 text-slate-300 px-4 py-2 rounded-xl border border-slate-700 text-center leading-tight">
                    <p class="text-[8px] font-black uppercase tracking-widest text-slate-500">Today</p>
                    <p class="font-mono text-xs font-black text-emerald-400">Rs {{ todayTotal }}</p>
                </div>
                <div
                    class="bg-slate-800 text-slate-300 px-4 py-2 rounded-xl border border-slate-700 text-center leading-tight">
                    <p class="text-[8px] font-black uppercase tracking-widest text-slate-500">Orders</p>
                    <p class="font-mono text-xs font-black text-sky-400">{{ todayCount }}</p>
                </div>
                <button v-if="lowStock.length" @click="showLowStock = true"
                    class="bg-amber-500/10 hover:bg-amber-500/20 transition-all text-amber-400 px-4 py-2 rounded-xl text-xs font-bold border border-amber-600/40 cursor-pointer">
                    Low Stock ⚠ {{ lowStock.length }}
                </button>
                <button @click="openHistory"
                    class="bg-slate-800 hover:bg-slate-700 hover:text-white transition-all text-slate-300 px-4 py-2 rounded-xl text-xs font-bold border border-slate-700 cursor-pointer">
                    Orders 📋
                </button>
                <button v-if="canManage" @click="openProductForm()"
                    class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-5 py-2 rounded-xl text-xs font-black tracking-wider transition-all cursor-pointer">
                    + ADD ITEM
                </button>
                <UserMenu />
            </div>
        </header>

        <div class="flex flex-1 items-start">
            <!-- Catalogue -->
            <main class="min-w-0 flex-1 flex gap-4">
                <div class="flex flex-col flex-1 gap-4">
                    <div class=" z-30 space-y-2.5 border-b border-slate-800/60 backdrop-blur">

                        <ListStrip :title="'Categories'" :empty="!allCategories.length"
                            :empty-text="'No categories yet'" :wrap="false" is-col>
                            <div class="w-full grid gap-4 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
                                :class="'grid-cols-' + allCategories.length">
                                <button v-for="cat in allCategories" :key="cat.id" @click="activeCategory = cat.id"
                                    class="flex flex-col gap-2 items-center justify-center shrink-0 cursor-pointer rounded-xl border p-3 text-[11px] font-black whitespace-nowrap transition-all"
                                    :class="activeCategory === cat.id
                                        ? 'border-emerald-500/50 bg-emerald-600/15 text-emerald-300'
                                        : 'border-slate-800 bg-slate-900/70 text-slate-400 hover:bg-slate-700/50 hover:border-slate-700 hover:text-slate-200'">
                                    <img :src="cat.imgUrl" :alt="cat.emoji" class="w-10 h-10"> {{ cat.label }}
                                </button>
                            </div>
                        </ListStrip>
                    </div>
                    <div class="flex flex-1 flex-col gap-4">
                        <div class="relative">
                            <span
                                class="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-slate-600">⌕</span>
                            <input v-model="search" type="search" placeholder="Search the menu…"
                                class="w-full rounded-3xl border border-slate-700 bg-slate-800 py-2.5 pr-4 pl-9 text-sm font-bold text-white outline-hidden transition-colors placeholder:font-normal placeholder:text-slate-600 focus:border-slate-600" />
                        </div>
                        <p v-if="loading" class="py-20 text-center text-xs font-bold text-slate-600">Loading menu…</p>

                        <p v-else-if="loadError"
                            class="mt-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-center text-xs font-bold text-rose-400">
                            {{ loadError }}
                        </p>
                        <!-- Grouped by category so a long menu reads as sections
                             rather than one undifferentiated wall of tiles. -->
                        <div v-else-if="filtered.length" class="flex flex-col gap-3">
                            <section v-for="group in grouped" :key="group.id"
                                class="rounded-4xl border border-slate-800 bg-slate-950/50 p-5">
                                <div class="mb-3 flex items-center gap-2.5 px-0.5">
                                    <img v-if="group.imgUrl" :src="group.imgUrl" alt=""
                                        class="h-5 w-5 shrink-0 object-contain opacity-80" />
                                    <h2 class="text-[11px] font-black uppercase tracking-widest text-slate-300">
                                        {{ group.label }}
                                    </h2>
                                    <span class="font-mono text-[10px] text-slate-600">{{ group.items.length }}</span>
                                    <span class="h-px flex-1 bg-gradient-to-r from-slate-800 to-transparent"></span>
                                </div>

                                <div class="grid grid-cols-1 gap-2.5 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
                                    <div v-for="item in group.items" :key="item.id" class="relative">
                                        <button @click="toggleCart(item)" :disabled="isOutOfStock(item)"
                                            class="group flex h-full w-full flex-col rounded-2xl border p-3.5 text-left transition-all"
                                            :class="isOutOfStock(item)
                                                ? 'cursor-not-allowed border-slate-800/60 bg-slate-800/40 opacity-45'
                                                : qtyInCart(item.id)
                                                    ? 'cursor-pointer border-emerald-500/60 bg-emerald-950/40 ring-1 ring-emerald-500/20 hover:bg-emerald-950/60 active:scale-[0.98]'
                                                    : 'cursor-pointer border-slate-700 bg-slate-800 hover:border-emerald-600/50 hover:bg-slate-700/70 active:scale-[0.98]'">
                                            <div class="flex items-start justify-between">
                                                <div class="flex flex-col gap-4">
                                                    <span v-if="qtyInCart(item.id)"
                                                        class="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-600 px-1.5 font-mono text-[10px] font-black text-white">
                                                        {{ qtyInCart(item.id) }}
                                                    </span>
                                                    <!-- Updated product image / emoji fallback -->
                                                    <!-- No fallback, fails loudly if URL is broken -->
                                                    <img v-if="item.imgUrl" :src="item.imgUrl.startsWith('http') ? item.imgUrl : `${API_URL}${item.imgUrl}`" :alt="item.name"
                                                        class="h-20 object-contain" />
                                                    <span v-else
                                                        class="text-[9px] text-slate-500 font-bold border border-dashed border-slate-700 rounded p-1 w-8 h-8 flex items-center justify-center text-center leading-tight">No
                                                        Img</span>

                                                    <span class="text-[11px] leading-tight font-black text-white">{{
                                                        item.name }}</span>
                                                </div>
                                                <div class="flex flex-col justify-between items-end gap-4 h-full">
                                                    <span
                                                        class="font-mono text-xs font-black text-emerald-400/80 bg-emerald-700/10 px-2 py-0.5 rounded-lg border-1 border-emerald-400/50 text-nowrap">Rs.
                                                        {{ item.price }}</span>
                                                    <div class="flex items-end justify-between gap-1">
                                                        <span v-if="isOutOfStock(item)"
                                                            class="text-[10px] font-black tracking-widest text-rose-400 uppercase">Out</span>
                                                        <span
                                                            v-else-if="item.stock !== null && item.stock <= lowStockThreshold"
                                                            class="text-[10px] leading-tight font-bold text-amber-400">Stock:
                                                            {{ item.stock }}</span>
                                                        <span v-else-if="item.stock !== null"
                                                            class="text-[10px] leading-tight text-slate-400 font-bold">Stock:
                                                            {{ item.stock }}</span>
                                                        <span v-else
                                                            class="font-mono text-[10px] text-slate-400 font-bold">Stock:
                                                            ∞</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </button>
                                        <button v-if="canManage" @click.stop="openProductForm(item)" title="Edit item"
                                            class="absolute bottom-2 left-2 hidden h-5 w-5 cursor-pointer items-center justify-center rounded-md border border-slate-600 bg-slate-950/80 text-[9px] text-slate-400 group-hover:flex hover:text-white sm:flex sm:opacity-0 sm:hover:opacity-100">
                                            ✎
                                        </button>
                                    </div>
                                </div>
                            </section>
                        </div>

                        <div v-else class="rounded-2xl border border-dashed border-slate-800 py-16 text-center">
                            <p class="text-sm font-bold text-slate-500">Nothing matches</p>
                            <button @click="search = ''; activeCategory = 'all'"
                                class="mt-2 cursor-pointer text-[11px] font-bold text-emerald-500 hover:text-emerald-400">
                                Clear filters
                            </button>
                        </div>
                    </div>
                </div>
                <!-- max-h keeps the panel from growing with the cart; the list
                     inside scrolls instead, so the totals and Charge button stay
                     put however many lines are added. -->
                <aside
                    class="inset-y-0 right-0 z-50 flex max-h-[calc(100dvh-10rem)] w-[21rem] max-w-full flex-col rounded-3xl border-1 border-slate-700 bg-slate-800 transition-transform duration-200 z-auto translate-x-0 sticky top-25 lg:shadow-none">
                    <div class="flex shrink-0 items-center justify-between border-b border-slate-800 px-5 py-4">
                        <h2 class="text-lg font-black tracking-tight leading-tight">Current Order</h2>
                        <div class="flex items-center gap-2">
                            <button v-if="cart.length" @click="cart = []"
                                class="cursor-pointer text-[9px] font-black tracking-widest text-slate-500 uppercase hover:text-rose-400">
                                Clear
                            </button>
                            <button @click="cartOpen = false" class="cursor-pointer text-slate-500 lg:hidden">✕</button>
                        </div>
                    </div>

                    <div class="shrink-0 border-b border-slate-800 px-3 py-3">
                        <DropdownField :form="charge" field="uid" :options="chargeOptions" label="Charge To"
                            placeholder="Select Customer" />
                        <p v-if="charge.uid && charge.uid !== 'walk-in'" class="mt-2 px-1 text-[10px] leading-snug text-slate-500">
                            Charged to the table's tab — the guest settles it when their session ends.
                        </p>
                        <p v-else class="mt-2 px-1 text-[10px] leading-snug text-slate-500">
                            Paid now at the counter; a receipt with a payment QR is printed.
                        </p>
                    </div>

                    <div v-if="!cart.length" class="flex flex-1 flex-col items-center justify-center px-6 text-center">
                        <span class="mb-2 text-2xl opacity-40">🧺</span>
                        <p class="text-[11px] font-bold text-slate-500">Cart is empty</p>
                        <p class="mt-1 text-[10px] text-slate-600">Tap an item to add it</p>
                    </div>

                    <ul v-else class="min-h-0 flex-1 space-y-1.5 overflow-y-auto px-3 py-3 canteen-scroll">
                        <li v-for="line in cart" :key="line.id"
                            class="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/50 py-2 pr-2 pl-2.5">
                            <div class="min-w-0 flex-1 p-2">
                                <p class="truncate text-[11px] font-black text-white">{{ line.name }}</p>
                                <p class="font-mono text-[10px] text-slate-500">
                                    {{ line.qty }} × {{ line.price }} = {{ line.qty * line.price }}
                                </p>
                            </div>
                            <div class="flex shrink-0 items-center gap-1 mr-2">
                                <button @click="changeQty(line, -1)"
                                    class="flex h-6 w-6 cursor-pointer items-center justify-center rounded-lg border border-slate-800 text-slate-400 hover:border-slate-600 hover:text-white">−</button>
                                <span class="w-5 text-center font-mono text-xs font-black">{{ line.qty }}</span>
                                <button @click="changeQty(line, 1)" :disabled="atStockLimit(line)"
                                    class="flex h-6 w-6 items-center justify-center rounded-lg border border-slate-800 text-slate-400 enabled:cursor-pointer enabled:hover:border-slate-600 enabled:hover:text-white disabled:opacity-30">+</button>
                            </div>
                        </li>
                    </ul>

                    <div v-if="cart.length" class="shrink-0 space-y-2.5 border-t border-slate-800 px-4 py-3">
                        <div class="flex items-center justify-between gap-2">
                            <span class="text-[9px] font-black tracking-widest text-slate-500 uppercase">Discount</span>
                            <div class="flex items-center gap-1">
                                <button v-for="preset in [0, 10, 20]" :key="preset" @click="discountPercent = preset"
                                    class="cursor-pointer rounded-lg border px-2 py-0.5 font-mono text-[10px] font-bold transition-colors"
                                    :class="discountPercent === preset
                                        ? 'border-emerald-600/50 bg-emerald-600/15 text-emerald-300'
                                        : 'border-slate-800 text-slate-500 hover:text-slate-300'">{{ preset
                                        }}%</button>
                            </div>
                        </div>

                        <dl class="space-y-1 font-mono text-[11px]">
                            <div class="flex justify-between text-slate-400">
                                <dt>Subtotal</dt>
                                <dd>Rs {{ subtotal }}</dd>
                            </div>
                            <div v-if="discountAmount" class="flex justify-between text-amber-400">
                                <dt>Discount</dt>
                                <dd>− Rs {{ discountAmount }}</dd>
                            </div>
                            <div
                                class="flex justify-between border-t border-slate-800 pt-1 text-sm font-black text-white">
                                <dt>Total</dt>
                                <dd>Rs {{ total }}</dd>
                            </div>
                        </dl>

                        <p v-if="charge.uid && charge.uid !== 'walk-in'"
                            class="flex items-center gap-1.5 rounded-lg border border-sky-500/30 bg-sky-500/10 px-2.5 py-1.5 text-[10px] font-bold text-sky-300">
                            <span>🧾</span> Billed with the session — no payment taken now
                        </p>
                        <p v-else class="px-0.5 text-[10px] leading-snug text-slate-500">
                            Mark it paid, or put it on a khata, on the receipt.
                        </p>

                        <p v-if="orderError"
                            class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-2.5 py-1.5 text-[10px] font-bold text-rose-400">
                            {{ orderError }}
                        </p>

                        <button @click="checkout" :disabled="charging"
                            class="w-full cursor-pointer rounded-xl bg-emerald-600 py-3 text-[11px] font-black tracking-widest text-white uppercase transition-all hover:bg-emerald-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500">
                            {{ charging ? 'Charging…' : (charge.uid && charge.uid !== 'walk-in' ? `Add Rs ${total} to Tab` : `Charge Rs
                            ${total}`) }}
                        </button>
                    </div>
                </aside>

            </main>
        </div>

        <!-- Mobile cart handle -->
        <!-- <button v-if="cart.length && !cartOpen" @click="cartOpen = true"
            class="fixed right-4 bottom-4 z-40 flex cursor-pointer items-center gap-3 rounded-2xl bg-emerald-600 px-5 py-3.5 shadow-2xl shadow-emerald-950/50 lg:hidden">
            <span
                class="flex h-6 min-w-6 items-center justify-center rounded-full bg-white/20 px-1.5 font-mono text-xs font-black text-white">
                {{ itemCount }}
            </span>
            <span class="text-xs font-black tracking-widest text-white uppercase">Rs {{ total }}</span>
        </button> -->

        <!-- Low stock -->
        <div v-if="showLowStock"
            class="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
            @click.self="showLowStock = false">
            <div class="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-5">
                <h2 class="mb-3 text-sm font-black text-amber-400">Running Low</h2>
                <ul class="max-h-80 space-y-1.5 overflow-y-auto canteen-scroll">
                    <li v-for="item in lowStock" :key="item.id"
                        class="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/50 px-3 py-2">
                        <span class="text-[11px] font-bold text-slate-200">{{ item.name }}</span>
                        <div class="flex items-center gap-2">
                            <span class="font-mono text-[10px]"
                                :class="item.stock === 0 ? 'text-rose-400' : 'text-amber-300'">
                                {{ item.stock === 0 ? 'out' : `${item.stock} left` }}
                            </span>
                            <button v-if="canManage" @click="restock(item)"
                                class="cursor-pointer rounded-lg border border-slate-700 px-2 py-1 text-[9px] font-black text-slate-300 hover:border-emerald-600/50 hover:text-emerald-400">
                                +10
                            </button>
                        </div>
                    </li>
                </ul>
                <button @click="showLowStock = false"
                    class="mt-4 w-full cursor-pointer rounded-xl bg-slate-800 py-2.5 text-[10px] font-black tracking-widest text-slate-200 uppercase">
                    Close
                </button>
            </div>
        </div>

        <!-- Same ledger the dashboard uses, opened on the canteen side. -->
        <!-- Add / edit item -->
        <div v-if="productForm"
            class="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
            @click.self="productForm = null">
            <div class="w-full max-w-sm rounded-3xl border border-slate-800 bg-slate-900 p-5">
                <h2 class="mb-4 text-sm font-black">{{ productForm.id ? 'Edit Item' : 'New Item' }}</h2>
                <div class="space-y-3">
                    <div class="flex gap-2">
                        <input v-model="productForm.emoji" maxlength="4" placeholder="🍫"
                            class="w-14 rounded-xl border border-slate-800 bg-slate-950 px-2 py-2 text-center text-lg outline-hidden focus:border-slate-600" />
                        <TextField :class="'flex-1'" :form="productForm" :field="'name'" :label="'Item Name'"
                            :placeholder="'Enter item name'" :type="'text'" />
                    </div>
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-black uppercase tracking-wider text-slate-400">Product
                            Image</label>
                        <div class="flex items-center gap-3">
                            <img v-if="imagePreview || productForm.imgUrl" :src="imagePreview || productForm.imgUrl"
                                class="h-10 w-10 rounded-lg object-contain bg-slate-950 border border-slate-800" />
                            <input type="file" accept="image/*" @change="handleFileSelect"
                                class="text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-[10px] file:font-bold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer" />
                        </div>
                    </div>
                    <DropdownField :form="productForm" :field="'category'" :label="'Category'" :options="categories"
                        :icons="true" :placeholder="'Choose item category'" />
                    <div class="grid grid-cols-2 gap-2">
                        <StepperField v-model="productForm.price" label="Price" suffix="Rs" :step-by="10"
                            accent="emerald" />
                        <!-- nullable: an empty box means made-to-order, which the
                             old steppers couldn't express — they always produced
                             a number, so "leave blank" was impossible. -->
                        <StepperField v-model="productForm.stock" label="Stock" placeholder="∞" nullable
                            accent="slate" />
                    </div>
                    <p class="text-[9px] leading-relaxed text-slate-600">
                        Clear the stock box for made-to-order items that never run out.
                    </p>
                    <p v-if="formError" class="text-[10px] font-bold text-rose-400">{{ formError }}</p>
                </div>
                <div class="mt-5 flex gap-2">
                    <button v-if="productForm.id" @click="removeProduct"
                        class="cursor-pointer rounded-xl border border-slate-800 px-3 py-2.5 text-[10px] font-black tracking-widest text-rose-400 uppercase hover:border-rose-800">
                        Delete
                    </button>
                    <button @click="productForm = null"
                        class="flex-1 cursor-pointer rounded-xl bg-slate-800 py-2.5 text-[10px] font-black tracking-widest text-slate-300 uppercase">
                        Cancel
                    </button>
                    <button @click="saveProduct" :disabled="savingProduct"
                        class="flex-1 cursor-pointer rounded-xl bg-emerald-600 py-2.5 text-[10px] font-black tracking-widest text-white uppercase hover:bg-emerald-500 disabled:bg-slate-800">
                        {{ savingProduct ? 'Saving…' : 'Save' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Charged -->
        <div v-if="lastOrder"
            class="fixed inset-0 z-70 flex items-center justify-center overflow-y-auto bg-slate-950/80 p-4 backdrop-blur-sm"
            @click.self="lastOrder = null">
            <!-- Walk-in: paid now, so print the bill with a payment QR. Same
                 component as the session bill so the two look identical. -->
            <BillingReceipt v-if="lastOrder.method !== 'tab'" variant="canteen" :receipt="canteenReceipt"
                @close="lastOrder = null" @settle="settleOrder" />

            <!-- On a tab: nothing to pay yet, it rides the session bill -->
            <div v-else class="w-full max-w-xs rounded-3xl border border-slate-800 bg-slate-900 p-6 text-center">
                <div
                    class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-sky-500/40 bg-sky-500/15 text-xl text-sky-400">
                    🧾
                </div>
                <h2 class="text-lg font-black">Added to Tab</h2>
                <p class="mt-1 text-[11px] text-slate-500">{{ lastOrder.code }} · {{ lastOrder.target }}</p>
                <p class="mt-4 font-mono text-2xl font-black text-sky-400">Rs {{ lastOrder.total }}</p>
                <p class="mx-auto mt-2 max-w-[15rem] text-[10px] leading-relaxed text-slate-600">
                    This will appear on {{ lastOrder.target }}'s bill when their session ends.
                </p>
                <button @click="lastOrder = null"
                    class="mt-6 w-full cursor-pointer rounded-xl bg-slate-800 py-3 text-[10px] font-black tracking-widest text-slate-200 uppercase hover:bg-slate-700">
                    Done
                </button>
            </div>
        </div>
        <!-- Announces QR payments so the till knows money arrived. -->
        <PaymentPings @received="refresh()" />
    </div>
</template>

<script setup>
import { usePageBackground } from '@/composables/usePageBackground.js'
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import UserMenu from './UserMenu.vue'
import DropdownField from './Fields/DropdownField.vue'
import StepperField from './Fields/StepperField.vue'
import PaymentPings from './PaymentPings.vue'
import BillingReceipt from './BillingReceipt.vue'
import { auth, authFetch, API_URL } from '@/Auth.js'
import { useAutoRefresh } from '@/utils/useAutoRefresh.js'
import * as api from '@/canteen/api.js'
import {
    addItem, changeQty as changeQtyIn, subtotalOf, discountOf, totalOf,
    itemCountOf, atStockLimit, isOutOfStock,
} from '@/canteen/cart.js'
import ListStrip from './ListStrip.vue'
import TextField from './Fields/TextField.vue'

const canManage = computed(() => ['owner', 'manager'].includes(auth.role))

// ── menu ──────────────────────────────────────────────────────────────────
const products = ref([])
const categories = ref([])
const paymentMethods = ref(['cash', 'easypaisa', 'jazzcash', 'tab'])
const lowStockThreshold = ref(5)
const loading = ref(true)
const loadError = ref('')

const orders = ref([])
const todayTotal = ref(0)
const todayCount = ref(0)
const stations = ref([])

const search = ref('')
const activeCategory = ref('all')
const showLowStock = ref(false)
const showHistory = ref(false)

// The ledger shows both sides, so the game sessions are fetched too — lazily,
// only when the log is actually opened.
const gameLogs = ref([])
const gameLogsTotal = ref(0)

async function openHistory() {
    showHistory.value = true
    try {
        const res = await authFetch(`${API_URL}/logs`)
        const data = await res.json()
        gameLogs.value = data.logs || []
        gameLogsTotal.value = data.grossTotal || 0
    } catch {
        gameLogs.value = []
    }
}

const allCategories = computed(() => [{ id: 'all', label: 'All', imgUrl: '/all.png' }, ...categories.value])

const filtered = computed(() => {
    const term = search.value.trim().toLowerCase()
    return products.value.filter((item) => {
        const inCategory = activeCategory.value === 'all' || item.category === activeCategory.value
        return inCategory && (!term || item.name.toLowerCase().includes(term))
    })
})

// Category artwork that failed to load; those headings fall back to the emoji
// instead of showing a broken-image icon.
const brokenImages = reactive(new Set())

/**
 * The filtered menu split into category sections.
 * Empty categories are dropped so a search doesn't leave hollow headings.
 */
const grouped = computed(() =>
    categories.value
        .map((cat) => ({
            ...cat,
            items: filtered.value.filter((item) => item.category === cat.id),
        }))
        .filter((group) => group.items.length),
)

const lowStock = computed(() =>
    products.value
        .filter((p) => p.stock !== null && p.stock <= lowStockThreshold.value)
        .sort((a, b) => a.stock - b.stock),
)

// ── cart ──────────────────────────────────────────────────────────────────
const cart = ref([])
const cartOpen = ref(false)
// DropdownField writes back into a form object, so the selection lives here.
const charge = reactive({ uid: '' })
const payment = ref('cash')
const discountPercent = ref(0)
const charging = ref(false)
const orderError = ref('')
const lastOrder = ref(null)

/**
 * Reshape a canteen order into the receipt component's vocabulary.
 * `receiptId` and `totalCost` are what drive its header and payment QR, so the
 * canteen sale gets billed exactly like a session does.
 */
const canteenReceipt = computed(() => {
    const order = lastOrder.value
    if (!order) return null
    return {
        receiptId: order.code,
        date: order.at ? new Date(order.at).toLocaleString() : new Date().toLocaleString(),
        player: order.target,
        servedBy: order.by,
        lineItems: (order.items || []).map((item) => ({
            name: item.name, qty: item.qty, cost: item.lineTotal,
        })),
        discountPercent: order.discountPercent,
        discountAmount: order.discountAmount,
        totalCost: order.total,
        orderId: order.id,
        payUrl: order.payUrl || '',
        paymentStatus: order.paymentStatus,
        paymentMethod: order.paymentMethod,
        khataName: order.khataName,
        // Counter sales have no named guest, so a khata has nobody to chase.
        isWalkIn: order.tableUid !== 'walk-in',
        segments: [],
    }
})

let billWatch = null

function stopBillWatch() {
    if (billWatch) clearInterval(billWatch)
    billWatch = null
}

async function refreshBillStatus() {
    const open = canteenReceipt.value
    if (!open?.orderId || open.paymentStatus === 'paid') { stopBillWatch(); return }
    try {
        const res = await authFetch(`${API_URL}/canteen/orders/${open.orderId}`)
        if (!res.ok) return
        const data = await res.json()

        const orderData = data.order || data

        if (orderData.paymentStatus !== open.paymentStatus || orderData.paymentMethod !== open.paymentMethod) {
            // Update the underlying reactive ref so canteenReceipt re-evaluates automatically
            lastOrder.value = {
                ...lastOrder.value,
                paymentStatus: orderData.paymentStatus,
                paymentMethod: orderData.paymentMethod || lastOrder.value.method,
                khataName: orderData.khataName,
            }
        }
    } catch {
        console.warn('error updating payment status')
    }
}

watch(() => canteenReceipt.value?.orderId, (orderId) => {
    stopBillWatch()
    if (orderId) billWatch = setInterval(refreshBillStatus, 2000)
}, { immediate: true })

onUnmounted(stopBillWatch)

// Selecting a station means "put it on their tab"; going back to walk-in has to
// restore a real payment method or the order would post with method 'tab'.
watch(() => charge.uid, (uid) => {
    payment.value = uid !== 'walk-in' ? 'tab' : 'cash'
    orderError.value = ''
})

const qtyInCart = (id) => cart.value.find((l) => l.id === id)?.qty || 0
const toggleCart = (item) => {
    if (qtyInCart(item.id) > 0) {
        cart.value = cart.value.filter((l) => l.id !== item.id)
    } else {
        cart.value = addItem(cart.value, item)
    }
    orderError.value = ''
}
const changeQty = (line, delta) => { cart.value = changeQtyIn(cart.value, line.id, delta) }

const subtotal = computed(() => subtotalOf(cart.value))
const discountAmount = computed(() => discountOf(subtotal.value, discountPercent.value))
const total = computed(() => totalOf(subtotal.value, discountPercent.value))
const itemCount = computed(() => itemCountOf(cart.value))

const METHOD_LABELS = { cash: 'Cash', easypaisa: 'Easypaisa', jazzcash: 'Jazzcash', tab: 'Tab' }
const methodLabel = (id) => METHOD_LABELS[id] || id

const timeOf = (iso) =>
    iso ? new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : ''

// Only RUNNING stations can take a charge: an idle table has no open tab, so
// anything put on it would never be billed to anyone.
const stationLabel = (t) => `${t.type.replace(/([A-Z])/g, ' $1').trim()} #${t.id}`
const chargeOptions = computed(() => [
    { value: 'walk-in', label: 'Walk-in customer' },
    ...stations.value
        .filter((t) => t.isActive)
        .map((t) => ({ value: t.uid, label: `${stationLabel(t)} · ${t.bookingName || 'Guest'}` })),
])

// Counter payments only; a tab isn't a payment method the user picks, it's
// implied by choosing a station.
const counterMethods = computed(() => paymentMethods.value.filter((m) => m !== 'tab'))

// ── data ──────────────────────────────────────────────────────────────────
async function refresh() {
    // Paint the document itself, the way the dashboard and overview do, so an
    // overscroll past the page shows the same slate-900 rather than the darker
    // body default from style.css.
    refreshBillStatus()

    const [menu, orderList, state] = await Promise.allSettled([
        api.fetchMenu(),
        api.fetchOrders(),
        authFetch(`${API_URL}/state`).then((r) => r.json()),
    ])

    if (menu.status === 'fulfilled') {
        products.value = menu.value.products
        categories.value = menu.value.categories
        paymentMethods.value = menu.value.paymentMethods
        lowStockThreshold.value = menu.value.lowStockThreshold
        loadError.value = ''
    } else {
        loadError.value = menu.reason?.message || 'Could not load the menu'
    }
    loading.value = false

    if (orderList.status === 'fulfilled') {
        orders.value = orderList.value.orders
        todayTotal.value = orderList.value.todayTotal
        todayCount.value = orderList.value.todayCount
    }
    if (state.status === 'fulfilled') {
        stations.value = state.value.tables || []
        // The chosen station may have been stopped and billed while this cart
        // was open — fall back to walk-in rather than posting a dead tab.
        if (charge.uid && !stations.value.some((t) => t.uid === charge.uid && t.isActive)) {
            charge.uid = ''
        }
    }
}

useAutoRefresh(refresh, 20000)


async function checkout() {
    if (!cart.value.length || charging.value) return
    if (!charge.uid) {
        orderError.value = 'Please select a customer to charge to.'
        return
    }
    charging.value = true
    orderError.value = ''
    try {
        // Only ids and quantities go up — the server prices it.
        const { order } = await api.placeOrder({
            items: cart.value.map((l) => ({ productId: l.id, qty: l.qty })),
            discountPercent: discountPercent.value,
            method: payment.value,
            tableUid: charge.uid? charge.uid !== 'walk-in'? charge.uid : '' : '' || null,
        })
        lastOrder.value = order
        cart.value = []
        discountPercent.value = 0
        charge.uid = ''
        cartOpen.value = false
        await refresh()
    } catch (error) {
        // A 409 means someone else sold the last one while this cart was open.
        orderError.value = error.message
        if (error.status === 409) await refresh()
    } finally {
        charging.value = false
    }
}

async function settleOrder({ status, done }) {
    const order = lastOrder.value
    if (!order) return
    try {
        const result = await api.settleOrder(order.id, { status })
        lastOrder.value = { ...order, paymentStatus: result.paymentStatus, khataName: result.khataName }
        done?.(result)
        await refresh()
    } catch (error) {
        done?.({ error: error.message })
    }
}

// ── product management ────────────────────────────────────────────────────
const productForm = ref(null)
const savingProduct = ref(false)
const formError = ref('')
const selectedFile = ref(null)
const imagePreview = ref(null)

function openProductForm(item = null) {
    formError.value = ''
    selectedFile.value = null
    imagePreview.value = null
    productForm.value = item
        ? { ...item, stock: item.stock === null ? '' : item.stock }
        : { name: '', category: categories.value[0]?.id || 'snacks', price: '', stock: '', emoji: '🍽️', imgUrl: '' }
}

function handleFileSelect(event) {
    const file = event.target.files[0]
    if (file) {
        selectedFile.value = file
        imagePreview.value = URL.createObjectURL(file)
    }
}

async function saveProduct() {
    if (savingProduct.value) return
    savingProduct.value = true
    formError.value = ''
    try {
        let uploadedUrl = productForm.value.imgUrl

        // 1. Upload selected image first
        if (selectedFile.value) {
            const formData = new FormData()
            formData.append('image', selectedFile.value)

            const uploadRes = await authFetch(`${API_URL}/canteen/upload`, {
                method: 'POST',
                body: formData,
            })

            if (!uploadRes.ok) {
                const err = await uploadRes.json()
                throw new Error(err.error || 'Failed to upload image')
            }

            const uploadData = await uploadRes.json()
            uploadedUrl = uploadData.imgUrl
        }

        // 2. Save product with returned image URL
        const payload = {
            name: productForm.value.name,
            category: productForm.value.category,
            price: productForm.value.price,
            stock: productForm.value.stock === '' ? null : productForm.value.stock,
            emoji: productForm.value.emoji,
            imgUrl: uploadedUrl,
        }

        if (productForm.value.id) await api.updateProduct(productForm.value.id, payload)
        else await api.createProduct(payload)

        productForm.value = null
        await refresh()
    } catch (error) {
        formError.value = error.message
    } finally {
        savingProduct.value = false
    }
}

async function removeProduct() {
    if (!productForm.value?.id) return
    if (!confirm('Are you sure you want to delete this item?')) return

    try {
        await api.deleteProduct(productForm.value.id)
        productForm.value = null
        await refresh()
    } catch (error) {
        formError.value = error.message || 'Failed to delete product'
    }
}

async function restock(item) {
    try {
        await api.updateProduct(item.id, { restock: 10 })
        await refresh()
    } catch (error) {
        console.error('Restock failed', error)
    }
}

async function void_(order) {
    try {
        await api.voidOrder(order.id)
        await refresh()
    } catch (error) {
        console.error('Void failed', error)
    }
}

usePageBackground('#0f172a')
</script>

<style scoped>
.canteen-scroll::-webkit-scrollbar {
    width: 6px;
}

.canteen-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.canteen-scroll::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 3px;
}

.canteen-scroll {
    scrollbar-width: thin;
    scrollbar-color: #334155 transparent;
}
</style>