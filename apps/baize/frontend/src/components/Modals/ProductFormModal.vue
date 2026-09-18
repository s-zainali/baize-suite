<template>
    <div class="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm md:pl-[var(--modal-inset,1rem)]"
        @click.self="close">
        <div class="w-full max-w-sm rounded-3xl border border-slate-800 bg-slate-900 p-5">

            <h2 class="mb-4 text-sm font-black text-white">{{ isEdit ? 'Edit Item' : 'New Item' }}</h2>

            <div class="space-y-3">
                <!-- Picture and name together. The thumbnail sits where the
                     emoji box used to: it's the same job — telling the item
                     apart on a crowded menu — done with the real photo the
                     staff will actually see on the tile. -->
                <div class="flex gap-3 items-center">
                    <button type="button" @click="pickFile" :title="preview ? 'Change picture' : 'Add a picture'"
                        class="group relative h-[4.5rem] w-[4.5rem] shrink-0 cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-950 transition-colors hover:border-slate-600">
                        <img v-if="preview" :src="preview" alt=""
                            class="h-full w-full object-contain p-1.5" />
                        <span v-else class="flex h-full w-full flex-col items-center justify-center gap-1 text-slate-600">
                            <span class="text-xl leading-none">🍽</span>
                            <span class="text-[8px] font-black uppercase tracking-widest">Photo</span>
                        </span>
                        <span
                            class="absolute inset-x-0 bottom-0 bg-slate-950/85 py-0.5 text-center text-[8px] font-black uppercase tracking-widest text-slate-300 opacity-0 transition-opacity group-hover:opacity-100">
                            {{ preview ? 'Change' : 'Add' }}
                        </span>
                    </button>

                    <div class="flex min-w-0 flex-1 flex-col justify-center">
                        <TextField :form="form" :field="'name'" :label="'Item Name'"
                            :placeholder="'Enter item name'" :type="'text'" />
                        <button v-if="preview" type="button" @click="clearImage"
                            class="mt-1.5 self-start cursor-pointer text-[9px] font-bold text-slate-500 hover:text-rose-400">
                            Remove picture
                        </button>
                    </div>
                </div>

                <!-- Hidden: the thumbnail above is the control. A bare file
                     input reads as a form field of its own and pushed the
                     layout around. -->
                <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelect" />

                <DropdownField :form="form" :field="'category'" :label="'Category'" :options="categories"
                    :icons="true" :placeholder="'Choose item category'" />

                <div class="grid grid-cols-2 gap-2">
                    <StepperField v-model="form.price" label="Price" suffix="Rs" :step-by="10" accent="emerald" />
                    <!-- nullable: an empty box means made-to-order, which a
                         plain stepper can't express — it always produces a
                         number, so "leave blank" would be impossible. -->
                    <StepperField v-model="form.stock" label="Stock" placeholder="∞" nullable accent="slate" />
                </div>

                <p class="text-[9px] leading-relaxed text-slate-600">
                    Clear the stock box for made-to-order items that never run out.
                </p>

                <p v-if="error" class="text-[10px] font-bold text-rose-400">{{ error }}</p>
            </div>

            <div class="mt-5 flex gap-2">
                <button v-if="isEdit" @click="emit('delete')"
                    class="cursor-pointer rounded-xl border border-slate-800 px-3 py-2.5 text-[10px] font-black tracking-widest text-rose-400 uppercase hover:border-rose-800">
                    Delete
                </button>
                <button @click="close"
                    class="flex-1 cursor-pointer rounded-xl bg-slate-800 py-2.5 text-[10px] font-black tracking-widest text-slate-300 uppercase">
                    Cancel
                </button>
                <button @click="emit('save', { form, file: selectedFile })" :disabled="saving || !canSave"
                    class="flex-1 cursor-pointer rounded-xl bg-emerald-600 py-2.5 text-[10px] font-black tracking-widest text-white uppercase hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500">
                    {{ saving ? 'Saving…' : 'Save' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
/**
 * Add or edit a canteen item.
 *
 * Lifted out of CanteenPage, which was carrying this dialog's markup, its file
 * handling and its own 700 lines of till. The page still owns saving — it has
 * the API client and the refresh — so this stays a form, not a controller.
 */
import { ref, computed, onUnmounted } from 'vue'
import TextField from '../Fields/TextField.vue'
import DropdownField from '../Fields/DropdownField.vue'
import StepperField from '../Fields/StepperField.vue'

const props = defineProps({
    /** The item being edited, or a blank one for a new item. */
    form: { type: Object, required: true },
    categories: { type: Array, default: () => [] },
    saving: { type: Boolean, default: false },
    error: { type: String, default: '' },
})

const emit = defineEmits(['save', 'delete', 'close-modal'])

const fileInput = ref(null)
const selectedFile = ref(null)
const localPreview = ref(null)

const isEdit = computed(() => !!props.form.id)

/** The chosen file if there is one, otherwise whatever the item already had. */
const preview = computed(() => localPreview.value || props.form.imgUrl || '')

const canSave = computed(() =>
    !!String(props.form.name || '').trim() && Number(props.form.price) > 0,
)

const pickFile = () => fileInput.value?.click()

function onFileSelect(event) {
    const file = event.target.files?.[0]
    if (!file) return
    revoke()
    selectedFile.value = file
    localPreview.value = URL.createObjectURL(file)
}

function clearImage() {
    revoke()
    selectedFile.value = null
    localPreview.value = null
    props.form.imgUrl = ''
    if (fileInput.value) fileInput.value.value = ''
}

/** Object URLs are held until revoked; without this each pick leaks one. */
function revoke() {
    if (localPreview.value) URL.revokeObjectURL(localPreview.value)
}

function close() {
    revoke()
    emit('close-modal')
}

onUnmounted(revoke)
</script>