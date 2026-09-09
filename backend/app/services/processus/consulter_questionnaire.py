from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, RessourceIntrouvable
from app.models.commentaire import Commentaire
from app.models.entretien import Entretien
from app.models.questionnaire import Questionnaire
from app.models.reponse import Reponse
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.commentaire_repository import CommentaireRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.reponse_repository import ReponseRepository
from app.services.regles import visibilite_reponses

ROLE_RH = "RH"


@dataclass(slots=True)
class VueQuestionnaire:
    entretien: Entretien
    questionnaire: Questionnaire
    reponses: list[Reponse]
    commentaires: list[Commentaire]
    contenu_masque: bool


def executer(
    session: Session,
    *,
    lecteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> VueQuestionnaire:
    entretiens = EntretienRepository(session)
    audit = AuditRepository(session)

    entretien = entretiens.get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    est_rh = ROLE_RH in lecteur.codes_roles()
    est_partie_prenante = lecteur.id in (entretien.collaborateur_id, entretien.manager_id)

    if not est_partie_prenante and not est_rh:
        audit.tracer_refus(
            utilisateur_id=lecteur.id,
            entretien_id=entretien.id,
            statut_avant=entretien.statut,
            donnees={"motif": "hors du périmètre de l'entretien"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse("Cet entretien ne vous concerne pas.")

    if entretien.questionnaire is None:
        raise RessourceIntrouvable("Ce entretien n'a pas de questionnaire.")

    auteurs = visibilite_reponses.auteurs_lisibles(
        entretien.statut,
        lecteur.id,
        entretien.collaborateur_id,
        entretien.manager_id,
        lecteur_est_rh=est_rh,
    )
    reponses = ReponseRepository(session).lister_du_questionnaire(
        entretien.questionnaire.id, auteurs
    )

    commentaires = _commentaires_visibles(session, entretien, lecteur)

    audit.tracer(
        action="CONSULTATION",
        utilisateur_id=lecteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"reponses_visibles": len(reponses)},
        adresse_ip=adresse_ip,
    )
    session.flush()

    return VueQuestionnaire(
        entretien=entretien,
        questionnaire=entretien.questionnaire,
        reponses=reponses,
        commentaires=commentaires,
        contenu_masque=auteurs is not None and len(auteurs) <= 1,
    )


def _commentaires_visibles(
    session: Session, entretien: Entretien, lecteur: Utilisateur
) -> list[Commentaire]:
    from app.services.regles.transitions_entretien import REVUE_MANAGER, au_moins

    tous = CommentaireRepository(session).lister_du_questionnaire(entretien.questionnaire.id)

    if lecteur.id == entretien.manager_id:
        return tous
    if lecteur.id == entretien.collaborateur_id:
        if au_moins(entretien.statut, REVUE_MANAGER):
            return tous
        return [c for c in tous if c.auteur_id == lecteur.id]
    from app.services.regles.transitions_entretien import CLOTURE

    return tous if entretien.statut == CLOTURE else []
