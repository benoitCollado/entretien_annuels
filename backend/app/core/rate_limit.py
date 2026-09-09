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
    try:
        return bool(obtenir_client().ping())
    except redis.RedisError as exc:
        logger.warning("Redis injoignable : %s", exc)
        return False


def exiger_sous_limite(cle: str, maximum: int, fenetre_secondes: int) -> None:
    try:
        client = obtenir_client()
        pipeline = client.pipeline()
        pipeline.incr(cle)
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
    try:
        obtenir_client().delete(cle)
    except redis.RedisError as exc:  # pragma: no cover
        logger.warning("Redis injoignable lors de la remise à zéro : %s", exc)


def cle_connexion(adresse_ip: str | None, email: str) -> str:
    return f"rl:connexion:{adresse_ip or 'inconnue'}:{email.lower()}"
