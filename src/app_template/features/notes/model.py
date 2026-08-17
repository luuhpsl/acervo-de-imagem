from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict


class NoteRecord(TypedDict):
    id: str
    title: str
    created_at: str


class NoteValidationError(ValueError):
    """Erro de validação com código estável para os adaptadores."""

    code = "NOTE_TITLE_REQUIRED"


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    created_at: str

    @classmethod
    def from_record(cls, value: object) -> Note:
        if not isinstance(value, dict):
            raise ValueError("Registro de nota inválido.")

        note_id = value.get("id")
        title = value.get("title")
        created_at = value.get("created_at")
        if not isinstance(note_id, str) or not note_id:
            raise ValueError("ID de nota inválido.")
        if not isinstance(title, str):
            raise ValueError("Título de nota inválido.")
        if not isinstance(created_at, str):
            raise ValueError("Data de nota inválida.")

        try:
            datetime.fromisoformat(created_at)
        except ValueError as exc:
            raise ValueError("Data de nota inválida.") from exc

        return cls(id=note_id, title=validate_title(title), created_at=created_at)

    def to_record(self) -> NoteRecord:
        return {"id": self.id, "title": self.title, "created_at": self.created_at}


def validate_title(title: str) -> str:
    cleaned = title.strip()
    if not cleaned:
        raise NoteValidationError("O título da nota é obrigatório.")
    return cleaned


def create_note(title: str) -> Note:
    """Cria uma nota com identificador único e data de criação em UTC.

    A data é gravada com fuso explícito para que notas criadas em máquinas ou
    fusos diferentes continuem comparáveis e ordenáveis entre si.
    """
    cleaned_title = validate_title(title)
    return Note(
        id=str(uuid.uuid4()),
        title=cleaned_title,
        created_at=datetime.now(UTC).isoformat(),
    )
