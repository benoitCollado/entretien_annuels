## Objectif

<!-- Que fait cette PR et pourquoi ? Lier l'US ou l'issue. -->

US concernée :

## Changements

-

## Couches touchées

- [ ] `models/` — tables SQLAlchemy
- [ ] `schemas/` — ce qui est exposé, et ce qui ne l'est pas
- [ ] `repositories/` — requêtes SQL
- [ ] `services/regles/` — règles pures
- [ ] `services/processus/` — orchestration
- [ ] `routers/` — HTTP
- [ ] `frontend/`
- [ ] Infrastructure, CI/CD, documentation

## Vérifications

- [ ] `make check` passe localement
- [ ] Les règles de couche sont respectées : aucun SQLAlchemy dans un router,
      aucun FastAPI dans un service, aucune décision métier dans un repository
- [ ] Migration ajoutée si le schéma change, **et relue ligne à ligne**
      (`--autogenerate` ne détecte ni les CHECK ni les renommages)
- [ ] `downgrade()` défait réellement `upgrade()`
- [ ] ADR ajoutée si une décision d'architecture a été prise
- [ ] Aucun secret committé

## Comment tester

1.
