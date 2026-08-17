from __future__ import annotations

from typing import Any

from app_template.features.notes.use_cases import add_note, list_notes, remove_note


def test_add_and_list_notes(isolated_data_dir: Any) -> None:
    assert len(list_notes()) == 0
    note = add_note("Primeira")
    notes = list_notes()
    assert len(notes) == 1
    assert notes[0].id == note.id
    assert notes[0].title == "Primeira"


def test_remove_note(isolated_data_dir: Any) -> None:
    note = add_note("Para remover")
    assert len(list_notes()) == 1

    assert remove_note(note.id) is True
    assert len(list_notes()) == 0

    assert remove_note("id_inexistente") is False
