<template>
    <div
            class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
            @click.self="editingUser = null">
            <div class="bg-slate-900 border border-slate-800 w-full max-w-sm rounded-3xl p-6 shadow-2xl">
                <div class="flex justify-between items-center mb-5">
                    <div>
                        <h3 class="text-lg font-black text-white">EDIT USER</h3>
                        <span
                            class="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md inline-block mt-1"
                            :class="roleBadgeClass(editingUser.role)">
                            {{ editingUser.role }}
                        </span>
                    </div>
                    <button @click="emit('close-modal')"
                        class="text-slate-500 hover:text-white hover:cursor-pointer">✕</button>
                </div>

                <div class="space-y-4 mb-6">
                    <TextField :form="editForm" :label="'Username'" :field="'username'" :placeholder="'New Username'" :type="'text'"/>

                    <PasswordField :form="editForm" :field="'password'" 
                        :label="'New Password'" :error="{
                            condition: editForm.password.length < 6 && editForm.password.length !== 0,
                            message: 'Passwords must be at least 6 characters'
                        }" :placeholder="'Leave blank to keep current'"
                     />
                    <PasswordField 
                        :form="editForm"
                        :field="'confirmPassword'"
                        :label="'Confirm New Password'"
                        :error="{
                            condition: editForm.confirmPassword !== editForm.password && editForm.password.length > 0,
                            message: 'Passwords do not match'
                        }"
                        :placeholder="'••••••••'" />

                    <div v-if="!capabilitiesLocked">
                        <span class="block text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1.5">
                            Can Work
                        </span>
                        <div class="grid grid-cols-2 gap-2">
                            <button v-for="area in ALL_CAPABILITIES" :key="area" type="button"
                                @click="toggleCapability(area)"
                                class="rounded-xl border px-3 py-2.5 text-xs font-bold cursor-pointer transition-colors"
                                :class="editForm.capabilities.includes(area)
                                    ? 'border-emerald-500/50 bg-emerald-600/15 text-emerald-300'
                                    : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600'">
                                {{ editForm.capabilities.includes(area) ? '✓ ' : '' }}{{ capabilityLabel(area) }}
                            </button>
                        </div>
                        <p class="mt-1.5 text-[9px] leading-snug text-slate-600">
                            Takes effect the next time they sign in.
                        </p>
                    </div>

                    <p v-else class="text-[10px] leading-snug text-slate-500">
                        This account covers both counters by rank.
                    </p>

                <!-- Branch assignment: employees single, managers multi. Hidden
                     when there's only one branch (auto-assigned to it). -->
                <div v-if="branches.length > 1 && (editingUser.role === 'receptionist' || editingUser.role === 'manager')">
                    <span class="block text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1.5">
                        {{ editingUser.role === 'manager' ? 'Branches' : 'Branch' }}
                    </span>
                    <div class="grid grid-cols-2 gap-2">
                        <button v-for="b in branches" :key="b.id" type="button" @click="toggleBranch(b.id)"
                            class="rounded-xl border px-3 py-2.5 text-xs font-bold cursor-pointer transition-colors"
                            :class="editForm.branchIds.includes(b.id)
                                ? 'border-emerald-500/50 bg-emerald-600/15 text-emerald-300'
                                : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600'">
                            {{ editForm.branchIds.includes(b.id) ? '✓ ' : '' }}{{ b.name }}
                        </button>
                    </div>
                    <p class="mt-1.5 text-[9px] leading-snug text-slate-600">
                        {{ editingUser.role === 'manager' ? 'Every branch this manager oversees.' : 'A receptionist works one branch.' }}
                    </p>
                </div>


                    <p v-if="props.editError"
                        class="text-[10px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 uppercase tracking-wide">
                        {{ editError }}
                    </p>
                </div>

                <div class="flex gap-2">
                    <button @click="emit('save-changes', {user: props.editingUser, form:editForm, editValid:editValid})" :disabled="saving || !editValid"
                        class="flex-1 py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
                        {{ saving ? 'SAVING…' : 'SAVE CHANGES' }}
                    </button>
                    <button @click="emit('close-modal')"
                        class="px-5 py-3 rounded-xl text-xs font-bold bg-slate-800 text-slate-400 hover:text-white transition-all cursor-pointer">
                        CANCEL
                    </button>
                </div>
            </div>
        </div>
</template>

<script setup>
import { ALL_CAPABILITIES, capabilityLabel } from '@/Auth'
import { branches, loadBranches } from '@/composables/useBranch.js'
import { onMounted } from 'vue'
onMounted(loadBranches)
import { reactive, computed } from 'vue'
import TextField from '../Fields/TextField.vue'
import PasswordField from '../Fields/PasswordField.vue'


const props = defineProps({editingUser: Object, saving:Boolean, roleBadgeClass:Function, editError:String})
const emit = defineEmits(['save-changes', 'close-modal'])
const editForm = reactive({
    username: props.editingUser.username,
    password: '',
    confirmPassword: '',
    capabilities: [...(props.editingUser.capabilities || ['floor'])],
    branchIds: [...(props.editingUser.branchIds || [])],
})

// Managers and owners cover both counters by rank; there's nothing to choose.
const capabilitiesLocked = computed(() => !!props.editingUser.capabilitiesLocked)

function toggleCapability(area) {
    editForm.capabilities = editForm.capabilities.includes(area)
        ? editForm.capabilities.filter((c) => c !== area)
        : [...editForm.capabilities, area]
}

function toggleBranch(id) {
    const multi = props.editingUser.role === 'manager'
    if (multi) {
        editForm.branchIds = editForm.branchIds.includes(id) ? editForm.branchIds.filter((x) => x !== id) : [...editForm.branchIds, id]
    } else {
        editForm.branchIds = [id]
    }
}

const editValid = computed(() =>
    editForm.username.trim().length > 0 &&
    (editForm.password === '' || editForm.password.length >= 6) &&
    (editForm.password === editForm.confirmPassword) &&
    (capabilitiesLocked.value || editForm.capabilities.length > 0)
)
</script>