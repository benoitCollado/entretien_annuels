from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import obtenir_parametres
from app.core import rate_limit, securite
from app.core.exceptions import NonAuthentifie
from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository

logger = logging.getLogger("app.auth")

MESSAGE_ECHEC = "Adresse ou mot de passe incorrect."


def executer(
    session: Session,
    *,
    email: str,
    mot_de_passe: str,
    adresse_ip: str | None = None,
) -> tuple[Utilisateur, str, int]:
    parametres = obtenir_parametres()
    cle = rate_limit.cle_connexion(adresse_ip, email)
    rate_limit.exiger_sous_limite(
        cle,
        maximum=parametres.connexion_tentatives_max,
        fenetre_secondes=parametres.connexion_fenetre_secondes,
    )

    utilisateur = UtilisateurRepository(session).get_par_email(email)

    if utilisateur is None:
        securite.verifier_mot_de_passe(mot_de_passe, securite.EMPREINTE_FACTICE)
        logger.info("Échec de connexion (adresse inconnue) depuis %s", adresse_ip)
        raise NonAuthentifie(MESSAGE_ECHEC)

    if not securite.verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
        logger.info("Échec de connexion pour %s depuis %s", utilisateur.id, adresse_ip)
        raise NonAuthentifie(MESSAGE_ECHEC)

    if not utilisateur.actif or utilisateur.archived_at is not None:
        logger.info("Connexion refusée, compte inactif : %s", utilisateur.id)
        raise NonAuthentifie(MESSAGE_ECHEC)

    rate_limit.reinitialiser(cle)

    if securite.rehachage_necessaire(utilisateur.mot_de_passe_hash):
        utilisateur.mot_de_passe_hash = securite.hacher_mot_de_passe(mot_de_passe)
        logger.info("Empreinte de mot de passe remise à niveau pour %s", utilisateur.id)

    jeton, duree = securite.creer_jeton(utilisateur.id, utilisateur.version_jeton)
    logger.info("Connexion réussie : %s", utilisateur.id)
    return utilisateur, jeton, duree
