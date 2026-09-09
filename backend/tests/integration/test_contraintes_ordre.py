from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.template import QuestionTemplate, SectionTemplate, Template

pytestmark = pytest.mark.integration


def _trame_a_deux_sections(session: Session) -> Template:
    template = Template(
        nom=f"Trame {id(session)}",
        type_entretien="ANNUEL",
        version=1,
        statut="BROUILLON",
        sections=[
            SectionTemplate(
                titre="Première",
                ordre=0,
                questions=[
                    QuestionTemplate(
                        libelle="Q1", type_question="texte_libre", cible="COLLABORATEUR", ordre=0
                    )
                ],
            ),
            SectionTemplate(
                titre="Seconde",
                ordre=1,
                questions=[
                    QuestionTemplate(
                        libelle="Q2", type_question="texte_libre", cible="COLLABORATEUR", ordre=0
                    )
                ],
            ),
        ],
    )
    session.add(template)
    session.flush()
    return template


class TestReordonnancement:
    def test_echanger_deux_sections_dans_une_transaction(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        premiere, seconde = template.sections

        premiere.ordre = 1
        seconde.ordre = 0
        session.flush()

        session.expire_all()
        ordres = {section.titre: section.ordre for section in template.sections}
        assert ordres == {"Première": 1, "Seconde": 0}

    def test_echanger_deux_questions_dans_une_transaction(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        section = template.sections[0]
        section.questions.append(
            QuestionTemplate(
                libelle="Q1bis", type_question="texte_libre", cible="COLLABORATEUR", ordre=1
            )
        )
        session.flush()

        premiere, seconde = section.questions
        premiere.ordre, seconde.ordre = 1, 0
        session.flush()

        session.expire_all()
        assert {q.libelle: q.ordre for q in section.questions} == {"Q1": 1, "Q1bis": 0}

    def test_la_contrainte_mord_quand_meme_au_commit(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        template.sections[1].ordre = 0

        with pytest.raises(IntegrityError):
            session.flush()
            session.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

    def test_une_contrainte_immediate_refuserait_l_echange(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        session.execute(text("SET CONSTRAINTS uq_section_template_ordre IMMEDIATE"))

        premiere, seconde = template.sections
        premiere.ordre = 1
        seconde.ordre = 0

        with pytest.raises(IntegrityError):
            session.flush()


class TestContraintesTemplate:
    def test_nom_et_version_uniques(self, session: Session) -> None:
        session.add(Template(nom="Doublon", type_entretien="ANNUEL", version=1))
        session.flush()
        session.add(Template(nom="Doublon", type_entretien="ANNUEL", version=1))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_deux_versions_du_meme_nom_coexistent(self, session: Session) -> None:
        session.add(Template(nom="Evolutive", type_entretien="ANNUEL", version=1))
        session.add(Template(nom="Evolutive", type_entretien="ANNUEL", version=2))
        session.flush()

    def test_statut_hors_liste_refuse(self, session: Session) -> None:
        session.add(Template(nom="Statut", type_entretien="ANNUEL", statut="INVENTE"))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_type_entretien_hors_liste_refuse(self, session: Session) -> None:
        session.add(Template(nom="Type", type_entretien="INVENTE"))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_version_zero_refusee(self, session: Session) -> None:
        session.add(Template(nom="V0", type_entretien="ANNUEL", version=0))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_supprimer_une_trame_emporte_son_arborescence(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        identifiant = template.id

        session.delete(template)
        session.flush()

        restantes = session.execute(
            text("SELECT count(*) FROM section_template WHERE template_id = :id"),
            {"id": identifiant},
        ).scalar()
        assert restantes == 0


class TestContraintesQuestion:
    def test_configuration_doit_etre_un_objet(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        template.sections[0].questions[0].configuration = ["pas", "un", "objet"]
        with pytest.raises(IntegrityError):
            session.flush()

    def test_type_question_hors_liste_refuse(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        template.sections[0].questions[0].type_question = "invente"
        with pytest.raises(IntegrityError):
            session.flush()

    def test_cible_hors_liste_refusee(self, session: Session) -> None:
        template = _trame_a_deux_sections(session)
        template.sections[0].questions[0].cible = "INVENTEE"
        with pytest.raises(IntegrityError):
            session.flush()


class TestContraintesCampagne:
    def test_dates_incoherentes_refusees(self, session: Session) -> None:
        from datetime import date

        from app.models.campagne import Campagne

        session.add(
            Campagne(
                libelle="Incohérente",
                annee=2026,
                type_entretien="ANNUEL",
                date_ouverture=date(2026, 12, 31),
                date_limite=date(2026, 1, 1),
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()

    def test_une_seule_campagne_par_annee_et_type(self, session: Session) -> None:
        from datetime import date

        from app.models.campagne import Campagne

        for libelle in ("Première", "Seconde"):
            session.add(
                Campagne(
                    libelle=libelle,
                    annee=2031,
                    type_entretien="ANNUEL",
                    date_ouverture=date(2031, 1, 1),
                    date_limite=date(2031, 12, 31),
                )
            )
        with pytest.raises(IntegrityError):
            session.flush()
