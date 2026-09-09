from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import StatutEntretien
from app.schemas.commun import SchemaEntree, SchemaSortie


class EntretienCree(SchemaEntree):
    campagne_id: UUID
    collaborateur_id: UUID
    template_id: UUID
    manager_id: UUID | None = None
    date_planifiee: date | None = None


class ActeurLu(SchemaSortie):
    id: UUID
    nom_complet: str
    email: str


class EntretienResume(SchemaSortie):
    id: UUID
    campagne_id: UUID
    type_entretien: str
    statut: str
    date_planifiee: date | None
    collaborateur: ActeurLu
    manager: ActeurLu
    soumis_collaborateur_le: datetime | None
    revue_ouverte_le: datetime | None
    realise_le: datetime | None
    signe_collaborateur_le: datetime | None
    signe_manager_le: datetime | None
    cloture_le: datetime | None
    created_at: datetime

    @classmethod
    def depuis_modele(cls, entretien) -> EntretienResume:
        return cls(
            id=entretien.id,
            campagne_id=entretien.campagne_id,
            type_entretien=entretien.type_entretien,
            statut=entretien.statut,
            date_planifiee=entretien.date_planifiee,
            collaborateur=ActeurLu(
                id=entretien.collaborateur.id,
                nom_complet=entretien.collaborateur.nom_complet,
                email=entretien.collaborateur.email,
            ),
            manager=ActeurLu(
                id=entretien.manager.id,
                nom_complet=entretien.manager.nom_complet,
                email=entretien.manager.email,
            ),
            soumis_collaborateur_le=entretien.soumis_collaborateur_le,
            revue_ouverte_le=entretien.revue_ouverte_le,
            realise_le=entretien.realise_le,
            signe_collaborateur_le=entretien.signe_collaborateur_le,
            signe_manager_le=entretien.signe_manager_le,
            cloture_le=entretien.cloture_le,
            created_at=entretien.created_at,
        )


class EntretienLu(EntretienResume):
    motif_annulation: str | None
    observation_collaborateur: str | None
    mon_role: str | None
    transitions_possibles: list[str]

    @classmethod
    def pour(cls, entretien, lecteur_id: UUID, est_rh: bool) -> EntretienLu:
        from app.services.regles import transitions_entretien as etats

        role = entretien.role_de(lecteur_id) or (etats.RH if est_rh else None)
        resume = EntretienResume.depuis_modele(entretien)
        return cls(
            **resume.model_dump(),
            motif_annulation=entretien.motif_annulation,
            observation_collaborateur=entretien.observation_collaborateur,
            mon_role=role,
            transitions_possibles=(
                etats.transitions_possibles(entretien.statut, role) if role else []
            ),
        )


class AnnulationEcrite(SchemaEntree):
    motif: str = Field(min_length=1, max_length=2000)


class StatutCompte(SchemaSortie):
    statut: str
    nombre: int


class TableauDeBordLu(SchemaSortie):
    campagne_id: UUID
    campagne_libelle: str
    annee: int
    date_limite: date
    echue: bool
    total: int
    termines: int
    taux_avancement: float
    par_statut: list[StatutCompte]
    en_retard: list[EntretienResume]

    @classmethod
    def depuis_modele(cls, tableau) -> TableauDeBordLu:
        return cls(
            campagne_id=tableau.campagne.id,
            campagne_libelle=tableau.campagne.libelle,
            annee=tableau.campagne.annee,
            date_limite=tableau.campagne.date_limite,
            echue=tableau.echue,
            total=tableau.total,
            termines=tableau.termines,
            taux_avancement=round(tableau.taux_avancement, 4),
            par_statut=[
                StatutCompte(statut=statut, nombre=nombre)
                for statut, nombre in sorted(
                    tableau.par_statut.items(), key=lambda paire: StatutEntretien(paire[0]).value
                )
            ],
            en_retard=[EntretienResume.depuis_modele(e) for e in tableau.en_retard],
        )
