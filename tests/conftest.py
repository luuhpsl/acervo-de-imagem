"""Configuracao e fixtures compartilhadas de teste.

Fixtures neutras (que servem a mais de uma feature) ficam aqui. Fixtures
especificas de uma feature devem morar junto dos testes daquela feature.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Isola a persistência das features em um diretório temporário.

    Aponta `APP_TEMPLATE_DATA_DIR` para um `tmp_path`, garantindo que os testes
    nunca toquem nos dados reais do usuario e sejam independentes entre si.
    """
    monkeypatch.setenv("APP_TEMPLATE_DATA_DIR", str(tmp_path))
    yield tmp_path
