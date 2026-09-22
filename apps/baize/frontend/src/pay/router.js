import { createRouter, createWebHistory } from 'vue-router'
import PayPage from './pages/PayPage.vue'

// This bundle exists only to serve the venue's QR payment page. It carries no
// booking/auth pages (those live in the separate customer app).
const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        { path: '/pay/:token', component: PayPage, meta: { public: true } },
        { path: '/:pathMatch(.*)*', redirect: () => '/pay/missing' },
    ],
})

export default router