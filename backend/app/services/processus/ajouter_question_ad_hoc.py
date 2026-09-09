from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, ConflitMetier, DonneesInvalides, RessourceIntrouvable
from app.models.questionnaire import Question
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.question_repository import QuestionRepository
from app.services.regles import transitions_entretien

STATUTS_MODIFIABLES = frozenset({transitions_entretien.PLANIFIE, transitions_entretien.PREPARATION})


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    section_id: UUID,
    libelle: str,
    type_question: str,
    cible: str,
    obligatoire: bool = False,
    aide: str | None = None,
    configuration: dict[str, Any] | None = None,
    adresse_ip: str | None = None,
) -> Question:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None or entretien.questionnaire is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    if auteur.id != entretien.manager_id:
        raise AccesRefuse("Seul le manager de l'entretien peut ajouter une question.")

    if entretien.statut not in STATUTS_MODIFIABLES:
        raise ConflitMetier(
            "Une question ne peut plus être ajoutée : le questionnaire est déjà soumis."
        )

    depot = QuestionRepository(session)

    if not depot.section_appartient_au_questionnaire(section_id, entretien.questionnaire.id):
        raise DonneesInvalides("Cette section ne fait pas partie de cet entretien.")

    question = depot.ajouter(
        Question(
            section_id=section_id,
            question_template_id=None,
            ajoutee_par_id=auteur.id,
            libelle=libelle,
            aide=aide,
            type_question=type_question,
            cible=cible,
            obligatoire=obligatoire,
            ordre=depot.prochain_ordre(section_id),
            configuration=configuration or {},
        )
    )

    AuditRepository(session).tracer(
        action="QUESTION_AD_HOC",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"question_id": str(question.id), "section_id": str(section_id)},
        adresse_ip=adresse_ip,
    )
    session.flush()
    return question
