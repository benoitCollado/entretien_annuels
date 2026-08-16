<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useUtilisateursStore } from '@/stores/utilisateurs'

const auth = useAuthStore()
const utilisateurs = useUtilisateursStore()
const router = useRouter()

onMounted(() => utilisateurs.charger())

async function seDeconnecter() {
  auth.deconnexion()
  await router.push({ name: 'connexion' })
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header class="flex items-center gap-4 border-b border-slate-200 bg-white px-6 py-3">
      <span class="font-semibold text-slate-900">Entretiens</span>
      <span class="flex-1" />
      <span v-if="auth.utilisateur" class="text-sm text-slate-600">
        {{ auth.utilisateur.nom_complet }}
        <span class="text-slate-400">({{ auth.roles.join(', ') }})</span>
      </span>
      <button
        type="button"
        class="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        @click="seDeconnecter"
      >
        Déconnexion
      </button>
    </header>

    <main class="mx-auto max-w-5xl p-6">
      <h1 class="mb-4 text-lg font-semibold text-slate-900">Utilisateurs</h1>

      <p v-if="utilisateurs.chargement" class="text-sm text-slate-500">Chargement…</p>
      <p v-else-if="utilisateurs.erreur" role="alert" class="text-sm text-red-600">
        {{ utilisateurs.erreur }}
      </p>

      <template v-else>
        <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table class="w-full text-sm">
            <thead class="border-b border-slate-200 bg-slate-50 text-left text-slate-600">
              <tr>
                <th class="px-4 py-2 font-medium">Nom</th>
                <th class="px-4 py-2 font-medium">Adresse</th>
                <th class="px-4 py-2 font-medium">Service</th>
                <th class="px-4 py-2 font-medium">Rôles</th>
                <th class="px-4 py-2 font-medium">Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="utilisateur in utilisateurs.elements"
                :key="utilisateur.id"
                class="border-b border-slate-100 last:border-0"
              >
                <td class="px-4 py-2 text-slate-900">{{ utilisateur.nom_complet }}</td>
                <td class="px-4 py-2 text-slate-600">{{ utilisateur.email }}</td>
                <td class="px-4 py-2 text-slate-600">{{ utilisateur.service ?? '—' }}</td>
                <td class="px-4 py-2 text-slate-600">
                  {{ utilisateur.roles.map((r) => r.libelle).join(', ') || '—' }}
                </td>
                <td class="px-4 py-2">
                  <span :class="utilisateur.actif ? 'text-emerald-700' : 'text-slate-400'">
                    {{ utilisateur.actif ? 'Actif' : 'Désactivé' }}
                  </span>
                </td>
              </tr>
              <tr v-if="utilisateurs.elements.length === 0">
                <td colspan="5" class="px-4 py-6 text-center text-slate-500">
                  Aucun utilisateur dans votre périmètre.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="mt-3 text-sm text-slate-500">
          {{ utilisateurs.total }} utilisateur(s)
          <!-- Un manager ne voit que son équipe : la restriction est appliquée
               côté serveur, en SQL. -->
        </p>
      </template>
    </main>
  </div>
</template>
