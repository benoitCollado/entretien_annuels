from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependances import AdresseClient, SessionDep, UtilisateurCourant, exige_permission
from app.schemas.commun import Page
from app.schemas.entretien import (
    AnnulationEcrite,
    EntretienCree,
    EntretienLu,
    EntretienResume,
)
from app.schemas.objectif import (
    ObjectifEcrit,
    ObjectifLu,
    ObjectifsDeLEntretien,
    SignatureEcrite,
)
from app.schemas.questionnaire import (
    BrouillonEcrit,
    CommentaireEcrit,
    CommentaireLu,
    QuestionAdHocEcrite,
    QuestionInstanciee,
    QuestionnaireLu,
    SyntheseEcrite,
)
from app.services.processus import (
    ajouter_question_ad_hoc,
    commenter_question,
    consulter_entretien,
    consulter_questionnaire,
    enregistrer_brouillon,
    exporter_pdf,
    gerer_objectifs,
    instancier_entretien,
    signer_entretien,
    soumettre_questionnaire,
    transitions_manager,
)
from app.services.processus.enregistrer_brouillon import ReponseSaisie

router = APIRouter(prefix="/entretiens", tags=["entretiens"])

ROLE_RH = "RH"


@router.get(
    "",
    response_model=Page[EntretienResume],
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Lister les entretiens de son périmètre",
)
def lister(
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    campagne_id: Annotated[UUID | None, Query()] = None,
    statut: Annotated[str | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    decalage: Annotated[int, Query(ge=0)] = 0,
) -> Page[EntretienResume]:
    lignes, total = consulter_entretien.lister(
        session,
        lecteur=utilisateur,
        campagne_id=campagne_id,
        statut=statut,
        limite=limite,
        decalage=decalage,
    )
    return Page(
        elements=[EntretienResume.depuis_modele(ligne) for ligne in lignes],
        total=total,
        limite=limite,
        decalage=decalage,
    )


@router.get(
    "/{entretien_id}",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Fiche d'un entretien, sans son contenu",
)
def consulter(
    entretien_id: UUID, session: SessionDep, utilisateur: UtilisateurCourant
) -> EntretienLu:
    entretien = consulter_entretien.consulter(
        session, lecteur=utilisateur, entretien_id=entretien_id
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.get(
    "/{entretien_id}/questionnaire",
    response_model=QuestionnaireLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Questionnaire et réponses visibles",
)
def questionnaire(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> QuestionnaireLu:
    vue = consulter_questionnaire.executer(
        session, lecteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return QuestionnaireLu.depuis_vue(vue)


@router.post(
    "",
    response_model=EntretienLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("entretien:creer"))],
    summary="Instancier un entretien depuis une trame",
)
def creer(
    donnees: EntretienCree,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = instancier_entretien.executer(
        session,
        auteur=utilisateur,
        campagne_id=donnees.campagne_id,
        collaborateur_id=donnees.collaborateur_id,
        template_id=donnees.template_id,
        manager_id=donnees.manager_id,
        date_planifiee=donnees.date_planifiee,
        adresse_ip=adresse_ip,
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.put(
    "/{entretien_id}/reponses",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Enregistrer un brouillon de réponses",
)
def enregistrer(
    entretien_id: UUID,
    donnees: BrouillonEcrit,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = enregistrer_brouillon.executer(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        reponses=[
            ReponseSaisie(question_id=r.question_id, valeur=r.valeur) for r in donnees.reponses
        ],
        adresse_ip=adresse_ip,
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/soumettre",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Soumettre son questionnaire",
)
def soumettre(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = soumettre_questionnaire.executer(
        session, auteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/revue",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Ouvrir la revue",
)
def ouvrir_revue(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = transitions_manager.ouvrir_revue(
        session, auteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/cloturer-echange",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Clore l'échange",
)
def cloturer_echange(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = transitions_manager.cloturer_echange(
        session, auteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/annuler",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:creer"))],
    summary="Annuler un entretien",
)
def annuler(
    entretien_id: UUID,
    donnees: AnnulationEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = transitions_manager.annuler(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        motif=donnees.motif,
        adresse_ip=adresse_ip,
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/questions",
    response_model=QuestionInstanciee,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Ajouter une question ad hoc",
)
def ajouter_question(
    entretien_id: UUID,
    donnees: QuestionAdHocEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> QuestionInstanciee:
    question = ajouter_question_ad_hoc.executer(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        section_id=donnees.section_id,
        libelle=donnees.libelle,
        type_question=donnees.type_question.value,
        cible=donnees.cible.value,
        obligatoire=donnees.obligatoire,
        aide=donnees.aide,
        configuration=donnees.configuration,
        adresse_ip=adresse_ip,
    )
    return QuestionInstanciee(
        id=question.id,
        libelle=question.libelle,
        aide=question.aide,
        type_question=question.type_question,
        cible=question.cible,
        obligatoire=question.obligatoire,
        ordre=question.ordre,
        configuration=question.configuration,
        est_ad_hoc=question.est_ad_hoc,
    )


@router.post(
    "/{entretien_id}/questions/{question_id}/commentaires",
    response_model=CommentaireLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Commenter une question",
)
def commenter(
    entretien_id: UUID,
    question_id: UUID,
    donnees: CommentaireEcrit,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> CommentaireLu:
    commentaire = commenter_question.commenter(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        question_id=question_id,
        contenu=donnees.contenu,
        adresse_ip=adresse_ip,
    )
    return _commentaire_lu(commentaire, utilisateur)


@router.post(
    "/{entretien_id}/synthese",
    response_model=CommentaireLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Rédiger la synthèse globale",
)
def synthese(
    entretien_id: UUID,
    donnees: SyntheseEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> CommentaireLu:
    commentaire = commenter_question.rediger_synthese(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        contenu=donnees.contenu,
        adresse_ip=adresse_ip,
    )
    return _commentaire_lu(commentaire, utilisateur)


def _commentaire_lu(commentaire, auteur) -> CommentaireLu:
    return CommentaireLu(
        id=commentaire.id,
        question_id=commentaire.question_id,
        auteur_id=commentaire.auteur_id,
        auteur_nom=auteur.nom_complet,
        contenu=commentaire.contenu,
        est_synthese=commentaire.est_synthese,
        created_at=commentaire.created_at,
    )


@router.post(
    "/{entretien_id}/signer",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Signer l'entretien",
)
def signer(
    entretien_id: UUID,
    donnees: SignatureEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = signer_entretien.executer(
        session,
        signataire=utilisateur,
        entretien_id=entretien_id,
        observation=donnees.observation,
        adresse_ip=adresse_ip,
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.post(
    "/{entretien_id}/cloturer",
    response_model=EntretienLu,
    dependencies=[Depends(exige_permission("tableau_bord:lire"))],
    summary="Clôturer l'entretien signé (RH)",
)
def cloturer(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> EntretienLu:
    entretien = signer_entretien.cloturer(
        session, auteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return EntretienLu.pour(entretien, utilisateur.id, ROLE_RH in utilisateur.codes_roles())


@router.get(
    "/{entretien_id}/objectifs",
    response_model=ObjectifsDeLEntretien,
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Objectifs fixés et objectifs à évaluer",
)
def lister_objectifs(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> ObjectifsDeLEntretien:
    fixes, a_evaluer = gerer_objectifs.consulter(
        session, lecteur=utilisateur, entretien_id=entretien_id
    )
    return ObjectifsDeLEntretien(
        fixes=[ObjectifLu.model_validate(o) for o in fixes],
        a_evaluer=[ObjectifLu.model_validate(o) for o in a_evaluer],
    )


@router.post(
    "/{entretien_id}/objectifs",
    response_model=ObjectifLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("objectif:fixer"))],
    summary="Fixer un objectif pour l'année à venir",
)
def fixer_objectif(
    entretien_id: UUID,
    donnees: ObjectifEcrit,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> ObjectifLu:
    objectif = gerer_objectifs.fixer(
        session,
        auteur=utilisateur,
        entretien_id=entretien_id,
        libelle=donnees.libelle,
        description=donnees.description,
        indicateur=donnees.indicateur,
        echeance=donnees.echeance,
        objectif_parent_id=donnees.objectif_parent_id,
        adresse_ip=adresse_ip,
    )
    return ObjectifLu.model_validate(objectif)


@router.get(
    "/{entretien_id}/export",
    dependencies=[Depends(exige_permission("export:lire"))],
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
    summary="Exporter le compte rendu en PDF",
)
def exporter(
    entretien_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> Response:
    octets, nom = exporter_pdf.executer(
        session, lecteur=utilisateur, entretien_id=entretien_id, adresse_ip=adresse_ip
    )
    return Response(
        content=octets,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nom}"'},
    )
