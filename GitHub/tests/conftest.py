"""Configuração compartilhada dos testes."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_SRC = REPOSITORY_ROOT / "Programa Acervo de Imagens" / "src"
if str(APPLICATION_SRC) not in sys.path:
    sys.path.insert(0, str(APPLICATION_SRC))


@pytest.fixture
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Isola dados locais em um diretório temporário."""
    monkeypatch.setenv("ACERVO_VISUAL_DATA_DIR", str(tmp_path))
    yield tmp_path
