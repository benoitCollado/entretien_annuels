.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_REF := docker compose -f compose.yml
COMPOSE_PROD := docker compose -f compose.yml -f compose.prod.yml
PY := backend/.venv/bin/python

.PHONY: help
help: ## Affiche cette aide
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Conteneurs -----------------------------------------------------------
.PHONY: up
up: ## Démarre la stack en développement (référence + surcharge dev)
	$(COMPOSE) up -d --build

.PHONY: infra
infra: ## Démarre uniquement PostgreSQL et Redis
	$(COMPOSE) up -d db redis

.PHONY: down
down: ## Arrête la stack
	$(COMPOSE) down

.PHONY: reset
reset: ## Arrête tout et supprime le volume PostgreSQL
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Suit les logs de l'API
	$(COMPOSE) logs -f api

.PHONY: ps
ps: ## État des conteneurs
	$(COMPOSE) ps

.PHONY: config
config: ## Valide et affiche la configuration Compose résolue
	$(COMPOSE_REF) config -q && echo "compose.yml            OK"
	$(COMPOSE) config -q      && echo "compose.yml + override OK"

# --- Backend --------------------------------------------------------------
.PHONY: install-back
install-back: ## Crée le venv et installe les dépendances Python
	python3 -m venv backend/.venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e "backend[dev]"

.PHONY: migrate
migrate: ## Applique les migrations (service one-shot dédié)
	$(COMPOSE) run --rm migrate

.PHONY: revision
revision: ## Crée une migration : make revision m="description"
	$(COMPOSE) run --rm migrate alembic revision --autogenerate -m "$(m)"
	@echo "⚠️  RELIRE la migration : --autogenerate ne détecte ni les CHECK ni les renommages."

.PHONY: test-back
test-back: ## Tests backend ne nécessitant aucun service
	cd backend && .venv/bin/python -m pytest -m "not migrations and not integration"

.PHONY: test-migrations
test-migrations: ## Tests de migration (exige PostgreSQL démarré)
	cd backend && DATABASE_ADMIN_URL=postgresql://$${POSTGRES_USER:-entretiens}:$${POSTGRES_PASSWORD}@localhost:$${PORT_DB:-5432}/postgres \
		.venv/bin/python -m pytest tests/migrations -v

.PHONY: lint-back
lint-back: ## Lint backend
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

.PHONY: format-back
format-back: ## Formate le backend
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check . --fix

# --- Frontend -------------------------------------------------------------
.PHONY: install-front
install-front: ## Installe les dépendances npm
	cd frontend && npm install

.PHONY: lint-front
lint-front: ## Lint et vérification des types
	cd frontend && npm run lint && npm run type-check

.PHONY: test-front
test-front: ## Tests frontend
	cd frontend && npm run test

# --- Transverse -----------------------------------------------------------
.PHONY: install
install: install-back install-front ## Installe tout

.PHONY: check
check: lint-back test-back lint-front test-front ## Exactement ce que la CI exécute hors services
	@echo "✔ Portes qualité franchies. Les tests de migration exigent PostgreSQL : make infra puis make test-migrations."
