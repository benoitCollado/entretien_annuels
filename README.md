# Plateforme de gestion des entretiens annuels et professionnels

Projet CDA · FastAPI synchrone · Vue 3 · PostgreSQL 16 · Redis · Docker

## État du dépôt

**Socle + épopée A** (authentification et administration des comptes).

| Implémenté | À venir |
|---|---|
| Socle : arborescence, Compose, CI/CD, tests de migration | Épopée B — trames et campagnes (US-03 à US-05) |
| **US-01** — connexion argon2id + JWT, révocation par `version_jeton` | Épopée C — conduite de l'entretien (US-06 à US-14) |
| **US-02** — CRUD comptes, rôles, hiérarchie, RBAC et portée | Épopée D — restitution (US-15, US-16) |
| Front : écran de connexion et liste des utilisateurs | Écrans des lots suivants |

113 tests backend (42 unitaires · 12 migrations · 25 intégration · 34 API) et
16 tests frontend.

## Démarrage

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # → SECRET_KEY

make up             # db, redis, migrate, api, web
make seed           # comptes de démonstration
```

| Service | URL |
|---|---|
| Front (Vite, rechargement à chaud) | http://localhost:5173 |
| API — documentation interactive | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` |

**Comptes de démonstration** — mot de passe commun `MotDePasseDemo2026!` :

| Adresse | Rôle | Ce qu'il voit |
|---|---|---|
| `admin@example.com` | ADMIN | tous les utilisateurs, toutes les actions |
| `rh@example.com` | RH | tous les utilisateurs, sauf archivage |
| `manager@example.com` | MANAGER | **son équipe seulement** |
| `collaborateur@example.com` | COLLABORATEUR | 403 sur la liste |

Le contraste entre ces quatre comptes est le scénario de démonstration du
§6.4 : il montre en une minute la différence entre RBAC et contrôle de portée.

### Sans Docker

```bash
make infra          # PostgreSQL + Redis seuls
make install        # venv Python + npm install
make check          # lint et tests, exactement ce que la CI exécute
```

## Architecture

```
routers/        contrôleur — routage, auth, codes HTTP    ne connaît pas SQLAlchemy
services/
  ├── regles/   règles pures — aucune entrée-sortie       ne reçoit pas de session
  └── processus/ orchestration — un fichier par cas d'usage  ne connaît pas FastAPI
repositories/   accès aux données — tout le SQL           ne décide de rien
models/         tables SQLAlchemy
```

Test de relecture rapide : `from sqlalchemy` dans un router ou `from fastapi`
dans un service signale une couche percée.

La correspondance user story → processus → endpoint est tenue dans
[docs/tracabilite.md](docs/tracabilite.md).

## Conteneurs

Trois fichiers Compose :

| Commande | Fichiers chargés |
|---|---|
| `docker compose up` | référence **+ `compose.override.yml` automatiquement** |
| `docker compose -f compose.yml up` | référence seule |
| `docker compose -f compose.yml -f compose.prod.yml up -d --no-build` | production |

Deux points structurants :

- **Les migrations tournent dans un service `migrate` dédié**, jamais dans
  l'entrypoint de l'API. Avec deux réplicas, deux migrations concurrentes
  produiraient un crash-loop illisible. `api` attend
  `condition: service_completed_successfully`.
- **Deux réseaux**, dont `backend` en `internal: true`. PostgreSQL et Redis ne
  sont publiés sur l'hôte que par la surcharge de développement.

## Tests de migration

Harnais **générique** : il ne connaît rien du schéma et devient plus exigeant à
mesure que des révisions apparaissent.

| Test | Vérifie | Base requise |
|---|---|---|
| `test_configuration_alembic_est_lisible` | `alembic.ini` et `env.py` cohérents | non |
| `test_au_plus_une_tete` | pas de branche divergente après une fusion | non |
| `test_chaine_sans_trou` | une seule racine, aucune parente manquante | non |
| `test_chaque_migration_a_un_downgrade_effectif` | `downgrade()` n'est pas un `pass` | non |
| `test_nommage_des_fichiers` | gabarit `AAAAMMJJ_<rev>_<slug>.py` | non |
| `test_upgrade_depuis_base_vierge` | s'applique sur une base neuve | oui |
| `test_upgrade_est_idempotent` | rejouer `migrate` ne casse rien | oui |
| `test_reversibilite_globale` | descente complète puis remontée, schéma identique | oui |
| `test_reversibilite_pas_a_pas` | chaque révision réversible isolément | oui |
| `test_aucune_derive_entre_modeles_et_migrations` | modèles ≡ schéma migré | oui |

Chaque test qui touche la base obtient une **base jetable** créée puis détruite
pour l'occasion.

```bash
make infra && make test-migrations
```

## CI/CD

| Workflow | Déclencheur | Contenu |
|---|---|---|
| `ci.yml` | pull request, appel depuis `cd.yml` | lint back/front, tests unitaires, **job dédié aux migrations**, intégration, tests front, audit des dépendances |
| `cd.yml` | push sur `main` / `develop` | build GHCR tagué par SHA, Trivy, déploiement staging puis production |
| `security.yml` | hebdomadaire | `pip-audit`, `npm audit`, Trivy sur le dépôt |

`ci.yml` ne déclare que `contents: read` et n'utilise aucun secret : une pull
request issue d'un fork ne peut donc ni publier une image ni déclencher un
déploiement.

**À configurer côté GitHub avant que `cd.yml` ne serve** : les environnements
`staging` et `production`, et les secrets `SSH_PRIVATE_KEY`, `DEPLOY_HOST`,
`DEPLOY_USER`, `DEPLOY_PATH`. L'approbation manuelle de la production repose
sur les *required reviewers* d'environnement, disponibles sur dépôt public ou
sur un plan Team/Enterprise.
