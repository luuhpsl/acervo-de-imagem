from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from scripts.generate_feature import generate_feature


def _project(root: Path, interface: str = "both") -> None:
    (root / "src/sample/features").mkdir(parents=True)
    (root / ".template-state.json").write_text(
        json.dumps({"packageName": "sample", "interface": interface}), encoding="utf-8"
    )


def test_planeja_e_cria_feature_respeitando_interfaces(tmp_path: Path) -> None:
    _project(tmp_path, "cli")
    planned = generate_feature(tmp_path, "Relatórios Mensais", None, True)
    assert len(planned) == 6
    assert not (tmp_path / "src/sample/features/relatorios_mensais").exists()

    generate_feature(tmp_path, "Relatórios Mensais", None, False)
    feature = tmp_path / "src/sample/features/relatorios_mensais"
    assert (feature / "commands.py").exists()
    assert not (feature / "gui.py").exists()
    assert (tmp_path / "tests/features/relatorios_mensais/test_model.py").exists()
    for file in [
        *feature.rglob("*.py"),
        tmp_path / "tests/features/relatorios_mensais/test_model.py",
    ]:
        source = file.read_text(encoding="utf-8")
        ast.parse(source)
        assert max(map(len, source.splitlines())) <= 100
    with pytest.raises(FileExistsError):
        generate_feature(tmp_path, "Relatórios Mensais", None, False)


def test_rejeita_interface_indisponivel(tmp_path: Path) -> None:
    _project(tmp_path, "gui")
    with pytest.raises(ValueError, match="não está disponível"):
        generate_feature(tmp_path, "Busca", "cli", False)
