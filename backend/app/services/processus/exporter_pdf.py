from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.objectif_repository import ObjectifRepository
from app.services.processus import consulter_questionnaire
from app.services.regles import transitions_entretien
from app.services.rendu import compte_rendu_pdf as rendu

CLES_VALEUR = ("contenu", "note", "option", "options", "valeur", "date")


def _lisible(valeur: dict | None) -> str:
    if not valeur:
        return "—"
    for cle in CLES_VALEUR:
        if cle in valeur:
            contenu = valeur[cle]
            if isinstance(contenu, bool):
                return "Oui" if contenu else "Non"
            if isinstance(contenu, list):
                return ", ".join(str(x) for x in contenu)
            return str(contenu)
    return "—"


def executer(
    session: Session,
    *,
    lecteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> tuple[bytes, str]:
    vue = consulter_questionnaire.executer(
        session, lecteur=lecteur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    entretien = vue.entretien

    if not transitions_entretien.au_moins(entretien.statut, transitions_entretien.SIGNE):
        raise ConflitMetier(
            "Le compte rendu ne peut être exporté qu'une fois l'entretien signé.",
            details=[{"statut": entretien.statut, "attendu": transitions_entretien.SIGNE}],
        )

    compte_rendu = _construire(session, vue)
    octets = rendu.rendre(compte_rendu)

    AuditRepository(session).tracer(
        action="EXPORT_PDF",
        utilisateur_id=lecteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"octets": len(octets), "contenu_masque": vue.contenu_masque},
        adresse_ip=adresse_ip,
    )
    session.flush()

    nom = f"entretien-{entretien.campagne.annee}-{entretien.collaborateur.nom}.pdf"
    return octets, nom.replace(" ", "-").lower()


def _construire(
    session: Session, vue: consulter_questionnaire.VueQuestionnaire
) -> rendu.CompteRendu:
    entretien = vue.entretien
    par_question: dict[UUID, list] = {}
    for reponse in vue.reponses:
        par_question.setdefault(reponse.question_id, []).append(reponse)

    commentaires_par_question: dict[UUID, list] = {}
    synthese: str | None = None
    for commentaire in vue.commentaires:
        if commentaire.est_synthese:
            synthese = commentaire.contenu
        elif commentaire.question_id is not None:
            commentaires_par_question.setdefault(commentaire.question_id, []).append(commentaire)

    sections = [
        rendu.LigneSection(
            titre=section.titre,
            questions=[
                rendu.LigneQuestion(
                    libelle=question.libelle,
                    cible=question.cible,
                    reponses=[
                        rendu.LigneReponse(
                            auteur=reponse.auteur.nom_complet,
                            valeur=_lisible(reponse.valeur),
                        )
                        for reponse in par_question.get(question.id, [])
                    ],
                    commentaires=[
                        f"{c.auteur.nom_complet} : {c.contenu}"
                        for c in commentaires_par_question.get(question.id, [])
                    ],
                )
                for question in section.questions
            ],
        )
        for section in vue.questionnaire.sections
    ]

    objectifs = [
        rendu.LigneObjectif(
            libelle=objectif.libelle,
            indicateur=objectif.indicateur,
            echeance=objectif.echeance,
            statut=objectif.statut,
            niveau_atteinte=objectif.niveau_atteinte,
        )
        for objectif in ObjectifRepository(session).lister_de_l_entretien(entretien.id)
    ]

    return rendu.CompteRendu(
        titre=vue.questionnaire.titre,
        collaborateur=entretien.collaborateur.nom_complet,
        manager=entretien.manager.nom_complet,
        campagne=entretien.campagne.libelle,
        type_entretien=entretien.type_entretien,
        statut=entretien.statut,
        sections=sections,
        synthese=synthese,
        objectifs=objectifs,
        signe_collaborateur_le=entretien.signe_collaborateur_le,
        signe_manager_le=entretien.signe_manager_le,
        observation_collaborateur=entretien.observation_collaborateur,
        contenu_masque=vue.contenu_masque,
    )
