<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md md:pl-[var(--modal-inset,1rem)]"
        @click.self="emit('close-modal')">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-md rounded-3xl p-6 shadow-2xl">

            <!-- Header -->
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-black text-white">CREATE NEW USER</h2>
                <button @click="emit('close-modal')"
                    class="text-slate-500 hover:text-white hover:cursor-pointer">✕</button>
            </div>

            <!-- Fields -->
            <div class="space-y-4 mb-6">

                <!-- Username -->
                <TextField :form="form" :field="'username'" :label="'Username'"
                    :placeholder="'e.g. receptionist1'" :id="'new-user-username'" :type="'text'" />

                <!-- Password -->
                <PasswordField :form="form" :id="'new-user-password'" :field="'password'" :placeholder="'•••••••• (min 6 characters)'" :label="'Password'" :error="{condition: form.password.length < 6 && form.password.length !== 0, message: 'Passwords must be at least 6 characters'}"/>

                <PasswordField :form="form" :id="'new-user-confirm'" :field="'confirmPassword'" :placeholder="'••••••••'" :label="'Confirm Password'" :error="{condition: form.confirmPassword !== form.password && form.password.length > 0, message: 'Passwords do not match'}"/>

                <!-- Role -->
                <DropdownField :form="form" :field="'role'" :label="'Role'" :options="roles" :placeholder="'Select User Role'"/>

                <!-- Counters. Managers and owners cover both by rank, so there
                     is nothing to choose for them. -->
                <div v-if="form.role === 'receptionist'">
                    <span class="block text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1.5">
                        Can Work
                    </span>
                    <div class="grid grid-cols-2 gap-2">
                        <button v-for="area in ALL_CAPABILITIES" :key="area" type="button"
                            @click="toggleCapability(area)"
                            class="rounded-xl border px-3 py-2.5 text-xs font-bold cursor-pointer transition-colors"
                            :class="form.capabilities.includes(area)
                                ? 'border-emerald-500/50 bg-emerald-600/15 text-emerald-300'
                                : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600'">
                            {{ form.capabilities.includes(area) ? '✓ ' : '' }}{{ capabilityLabel(area) }}
                        </button>
                    </div>
                    <p class="mt-1.5 text-[9px] leading-snug text-slate-600">
                        Pick one or both. They'll only see the pages they can work.
                    </p>
                </div>

                <p v-else-if="form.role" class="text-[10px] leading-snug text-slate-500">
                    {{ roleLabel(form.role) }}s can work both the dashboard and the canteen.
                </p>

                <!-- Branch assignment: employees single, managers multi. Hidden
                     when there's only one branch (auto-assigned to it). -->
                <div v-if="branches.length > 1 && (form.role === 'receptionist' || form.role === 'manager')">
                    <span class="block text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1.5">
                        {{ form.role === 'manager' ? 'Branches' : 'Branch' }}
                    </span>
                    <div class="grid grid-cols-2 gap-2">
                        <button v-for="b in branches" :key="b.id" type="button" @click="toggleBranch(b.id)"
                            class="rounded-xl border px-3 py-2.5 text-xs font-bold cursor-pointer transition-colors"
                            :class="form.branchIds.includes(b.id)
                                ? 'border-emerald-500/50 bg-emerald-600/15 text-emerald-300'
                                : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600'">
                            {{ form.branchIds.includes(b.id) ? '✓ ' : '' }}{{ b.name }}
                        </button>
                    </div>
                    <p class="mt-1.5 text-[9px] leading-snug text-slate-600">
                        {{ form.role === 'manager' ? 'Every branch this manager oversees.' : 'A receptionist works one branch.' }}
                    </p>
                </div>


                <!-- Error -->
                <p v-if="props.error"
                    class="text-[10px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 uppercase tracking-wide">
                    {{ error }}
                </p>

                <button class="text-[10px] text-slate-400 font-bold uppercase tracking-widest cursor-pointer"
                    @click="emit('close-modal')">← Back to users list</button>
            </div>

            <!-- Submit -->
            <button @click="emit('submit', {isValid: isValid, form: form, })" :disabled="loading || !isValid"
                class="w-full py-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all cursor-pointer">
                {{ loading ? 'CREATING…' : 'CREATE USER' }}
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue';
import TextField from '../Fields/TextField.vue';
import PasswordField from '../Fields/PasswordField.vue';
import DropdownField from '../Fields/DropdownField.vue';
const props = defineProps({
    error: String,
    loading: Boolean,

})
import { ALL_CAPABILITIES, capabilityLabel, roleLabel } from '@/Auth.js'
import { branches, loadBranches } from '@/composables/useBranch.js'
import { onMounted } from 'vue'
onMounted(loadBranches)

const roles = [
    { value: 'receptionist', label: 'Receptionist' },
    { value: 'manager', label: 'Manager' },
    { value: 'owner', label: 'Owner' },
]

const isValid = computed(() =>
    form.username.trim().length > 0 &&
    form.password.length >= 6 &&
    form.password === form.confirmPassword &&
    roles.some(role => role.value === form.role) &&
    // A receptionist with no counter could sign in and find every page shut.
    (form.role !== 'receptionist' || form.capabilities.length > 0)
)

const form = reactive({
    username: '',
    password: '',
    confirmPassword: '',
    role: '',
    capabilities: ['floor'],
    branchIds: [],
})

function toggleBranch(id) {
    if (form.role === 'manager') {
        form.branchIds = form.branchIds.includes(id) ? form.branchIds.filter((x) => x !== id) : [...form.branchIds, id]
    } else {
        form.branchIds = [id]   // employees are single-branch
    }
}

function toggleCapability(area) {
    form.capabilities = form.capabilities.includes(area)
        ? form.capabilities.filter((c) => c !== area)
        : [...form.capabilities, area]
}

const emit = defineEmits(['close-modal', 'submit'])

const dropdownOpen = ref(false)


function selectRole(role) {
    form.role = role
    dropdownOpen.value = false
}


</script>