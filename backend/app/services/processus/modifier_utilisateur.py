"""Processus — US-02. Endpoint appelant : `PATCH /utilisateurs/{id}`."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier, DonneesInvalides, RessourceIntrouvable
from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import portee_hierarchique

_CHAMPS_SIMPLES = ("nom", "prenom", "poste", "service")


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    utilisateur_id: UUID,
    email: str | None = None,
    nom: str | None = None,
    prenom: str | None = None,
    poste: str | None = None,
    service: str | None = None,
    date_entree: date | None = None,
    manager_id: UUID | None = None,
    actif: bool | None = None,
    champs_fournis: set[str] | None = None,
) -> Utilisateur:
    """`champs_fournis` distingue « champ absent » de « champ mis à None ».

    Sans cette distinction, une requête partielle effacerait silencieusement les
    champs facultatifs non transmis.
    """
    fournis = champs_fournis if champs_fournis is not None else set()
    utilisateurs = UtilisateurRepository(session)

    if not portee_hierarchique.peut_gerer(auteur.codes_roles()):
        raise DonneesInvalides("Votre rôle ne permet pas de modifier un compte.")

    utilisateur = utilisateurs.get_non_archive(utilisateur_id)
    if utilisateur is None:
        raise RessourceIntrouvable("Utilisateur introuvable.")

    if "email" in fournis and email is not None and email != utilisateur.email:
        if utilisateurs.email_existe(email, sauf_id=utilisateur.id):
            raise ConflitMetier("Cette adresse est déjà utilisée.")
        utilisateur.email = email
        # Changer l'adresse de connexion invalide les sessions en cours.
        utilisateur.version_jeton += 1

    valeurs: dict[str, Any] = {
        "nom": nom,
        "prenom": prenom,
        "poste": poste,
        "service": service,
    }
    for champ in _CHAMPS_SIMPLES:
        if champ in fournis:
            setattr(utilisateur, champ, valeurs[champ])

    if "date_entree" in fournis:
        utilisateur.date_entree = date_entree

    if "manager_id" in fournis:
        if manager_id is not None:
            if utilisateurs.get_non_archive(manager_id) is None:
                raise DonneesInvalides("Le manager désigné est introuvable.")
            ancetres = utilisateurs.chaine_hierarchique(manager_id)
            portee_hierarchique.exiger_rattachement_valide(utilisateur.id, manager_id, ancetres)
        utilisateur.manager_id = manager_id

    if "actif" in fournis and actif is not None and actif != utilisateur.actif:
        utilisateur.actif = actif
        # Désactiver un compte doit couper l'accès immédiatement, sans attendre
        # l'expiration du jeton en cours (§7.3).
        utilisateur.version_jeton += 1

    session.flush()
    return utilisateur
