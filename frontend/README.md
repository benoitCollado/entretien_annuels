# Frontend — Vue 3 + TypeScript

## État

Seul l'outillage est en place : Vite, TypeScript, ESLint, vue-tsc et Vitest.
Aucun écran, aucun composant. L'arborescence `src/` matérialise le découpage
attendu.

## Règle d'organisation

**Les stores Pinia n'appellent jamais `fetch` directement.** La couche
`src/api/` isole les appels HTTP ; les stores ne portent que l'état et les
actions. C'est ce qui les rend testables avec des appels simulés.

Les types de `src/types/` seront **générés depuis l'OpenAPI** de FastAPI
(`openapi-typescript`) : un seul contrat, aucune dérive entre le front et le
back.

## Commandes

```bash
npm install
npm run lint         # eslint
npm run type-check   # vue-tsc
npm run test         # vitest
npm run dev          # http://localhost:5173, /api proxifié vers le backend
```
