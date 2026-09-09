from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.rate_limit import cache_repond
from app.repositories.sante_repository import SanteRepository


def executer(session: Session) -> dict[str, str]:
    base_ok = SanteRepository(session).base_repond()
    cache_ok = cache_repond()

    return {
        "statut": "ok" if (base_ok and cache_ok) else "degrade",
        "base": "ok" if base_ok else "injoignable",
        "cache": "ok" if cache_ok else "injoignable",
    }
