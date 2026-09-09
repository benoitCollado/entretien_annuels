from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.models.template import QuestionTemplate, SectionTemplate, Template
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    modele = Template

    def _avec_arborescence(self) -> Select[tuple[Template]]:
        return select(Template).options(
            selectinload(Template.sections).selectinload(SectionTemplate.questions)
        )

    def get_avec_arborescence(self, id_: UUID) -> Template | None:
        stmt = self._avec_arborescence().where(Template.id == id_)
        return self.session.scalars(stmt).one_or_none()

    def get_par_nom_et_version(self, nom: str, version: int) -> Template | None:
        stmt = select(Template).where(Template.nom == nom, Template.version == version)
        return self.session.scalars(stmt).one_or_none()

    def derniere_version(self, nom: str) -> int:
        stmt = select(func.max(Template.version)).where(Template.nom == nom)
        return self.session.scalar(stmt) or 0

    def _base_liste(
        self, *, statut: str | None, type_entretien: str | None
    ) -> Select[tuple[Template]]:
        stmt = select(Template)
        if statut is not None:
            stmt = stmt.where(Template.statut == statut)
        if type_entretien is not None:
            stmt = stmt.where(Template.type_entretien == type_entretien)
        return stmt

    def lister_filtre(
        self,
        *,
        statut: str | None = None,
        type_entretien: str | None = None,
        limite: int = 50,
        decalage: int = 0,
    ) -> list[Template]:
        stmt = (
            self._base_liste(statut=statut, type_entretien=type_entretien)
            .options(selectinload(Template.sections).selectinload(SectionTemplate.questions))
            .order_by(Template.nom, Template.version.desc())
            .limit(limite)
            .offset(decalage)
        )
        return list(self.session.scalars(stmt))

    def compter(self, *, statut: str | None = None, type_entretien: str | None = None) -> int:
        stmt = self._base_liste(statut=statut, type_entretien=type_entretien).with_only_columns(
            func.count(Template.id)
        )
        return self.session.scalar(stmt) or 0

    def remplacer_sections(self, template: Template, sections: list[SectionTemplate]) -> None:
        template.sections = sections
        self.session.flush()

    def compter_questions(self, template_id: UUID) -> int:
        stmt = (
            select(func.count(QuestionTemplate.id))
            .join(SectionTemplate, SectionTemplate.id == QuestionTemplate.section_template_id)
            .where(SectionTemplate.template_id == template_id)
        )
        return self.session.scalar(stmt) or 0
