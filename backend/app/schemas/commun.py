from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SchemaEntree(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SchemaSortie(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReponseErreur(BaseModel):
    message: str
    details: list = Field(default_factory=list)


class Page[T](SchemaSortie):
    elements: list[T]
    total: int
    limite: int
    decalage: int
