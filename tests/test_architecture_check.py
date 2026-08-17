from __future__ import annotations

from pathlib import Path

from scripts.check_architecture import check_architecture


def _write(root: Path, relative: str, content: str) -> None:
    file = root / "src" / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")


def test_aceita_interface_publica_da_feature(tmp_path: Path) -> None:
    _write(tmp_path, "sample/app.py", "from sample.features.notes import list_notes\n")
    _write(tmp_path, "sample/features/notes/__init__.py", "list_notes = object()\n")
    assert check_architecture(tmp_path) == []


def test_rejeita_import_interno_entre_features(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "sample/features/search/use_cases.py",
        "from sample.features.notes.model import Note\n",
    )
    errors = check_architecture(tmp_path)
    assert len(errors) == 1
    assert "__init__.py" in errors[0]


def test_rejeita_import_relativo_entre_features(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "sample/features/search/use_cases.py",
        "from ..notes.model import Note\n",
    )
    assert len(check_architecture(tmp_path)) == 1


def test_rejeita_feature_dentro_de_shared(tmp_path: Path) -> None:
    _write(tmp_path, "sample/shared/lib.py", "from sample.features.notes import Note\n")
    assert len(check_architecture(tmp_path)) == 1
