from __future__ import annotations

from datetime import UTC, date, datetime

from app.services.rendu.compte_rendu_pdf import (
    CompteRendu,
    LigneObjectif,
    LigneQuestion,
    LigneReponse,
    LigneSection,
    rendre,
)


def compte_rendu(**remplacements) -> CompteRendu:
    base = {
        "titre": "Entretien annuel 2026",
        "collaborateur": "Sophie Petit",
        "manager": "Julien Dupont",
        "campagne": "Campagne 2026",
        "type_entretien": "ANNUEL",
        "statut": "SIGNE",
        "sections": [
            LigneSection(
                titre="Bilan",
                questions=[
                    LigneQuestion(
                        libelle="Vos réussites ?",
                        cible="COLLABORATEUR",
                        reponses=[LigneReponse(auteur="Sophie Petit", valeur="Refonte livrée")],
                        commentaires=["Julien Dupont : très bon travail"],
                    )
                ],
            )
        ],
        "signe_collaborateur_le": datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
        "signe_manager_le": datetime(2026, 3, 1, 11, 0, tzinfo=UTC),
    }
    return CompteRendu(**{**base, **remplacements})


def test_produit_un_pdf_valide() -> None:
    octets = rendre(compte_rendu())
    assert octets.startswith(b"%PDF-")
    assert b"%%EOF" in octets
    assert len(octets) > 800


def test_un_document_sans_reponse_reste_exportable() -> None:
    octets = rendre(compte_rendu(sections=[]))
    assert octets.startswith(b"%PDF-")


def test_les_caracteres_hors_latin1_ne_font_pas_echouer_l_export() -> None:
    octets = rendre(
        compte_rendu(
            titre="Entretien « annuel » 2026 🎯",
            sections=[
                LigneSection(
                    titre="Bilan — synthèse",
                    questions=[
                        LigneQuestion(
                            libelle="Réussites ✓",
                            cible="COLLABORATEUR",
                            reponses=[LigneReponse(auteur="Sophie", valeur="Projet « Alpha » 🚀")],
                        )
                    ],
                )
            ],
        )
    )
    assert octets.startswith(b"%PDF-")


def test_les_accents_francais_passent() -> None:
    octets = rendre(compte_rendu(collaborateur="Benoît Éléonore Ç"))
    assert octets.startswith(b"%PDF-")


def test_les_objectifs_figurent() -> None:
    octets = rendre(
        compte_rendu(
            objectifs=[
                LigneObjectif(
                    libelle="Former deux alternants",
                    indicateur="Nombre d'alternants",
                    echeance=date(2026, 12, 31),
                    statut="PARTIEL",
                    niveau_atteinte=50,
                )
            ]
        )
    )
    assert len(octets) > len(rendre(compte_rendu()))


def test_un_export_sans_contenu_le_dit() -> None:
    masque = rendre(compte_rendu(contenu_masque=True, sections=[]))
    normal = rendre(compte_rendu(contenu_masque=False, sections=[]))
    assert len(masque) > len(normal)


def test_l_observation_du_collaborateur_est_imprimee() -> None:
    avec = rendre(compte_rendu(observation_collaborateur="Je ne partage pas cette évaluation."))
    assert len(avec) > len(rendre(compte_rendu()))


def test_un_entretien_non_signe_indique_les_signatures_manquantes() -> None:
    octets = rendre(compte_rendu(signe_collaborateur_le=None, signe_manager_le=None))
    assert octets.startswith(b"%PDF-")
