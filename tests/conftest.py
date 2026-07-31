"""Configuração compartilhada dos testes."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Isola dados locais em um diretório temporário."""
    monkeypatch.setenv("ACERVO_VISUAL_DATA_DIR", str(tmp_path))
    yield tmp_path
