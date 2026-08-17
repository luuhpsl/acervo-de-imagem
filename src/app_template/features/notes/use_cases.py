from __future__ import annotations

from app_template.features.notes.model import Note, create_note
from app_template.features.notes.services import load_notes_snapshot, save_notes


def list_notes() -> list[Note]:
    return load_notes_snapshot().notes


def add_note(title: str) -> Note:
    note = create_note(title)
    snapshot = load_notes_snapshot()
    save_notes([*snapshot.notes, note], expected_revision=snapshot.revision)
    return note


def remove_note(note_id: str) -> bool:
    snapshot = load_notes_snapshot()
    filtered_notes = [note for note in snapshot.notes if note.id != note_id]
    if len(filtered_notes) == len(snapshot.notes):
        return False
    save_notes(filtered_notes, expected_revision=snapshot.revision)
    return True
