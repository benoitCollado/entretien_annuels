from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

PARTAGEE = "PARTAGEE"


class QuestionLisible(Protocol):
    id: UUID
    libelle: str
    obligatoire: bool
    cible: str


def concerne(cible_question: str, cible_acteur: str) -> bool:
    return cible_question in (cible_acteur, PARTAGEE)


def questions_obligatoires_manquantes(
    questions: Iterable[QuestionLisible],
    questions_repondues: set[UUID],
    cible: str,
) -> list[QuestionLisible]:
    return [
        question
        for question in questions
        if question.obligatoire
        and concerne(question.cible, cible)
        and question.id not in questions_repondues
    ]


def taux_avancement(
    questions: Iterable[QuestionLisible],
    questions_repondues: set[UUID],
    cible: str,
) -> float:
    concernees = [q for q in questions if concerne(q.cible, cible)]
    if not concernees:
        return 1.0
    repondues = sum(1 for q in concernees if q.id in questions_repondues)
    return repondues / len(concernees)
