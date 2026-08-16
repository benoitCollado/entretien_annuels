"""Processus — US-02. Endpoint appelant : `POST /utilisateurs`.

Lecture : portée → règles métier → effets.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier, DonneesInvalides
from app.core.securite import hacher_mot_de_passe
from app.models.utilisateur import Utilisateur
from app.repositories.role_repository import RoleRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import portee_hierarchique, rbac


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    email: str,
    mot_de_passe: str,
    nom: str,
    prenom: str,
    codes_roles: list[str],
    poste: str | None = None,
    service: str | None = None,
    date_entree: date | None = None,
    manager_id: UUID | None = None,
) -> Utilisateur:
    utilisateurs = UtilisateurRepository(session)
    roles_repo = RoleRepository(session)

    # 1. Portée : seuls l'administrateur et le RH créent des comptes.
    if not portee_hierarchique.peut_gerer(auteur.codes_roles()):
        raise DonneesInvalides("Votre rôle ne permet pas de créer un compte.")

    # 2. Unicité de l'adresse
    if utilisateurs.email_existe(email):
        raise ConflitMetier("Cette adresse est déjà utilisée.")

    # 3. Rôles : existence, puis droit de les attribuer
    roles = roles_repo.lister_par_codes(codes_roles)
    rbac.exiger_roles_connus(codes_roles, [role.code for role in roles])
    rbac.exiger_attribution_autorisee(auteur.codes_roles(), codes_roles)

    # 4. Rattachement hiérarchique
    nouvel_id = _identifiant_provisoire()
    if manager_id is not None:
        if utilisateurs.get_non_archive(manager_id) is None:
            raise DonneesInvalides("Le manager désigné est introuvable.")
        ancetres = utilisateurs.chaine_hierarchique(manager_id)
        portee_hierarchique.exiger_rattachement_valide(nouvel_id, manager_id, ancetres)

    # 5. Effets
    utilisateur = Utilisateur(
        id=nouvel_id,
        email=email,
        mot_de_passe_hash=hacher_mot_de_passe(mot_de_passe),
        nom=nom,
        prenom=prenom,
        poste=poste,
        service=service,
        date_entree=date_entree,
        manager_id=manager_id,
        roles=list(roles),
    )
    return utilisateurs.ajouter(utilisateur)


def _identifiant_provisoire() -> UUID:
    """L'identifiant est généré avant l'insertion pour pouvoir vérifier le cycle
    hiérarchique **avant** d'écrire quoi que ce soit."""
    from uuid_utils.compat import uuid7

    return uuid7()
