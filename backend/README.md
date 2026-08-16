# Backend — API Entretiens

Découpage en quatre couches (voir `docs/adr/0001-architecture-en-couches.md`) :

```
routers/        contrôleur — routage, codes HTTP     ne connaît pas SQLAlchemy
services/       métier — regles/ pures, processus/   ne connaît pas FastAPI
repositories/   accès aux données — tout le SQL      ne décide de rien
models/         tables SQLAlchemy
```

## État

Seule l'infrastructure est en place : configuration Alembic et tests de
migration. Les fichiers des couches applicatives sont des amorces portant leur
rôle et leur user story — voir `docs/tracabilite.md`.

## Migrations

```bash
alembic revision --autogenerate -m "description"   # puis RELIRE le fichier
alembic upgrade head
alembic downgrade -1
```

L'URL de la base vient de `DATABASE_URL`, jamais de `alembic.ini`.

## Tests

```bash
pytest tests/migrations/test_lignee.py   # sans base, instantané
pytest tests/migrations -m migrations    # exige PostgreSQL
```
