from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable
from app.models.commentaire import Commentaire
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.commentaire_repository import CommentaireRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.reponse_repository import ReponseRepository
from app.services.regles import immutabilite, visibilite_reponses


def commenter(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    question_id: UUID,
    contenu: str,
    adresse_ip: str | None = None,
) -> Commentaire:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None or entretien.questionnaire is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    _exiger_droit_de_commenter(session, entretien, auteur, adresse_ip)

    if not ReponseRepository(session).question_appartient_au_questionnaire(
        question_id, entretien.questionnaire.id
    ):
        raise DonneesInvalides("Cette question ne fait pas partie de cet entretien.")

    commentaire = CommentaireRepository(session).ajouter(
        Commentaire(
            questionnaire_id=entretien.questionnaire.id,
            question_id=question_id,
            auteur_id=auteur.id,
            contenu=contenu,
        )
    )

    AuditRepository(session).tracer(
        action="COMMENTAIRE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"question_id": str(question_id)},
        adresse_ip=adresse_ip,
    )
    session.flush()
    return commentaire


def rediger_synthese(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    contenu: str,
    adresse_ip: str | None = None,
) -> Commentaire:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None or entretien.questionnaire is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    _exiger_droit_de_commenter(session, entretien, auteur, adresse_ip)

    if not contenu.strip():
        raise DonneesInvalides("La synthèse ne peut pas être vide.")

    depot = CommentaireRepository(session)
    existante = depot.get_synthese(entretien.questionnaire.id, auteur.id)

    if existante is not None:
        existante.contenu = contenu
        synthese = existante
    else:
        synthese = depot.ajouter(
            Commentaire(
                questionnaire_id=entretien.questionnaire.id,
                question_id=None,
                auteur_id=auteur.id,
                contenu=contenu,
            )
        )

    AuditRepository(session).tracer(
        action="SYNTHESE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        adresse_ip=adresse_ip,
    )
    session.flush()
    return synthese


def _exiger_droit_de_commenter(
    session: Session, entretien, auteur: Utilisateur, adresse_ip: str | None
) -> None:
    immutabilite.exiger_non_gele(entretien.statut, "Un commentaire")

    if not visibilite_reponses.peut_commenter(entretien.statut, auteur.id, entretien.manager_id):
        AuditRepository(session).tracer_refus(
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=entretien.statut,
            donnees={"motif": "commentaire non autorisé à ce stade"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse("Vous ne pouvez pas commenter cet entretien à ce stade.")
