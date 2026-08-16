"""Jeu de données de démonstration.

Idempotent : relançable sans créer de doublon. Les **rôles et permissions** ne
sont pas créés ici — ce sont des données structurantes, posées par la migration
`4e2bb21d65e6`. Ce script ne crée que des comptes.

    python -m app.seed
"""

from __future__ import annotations

import logging
import os
import sys

from sqlalchemy.orm import Session

from app.core.securite import hacher_mot_de_passe
from app.database import obtenir_fabrique_sessions
from app.models.utilisateur import Utilisateur
from app.repositories.role_repository import RoleRepository
from app.repositories.utilisateur_repository import UtilisateurRepository

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("app.seed")

MOT_DE_PASSE_DEMO = os.environ.get("SEED_MOT_DE_PASSE", "MotDePasseDemo2026!")

COMPTES: list[dict[str, object]] = [
    {
        "email": "admin@example.com",
        "nom": "Martin",
        "prenom": "Alice",
        "poste": "Administratrice",
        "service": "Direction",
        "roles": ["ADMIN"],
    },
    {
        "email": "rh@example.com",
        "nom": "Bernard",
        "prenom": "Claire",
        "poste": "Responsable RH",
        "service": "Ressources humaines",
        "roles": ["RH"],
    },
    {
        "email": "manager@example.com",
        "nom": "Dupont",
        "prenom": "Julien",
        "poste": "Chef d'équipe",
        "service": "Production",
        "roles": ["MANAGER", "COLLABORATEUR"],
    },
    {
        "email": "collaborateur@example.com",
        "nom": "Petit",
        "prenom": "Sophie",
        "poste": "Technicienne",
        "service": "Production",
        "roles": ["COLLABORATEUR"],
        "manager": "manager@example.com",
    },
]


def peupler(session: Session) -> int:
    utilisateurs = UtilisateurRepository(session)
    roles_repo = RoleRepository(session)
    crees = 0

    # Premier passage : les comptes, sans rattachement hiérarchique.
    for compte in COMPTES:
        email = str(compte["email"])
        if utilisateurs.get_par_email(email) is not None:
            logger.info("= %s existe déjà", email)
            continue

        codes = [str(code) for code in compte["roles"]]  # type: ignore[union-attr]
        roles = roles_repo.lister_par_codes(codes)
        if len(roles) != len(codes):
            trouves = {role.code for role in roles}
            manquants = sorted(set(codes) - trouves)
            raise RuntimeError(
                f"Rôles absents du référentiel : {manquants}. "
                "Lancer `alembic upgrade head` avant le seed."
            )

        utilisateurs.ajouter(
            Utilisateur(
                email=email,
                mot_de_passe_hash=hacher_mot_de_passe(MOT_DE_PASSE_DEMO),
                nom=str(compte["nom"]),
                prenom=str(compte["prenom"]),
                poste=str(compte["poste"]),
                service=str(compte["service"]),
                roles=list(roles),
            )
        )
        crees += 1
        logger.info("+ %s (%s)", email, ", ".join(codes))

    # Second passage : les rattachements, une fois tous les comptes présents.
    for compte in COMPTES:
        if "manager" not in compte:
            continue
        salarie = utilisateurs.get_par_email(str(compte["email"]))
        manager = utilisateurs.get_par_email(str(compte["manager"]))
        if salarie is not None and manager is not None and salarie.manager_id is None:
            salarie.manager_id = manager.id
            logger.info("  %s rattaché à %s", salarie.email, manager.email)

    return crees


def main() -> int:
    with obtenir_fabrique_sessions()() as session:
        try:
            crees = peupler(session)
            session.commit()
        except Exception:
            session.rollback()
            raise

    logger.info("")
    logger.info("%d compte(s) créé(s). Mot de passe commun : %s", crees, MOT_DE_PASSE_DEMO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
