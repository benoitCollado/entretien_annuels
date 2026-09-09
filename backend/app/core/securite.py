from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from uuid_utils.compat import uuid7

from app.config import obtenir_parametres
from app.core.exceptions import NonAuthentifie

_hacheur = PasswordHasher()

EMPREINTE_FACTICE = _hacheur.hash("mot-de-passe-qui-n-existe-pas")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return _hacheur.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    try:
        return _hacheur.verify(empreinte, mot_de_passe)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def rehachage_necessaire(empreinte: str) -> bool:
    try:
        return _hacheur.check_needs_rehash(empreinte)
    except (InvalidHashError, ValueError):
        return False


def creer_jeton(utilisateur_id: UUID, version_jeton: int) -> tuple[str, int]:
    parametres = obtenir_parametres()
    duree = timedelta(minutes=parametres.duree_jeton_minutes)
    maintenant = datetime.now(UTC)

    charge: dict[str, Any] = {
        "sub": str(utilisateur_id),
        "ver": version_jeton,
        "iat": int(maintenant.timestamp()),
        "exp": int((maintenant + duree).timestamp()),
        "jti": str(uuid7()),
    }
    jeton = jwt.encode(charge, parametres.secret_key, algorithm=parametres.algorithme_jwt)
    return jeton, int(duree.total_seconds())


def decoder_jeton(jeton: str) -> tuple[UUID, int]:
    parametres = obtenir_parametres()
    try:
        charge = jwt.decode(
            jeton,
            parametres.secret_key,
            algorithms=[parametres.algorithme_jwt],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise NonAuthentifie("Session expirée") from exc
    except jwt.PyJWTError as exc:
        raise NonAuthentifie("Jeton invalide") from exc

    try:
        identifiant = UUID(charge["sub"])
        version = int(charge["ver"])
    except (KeyError, ValueError, TypeError) as exc:
        raise NonAuthentifie("Jeton invalide") from exc

    return identifiant, version
