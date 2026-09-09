from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from fpdf import FPDF

POLICE = "helvetica"
MARGE = 15
LARGEUR_UTILE = 210 - 2 * MARGE


@dataclass(slots=True)
class LigneReponse:
    auteur: str
    valeur: str


@dataclass(slots=True)
class LigneQuestion:
    libelle: str
    cible: str
    reponses: list[LigneReponse] = field(default_factory=list)
    commentaires: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LigneSection:
    titre: str
    questions: list[LigneQuestion] = field(default_factory=list)


@dataclass(slots=True)
class LigneObjectif:
    libelle: str
    indicateur: str | None
    echeance: date | None
    statut: str
    niveau_atteinte: int | None


@dataclass(slots=True)
class CompteRendu:
    titre: str
    collaborateur: str
    manager: str
    campagne: str
    type_entretien: str
    statut: str
    sections: list[LigneSection] = field(default_factory=list)
    synthese: str | None = None
    objectifs: list[LigneObjectif] = field(default_factory=list)
    signe_collaborateur_le: datetime | None = None
    signe_manager_le: datetime | None = None
    observation_collaborateur: str | None = None
    contenu_masque: bool = False


def _imprimable(texte: str) -> str:
    return texte.encode("latin-1", errors="replace").decode("latin-1")


def _horodatage(valeur: datetime | None) -> str:
    return valeur.strftime("%d/%m/%Y à %H:%M UTC") if valeur else "non signé"


class _Document(FPDF):
    def footer(self) -> None:  # pragma: no cover
        self.set_y(-15)
        self.set_font(POLICE, "I", 8)
        self.set_text_color(120)
        self.cell(0, 10, _imprimable(f"Page {self.page_no()}/{{nb}}"), align="C")


def rendre(compte_rendu: CompteRendu) -> bytes:
    pdf = _Document()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(MARGE, MARGE, MARGE)
    pdf.add_page()

    _entete(pdf, compte_rendu)
    if compte_rendu.contenu_masque:
        _encadre_confidentialite(pdf)
    _sections(pdf, compte_rendu)
    _synthese(pdf, compte_rendu)
    _objectifs(pdf, compte_rendu)
    _signatures(pdf, compte_rendu)

    return bytes(pdf.output())


def _titre(pdf: FPDF, texte: str, taille: int = 12) -> None:
    pdf.ln(4)
    pdf.set_font(POLICE, "B", taille)
    pdf.set_text_color(0)
    pdf.multi_cell(LARGEUR_UTILE, 7, _imprimable(texte))


def _paragraphe(pdf: FPDF, texte: str, style: str = "", gris: int = 0) -> None:
    pdf.set_font(POLICE, style, 10)
    pdf.set_text_color(gris)
    pdf.multi_cell(LARGEUR_UTILE, 5, _imprimable(texte))


def _entete(pdf: FPDF, cr: CompteRendu) -> None:
    pdf.set_font(POLICE, "B", 16)
    pdf.multi_cell(LARGEUR_UTILE, 9, _imprimable(cr.titre))
    pdf.ln(2)
    _paragraphe(pdf, f"Collaborateur : {cr.collaborateur}")
    _paragraphe(pdf, f"Manager : {cr.manager}")
    _paragraphe(pdf, f"Campagne : {cr.campagne} ({cr.type_entretien})")
    _paragraphe(pdf, f"Statut : {cr.statut}", gris=100)


def _encadre_confidentialite(pdf: FPDF) -> None:
    pdf.ln(3)
    _paragraphe(
        pdf,
        "Les reponses ne figurent pas dans ce document : elles n'etaient pas "
        "accessibles au demandeur au moment de l'export.",
        style="I",
        gris=120,
    )


def _sections(pdf: FPDF, cr: CompteRendu) -> None:
    for section in cr.sections:
        _titre(pdf, section.titre)
        for question in section.questions:
            _paragraphe(pdf, question.libelle, style="B")
            if not question.reponses:
                _paragraphe(pdf, "(sans reponse)", style="I", gris=140)
            for reponse in question.reponses:
                _paragraphe(pdf, f"  {reponse.auteur} : {reponse.valeur}")
            for commentaire in question.commentaires:
                _paragraphe(pdf, f"  Commentaire : {commentaire}", style="I", gris=90)
            pdf.ln(1)


def _synthese(pdf: FPDF, cr: CompteRendu) -> None:
    if not cr.synthese:
        return
    _titre(pdf, "Synthese de l'entretien")
    _paragraphe(pdf, cr.synthese)


def _objectifs(pdf: FPDF, cr: CompteRendu) -> None:
    if not cr.objectifs:
        return
    _titre(pdf, "Objectifs")
    for objectif in cr.objectifs:
        _paragraphe(pdf, objectif.libelle, style="B")
        details = [f"Statut : {objectif.statut}"]
        if objectif.indicateur:
            details.append(f"Indicateur : {objectif.indicateur}")
        if objectif.echeance:
            details.append(f"Echeance : {objectif.echeance:%d/%m/%Y}")
        if objectif.niveau_atteinte is not None:
            details.append(f"Atteinte : {objectif.niveau_atteinte} %")
        _paragraphe(pdf, "  " + " | ".join(details), gris=90)


def _signatures(pdf: FPDF, cr: CompteRendu) -> None:
    _titre(pdf, "Signatures")
    _paragraphe(pdf, f"{cr.collaborateur} : {_horodatage(cr.signe_collaborateur_le)}")
    _paragraphe(pdf, f"{cr.manager} : {_horodatage(cr.signe_manager_le)}")
    if cr.observation_collaborateur:
        pdf.ln(2)
        _paragraphe(pdf, "Observation du collaborateur (droit de reserve) :", style="B")
        _paragraphe(pdf, cr.observation_collaborateur)
