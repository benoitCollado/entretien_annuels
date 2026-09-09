from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, ConflitMetier, DonneesInvalides, RessourceIntrouvable
from app.models.campagne import Campagne
from app.models.entretien import Entretien
from app.models.questionnaire import Question, Questionnaire, Section
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.campagne_repository import CampagneRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.template_repository import TemplateRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import (
    coherence_campagne,
    publication_template,
    transitions_entretien,
)

ROLE_RH = "RH"


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    campagne_id: UUID,
    collaborateur_id: UUID,
    template_id: UUID,
    manager_id: UUID | None = None,
    date_planifiee: date | None = None,
    adresse_ip: str | None = None,
) -> Entretien:
    entretiens = EntretienRepository(session)
    utilisateurs = UtilisateurRepository(session)
    campagnes = CampagneRepository(session)
    templates = TemplateRepository(session)
    audit = AuditRepository(session)

    est_rh = ROLE_RH in auteur.codes_roles()

    collaborateur = utilisateurs.get_actif(collaborateur_id)
    if collaborateur is None:
        raise RessourceIntrouvable("Collaborateur introuvable ou inactif.")

    manager_effectif = manager_id or collaborateur.manager_id
    if manager_effectif is None:
        raise DonneesInvalides(
            "Ce collaborateur n'a pas de manager : précisez-en un explicitement."
        )

    if not est_rh and manager_effectif != auteur.id:
        raise AccesRefuse("Vous ne pouvez créer un entretien que pour votre équipe.")

    if manager_effectif == collaborateur_id:
        raise DonneesInvalides("Le collaborateur ne peut pas être son propre manager.")

    if utilisateurs.get_actif(manager_effectif) is None:
        raise RessourceIntrouvable("Manager introuvable ou inactif.")

    if entretiens.existe_pour_campagne(campagne_id, collaborateur_id):
        raise ConflitMetier("Un entretien existe déjà pour ce collaborateur sur cette campagne.")

    campagne = campagnes.get(campagne_id)
    if campagne is None:
        raise RessourceIntrouvable("Campagne introuvable.")
    if not coherence_campagne.accepte_des_entretiens(campagne.statut):
        raise ConflitMetier(
            f"La campagne est {campagne.statut} : elle n'accepte pas de nouvel entretien."
        )

    template = templates.get_avec_arborescence(template_id)
    if template is None:
        raise RessourceIntrouvable("Trame introuvable.")
    if not publication_template.est_instanciable(template.statut):
        raise ConflitMetier("Seule une trame publiée peut être instanciée.")
    coherence_campagne.exiger_types_compatibles(campagne.type_entretien, template.type_entretien)

    entretien = Entretien(
        campagne_id=campagne.id,
        collaborateur_id=collaborateur_id,
        manager_id=manager_effectif,
        type_entretien=campagne.type_entretien,
        statut=transitions_entretien.BROUILLON,
        date_planifiee=date_planifiee,
        questionnaire=_copier_la_trame(template, campagne),
    )
    entretiens.ajouter(entretien)

    acteur = transitions_entretien.RH if est_rh else transitions_entretien.MANAGER
    transitions_entretien.exiger_transition(
        entretien.statut, transitions_entretien.PLANIFIE, acteur
    )
    entretien.statut = transitions_entretien.PLANIFIE

    audit.tracer(
        action="ASSIGNATION",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=transitions_entretien.BROUILLON,
        statut_apres=transitions_entretien.PLANIFIE,
        donnees={"template_id": str(template.id), "template_version": template.version},
        adresse_ip=adresse_ip,
    )

    session.flush()
    return entretien


def _copier_la_trame(template, campagne: Campagne) -> Questionnaire:
    return Questionnaire(
        template_id=template.id,
        template_version=template.version,
        titre=f"{template.nom} — {campagne.libelle}",
        sections=[
            Section(
                titre=section.titre,
                description=section.description,
                ordre=section.ordre,
                questions=[
                    Question(
                        question_template_id=question.id,
                        libelle=question.libelle,
                        aide=question.aide,
                        type_question=question.type_question,
                        cible=question.cible,
                        obligatoire=question.obligatoire,
                        ordre=question.ordre,
                        configuration=dict(question.configuration),
                    )
                    for question in section.questions
                ],
            )
            for section in template.sections
        ],
    )
