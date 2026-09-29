<template>
    <div class="relative inline-flex items-center justify-center p-0 select-none">
        <!-- Snug Racked Balls Container -->
        <div class="relative z-25 flex flex-col items-center p-0.5 mt-2">
            <div v-for="(row, rowIndex) in rackRows" :key="rowIndex"
                class="flex items-center justify-center -mt-[1.5px]">
                <div v-for="(ballType, ballIndex) in row" :key="`${rowIndex}-${ballIndex}`" class="">
                    <PoolBall :type="ballType" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import PoolBall from './PoolBall.vue'

const props = defineProps({
    // Game variations: '8-ball', '9-ball', '10-ball', 'snooker-15', 'snooker-10', 'snooker-6', 'century'
    gameType: {
        type: String,
        default: '8-ball',
    },
})

const isDiamond = computed(() => props.gameType.toLowerCase() === '9-ball')

function shuffle(array) {
    const arr = [...array]
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
            ;[arr[i], arr[j]] = [arr[j], arr[i]]
    }
    return arr
}

const rackRows = computed(() => {
    const type = props.gameType.toLowerCase()

    // 1. STANDARD 8-BALL POOL (15-Ball Triangle)
    if (type === '8-ball' || type === 'default') {
        const solids = Array.from({ length: 7 }, (_, i) => `solid-${i + 1}`)
        const stripes = Array.from({ length: 7 }, (_, i) => `stripe-${i + 9}`)

        const shuffledSolids = shuffle(solids)
        const shuffledStripes = shuffle(stripes)

        const leftCorner = shuffledSolids.pop()
        const rightCorner = shuffledStripes.pop()
        const remaining = shuffle([...shuffledSolids, ...shuffledStripes])

        const rack = new Array(15)
        rack[4] = 'black-8'
        rack[10] = leftCorner
        rack[14] = rightCorner

        const openSlots = [0, 1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13]
        openSlots.forEach((slot, idx) => {
            rack[slot] = remaining[idx]
        })

        return [
            rack.slice(0, 1),
            rack.slice(1, 3),
            rack.slice(3, 6),
            rack.slice(6, 10),
            rack.slice(10, 15)
        ]
    }

    // 2. 9-BALL POOL (Diamond Rack)
    if (type === '9-ball') {
        const pool = shuffle(['solid-2', 'solid-3', 'solid-4', 'solid-5', 'solid-6', 'solid-7', 'black-8'])
        return [
            ['solid-1'],
            [pool[0], pool[1]],
            [pool[2], 'stripe-9', pool[3]],
            [pool[4], pool[5]],
            [pool[6]]
        ]
    }

    // 3. 10-BALL POOL (10-Ball Triangle)
    if (type === '10-ball') {
        const pool = shuffle(['solid-2', 'solid-3', 'solid-4', 'solid-5', 'solid-6', 'solid-7', 'black-8', 'stripe-9'])
        return [
            ['solid-1'],
            [pool[0], pool[1]],
            [pool[2], 'stripe-10', pool[3]],
            [pool[4], pool[5], pool[6], pool[7]]
        ]
    }

    // 4. 15-RED SNOOKER
    if (type === 'snooker-15' || type === 'snooker') {
        const reds = Array(15).fill('snooker-red')
        return [
            reds.slice(0, 1),
            reds.slice(1, 3),
            reds.slice(3, 6),
            reds.slice(6, 10),
            reds.slice(10, 15)
        ]
    }

    // 5. 10-RED SNOOKER
    if (type === 'snooker-10') {
        const reds = Array(10).fill('snooker-red')
        return [
            reds.slice(0, 1),
            reds.slice(1, 3),
            reds.slice(3, 6),
            reds.slice(6, 10)
        ]
    }

    // 6. 6-RED SNOOKER
    if (type === 'snooker-6') {
        const reds = Array(6).fill('snooker-red')
        return [
            reds.slice(0, 1),
            reds.slice(1, 3),
            reds.slice(3, 6)
        ]
    }

    // 7. CENTURY GAME (10 Century Reds)
    if (type === 'century') {
        const reds = Array(10).fill('century-red')
        return [
            reds.slice(0, 1),
            reds.slice(1, 3),
            reds.slice(3, 6),
            reds.slice(6, 10)
        ]
    }

    return []
})
</script>