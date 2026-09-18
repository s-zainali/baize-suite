// Canteen API client (staff surface — uses the staff authFetch).
//
// The server owns prices, discounts, totals and stock. This module only sends
// product ids and quantities and renders what comes back, so there is no second
// copy of the pricing rules to drift out of step.

import { authFetch, API_URL } from '@/Auth.js'

async function request(path, options = {}) {
    const res = await authFetch(`${API_URL}/canteen${path}`, options)
    const text = await res.text()
    let data = {}
    try {
        data = text ? JSON.parse(text) : {}
    } catch {
        throw new Error(
            res.status === 404
                ? `Endpoint /canteen${path} not found — is the backend running the canteen blueprint?`
                : `Server returned ${res.status}`,
        )
    }
    if (!res.ok) throw Object.assign(new Error(data.error || `Request failed (${res.status})`), {
        status: res.status,
        productId: data.productId,
    })
    return data
}

const json = (body) => ({
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
})

export const fetchMenu = () => request('/products')
export const fetchOrders = () => request('/orders')
export const fetchOrder = (orderId) => request(`/orders/${orderId}`)

export const placeOrder = ({ items, discountPercent, method, target, tableUid }) =>
    request('/orders', { method: 'POST', ...json({ items, discountPercent, method, target, tableUid }) })

export const createProduct = (product) =>
    request('/products', { method: 'POST', ...json(product) })

export const updateProduct = (id, changes) =>
    request(`/products/${id}`, { method: 'PATCH', ...json(changes) })

export const deleteProduct = (id) => request(`/products/${id}`, { method: 'DELETE' })

export const voidOrder = (id) => request(`/orders/${id}/void`, { method: 'POST' })

/** Mark a counter sale paid, or put it on a khata. */
export const settleOrder = (id, body) =>
    request(`/orders/${id}/settle`, { method: 'POST', ...json(body) })

/** Settlement state of one order — polled while its receipt is open. */
export const orderStatus = (id) => request(`/orders/${id}/status`)