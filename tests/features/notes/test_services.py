from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest

from app_template.features.notes.model import create_note
from app_template.features.notes.services import (
    NoteStorageConflictError,
    NoteStorageError,
    load_notes,
    load_notes_snapshot,
    save_notes,
)


def test_preserva_arquivo_corrompido_e_reporta_erro(isolated_data_dir: Any) -> None:
    path = isolated_data_dir / "notes.json"
    path.write_text("{corrompido", encoding="utf-8")

    with pytest.raises(NoteStorageError, match="corrompido"):
        load_notes()
    assert path.read_text(encoding="utf-8") == "{corrompido"
    assert (isolated_data_dir / "notes.backup.json").read_text(encoding="utf-8") == "{corrompido"


def test_salva_e_carrega_notas_validas(isolated_data_dir: Any) -> None:
    note = create_note("Persistida")
    snapshot = save_notes([note])
    assert snapshot.revision == 1
    assert load_notes() == [note]


def test_migra_lista_legada_para_envelope_versionado(isolated_data_dir: Any) -> None:
    note = create_note("Legada")
    path = isolated_data_dir / "notes.json"
    path.write_text(json.dumps([note.to_record()]), encoding="utf-8")

    assert load_notes_snapshot().revision == 1
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


def test_detecta_revisao_desatualizada(isolated_data_dir: Any) -> None:
    first = save_notes([create_note("Primeira")])
    save_notes([create_note("Segunda")], expected_revision=first.revision)

    with pytest.raises(NoteStorageConflictError):
        save_notes([], expected_revision=first.revision)


def test_detecta_outro_processo_com_lock_ativo(isolated_data_dir: Any) -> None:
    (isolated_data_dir / "notes.lock").write_text("ocupado", encoding="utf-8")
    with pytest.raises(NoteStorageConflictError):
        save_notes([create_note("Concorrente")])


def test_recupera_lock_abandonado_por_processo_morto(isolated_data_dir: Any) -> None:
    """Um lock órfão não pode deixar as notas permanentemente somente-leitura."""
    lock = isolated_data_dir / "notes.lock"
    lock.write_text(json.dumps({"pid": 999_999, "acquired_at": 0.0}), encoding="utf-8")

    note = create_note("Depois do crash")
    assert save_notes([note]).revision == 1
    assert load_notes() == [note]
    assert not lock.exists()


def test_recupera_lock_antigo_sem_metadados(isolated_data_dir: Any) -> None:
    lock = isolated_data_dir / "notes.lock"
    lock.write_text("formato desconhecido", encoding="utf-8")
    stale = time.time() - 3600
    os.utime(lock, (stale, stale))

    assert save_notes([create_note("Recuperada")]).revision == 1


def test_reporta_falha_de_escrita(isolated_data_dir: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    original_open: Any = Path.open

    def fail_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        # Só a escrita do arquivo temporário falha; a leitura precisa continuar.
        if self.suffix == ".tmp":
            raise OSError("sem espaço")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.open", fail_open)
    with pytest.raises(NoteStorageError, match="salvar"):
        save_notes([create_note("Falha")])
