from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.reponse import Reponse
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.reponse_repository import ReponseRepository
from app.services.regles import transitions_entretien, validation_reponse, visibilite_reponses


@dataclass(slots=True)
class ReponseSaisie:
    question_id: UUID
    valeur: dict[str, Any] | None


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    reponses: list[ReponseSaisie],
    adresse_ip: str | None = None,
) -> Entretien:
    entretiens = EntretienRepository(session)
    depot_reponses = ReponseRepository(session)
    audit = AuditRepository(session)

    entretien = entretiens.get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")
    if entretien.questionnaire is None:
        raise RessourceIntrouvable("Cet entretien n'a pas de questionnaire.")

    if not visibilite_reponses.peut_ecrire_ses_reponses(
        entretien.statut, auteur.id, entretien.collaborateur_id
    ):
        audit.tracer_refus(
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=entretien.statut,
            donnees={"motif": "écriture de réponses non autorisée"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse(
            "Vous ne pouvez plus modifier vos réponses : le questionnaire est soumis."
        )

    questions = {
        question.id: question
        for question in QuestionRepository(session).lister_du_questionnaire(
            entretien.questionnaire.id
        )
    }

    for saisie in reponses:
        question = questions.get(saisie.question_id)
        if question is None:
            raise DonneesInvalides("Cette question ne fait pas partie de ce questionnaire.")
        validation_reponse.valider(question.type_question, saisie.valeur, question.configuration)

    for saisie in reponses:
        existante = depot_reponses.get_par_question_et_auteur(saisie.question_id, auteur.id)
        if existante is None:
            depot_reponses.ajouter(
                Reponse(question_id=saisie.question_id, auteur_id=auteur.id, valeur=saisie.valeur)
            )
        else:
            existante.valeur = saisie.valeur

    statut_avant = entretien.statut
    if entretien.statut == transitions_entretien.PLANIFIE:
        transitions_entretien.exiger_transition(
            entretien.statut,
            transitions_entretien.PREPARATION,
            transitions_entretien.COLLABORATEUR,
        )
        entretien.statut = transitions_entretien.PREPARATION
        audit.tracer(
            action="PREMIERE_SAISIE",
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=statut_avant,
            statut_apres=entretien.statut,
            adresse_ip=adresse_ip,
        )
    else:
        audit.tracer(
            action="ENREGISTREMENT_BROUILLON",
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=statut_avant,
            donnees={"nombre_reponses": len(reponses)},
            adresse_ip=adresse_ip,
        )

    session.flush()
    return entretien
