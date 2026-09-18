<template>
    <ListStrip title="Bookings" :empty="bookings.length === 0" empty-text="No upcoming bookings" :wrap="true">
        <div class="grid grid-cols-[repeat(auto-fill,minmax(225px,1fr))] gap-2 w-full">
            <BookingItem v-for="b in sorted" :key="b.id" :booking="b" class="shrink-0" @cancel="cancel(b.id)"
                @start-from-booking="fulfil(b.id, $event)" />
        </div>

        <!-- <template #action>
            <RouterLink to="/booking"
                class="bg-gradient-to-r from-emerald-600 to-teal-800 text-white w-30 text-center py-4 rounded-xl text-xs font-black tracking-wider transition-all cursor-pointer">
                + BOOKING
            </RouterLink>
        </template> -->
    </ListStrip>
</template>

<script setup>
import { computed } from 'vue'
import { API_URL, authFetch } from '../Auth.js'
import ListStrip from './ListStrip.vue'
import BookingItem from './BookingItem.vue'

const props = defineProps({ bookings: { type: Array, default: () => [] } })
const emit = defineEmits(['refresh', 'start-from-booking'])

const sorted = computed(() =>
    [...props.bookings].sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
)

async function cancel(id) {
    try {
        await authFetch(`${API_URL}/bookings/${id}`, { method: 'DELETE' })
        emit('refresh')
    } catch (_) { /* ignore */ }
}

async function fulfil(id, event) {
    try {
        emit('start-from-booking', id, event)
    } catch (_) { /* ignore */ }
}
</script>