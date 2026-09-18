import { ref, watch, onUnmounted } from 'vue'

/**
 * A request to open a modal that lives on a page.
 *
 * The sidebar isn't the parent of these modals — they belong to the dashboard
 * and the canteen, with the props and page state they need. So the sidebar
 * doesn't open anything; it raises a request, and whichever page owns that
 * modal answers it.
 *
 * The request clears once handled, so re-clicking the button fires again.
 */
export const modalRequest = ref(null)

export const requestModal = (name) => { modalRequest.value = name }

/**
 * Answer a request from a page.
 *
 *   onModalRequest('rates', () => { activeModal.value = 'rates' })
 */
export function onModalRequest(name, handler) {
    const stop = watch(modalRequest, (requested) => {
        if (requested !== name) return
        modalRequest.value = null       // consume it, so the next click re-fires
        handler()
    })
    onUnmounted(stop)
}