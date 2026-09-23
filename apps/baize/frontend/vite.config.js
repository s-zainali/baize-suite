import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import { SourceMap } from 'node:module'

// https://vite.dev/config/
/**
 * Multi-page apps need a dev-server fallback per entry.
 *
 * Vite's dev server rewrites unknown paths to index.html — the staff app.
 * So in dev, /staff/login loaded the customer bundle, whose router has no
 * /staff route and bounced it to the customer home. Production was fine because
 * Flask routes /staff separately; this makes dev behave the same way.
 */
export default defineConfig({
  plugins: [vue(), vueDevTools(), tailwindcss(),     VitePWA({
        registerType: 'autoUpdate',
        injectRegister: 'auto',
        manifest: {
          name: "Baize: Lounge Management System",
          short_name: 'Baize',
          description: 'Lounge Management System',
          theme_color: '#0f172a',
          background_color: '#0f172a',
          display: 'standalone',
          icons: [
            {
              src: '/pwa-192x192.png', // Add these image files to your public/ folder
              sizes: '192x192',
              type: 'image/png'
            },
            {
              src: '/pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png'
            }
          ]
        }
      })
  ],
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['raspberrypi.local', '*'],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    sourcemap: false,
    outDir: '../backend/dist',
    emptyOutDir: true,
    rollupOptions: {
      // Two entries, two bundles.
      //   index.html -> the staff app (the only bundle, served at /)
      input: {
        index: resolve(__dirname, 'index.html'),   // the staff app — the only bundle
      },
    },
  },
})