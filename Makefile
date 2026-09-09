.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_REF := docker compose -f compose.yml
COMPOSE_PROD := docker compose -f compose.yml -f compose.prod.yml
PY := backend/.venv/bin/python
ENV_FICHIER := $(CURDIR)/.env

# Arguments supplémentaires passés à pytest ou vitest :
#   make test-back ARGS="-k auth -v"
ARGS ?=

# Charge .env dans le shell de la recette. Le parsing est fait par le shell et
# non par `include`, ce qui évite que make interprète un $ ou un # présent dans
# un mot de passe.
CHARGER_ENV = set -a; . $(ENV_FICHIER); set +a

# Les tests tournent sur l'hôte et parlent à PostgreSQL par le port publié par
# la surcharge de développement. Les URL sont donc composées ici, à partir des
# mêmes variables que celles données aux conteneurs : une seule source.
ENV_TEST = $(CHARGER_ENV); \
	export DATABASE_URL="postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASSWORD@localhost:$${PORT_DB:-5432}/$$POSTGRES_DB"; \
	export DATABASE_ADMIN_URL="postgresql://$$POSTGRES_USER:$$POSTGRES_PASSWORD@localhost:$${PORT_DB:-5432}/postgres"; \
	export REDIS_URL="redis://:$$REDIS_PASSWORD@localhost:$${PORT_REDIS:-6379}/0"

.PHONY: help
help: ## Affiche cette aide
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Garde-fous -----------------------------------------------------------
.PHONY: _env
_env:
	@test -f $(ENV_FICHIER) || { \
		echo "✖ .env absent."; \
		echo "  cp .env.example .env  puis renseigner SECRET_KEY :"; \
		echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""; \
		exit 1; }

.PHONY: _venv
_venv:
	@test -x $(PY) || { echo "✖ venv absent. Lancer : make install-back"; exit 1; }

.PHONY: _db
_db: _env
	@$(CHARGER_ENV); \
	nc -z localhost $${PORT_DB:-5432} 2>/dev/null || { \
		echo "✖ PostgreSQL injoignable sur le port $${PORT_DB:-5432}."; \
		echo "  Lancer : make infra"; \
		exit 1; }

# --- Conteneurs -----------------------------------------------------------
.PHONY: up
up: _env ## Démarre la stack complète en développement
	$(COMPOSE) up -d --build
	@echo "  Front : http://localhost:5173"
	@echo "  API   : http://localhost:8000/docs"

.PHONY: infra
infra: _env ## Démarre PostgreSQL et Redis seuls (suffit pour les tests)
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
config: ## Valide les combinaisons Compose
	@$(COMPOSE_REF) config -q && echo "  compose.yml                  OK"
	@$(COMPOSE) config -q      && echo "  compose.yml + override (dev) OK"

# --- Installation ---------------------------------------------------------
.PHONY: install-back
install-back: ## Crée le venv et installe les dépendances Python
	python3 -m venv backend/.venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e "backend[dev]"

.PHONY: install-front
install-front: ## Installe les dépendances npm
	cd frontend && npm install

.PHONY: install
install: install-back install-front ## Installe tout

# --- Base de données ------------------------------------------------------
.PHONY: migrate
migrate: _env ## Applique les migrations (service one-shot dédié)
	$(COMPOSE) run --rm migrate

.PHONY: revision
revision: _env ## Crée une migration : make revision m="description"
	@test -n "$(m)" || { echo '✖ Usage : make revision m="description"'; exit 1; }
	$(COMPOSE) run --rm migrate alembic revision --autogenerate -m "$(m)"
	@echo "⚠️  RELIRE la migration générée : les extensions, renommages et"
	@echo "   triggers ne sont jamais produits par --autogenerate."

.PHONY: seed
seed: _env ## Crée les comptes de démonstration (idempotent)
	$(COMPOSE) run --rm api python -m app.seed

# --- Tests ----------------------------------------------------------------
.PHONY: test-unit
test-unit: _venv ## Tests backend sans aucun service (instantané)
	@cd backend && .venv/bin/python -m pytest -m "not migrations and not integration" $(ARGS)

.PHONY: test-migrations
test-migrations: _venv _db ## Tests de migration (exige PostgreSQL)
	@$(ENV_TEST); cd backend && .venv/bin/python -m pytest tests/migrations $(ARGS)

.PHONY: test-integration
test-integration: _venv _db ## Tests d'intégration et d'API (exige PostgreSQL)
	@$(ENV_TEST); cd backend && .venv/bin/python -m pytest tests/integration tests/api $(ARGS)

.PHONY: test-back
test-back: _venv _db ## Toute la suite backend (exige PostgreSQL)
	@$(ENV_TEST); cd backend && .venv/bin/python -m pytest $(ARGS)

.PHONY: cov-back
cov-back: _venv _db ## Suite backend avec rapport de couverture
	@$(ENV_TEST); cd backend && .venv/bin/python -m pytest --cov --cov-report=term-missing $(ARGS)

.PHONY: test-front
test-front: ## Tests frontend
	cd frontend && npm run test -- $(ARGS)

.PHONY: test
test: test-back test-front ## Tous les tests

# --- Qualité --------------------------------------------------------------
.PHONY: lint-back
lint-back: _venv ## Lint et format backend
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

.PHONY: format-back
format-back: _venv ## Formate le backend
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check . --fix

.PHONY: lint-front
lint-front: ## Lint et vérification des types frontend
	cd frontend && npm run lint && npm run type-check

.PHONY: lint
lint: lint-back lint-front ## Lint des deux côtés

.PHONY: build-front
build-front: ## Build de production du frontend
	cd frontend && npm run build

# --- Portes qualité -------------------------------------------------------
.PHONY: check-rapide
check-rapide: lint-back test-unit lint-front test-front ## Sans PostgreSQL, quelques secondes
	@echo "✔ Portes rapides franchies. `make check` ajoute migrations, intégration et API."

.PHONY: check
check: lint test build-front ## Tout ce que la CI exécute
	@echo "✔ Tout est vert."
