from __future__ import annotations

import re
import zlib

MOTIF_TEXTE = re.compile(rb"\((?:\\.|[^\\()])*\)\s*Tj")
MOTIF_FLUX = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)


def _desechapper(fragment: bytes) -> str:
    contenu = fragment[1 : fragment.rindex(b")")]
    contenu = contenu.replace(rb"\(", b"(").replace(rb"\)", b")").replace(rb"\\", b"\\")
    return contenu.decode("latin-1", errors="replace")


def texte_du_pdf(octets: bytes) -> str:
    morceaux: list[str] = []
    for flux in MOTIF_FLUX.findall(octets):
        try:
            contenu = zlib.decompress(flux)
        except zlib.error:
            contenu = flux
        for fragment in MOTIF_TEXTE.findall(contenu):
            morceaux.append(_desechapper(fragment[: fragment.rindex(b")") + 1]))
    return "\n".join(morceaux)
