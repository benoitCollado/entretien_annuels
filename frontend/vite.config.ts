import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
        // L'API expose /auth/login, pas /api/auth/login : le préfixe est une
        // convention de routage du front, pas une partie du contrat.
        // nginx fait la même réécriture en production grâce au slash final de
        // `proxy_pass http://api:8000/` ; Vite, lui, ne l'implique pas.
        rewrite: (chemin) => chemin.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.spec.ts', 'tests/**/*.spec.ts'],
    coverage: {
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{ts,vue}'],
    },
  },
})
