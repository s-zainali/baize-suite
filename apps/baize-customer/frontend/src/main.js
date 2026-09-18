import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import './style.css'
import { configureTableTypes, loadTableTypes } from '@baize/ui'
import { apiGet } from './auth.js'

// Feed the shared table-type registry from THIS app's API (no auth coupling in @baize/ui).
configureTableTypes({ fetchTypes: () => apiGet('/table-types') })
loadTableTypes()

createApp(App).use(router).mount('#app')