// Cart and pricing rules for the canteen till.
//
// Kept out of the component because this is the part that must not be wrong:
// a mistake here shows up as a guest being overcharged, or stock being sold
// that isn't on the shelf. Pure functions, so they can be tested directly.

/** `stock: null` means made-to-order — a tea has no shelf count. */
export const isUnlimited = (item) => item.stock === null || item.stock === undefined

export const isOutOfStock = (item) => !isUnlimited(item) && item.stock <= 0

/** True when this line has already claimed every unit on the shelf. */
export const atStockLimit = (line) => !isUnlimited(line) && line.qty >= line.stock

/**
 * Add one unit, returning a NEW cart array.
 * Refuses to go past available stock, and refuses out-of-stock items outright.
 */
export function addItem(cart, item) {
    if (isOutOfStock(item)) return cart
    const existing = cart.find((line) => line.id === item.id)
    if (!existing) return [...cart, { ...item, qty: 1 }]
    if (atStockLimit(existing)) return cart
    return cart.map((line) => (line.id === item.id ? { ...line, qty: line.qty + 1 } : line))
}

/** Nudge a line's quantity; dropping to zero removes it entirely. */
export function changeQty(cart, id, delta) {
    const line = cart.find((l) => l.id === id)
    if (!line) return cart
    if (delta > 0 && atStockLimit(line)) return cart
    const qty = line.qty + delta
    if (qty <= 0) return cart.filter((l) => l.id !== id)
    return cart.map((l) => (l.id === id ? { ...l, qty } : l))
}

export const subtotalOf = (cart) => cart.reduce((sum, line) => sum + line.qty * line.price, 0)

/** Rounded to whole rupees — there are no paisa in practice. */
export const discountOf = (subtotal, percent) =>
    Math.round((subtotal * clampPercent(percent)) / 100)

export const totalOf = (subtotal, percent) => subtotal - discountOf(subtotal, percent)

/** A discount outside 0-100 would produce a negative or inflated bill. */
export function clampPercent(percent) {
    const value = Number(percent) || 0
    return Math.min(Math.max(value, 0), 100)
}

export const itemCountOf = (cart) => cart.reduce((sum, line) => sum + line.qty, 0)

/** Take sold units off the shelf. Returns a new product list. */
export function applyStockSale(products, cart) {
    return products.map((product) => {
        const line = cart.find((l) => l.id === product.id)
        if (!line || isUnlimited(product)) return product
        return { ...product, stock: Math.max(0, product.stock - line.qty) }
    })
}