import { hasFeature } from '@/composables/useLicense.js'
import { createRouter, createWebHistory } from 'vue-router'
import PoolHallDashboard from '../pages/PoolHallDashboard.vue'
import OverviewPage from '../pages/OverviewPage.vue'
import CanteenPage from '../pages/CanteenPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ActiveBillsPage from '../pages/ActiveBillsPage.vue'
import LogsPage from '../pages/LogsPage.vue'
import InsightsPage from '../pages/InsightsPage.vue'
import ManageLicensePage from '@/pages/ManageLicensePage.vue'
import { auth, isLoggedIn } from '../Auth.js'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/login',
      component: LoginPage,
    },
    {
      path: '/dashboard',
      component: PoolHallDashboard,
    },
    {
      path: '/overview',
      component: OverviewPage,
      meta: { roles: ['owner'] },
    },
    {
      path: '/active-bills',
      component: ActiveBillsPage,
    },
    {
      path: '/canteen',
      component: CanteenPage,
      meta: { feature: 'canteen' },
    },
    // '/' is just a role-aware redirect, not a page
    {
      path: '/',
      redirect: () => (auth.role === 'owner' ? '/overview' : auth.capabilities.includes('floor')? '/dashboard' : '/canteen'),
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
    {
      path: '/logs',
      component: LogsPage,
      meta: { capability: 'floor' },
    },
    {
      path: '/insights',
      component: InsightsPage,
      meta: { capability: 'floor', feature: 'insights' },
    },
    {
        path: '/manage',
        component : ManageLicensePage,
        meta: { roles: ['owner'] },
    }
  ],
})

router.beforeEach((to) => {
  // not logged in → only /login is allowed
  if (!isLoggedIn.value) {
    return to.path === '/login' ? true : '/login'
  }
  // logged in and heading to /login → send to their home
  if (to.path === '/login') {
    return auth.role === 'owner' ? '/overview' : auth.capabilities.includes('floor')? '/dashboard' : '/canteen'
  }
  // role-gated route they can't access → send to their home
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return auth.role === 'owner' ? '/overview' : auth.capabilities.includes('floor')? '/dashboard' : '/canteen'
  }
  // feature-gated route the club isn't licensed for → send home (backend also 403s it)
  if (to.meta.feature && !hasFeature(to.meta.feature)) {
    return auth.role === 'owner' ? '/overview' : auth.capabilities.includes('floor')? '/dashboard' : '/canteen'
  }
  return true
})

router.afterEach((to) => {
  const colors = {
    '/dashboard': '#1e293b',
    '/booking': '#1e293b',
    '/login': '#1e293b',
    '/overview': '#262626',
    '/canteen': '#1e293b',
  }
  const activateColor = colors[to.path] || '#1e293b'

  let metaThemeColor = document.querySelector('meta[name=theme-color]')
  if (!metaThemeColor) {
    metaThemeColor = document.createElement('meta')
    metaThemeColor.setAttribute('name', 'theme-color')
    document.head.appendChild(metaThemeColor)
  }
  metaThemeColor.setAttribute('content', activateColor)
})

export default router