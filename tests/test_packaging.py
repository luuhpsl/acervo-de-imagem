"""Contratos do empacotamento declarados em `pyproject.toml`."""

from __future__ import annotations

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _pyproject() -> dict[str, object]:
    data: dict[str, object] = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return data


def test_grupo_dev_e_extra_dev_permanecem_espelhados() -> None:
    """O extra existe para quem usa pip e precisa acompanhar o grupo PEP 735.

    `[project.optional-dependencies]` não aceita `include-group`, então a cópia
    é inevitável. Este teste garante que ela não fique para trás em silêncio.
    """
    data = _pyproject()
    group = data["dependency-groups"]["dev"]  # type: ignore[index]
    extra = data["project"]["optional-dependencies"]["dev"]  # type: ignore[index]

    assert sorted(group) == sorted(extra)


def test_template_permanece_sem_dependencia_de_runtime() -> None:
    data = _pyproject()

    assert data["project"]["dependencies"] == []  # type: ignore[index]
