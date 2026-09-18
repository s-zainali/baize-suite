import { createRouter, createWebHistory } from 'vue-router'
import AdminLogin from '../pages/AdminLogin.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import ClubDetailPage from '../pages/ClubDetailPage.vue'
import LicensesPage from '../pages/LicensesPage.vue'
import AuditPage from '../pages/AuditPage.vue'

const router = createRouter({
  history: createWebHistory('/admin'),
  routes: [
    { path: '/login', component: AdminLogin },
    { path: '/dashboard', component: DashboardPage },
    { path: '/club/:uuid', component: ClubDetailPage },
    { path: '/licenses', component: LicensesPage },
    { path: '/audit', component: AuditPage },
    { path: '/', redirect: '/dashboard' },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('admin_token')
  if (!token && to.path !== '/login') return '/login'
  if (token && to.path === '/login') return '/dashboard'
  return true
})

export default router