"""Modèles ORM.

⚠️ Chaque nouveau module de modèle DOIT être importé ici. L'oublier rend le test
de dérive `test_aucune_derive_entre_modeles_et_migrations` **faussement vert** :
une table absente des métadonnées ne peut produire aucune différence. Le test
comporte une assertion de garde sur le nombre de tables pour rattraper l'oubli.
"""

from app.models.base import ArchivableMixin, Base, HorodatageMixin
from app.models.role import Permission, Role, role_permission, utilisateur_role
from app.models.utilisateur import Utilisateur

# Lots suivants — décommenter et mettre à jour TABLES_ATTENDUES dans
# tests/migrations/test_schema.py :
#   from app.models.campagne import Campagne                    # lot 2
#   from app.models.template import Template, ...               # lot 2
#   from app.models.entretien import Entretien                  # lot 3
#   from app.models.questionnaire import Questionnaire, ...     # lot 3
#   from app.models.reponse import Reponse                      # lot 4

__all__ = [
    "ArchivableMixin",
    "Base",
    "HorodatageMixin",
    "Permission",
    "Role",
    "Utilisateur",
    "role_permission",
    "utilisateur_role",
]
