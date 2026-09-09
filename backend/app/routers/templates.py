from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependances import SessionDep, UtilisateurCourant, exige_permission
from app.schemas.commun import Page
from app.schemas.template import (
    ReferentielQuestions,
    StructureEcrite,
    TemplateCree,
    TemplateLu,
    TemplateModifie,
    TemplateResume,
)
from app.services.processus import (
    consulter_template,
    creer_template,
    definir_structure_template,
    modifier_template,
    nouvelle_version_template,
    publier_template,
)
from app.services.processus.definir_structure_template import QuestionVoulue, SectionVoulue

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get(
    "/referentiel",
    response_model=ReferentielQuestions,
    dependencies=[Depends(exige_permission("template:lire"))],
    summary="Types de question et cibles disponibles",
)
def referentiel() -> ReferentielQuestions:
    return ReferentielQuestions.actuel()


@router.get(
    "",
    response_model=Page[TemplateResume],
    dependencies=[Depends(exige_permission("template:lire"))],
    summary="Lister les trames",
)
def lister(
    session: SessionDep,
    statut: Annotated[str | None, Query()] = None,
    type_entretien: Annotated[str | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    decalage: Annotated[int, Query(ge=0)] = 0,
) -> Page[TemplateResume]:
    lignes, total = consulter_template.lister(
        session,
        statut=statut,
        type_entretien=type_entretien,
        limite=limite,
        decalage=decalage,
    )
    return Page(
        elements=[TemplateResume.depuis_modele(ligne) for ligne in lignes],
        total=total,
        limite=limite,
        decalage=decalage,
    )


@router.get(
    "/{template_id}",
    response_model=TemplateLu,
    dependencies=[Depends(exige_permission("template:lire"))],
    summary="Consulter une trame et son arborescence",
)
def consulter(template_id: UUID, session: SessionDep) -> TemplateLu:
    return TemplateLu.depuis_modele(consulter_template.consulter(session, template_id=template_id))


@router.post(
    "",
    response_model=TemplateLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("template:creer"))],
    summary="Créer une trame en brouillon",
)
def creer(
    donnees: TemplateCree, session: SessionDep, utilisateur: UtilisateurCourant
) -> TemplateLu:
    template = creer_template.executer(
        session,
        auteur=utilisateur,
        nom=donnees.nom,
        type_entretien=donnees.type_entretien.value,
        description=donnees.description,
    )
    return TemplateLu.depuis_modele(template)


@router.patch(
    "/{template_id}",
    response_model=TemplateLu,
    dependencies=[Depends(exige_permission("template:modifier"))],
    summary="Modifier les métadonnées d'une trame",
)
def modifier(
    template_id: UUID,
    donnees: TemplateModifie,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> TemplateLu:
    template = modifier_template.executer(
        session,
        auteur=utilisateur,
        template_id=template_id,
        nom=donnees.nom,
        description=donnees.description,
        champs_fournis=donnees.model_fields_set,
    )
    return TemplateLu.depuis_modele(template)


@router.put(
    "/{template_id}/structure",
    response_model=TemplateLu,
    dependencies=[Depends(exige_permission("template:modifier"))],
    summary="Remplacer l'arborescence d'une trame",
)
def definir_structure(
    template_id: UUID,
    donnees: StructureEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> TemplateLu:
    template = definir_structure_template.executer(
        session,
        auteur=utilisateur,
        template_id=template_id,
        sections=[
            SectionVoulue(
                titre=section.titre,
                description=section.description,
                questions=[
                    QuestionVoulue(
                        libelle=question.libelle,
                        type_question=question.type_question.value,
                        cible=question.cible.value,
                        obligatoire=question.obligatoire,
                        aide=question.aide,
                        configuration=question.configuration,
                    )
                    for question in section.questions
                ],
            )
            for section in donnees.sections
        ],
    )
    return TemplateLu.depuis_modele(template)


@router.post(
    "/{template_id}/publier",
    response_model=TemplateLu,
    dependencies=[Depends(exige_permission("template:publier"))],
    summary="Publier une trame",
)
def publier(template_id: UUID, session: SessionDep, utilisateur: UtilisateurCourant) -> TemplateLu:
    template = publier_template.executer(session, auteur=utilisateur, template_id=template_id)
    return TemplateLu.depuis_modele(template)


@router.post(
    "/{template_id}/nouvelle-version",
    response_model=TemplateLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("template:creer"))],
    summary="Créer une nouvelle version d'une trame publiée",
)
def nouvelle_version(
    template_id: UUID, session: SessionDep, utilisateur: UtilisateurCourant
) -> TemplateLu:
    template = nouvelle_version_template.executer(
        session, auteur=utilisateur, template_id=template_id
    )
    return TemplateLu.depuis_modele(template)
