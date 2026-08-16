"""Dépendances FastAPI partagées.

Les alias `SessionDep` et `UtilisateurCourant` existent pour que les routers
n'aient **jamais** à importer SQLAlchemy ni les modèles : ils reçoivent des
objets déjà annotés. La règle de couche « un router ne connaît pas la
persistance » reste ainsi vérifiable littéralement par
`tests/unit/test_architecture.py`.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, NonAuthentifie
from app.core.securite import decoder_jeton
from app.database import obtenir_fabrique_sessions
from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository


def get_db() -> Generator[Session, None, None]:
    """Une requête HTTP = une transaction.

    C'est ici — et nulle part ailleurs — que l'on commite. Les repositories
    utilisent `flush()` pour obtenir un identifiant, les services orchestrent
    dans la transaction en cours. Conséquence : **un processus métier est
    atomique par construction**. Si l'écriture de l'audit échoue après une
    transition d'état, rien n'est persisté (addendum §1.2).
    """
    session = obtenir_fabrique_sessions()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db)]

# `auto_error=False` : sans en-tête, FastAPI lèverait sa propre HTTPException,
# dont le corps ne suivrait pas le format d'erreur du projet. On préfère lever
# `NonAuthentifie` et laisser `gestion_erreurs` produire la réponse.
_schema_bearer = HTTPBearer(auto_error=False)


def utilisateur_courant(
    session: SessionDep,
    identifiants: Annotated[HTTPAuthorizationCredentials | None, Depends(_schema_bearer)] = None,
) -> Utilisateur:
    if identifiants is None:
        raise NonAuthentifie("Authentification requise")

    utilisateur_id, version_jeton = decoder_jeton(identifiants.credentials)

    utilisateur = UtilisateurRepository(session).get_actif(utilisateur_id)
    if utilisateur is None:
        # Compte inexistant, désactivé ou archivé : message volontairement
        # identique dans les trois cas.
        raise NonAuthentifie("Session invalide")

    # Révocation sans denylist (§7.3). Un changement de mot de passe, une
    # déconnexion ou une désactivation incrémente `version_jeton` : tous les
    # jetons émis avant deviennent immédiatement inutilisables.
    if utilisateur.version_jeton != version_jeton:
        raise NonAuthentifie("Session révoquée")

    return utilisateur


UtilisateurCourant = Annotated[Utilisateur, Depends(utilisateur_courant)]


def exige_permission(code_permission: str) -> Callable[[Utilisateur], Utilisateur]:
    """Contrôle RBAC. Usage : `Depends(exige_permission("utilisateur:creer"))`.

    Le RBAC répond à « ce rôle peut-il faire cette action ? ». Il ne dit **rien
    du périmètre** : « cet utilisateur-là, précisément ? » relève du contrôle de
    portée, appliqué dans les processus (§6.1).
    """

    def dependance(utilisateur: UtilisateurCourant) -> Utilisateur:
        if code_permission not in utilisateur.codes_permissions():
            raise AccesRefuse(f"Permission requise : {code_permission}")
        return utilisateur

    return dependance


def adresse_client(request: Request) -> str | None:
    """IP réelle de l'appelant.

    Derrière nginx, `request.client.host` est l'IP du proxy. Uvicorn tourne avec
    `--proxy-headers`, qui réécrit `client` à partir de `X-Forwarded-For` : la
    valeur lue ici est donc déjà la bonne.
    """
    return request.client.host if request.client else None


AdresseClient = Annotated[str | None, Depends(adresse_client)]
