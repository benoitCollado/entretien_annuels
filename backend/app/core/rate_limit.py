"""Limitation de débit adossée à Redis (§7.3).

Cible : `POST /auth/login` à 5 tentatives par 15 minutes et par couple IP +
email. Implémentation `INCR` + `EXPIRE`, la primitive la plus simple qui rende
le compteur atomique.

**Arbitrage assumé — comportement quand Redis est injoignable.** Le module est
*fail-open* : il laisse passer et journalise un avertissement. Fermer
l'authentification entière parce qu'un cache de compteurs est tombé
transformerait une panne mineure en interruption de service. Le compromis est
défendable ici parce que Redis ne porte aucune donnée RH et que le rate limiting
est une défense contre le bourrage d'identifiants, pas le contrôle d'accès
lui-même — celui-ci reste assuré par argon2id et par le RBAC.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import redis

from app.config import obtenir_parametres
from app.core.exceptions import TropDeTentatives

logger = logging.getLogger("app.rate_limit")


@lru_cache
def obtenir_client() -> redis.Redis:
    return redis.Redis.from_url(
        obtenir_parametres().redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def cache_repond() -> bool:
    """Sonde de disponibilité, utilisée par `/health/ready`."""
    try:
        return bool(obtenir_client().ping())
    except redis.RedisError as exc:
        logger.warning("Redis injoignable : %s", exc)
        return False


def exiger_sous_limite(cle: str, maximum: int, fenetre_secondes: int) -> None:
    """Incrémente le compteur `cle` et lève `TropDeTentatives` au-delà du seuil."""
    try:
        client = obtenir_client()
        pipeline = client.pipeline()
        pipeline.incr(cle)
        # L'expiration n'est posée que sur la première incrémentation : sans le
        # test `nx=True`, chaque tentative repousserait la fenêtre et un
        # attaquant régulier ne serait jamais bloqué.
        pipeline.expire(cle, fenetre_secondes, nx=True)
        compteur, _ = pipeline.execute()
    except redis.RedisError as exc:
        logger.warning("Rate limiting désactivé, Redis injoignable : %s", exc)
        return

    if int(compteur) > maximum:
        logger.warning("Seuil de tentatives dépassé pour %s", cle)
        raise TropDeTentatives(
            "Trop de tentatives. Réessayez dans quelques minutes.",
        )


def reinitialiser(cle: str) -> None:
    """Efface le compteur — appelé après une connexion réussie."""
    try:
        obtenir_client().delete(cle)
    except redis.RedisError as exc:  # pragma: no cover - dépend de l'infrastructure
        logger.warning("Redis injoignable lors de la remise à zéro : %s", exc)


def cle_connexion(adresse_ip: str | None, email: str) -> str:
    """Compteur par couple IP + email (§7.3).

    Le seul critère de l'IP pénaliserait tous les salariés derrière une même
    sortie internet ; le seul critère de l'email permettrait de balayer les
    comptes depuis autant d'adresses que voulu.
    """
    return f"rl:connexion:{adresse_ip or 'inconnue'}:{email.lower()}"
