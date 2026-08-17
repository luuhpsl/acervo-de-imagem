"""Utilitarios puros e neutros de dominio (formatadores, helpers, etc.).

Mantenha aqui apenas funcoes genericas, sem conhecimento de nenhuma feature.
Adicione utilitarios somente quando forem realmente reutilizados.
"""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Converte um texto em um formato amigavel para URLs e identificadores.

    Remove acentos, converte para minusculas e substitui espacos por hifens.
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")
