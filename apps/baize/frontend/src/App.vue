<script setup>
import { RouterView, useRoute } from 'vue-router'
import RouteLoader from './components/RouteLoader.vue'
import LoadingScreen from './pages/LoadingScreen.vue'
import LicenseActivation from './components/LicenseActivation.vue'
import Sidebar from './components/Sidebar.vue'
import PoweredByZain from './components/PoweredByZain.vue'
import { contentOffset } from './composables/useSidebar.js'
import { isLoggedIn } from './Auth.js'
import { progress, ready, label, boot, resetLoader } from './composables/useAppLoader.js'
import { loadBranding, loadLicense, needsActivation, startHeartbeat, status, syncBranchLicenses } from './composables/useLicense.js'
import { loadTableTypes } from './composables/useTableTypes.js'
import { computed, watch, onMounted } from 'vue'


const route = useRoute()

// Branding + license status are public and needed BEFORE staff login: the club
// gate (register/activate) must appear first, so we check on mount, not after login.
onMounted(() => { loadBranding(); loadLicense(); startHeartbeat() })

// Warm settings + floor/canteen data + artwork once we're signed in (including a
// hard refresh with a saved token); re-arm after logout. Refresh license too.
watch(isLoggedIn, (yes) => {
    if (yes) {
        boot(); loadLicense()
        // Pull any feature changes made in admin since this branch was activated,
        // then refresh the type registry so newly-enabled stations appear.
        syncBranchLicenses().then((changed) => { if (changed) loadTableTypes(true) })
    } else { resetLoader() }
}, { immediate: true })

// Hold the app behind the loader until boot finishes (staff side).
// The station-type registry is license-gated on the backend. If boot ran while
// the install was still unlicensed (staff session persisted across the gate),
// that fetch 403'd and every station fell back to the default pool renderer.
// So (re)load it the moment the install is CONFIRMED licensed — force, to
// override a prior empty/blocked load. Keying off a definite "licensed" signal
// (not !needsActivation, which is falsy while status is still null) guarantees
// the false→true transition actually fires once the license resolves.
const clientLicensed = computed(() => {
    const st = status.value
    return !!st && (st.valid || st.enforced === false)
})
watch(clientLicensed, (ok) => { if (ok) loadTableTypes(true) }, { immediate: true })
// The licence poll adopts a re-minted branch token (e.g. a newly-enabled module);
// refresh the type registry when the reported entitlements change so the new
// station types appear without a manual reload.
watch(() => (status.value?.entitlements || []).join(','), () => { if (clientLicensed.value) loadTableTypes(true) })

const booting = computed(() => isLoggedIn.value && !ready.value)

// The license status loads async on mount. Until it resolves we must NOT render
// the app/login — otherwise the gate only appears after status arrives, which
// looked like "needs a reload". Show the loader until the check has resolved.
const licenseChecked = computed(() => status.value !== null)

/** A page-specific message beats a generic spinner for a wait this visible. */
const LOADERS = {
    '/canteen': { icon: '🍟', label: 'Opening the canteen', hint: 'Loading the menu and artwork' },
}
const loaderFor = (path) => LOADERS[path] || { label: 'Loading', hint: 'One moment…' }

/**
 * The sidebar is chrome for signed-in staff. Showing it on the login screen
 * would offer a menu to someone who can't open any of it, and squeeze the
 * login form for no reason.
 */
const showChrome = () => isLoggedIn.value && route.path !== '/login'
const isOverview = computed(() => route.path === '/overview' )

</script>

<template>
    <!-- The club gate comes first: an unactivated install can't be used by staff
         at all, so this precedes the loader and the staff login. -->
    <LicenseActivation v-if="needsActivation" />

    <LoadingScreen v-else-if="!licenseChecked || booting" :progress="progress" :label="label" />

    <div v-else class="min-h-[100dvh]">
        <Sidebar v-if="showChrome()" :isOverview="isOverview" />

        <div class="flex min-h-[100dvh] flex-col transition-[padding] duration-200"
            :class="showChrome() ? contentOffset : ''">
            <div class="flex-1">
                <!-- Routes are lazily loaded, so give the wait something to look at
                     rather than a blank screen staff will tap twice. -->
                <RouterView v-slot="{ Component }">
                    <template v-if="Component">
                        <!-- KeepAlive: once a page is visited it stays mounted, so
                             navigating back to it is instant — no re-mount, no
                             re-fetch, no re-render. Its poller pauses while it's
                             off-screen (see useAutoRefresh) and catches up on return. -->
                            <Suspense timeout="0">
                                <component :is="Component" />
                                <template #fallback>
                                    <RouteLoader v-bind="loaderFor($route.path)" />
                                </template>
                            </Suspense>
                    </template>
                </RouterView>
            </div>
            <PoweredByZain />
        </div>
    </div>
</template>

<style scoped></style>