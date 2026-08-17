from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app_template.features.notes.model import Note, NoteValidationError, create_note, validate_title


def test_validate_title_valid() -> None:
    assert validate_title("  Minha nota  ") == "Minha nota"


def test_validate_title_empty() -> None:
    with pytest.raises(NoteValidationError, match="obrigatório") as error:
        validate_title("   ")
    assert error.value.code == "NOTE_TITLE_REQUIRED"


def test_create_note() -> None:
    note = create_note("Teste")
    assert note.title == "Teste"
    assert note.id is not None
    assert note.created_at is not None


def test_create_note_registra_data_com_fuso() -> None:
    """Sem fuso explícito, notas de máquinas diferentes ficariam incomparáveis."""
    created_at = datetime.fromisoformat(create_note("Com fuso").created_at)

    assert created_at.tzinfo is not None
    assert created_at.utcoffset() == timedelta(0)


def test_note_record_round_trip() -> None:
    note = create_note("Persistida")
    assert Note.from_record(note.to_record()) == note


def test_note_rejects_invalid_record() -> None:
    with pytest.raises(ValueError, match="Data"):
        Note.from_record({"id": "1", "title": "Nota", "created_at": "ontem"})
