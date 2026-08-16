<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-slate-50 p-6">
    <div class="max-w-md space-y-3 text-center">
      <h1 class="text-xl font-semibold text-slate-900">403 — Accès refusé</h1>
      <p class="text-sm text-slate-600">
        Votre compte ne dispose pas des permissions nécessaires pour cette page.
      </p>
      <RouterLink to="/" class="inline-block text-sm text-slate-900 underline">
        Retour à l'accueil
      </RouterLink>
    </div>
  </main>
</template>
