import { createRouter, createWebHistory } from 'vue-router'
import { isSignedIn } from '../auth.js'
import AuthPage from '../pages/AuthPage.vue'
import HomePage from '../pages/HomePage.vue'
import BookingPage from '../pages/BookingPage.vue'
import PayPage from '../pages/PayPage.vue'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        { 
            path: '/', 
            component: AuthPage,
            meta: { 
                guestOnly: true,
                themeColor: '#020618', // Dark slate top bar for dashboard
                statusBarStyle: 'black-translucent'
            } },
        { 
            path: '/home', 
            component: HomePage, 
            meta: { 
                requiresCustomer: true,
                themeColor: '#0f172a', // Dark slate top bar for dashboard
                statusBarStyle: 'black-translucent'
            } },
        { 
            path: '/booking', 
            component: BookingPage, 
            meta: { 
                requiresCustomer: true,
                themeColor: '#0f172a', // Dark slate top bar for dashboard
                statusBarStyle: 'black-translucent'
            } },
        // Public: whoever scans the QR is at the counter, and forcing a
        // sign-in would make paying harder than not paying.
        { path: '/pay/:token', component: PayPage, meta: { public: true } },
        { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
})

router.beforeEach((to) => {
    if (to.meta.public) return true
    if (to.meta.requiresCustomer && !isSignedIn.value) return '/'
    if (to.meta.guestOnly && isSignedIn.value) return '/home'
    return true
})

export default router