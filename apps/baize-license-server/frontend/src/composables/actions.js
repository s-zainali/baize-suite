import { useToast } from './useToast.js'

const toast = useToast()

export async function copy(text, label = 'Copied') {
  try { await navigator.clipboard.writeText(text); toast.success(`${label} copied`) }
  catch { toast.error('Copy failed — select it manually') }
}

export function downloadKey(token, name) {
  const blob = new Blob([token], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${name}.key`; a.click()
  URL.revokeObjectURL(url)
}

export function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })
}

export function fmtDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleString([], { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}