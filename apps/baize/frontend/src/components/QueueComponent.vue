<template>
    <ListStrip title="Queue" :empty="queue.length === 0" empty-text="Queue is empty" :wrap="false">
        <QueueItem v-for="guest in queue" :key="guest.id" :guest="guest" class="shrink-0"
            @removeGuest="emit('removeGuest', $event)" @start-from-queue="emit('start-from-queue', $event)" />

        <template #action>
            <button @click="emit('add-guest')"
                class="bg-gradient-to-r from-emerald-600 to-teal-800 text-white text-center w-30 py-4 rounded-xl text-xs font-black tracking-wider transition-all cursor-pointer">
                + GUEST
            </button>
        </template>
    </ListStrip>
</template>

<script setup>
import ListStrip from './ListStrip.vue'
import QueueItem from './QueueItem.vue'

const props = defineProps({ queue: { type: Array, default: () => [] }})
const emit = defineEmits(['removeGuest', 'start-from-queue', 'add-guest'])
</script>