<script setup lang="ts">
import { computed } from 'vue'

import type { StatutEntretien } from '@/types/api'

const props = defineProps<{ statut: StatutEntretien }>()

const LIBELLES: Record<StatutEntretien, string> = {
  BROUILLON: 'Brouillon',
  PLANIFIE: 'Planifié',
  PREPARATION: 'En préparation',
  SOUMIS_COLLABORATEUR: 'Transmis au manager',
  REVUE_MANAGER: 'Revue du manager',
  ENTRETIEN_REALISE: 'Entretien réalisé',
  SIGNE: 'Signé',
  CLOTURE: 'Clôturé',
  ANNULE: 'Annulé',
}

const COULEURS: Record<StatutEntretien, string> = {
  BROUILLON: 'bg-slate-100 text-slate-700',
  PLANIFIE: 'bg-slate-100 text-slate-700',
  PREPARATION: 'bg-blue-100 text-blue-800',
  SOUMIS_COLLABORATEUR: 'bg-indigo-100 text-indigo-800',
  REVUE_MANAGER: 'bg-violet-100 text-violet-800',
  ENTRETIEN_REALISE: 'bg-amber-100 text-amber-800',
  SIGNE: 'bg-emerald-100 text-emerald-800',
  CLOTURE: 'bg-emerald-100 text-emerald-800',
  ANNULE: 'bg-red-100 text-red-800',
}

const libelle = computed(() => LIBELLES[props.statut] ?? props.statut)
const couleur = computed(() => COULEURS[props.statut] ?? 'bg-slate-100 text-slate-700')
</script>

<template>
  <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="couleur">
    {{ libelle }}
  </span>
</template>
