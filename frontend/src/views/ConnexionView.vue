<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ErreurHttp } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const motDePasse = ref('')
const erreur = ref<string | null>(null)

async function soumettre() {
  erreur.value = null
  try {
    await auth.connexion(email.value, motDePasse.value)
    const redirection = (route.query.redirection as string) || '/'
    await router.push(redirection)
  } catch (e) {
    // Le message vient de l'API et reste volontairement identique que
    // l'adresse existe ou non (§7.3).
    erreur.value = e instanceof ErreurHttp ? e.message : 'Connexion impossible. Réessayez.'
  }
}
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-slate-50 p-6">
    <form
      class="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-8 shadow-sm"
      @submit.prevent="soumettre"
    >
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Connexion</h1>
        <p class="mt-1 text-sm text-slate-500">Gestion des entretiens</p>
      </div>

      <div class="space-y-1">
        <label for="email" class="block text-sm font-medium text-slate-700">
          Adresse professionnelle
        </label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="username"
          required
          class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
        />
      </div>

      <div class="space-y-1">
        <label for="mot-de-passe" class="block text-sm font-medium text-slate-700">
          Mot de passe
        </label>
        <input
          id="mot-de-passe"
          v-model="motDePasse"
          type="password"
          autocomplete="current-password"
          required
          class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
        />
      </div>

      <p v-if="erreur" role="alert" class="text-sm text-red-600">{{ erreur }}</p>

      <button
        type="submit"
        :disabled="auth.chargement"
        class="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {{ auth.chargement ? 'Connexion…' : 'Se connecter' }}
      </button>
    </form>
  </main>
</template>
