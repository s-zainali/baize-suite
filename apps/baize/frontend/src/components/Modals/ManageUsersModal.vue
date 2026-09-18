<template>
    <!-- MANAGE VIEW -->
    <div v-if="modalType === 'manage'"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-3xl p-6 shadow-2xl">

            <!-- Header -->
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-black text-white">MANAGE USERS</h2>
                <button @click="emit('close-modal')"
                    class="text-slate-500 hover:text-white hover:cursor-pointer">✕</button>
            </div>

            <!-- User list -->
            <div class="space-y-2 mb-4 max-h-[70vh] overflow-y-auto pr-1">
                <p v-if="fetching" class="text-xs text-slate-500 text-center py-6">Loading users…</p>
                <p v-else-if="users.length === 0" class="text-xs text-slate-500 text-center py-6">No users found.</p>

                <div v-for="user in users" :key="user.id"
                    class="bg-slate-950/40 border border-slate-800 hover:border-slate-700 rounded-2xl overflow-hidden transition-colors">
                    <!-- Row (click to edit) -->
                    <div class="flex items-center justify-between px-4 py-3 cursor-pointer select-none"
                        @click="openEdit(user)">
                        <div class="flex items-center gap-3 min-w-0">
                            <div
                                class="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-xs font-black text-slate-300 uppercase shrink-0">
                                {{ user.username.slice(0, 2) }}
                            </div>
                            <div class="min-w-0 flex flex-col gap-2">
                                <p class="text-sm font-bold text-white truncate">
                                    {{ user.username }}
                                    <span v-if="user.username === auth.username"
                                        class="text-[9px] text-slate-500 font-normal">(you)</span>
                                </p>
                                <div class="flex gap-2">
                                    <span class="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md"
                                        :class="roleBadgeClass(user.role)">
                                        {{ roleLabel(user.role) }}
                                    </span>
                                    <span v-for="area in (user.capabilities || [])" :key="area"
                                        class="text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded-md border"
                                        :class="user.capabilitiesLocked
                                            ? 'border-slate-700 text-slate-500'
                                            : 'border-emerald-600/40 text-emerald-400'">
                                        {{ capabilityLabel(area) }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center gap-2 shrink-0">
                            <button v-if="user.username !== auth.username" @click.stop="handleDelete(user)"
                                class="text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition-all cursor-pointer"
                                :class="deleteConfirmId === user.id
                                    ? 'bg-rose-500 border-rose-400 text-white'
                                    : 'border-slate-700 text-slate-500 hover:text-rose-400 hover:border-rose-500/40'">
                                {{ deleteConfirmId === user.id ? 'Confirm?' : 'Remove' }}
                            </button>
                            <span class="text-[10px] font-bold text-slate-600">✎</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Error -->
            <p v-if="error"
                class="text-[10px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 uppercase tracking-wide mb-4">
                {{ error }}
            </p>

            <button @click="openAdd"
                class="w-full py-3 rounded-xl text-xs font-black bg-indigo-600 hover:bg-indigo-500 text-white transition-all cursor-pointer mb-3">
                + ADD USER
            </button>

            <button @click="emit('close-modal')"
                class="w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white transition-all cursor-pointer">
                FINISH
            </button>
        </div>

        <!-- EDIT USER (floating above the list, same nested pattern as Split Bill) -->
        <EditUserModal v-if="editingUser" :editingUser="editingUser" :saving="saving" :roleBadgeClass="roleBadgeClass" :editError="editError" @close-modal="editingUser = null" @save-changes="handleEditSave($event)"/>
    </div>
    <AddUserModal v-if="modalType === 'add'" :loading="loading" @close-modal="modalType = 'manage'" @submit="handleCreate($event)"/>
    <!-- ADD VIEW -->
    
</template>

<script setup>
import { auth, authFetch, API_URL, roleLabel, capabilityLabel } from '@/Auth'
import { reactive, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import EditUserModal from './EditUserModal.vue'
import AddUserModal from './AddUserModal.vue'
// const API_URL = import.meta.env.VITE_API_URL

const emit = defineEmits(['close-modal'])


const modalType = ref('manage')
const users = ref([])
const fetching = ref(false)
const loading = ref(false)
const error = ref('')
const deleteConfirmId = ref(null)



// ---------- USERS ----------
async function fetchUsers() {
    fetching.value = true
    error.value = ''
    try {
        const res = await authFetch(`${API_URL}/auth/users`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed to load users')
        users.value = data.users
    } catch (e) {
        error.value = e.message
    } finally {
        fetching.value = false
    }
}

async function handleDelete(user) {
    // first tap arms the button, second tap confirms
    if (deleteConfirmId.value !== user.id) {
        deleteConfirmId.value = user.id
        return
    }
    deleteConfirmId.value = null
    error.value = ''
    try {
        const res = await authFetch(`${API_URL}/auth/users/${user.id}`, { method: 'DELETE' })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed to remove user')
        users.value = users.value.filter(u => u.id !== user.id)
        if (editingUser.value?.id === user.id) editingUser.value = null
    } catch (e) {
        error.value = e.message
    }
}

// ---------- EDIT (floating modal) ----------
const editingUser = ref(null)
const saving = ref(false)
const editError = ref('')

function openEdit(user) {
    deleteConfirmId.value = null
    editError.value = ''
    editingUser.value = user
}

async function handleEditSave(returnObj) {
    if (!returnObj.editValid || saving.value) return
    saving.value = true
    editError.value = ''
    try {
        const payload = { username: returnObj.form.username.trim() }
        if (returnObj.form.password) payload.password = returnObj.form.password
        // Locked accounts (manager/owner) have nothing to send.
        if (!returnObj.user.capabilitiesLocked) payload.capabilities = returnObj.form.capabilities
        if (returnObj.form.branchIds) payload.branchIds = returnObj.form.branchIds
        const res = await authFetch(`${API_URL}/auth/users/${returnObj.user.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed to save changes')

        // sync the list, and the auth store if the owner renamed themselves
        const wasSelf = returnObj.user.username === auth.username
        const row = users.value.find(u => u.id === returnObj.user.id)
        if (row) row.username = data.username
        if (wasSelf && data.username !== auth.username) {
            auth.username = data.username
            localStorage.setItem('ls_user', data.username)
        }
        editingUser.value = null
    } catch (e) {
        editError.value = e.message
    } finally {
        saving.value = false
    }
}

function openAdd() {
    error.value = ''
    modalType.value = 'add'
}

async function handleCreate(returnObj) {
    if (!returnObj.isValid || loading.value) return
    loading.value = true
    error.value = ''
    try {
        const res = await authFetch(`${API_URL}/auth/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: returnObj.form.username.trim(),
                password: returnObj.form.password,
                role: returnObj.form.role,
                capabilities: returnObj.form.capabilities,
                branchIds: returnObj.form.branchIds || [],
            }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed to create user')
        await fetchUsers()
        modalType.value = 'manage'
    } catch (e) {
        error.value = e.message
    } finally {
        loading.value = false
    }
}

// ---------- ROLE DROPDOWN ----------

const dropdownRoot = ref(null)
function handleClickOutside(e) {
    if (dropdownRoot.value && !dropdownRoot.value.contains(e.target)) {
        dropdownOpen.value = false
    }
}

const roleBadgeClass = (role) => ({
    owner: 'bg-amber-500/10 text-amber-400',
    manager: 'bg-indigo-500/10 text-indigo-400',
    receptionist: 'bg-sky-500/10 text-sky-400',
}[role] || 'bg-slate-800 text-slate-400')

onMounted(() => {
    fetchUsers()
    document.addEventListener('mousedown', handleClickOutside)
})
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>