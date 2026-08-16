"""Hachage des mots de passe et jetons JWT (US-01, §7.3).

Trois décisions y sont matérialisées :

- **argon2id** pour les mots de passe, jamais de stockage en clair ;
- **JWT HS256**, durée 60 minutes, **sans rafraîchissement** ;
- révocation par `utilisateur.version_jeton` : le numéro est embarqué dans le
  jeton et comparé à chaque requête. L'utilisateur étant de toute façon chargé
  à chaque requête, cette vérification ne coûte **aucune requête
  supplémentaire**. C'est un arbitrage assumé face à une denylist Redis, pas un
  oubli.
"""

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

# Paramètres par défaut d'argon2-cffi : profil argon2id conforme aux
# recommandations OWASP courantes.
_hacheur = PasswordHasher()

# Empreinte factice, calculée une seule fois au chargement du module.
# Sert à égaliser le temps de réponse de la connexion quand l'adresse est
# inconnue : sans elle, une réponse immédiate signalerait « ce compte n'existe
# pas » et permettrait d'énumérer les comptes par simple chronométrage (§7.3).
EMPREINTE_FACTICE = _hacheur.hash("mot-de-passe-qui-n-existe-pas")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return _hacheur.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    """Retourne `False` plutôt que de laisser remonter l'exception.

    L'appelant n'a pas à distinguer « mauvais mot de passe » de « empreinte
    corrompue » : dans les deux cas la connexion échoue, et le message renvoyé
    au client doit rester identique (pas d'énumération de comptes, §7.3).
    """
    try:
        return _hacheur.verify(empreinte, mot_de_passe)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def rehachage_necessaire(empreinte: str) -> bool:
    """Vrai si l'empreinte a été produite avec des paramètres désormais plus
    faibles que ceux en vigueur — permet de remettre à niveau au fil des
    connexions réussies."""
    try:
        return _hacheur.check_needs_rehash(empreinte)
    except (InvalidHashError, ValueError):
        return False


def creer_jeton(utilisateur_id: UUID, version_jeton: int) -> tuple[str, int]:
    """Retourne `(jeton, duree_en_secondes)`."""
    parametres = obtenir_parametres()
    duree = timedelta(minutes=parametres.duree_jeton_minutes)
    maintenant = datetime.now(UTC)

    charge: dict[str, Any] = {
        "sub": str(utilisateur_id),
        # Version de jeton : c'est elle qui permet la révocation immédiate.
        "ver": version_jeton,
        "iat": int(maintenant.timestamp()),
        "exp": int((maintenant + duree).timestamp()),
        "jti": str(uuid7()),
    }
    jeton = jwt.encode(charge, parametres.secret_key, algorithm=parametres.algorithme_jwt)
    return jeton, int(duree.total_seconds())


def decoder_jeton(jeton: str) -> tuple[UUID, int]:
    """Retourne `(utilisateur_id, version_jeton)` ou lève `NonAuthentifie`."""
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
