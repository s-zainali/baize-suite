import { reactive } from 'vue'

const toasts = reactive([])
let seq = 0

export function useToast() {
  function push(message, type = 'info', ms = 3800) {
    const id = ++seq
    toasts.push({ id, message, type })
    if (ms) setTimeout(() => remove(id), ms)
    return id
  }
  function remove(id) {
    const i = toasts.findIndex((t) => t.id === id)
    if (i >= 0) toasts.splice(i, 1)
  }
  return {
    toasts, push, remove,
    success: (m) => push(m, 'success'),
    error: (m) => push(m, 'error', 5000),
    info: (m) => push(m, 'info'),
  }
}