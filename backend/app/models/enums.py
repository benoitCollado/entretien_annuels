from __future__ import annotations

from enum import StrEnum


def valeurs_sql(enumeration: type[StrEnum]) -> str:
    return ", ".join(f"'{membre.value}'" for membre in enumeration)


class TypeEntretien(StrEnum):
    ANNUEL = "ANNUEL"
    PROFESSIONNEL = "PROFESSIONNEL"


class StatutTemplate(StrEnum):
    BROUILLON = "BROUILLON"
    PUBLIEE = "PUBLIEE"
    ARCHIVEE = "ARCHIVEE"


class StatutEntretien(StrEnum):
    BROUILLON = "BROUILLON"
    PLANIFIE = "PLANIFIE"
    PREPARATION = "PREPARATION"
    SOUMIS_COLLABORATEUR = "SOUMIS_COLLABORATEUR"
    REVUE_MANAGER = "REVUE_MANAGER"
    ENTRETIEN_REALISE = "ENTRETIEN_REALISE"
    SIGNE = "SIGNE"
    CLOTURE = "CLOTURE"
    ANNULE = "ANNULE"


class RoleActeur(StrEnum):
    COLLABORATEUR = "COLLABORATEUR"
    MANAGER = "MANAGER"
    RH = "RH"


class Action(StrEnum):
    ASSIGNATION = "ASSIGNATION"
    PREMIERE_SAISIE = "PREMIERE_SAISIE"
    ENREGISTREMENT_BROUILLON = "ENREGISTREMENT_BROUILLON"
    SOUMISSION_COLLABORATEUR = "SOUMISSION_COLLABORATEUR"
    OUVERTURE_REVUE = "OUVERTURE_REVUE"
    COMMENTAIRE = "COMMENTAIRE"
    SYNTHESE = "SYNTHESE"
    CLOTURE_ECHANGE = "CLOTURE_ECHANGE"
    SIGNATURE = "SIGNATURE"
    CLOTURE = "CLOTURE"
    ANNULATION = "ANNULATION"
    QUESTION_AD_HOC = "QUESTION_AD_HOC"
    ACCES_REFUSE = "ACCES_REFUSE"
    CONSULTATION = "CONSULTATION"
    OBJECTIF_FIXE = "OBJECTIF_FIXE"
    OBJECTIF_EVALUE = "OBJECTIF_EVALUE"
    EXPORT_PDF = "EXPORT_PDF"


class StatutObjectif(StrEnum):
    EN_COURS = "EN_COURS"
    ATTEINT = "ATTEINT"
    PARTIEL = "PARTIEL"
    NON_ATTEINT = "NON_ATTEINT"


class StatutCampagne(StrEnum):
    BROUILLON = "BROUILLON"
    OUVERTE = "OUVERTE"
    CLOTUREE = "CLOTUREE"


class TypeQuestion(StrEnum):
    TEXTE_LIBRE = "texte_libre"
    TEXTE_COURT = "texte_court"
    ECHELLE = "echelle"
    CHOIX_UNIQUE = "choix_unique"
    CHOIX_MULTIPLE = "choix_multiple"
    OUI_NON = "oui_non"
    DATE = "date"
    NOTE_5 = "note_5"


class Cible(StrEnum):
    COLLABORATEUR = "COLLABORATEUR"
    MANAGER = "MANAGER"
    PARTAGEE = "PARTAGEE"


class CodeRole(StrEnum):
    COLLABORATEUR = "COLLABORATEUR"
    MANAGER = "MANAGER"
    RH = "RH"
    ADMIN = "ADMIN"


class CodePermission(StrEnum):
    UTILISATEUR_LIRE = "utilisateur:lire"
    UTILISATEUR_CREER = "utilisateur:creer"
    UTILISATEUR_MODIFIER = "utilisateur:modifier"
    UTILISATEUR_ARCHIVER = "utilisateur:archiver"
    ROLE_LIRE = "role:lire"
    ROLE_ATTRIBUER = "role:attribuer"
    TEMPLATE_LIRE = "template:lire"
    TEMPLATE_CREER = "template:creer"
    TEMPLATE_MODIFIER = "template:modifier"
    TEMPLATE_PUBLIER = "template:publier"
    CAMPAGNE_LIRE = "campagne:lire"
    CAMPAGNE_CREER = "campagne:creer"
    CAMPAGNE_OUVRIR = "campagne:ouvrir"
    CAMPAGNE_CLOTURER = "campagne:cloturer"
    ENTRETIEN_LIRE = "entretien:lire"
    ENTRETIEN_CREER = "entretien:creer"
    TABLEAU_BORD_LIRE = "tableau_bord:lire"
    OBJECTIF_FIXER = "objectif:fixer"
    EXPORT_LIRE = "export:lire"


PERMISSIONS_PAR_ROLE: dict[CodeRole, tuple[CodePermission, ...]] = {
    CodeRole.ADMIN: tuple(CodePermission),
    CodeRole.RH: (
        CodePermission.UTILISATEUR_LIRE,
        CodePermission.UTILISATEUR_CREER,
        CodePermission.UTILISATEUR_MODIFIER,
        CodePermission.ROLE_LIRE,
        CodePermission.TEMPLATE_LIRE,
        CodePermission.TEMPLATE_CREER,
        CodePermission.TEMPLATE_MODIFIER,
        CodePermission.TEMPLATE_PUBLIER,
        CodePermission.CAMPAGNE_LIRE,
        CodePermission.CAMPAGNE_CREER,
        CodePermission.CAMPAGNE_OUVRIR,
        CodePermission.CAMPAGNE_CLOTURER,
        CodePermission.ENTRETIEN_LIRE,
        CodePermission.ENTRETIEN_CREER,
        CodePermission.TABLEAU_BORD_LIRE,
        CodePermission.EXPORT_LIRE,
    ),
    CodeRole.MANAGER: (
        CodePermission.UTILISATEUR_LIRE,
        CodePermission.ROLE_LIRE,
        CodePermission.TEMPLATE_LIRE,
        CodePermission.CAMPAGNE_LIRE,
        CodePermission.ENTRETIEN_LIRE,
        CodePermission.ENTRETIEN_CREER,
        CodePermission.OBJECTIF_FIXER,
        CodePermission.EXPORT_LIRE,
    ),
    CodeRole.COLLABORATEUR: (
        CodePermission.ENTRETIEN_LIRE,
        CodePermission.EXPORT_LIRE,
    ),
}

LIBELLES_ROLE: dict[CodeRole, str] = {
    CodeRole.COLLABORATEUR: "Collaborateur",
    CodeRole.MANAGER: "Manager",
    CodeRole.RH: "Responsable RH",
    CodeRole.ADMIN: "Administrateur",
}

LIBELLES_PERMISSION: dict[CodePermission, str] = {
    CodePermission.UTILISATEUR_LIRE: "Consulter les utilisateurs",
    CodePermission.UTILISATEUR_CREER: "Créer un utilisateur",
    CodePermission.UTILISATEUR_MODIFIER: "Modifier un utilisateur",
    CodePermission.UTILISATEUR_ARCHIVER: "Archiver un utilisateur",
    CodePermission.ROLE_LIRE: "Consulter les rôles",
    CodePermission.ROLE_ATTRIBUER: "Attribuer un rôle",
    CodePermission.TEMPLATE_LIRE: "Consulter les trames",
    CodePermission.TEMPLATE_CREER: "Créer une trame",
    CodePermission.TEMPLATE_MODIFIER: "Modifier une trame en brouillon",
    CodePermission.TEMPLATE_PUBLIER: "Publier une trame",
    CodePermission.CAMPAGNE_LIRE: "Consulter les campagnes",
    CodePermission.CAMPAGNE_CREER: "Créer une campagne",
    CodePermission.CAMPAGNE_OUVRIR: "Ouvrir une campagne",
    CodePermission.CAMPAGNE_CLOTURER: "Clôturer une campagne",
    CodePermission.ENTRETIEN_LIRE: "Consulter les entretiens de son périmètre",
    CodePermission.ENTRETIEN_CREER: "Créer un entretien",
    CodePermission.TABLEAU_BORD_LIRE: "Consulter l'avancement (statuts seuls)",
    CodePermission.OBJECTIF_FIXER: "Fixer et évaluer des objectifs",
    CodePermission.EXPORT_LIRE: "Exporter un compte rendu en PDF",
}
