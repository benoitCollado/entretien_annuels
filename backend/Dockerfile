# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Socle commun
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------------------------------------------------------------------------
# Dépendances — couche invalidée uniquement quand pyproject.toml change
# ---------------------------------------------------------------------------
FROM base AS builder

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Exécution — image finale, sans outils de développement
# ---------------------------------------------------------------------------
FROM base AS runtime

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Sélection explicite de ce qui entre dans l'image : ni tests, ni outillage.
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini pyproject.toml ./

# Utilisateur non privilégié : un conteneur applicatif n'a aucune raison de
# tourner en root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Sonde en Python : l'image slim n'embarque ni curl ni wget, et les installer
# pour ce seul usage grossirait l'image et élargirait la surface de CVE.
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

# ⚠️ Aucune migration dans l'entrypoint : elle est jouée par le service
# `migrate` du compose (§10.2). Avec deux réplicas, deux migrations
# concurrentes produiraient un crash-loop illisible.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]

# ---------------------------------------------------------------------------
# Développement — dépendances de test, code monté en volume par le compose
# ---------------------------------------------------------------------------
FROM base AS dev

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
