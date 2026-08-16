"""Tests de migration.

Harnais **générique** : ces tests ne connaissent rien du schéma. Ils vérifient
la mécanique Alembic elle-même et deviennent progressivement plus exigeants au
fur et à mesure que des révisions sont ajoutées.

Tant que `migrations/versions/` est vide, les tests qui n'ont rien à vérifier
se marquent « ignoré » plutôt que de passer en silence — un test vert qui ne
teste rien est pire qu'un test absent.
"""
