from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.reponse_repository import ReponseRepository
from app.services.regles import completude_questionnaire, transitions_entretien

CIBLE_COLLABORATEUR = "COLLABORATEUR"


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> Entretien:
    entretiens = EntretienRepository(session)
    audit = AuditRepository(session)

    entretien = entretiens.get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")
    if entretien.questionnaire is None:
        raise RessourceIntrouvable("Cet entretien n'a pas de questionnaire.")

    if auteur.id != entretien.collaborateur_id:
        audit.tracer_refus(
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=entretien.statut,
            donnees={"motif": "soumission par un tiers"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse("Seul le collaborateur peut soumettre son questionnaire.")

    statut_avant = entretien.statut
    transitions_entretien.exiger_transition(
        statut_avant,
        transitions_entretien.SOUMIS_COLLABORATEUR,
        transitions_entretien.COLLABORATEUR,
    )

    questions = QuestionRepository(session).lister_du_questionnaire(entretien.questionnaire.id)
    repondues = ReponseRepository(session).ids_questions_repondues(
        entretien.questionnaire.id, auteur.id
    )
    manquantes = completude_questionnaire.questions_obligatoires_manquantes(
        questions, repondues, CIBLE_COLLABORATEUR
    )
    if manquantes:
        raise DonneesInvalides(
            "Des questions obligatoires sont sans réponse.",
            details=[
                {"question_id": str(question.id), "libelle": question.libelle}
                for question in manquantes
            ],
        )

    maintenant = datetime.now(UTC)
    entretien.statut = transitions_entretien.SOUMIS_COLLABORATEUR
    entretien.soumis_collaborateur_le = maintenant

    audit.tracer(
        action="SOUMISSION_COLLABORATEUR",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut,
        donnees={"questions_repondues": len(repondues)},
        adresse_ip=adresse_ip,
    )

    session.flush()
    return entretien
