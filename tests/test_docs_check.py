from __future__ import annotations

from pathlib import Path

from scripts.check_docs import check_docs


def test_aceita_link_e_tarefa_documentada(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[Arquitetura](docs/architecture.md) e `python scripts/dev.py validate`.",
        encoding="utf-8",
    )
    (tmp_path / "docs/architecture.md").write_text("# Arquitetura\n", encoding="utf-8")
    assert check_docs(tmp_path) == []


def test_encontra_link_e_tarefa_inexistentes(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[Ausente](docs/nope.md) e `python scripts/dev.py nao-existe`.", encoding="utf-8"
    )
    assert len(check_docs(tmp_path)) == 2
