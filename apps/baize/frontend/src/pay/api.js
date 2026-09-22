// Customer API client. Thin on purpose — validation and policy live on the
// server; this only shapes requests and hands back what the UI renders.

import { apiPost, setSession } from './auth.js'

export async function signUp({ name, phone, email, password }) {
    const data = await apiPost('/register', { name, phone, email, password })
    setSession(data.token, data.customer)
    return data
}

export async function signIn({ phone, password }) {
    const data = await apiPost('/login', { phone, password })
    setSession(data.token, data.customer)
    return data
}

/** Always resolves — the server answers identically whether or not the
 *  account exists, and the UI must not behave differently either. */
export const requestReset = ({ phone }) => apiPost('/password/forgot', { phone })

export const verifyCode = ({ phone, code }) => apiPost('/password/verify', { phone, code })

export const resetPassword = ({ resetToken, password }) =>
    apiPost('/password/reset', { resetToken, password })