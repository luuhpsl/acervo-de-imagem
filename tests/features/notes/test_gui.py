from __future__ import annotations

import pytest

from app_template.features.notes.gui import NotesController
from app_template.features.notes.model import Note, create_note
from app_template.features.notes.services import NoteStorageError


def test_controller_compartilha_as_acoes_observaveis() -> None:
    notes: list[Note] = []

    def add(title: str) -> Note:
        note = create_note(title)
        notes.append(note)
        return note

    def remove(note_id: str) -> bool:
        before = len(notes)
        notes[:] = [note for note in notes if note.id != note_id]
        return len(notes) != before

    controller = NotesController(lambda: list(notes), add, remove)
    added = controller.add("GUI")
    assert [note.title for note in added] == ["GUI"]
    assert controller.remove([added[0].id]) == []


def test_controller_propaga_falha_de_armazenamento() -> None:
    def fail() -> list[Note]:
        raise NoteStorageError("NOTE_STORAGE_READ_FAILED", "indisponível")

    controller = NotesController(list_fn=fail)
    with pytest.raises(NoteStorageError, match="indisponível"):
        controller.get_notes()
