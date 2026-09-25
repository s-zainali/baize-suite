import { createRouter, createWebHistory } from 'vue-router'
import { isSignedIn } from '../auth.js'
import AuthPage from '../pages/AuthPage.vue'
import HomePage from '../pages/HomePage.vue'
import BookingPage from '../pages/BookingPage.vue'
import PayPage from '../pages/PayPage.vue'

// Shared meta for the three customer areas — same dark top bar as before.
const customerMeta = {
    requiresCustomer: true,
    themeColor: '#0f172a', // Dark slate top bar for dashboard
    statusBarStyle: 'black-translucent',
}

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {
            path: '/',
            component: AuthPage,
            meta: {
                guestOnly: true,
                themeColor: '#020618', // Dark slate top bar for dashboard
                statusBarStyle: 'black-translucent',
            },
        },
        // The three logical areas are distinct routes but share one HomePage
        // container (shared state + polling); the tab is derived from the path.
        { path: '/dashboard', component: HomePage, meta: { ...customerMeta } },
        { path: '/clubs', component: HomePage, meta: { ...customerMeta } },
        { path: '/friends', component: HomePage, meta: { ...customerMeta } },
        { path: '/home', redirect: '/dashboard' },
        {
            path: '/booking',
            component: BookingPage,
            meta: { ...customerMeta },
        },
        // Public: whoever scans the QR is at the counter, and forcing a
        // sign-in would make paying harder than not paying.
        { path: '/pay/:token', component: PayPage, meta: { public: true } },
        { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
})

router.beforeEach((to) => {
    if (to.meta.public) return true
    if (to.meta.requiresCustomer && !isSignedIn.value) return '/'
    if (to.meta.guestOnly && isSignedIn.value) return '/dashboard'
    return true
})

export default router