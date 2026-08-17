from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path

from app_template.features.notes.model import Note

_STATE_FILENAME = "notes.json"
_SCHEMA_VERSION = 1
_ENV_DATA_DIR = "APP_TEMPLATE_DATA_DIR"
# Um lock mais antigo que isto pertence a um processo que morreu sem liberá-lo.
# Todas as operações protegidas são curtas (ler e reescrever um JSON pequeno),
# então a margem é folgada o bastante para nunca roubar um lock legítimo.
_LOCK_TTL_SECONDS = 30.0


@dataclass(frozen=True)
class NotesSnapshot:
    notes: list[Note]
    revision: int


class NoteStorageError(RuntimeError):
    """Falha observável ao ler ou persistir notas."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class NoteStorageConflictError(NoteStorageError):
    def __init__(self) -> None:
        super().__init__(
            "NOTE_STORAGE_CONFLICT",
            "As notas estão sendo alteradas por outro processo. Tente novamente.",
        )


def _default_data_dir() -> Path:
    override = os.environ.get(_ENV_DATA_DIR)
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "app-template"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "app-template"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "app-template"


def _state_path() -> Path:
    return _default_data_dir() / _STATE_FILENAME


def _backup_path() -> Path:
    return _state_path().with_suffix(".backup.json")


def _lock_path() -> Path:
    return _state_path().with_suffix(".lock")


def _create_lock(lock: Path) -> None:
    """Cria o lock de forma exclusiva, registrando quem o adquiriu e quando.

    Levanta ``FileExistsError`` quando outro processo já detém o lock.
    """
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps({"pid": os.getpid(), "acquired_at": time.time()}))


def _lock_is_stale(lock: Path) -> bool:
    """Indica se o lock foi abandonado por um processo que não o liberou."""
    acquired: float | None = None
    with suppress(OSError, json.JSONDecodeError, TypeError, ValueError):
        payload = json.loads(lock.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            acquired = float(payload["acquired_at"])
    if acquired is None:
        # Lock de formato desconhecido: a data de modificação é o melhor sinal.
        try:
            acquired = lock.stat().st_mtime
        except OSError:
            return False
    return (time.time() - acquired) > _LOCK_TTL_SECONDS


@contextmanager
def _exclusive_lock() -> Iterator[None]:
    """Protege a escrita, recuperando-se de locks deixados por processos mortos."""
    lock = _lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        _create_lock(lock)
    except FileExistsError as exc:
        if not _lock_is_stale(lock):
            raise NoteStorageConflictError() from exc
        # O detentor anterior morreu: descarta o lock órfão e tenta uma vez mais.
        # Se outro processo vencer a corrida, o O_EXCL abaixo falha e o conflito
        # volta a ser reportado — nunca dois escritores ao mesmo tempo.
        with suppress(OSError):
            lock.unlink()
        try:
            _create_lock(lock)
        except FileExistsError as retry_exc:
            raise NoteStorageConflictError() from retry_exc
    try:
        yield
    finally:
        with suppress(OSError):
            lock.unlink()


def _preserve_invalid_data(raw: str) -> None:
    backup = _backup_path()
    with suppress(OSError):
        if not backup.exists():
            backup.write_text(raw, encoding="utf-8")


def _parse_notes(values: object) -> list[Note]:
    if not isinstance(values, list):
        raise NoteStorageError(
            "NOTE_STORAGE_INVALID_DATA", "O arquivo de notas está em um formato inválido."
        )
    try:
        return [Note.from_record(item) for item in values]
    except ValueError as exc:
        raise NoteStorageError(
            "NOTE_STORAGE_INVALID_DATA", "Uma ou mais notas salvas estão corrompidas."
        ) from exc


def _read_snapshot() -> tuple[NotesSnapshot, bool]:
    path = _state_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return NotesSnapshot([], 0), False
    except OSError as exc:
        raise NoteStorageError(
            "NOTE_STORAGE_READ_FAILED", "Não foi possível ler as notas salvas."
        ) from exc

    try:
        data: object = json.loads(raw)
        if isinstance(data, list):
            return NotesSnapshot(_parse_notes(data), 0), True
        if not isinstance(data, dict):
            raise NoteStorageError(
                "NOTE_STORAGE_INVALID_DATA", "O arquivo de notas está em um formato inválido."
            )
        if data.get("version") != _SCHEMA_VERSION:
            raise NoteStorageError(
                "NOTE_STORAGE_INVALID_DATA",
                "A versão do arquivo de notas não é compatível com esta aplicação.",
            )
        revision = data.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            raise NoteStorageError(
                "NOTE_STORAGE_INVALID_DATA", "A revisão do arquivo de notas é inválida."
            )
        return NotesSnapshot(_parse_notes(data.get("notes")), revision), False
    except (json.JSONDecodeError, TypeError) as exc:
        _preserve_invalid_data(raw)
        raise NoteStorageError(
            "NOTE_STORAGE_INVALID_DATA", "O arquivo de notas está corrompido."
        ) from exc
    except NoteStorageError:
        _preserve_invalid_data(raw)
        raise


def _sync_directory(directory: Path) -> None:
    """Persiste a própria entrada de diretório após um rename atômico.

    Sem isso, uma queda de energia pode desfazer a troca do arquivo. O Windows
    não permite abrir um diretório para sincronizar, então lá o passo é omitido.
    """
    if os.name == "nt":
        return
    with suppress(OSError):
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _write_snapshot(snapshot: NotesSnapshot) -> None:
    path = _state_path()
    temporary = path.with_suffix(".tmp")
    payload = {
        "version": _SCHEMA_VERSION,
        "revision": snapshot.revision,
        "notes": [note.to_record() for note in snapshot.notes],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Grava, força o conteúdo em disco e só então troca o arquivo: uma queda
        # no meio do caminho deixa o arquivo anterior intacto, nunca um truncado.
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _sync_directory(path.parent)
    except OSError as exc:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise NoteStorageError(
            "NOTE_STORAGE_WRITE_FAILED", "Não foi possível salvar as notas."
        ) from exc


def load_notes_snapshot() -> NotesSnapshot:
    snapshot, legacy = _read_snapshot()
    if not legacy:
        return snapshot
    return save_notes(snapshot.notes, expected_revision=0)


def load_notes() -> list[Note]:
    return load_notes_snapshot().notes


def save_notes(notes: list[Note], expected_revision: int | None = None) -> NotesSnapshot:
    with _exclusive_lock():
        current, _legacy = _read_snapshot()
        if expected_revision is not None and current.revision != expected_revision:
            raise NoteStorageConflictError()
        snapshot = NotesSnapshot(notes, current.revision + 1)
        _write_snapshot(snapshot)
        return snapshot
