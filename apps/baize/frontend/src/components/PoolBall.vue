<template>
    <div
      class="rounded-full transition-all duration-300 border border-black/10 flex items-center justify-center font-bold text-center select-none"
      :style="ballStyle"
      :title="ballData.name"
    >
      <!-- Inner Stripe / Number Details (Disabled for 12px scale) -->
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const props = defineProps({
    type: {
      type: String,
      required: true,
    },
  })
  
  const ballRegistry = {
    // --- SPECIAL & POOL BASE ---
    'cue-ball': { name: 'Cue Ball', color: '#ffffff', number: null },
    'black-8': { name: '8 Ball (Black)', color: '#111111', number: 8 },
  
    // --- POOL: SOLIDS (1 to 7) ---
    'solid-1': { name: '1 Ball (Yellow)', color: '#facc15', number: 1 },
    'solid-2': { name: '2 Ball (Blue)', color: '#2563eb', number: 2 },
    'solid-3': { name: '3 Ball (Red)', color: '#dc2626', number: 3 },
    'solid-4': { name: '4 Ball (Purple)', color: '#7c3aed', number: 4 },
    'solid-5': { name: '5 Ball (Orange)', color: '#ea580c', number: 5 },
    'solid-6': { name: '6 Ball (Green)', color: '#16a34a', number: 6 },
    'solid-7': { name: '7 Ball (Burgundy)', color: '#7f1d1d', number: 7 },
  
    // --- POOL: STRIPES (9 to 15) ---
    'stripe-9': { name: '9 Ball (Yellow Stripe)', color: '#facc15', number: 9, isStripe: true },
    'stripe-10': { name: '10 Ball (Blue Stripe)', color: '#2563eb', number: 10, isStripe: true },
    'stripe-11': { name: '11 Ball (Red Stripe)', color: '#dc2626', number: 11, isStripe: true },
    'stripe-12': { name: '12 Ball (Purple Stripe)', color: '#7c3aed', number: 12, isStripe: true },
    'stripe-13': { name: '13 Ball (Orange Stripe)', color: '#ea580c', number: 13, isStripe: true },
    'stripe-14': { name: '14 Ball (Green Stripe)', color: '#16a34a', number: 14, isStripe: true },
    'stripe-15': { name: '15 Ball (Burgundy Stripe)', color: '#7f1d1d', number: 15, isStripe: true },
  
    // --- SNOOKER & PAKISTANI CLUB VARIANTS ---
    'snooker-red': { name: 'Snooker Red', color: '#e11d48', number: null },
    'century-red': { name: 'Century Red', color: '#be123c', number: null },
    'snooker-yellow': { name: 'Yellow (2 Points)', color: '#eab308', number: null },
    'snooker-green': { name: 'Green (3 Points)', color: '#15803d', number: null },
    'snooker-brown': { name: 'Brown (4 Points)', color: '#a16207', number: null },
    'snooker-blue': { name: 'Blue (5 Points)', color: '#1d4ed8', number: null },
    'snooker-pink': { name: 'Pink (6 Points)', color: '#ec4899', number: null },
    'snooker-black': { name: 'Black (7 Points)', color: '#171717', number: null },
  }
  
  const ballData = computed(() => {
    return ballRegistry[props.type] || ballRegistry['solid-1']
  })
  
  const ballStyle = computed(() => {
    const data = ballData.value
    
    // Reduced top/bottom white caps to 15% so color band is wider and clearer
    const backgroundStyle = data.isStripe
      ? `linear-gradient(to bottom, #ffffff 15%, ${data.color} 15%, ${data.color} 85%, #ffffff 85%)`
      : data.color
  
    return {
      width: '10px',
      height: '10px',
      background: backgroundStyle
    }
  })
  </script>