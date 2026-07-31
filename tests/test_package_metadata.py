"""Testes básicos de metadados do pacote."""

from __future__ import annotations

import tomllib
from pathlib import Path

import acervo_visual_inteligente


def test_package_version_matches_project_metadata() -> None:
    """A versão pública do pacote deve seguir o padrão esperado."""
    assert acervo_visual_inteligente.__version__ == "2.0.0"


def test_pyproject_points_to_gui_entrypoint() -> None:
    """O template adaptado deve expor a entrada gráfica do acervo."""
    pyproject = Path("pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    assert data["project"]["name"] == "acervo-visual-inteligente"
    assert (
        data["project"]["gui-scripts"]["acervo-visual-gui"]
        == "acervo_visual_inteligente.gui:main"
    )
