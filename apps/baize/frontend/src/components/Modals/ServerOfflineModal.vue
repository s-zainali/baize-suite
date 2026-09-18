<template>
    <div
        class="flex-1 mt-25 flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto animate-in fade-in zoom-in-95 duration-200">
        <div class="relative mb-6">
            <span class="text-6xl block filter drop-shadow-[0_0_15px_rgba(239,68,68,0.4)] animate-pulse">🔌</span>
            <div class="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 border-2 border-slate-900 rounded-full"></div>
        </div>
        <h2 class="text-2xl font-black text-white tracking-tight">System Core Offline</h2>
        <p class="text-slate-400 text-sm mt-2 mb-6 leading-relaxed">
            The Baize panel cannot establish a handshake with the local database server
            architecture.
        </p>
        <div
            class="w-full text-left bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 font-mono text-xs text-slate-400 mb-6 space-y-2">
            <div class="text-rose-400 font-bold tracking-wide uppercase text-[10px] mb-1">
                Troubleshooting Checklist:
            </div>
            <div class="flex items-start gap-2">
                <span>1.</span><span>Navigate to your backend project directory.</span>
            </div>
            <div class="flex items-start gap-2">
                <span>2.</span><span>Run
                    <code class="text-indigo-400 bg-slate-900 px-1 py-0.5 rounded">python app.py</code> to
                    initialize the Flask server.</span>
            </div>
            <div class="flex items-start gap-2">
                <span>3.</span><span>Ensure the terminal outputs
                    <code class="text-emerald-400">Running on http://127.0.0.1:5000</code>.</span>
            </div>
        </div>
        <button @click="emit('attempt-connection')"
            class="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl border border-slate-700 text-xs tracking-wider uppercase shadow-md transition-all active:scale-95 cursor-pointer flex items-center gap-2">
            <span>Reconnect Terminal</span> 🔄
        </button>
    </div>
</template>

<script setup>
const emit = defineEmits(['attempt-connection'])
</script>